import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { resolveVaultRoot, resolveWikiRoot } from './vault-resolver.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const vaultRoot = resolveVaultRoot();
const wikiRoot = resolveWikiRoot(vaultRoot);
const systemDir = path.join(wikiRoot, 'System');

const failOnDrift = process.argv.includes('--fail') || process.argv.includes('--fail-on-drift');

if (!fs.existsSync(systemDir)) fs.mkdirSync(systemDir, { recursive: true });

const versionMetaPath = path.join(vaultRoot, 'vault-version.json');
const packageJsonPath = path.join(vaultRoot, 'package.json');
const ontologyPath = path.join(vaultRoot, 'ONTOLOGY.json');
const pmOntologyPath = path.join(vaultRoot, 'PROJECT-MANAGEMENT-ONTOLOGY.json');
const claudeMdPath = path.join(vaultRoot, 'CLAUDE.md');

function loadJson(p) {
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

function scanMds(dir) {
  let list = [];
  if (!fs.existsSync(dir)) return list;
  for (const f of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, f.name);
    if (f.isDirectory()) {
      if (!['.git', 'node_modules', '.trash'].includes(f.name)) {
        list = list.concat(scanMds(full));
      }
    } else if (f.name.endsWith('.md')) {
      list.push(full);
    }
  }
  return list;
}

function parseFrontmatter(content) {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return null;
  const raw = match[1];
  const fm = {};
  const lines = raw.split(/\r?\n/);
  let currentKey = null;
  for (const line of lines) {
    const keyVal = line.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (keyVal && !line.trim().startsWith('-')) {
      currentKey = keyVal[1];
      let val = keyVal[2].trim();
      if (val.startsWith('"') && val.endsWith('"')) val = val.slice(1, -1);
      if (val === '') {
        fm[currentKey] = [];
      } else {
        if (!Array.isArray(fm[currentKey])) fm[currentKey] = val;
      }
    } else if (currentKey && Array.isArray(fm[currentKey]) && line.trim().startsWith('-')) {
      let item = line.trim().slice(1).trim();
      if (item.startsWith('"') && item.endsWith('"')) item = item.slice(1, -1);
      fm[currentKey].push(item);
    }
  }
  return fm;
}

function toIsoDate(d) {
  if (!d) return null;
  try {
    return new Date(d).toISOString();
  } catch {
    return null;
  }
}

// Load canonical version metadata
const vaultVersion = loadJson(versionMetaPath);
const packageJson = loadJson(packageJsonPath);
const ontology = loadJson(ontologyPath);
const pmOntology = loadJson(pmOntologyPath);
const claudeMd = fs.readFileSync(claudeMdPath, 'utf8');

const canonicalVersions = {
  vault: vaultVersion.vault_version,
  ontology: vaultVersion.ontology_version,
  pm_ontology: vaultVersion.pm_ontology_version,
  package: vaultVersion.expected_package_version,
  claude: vaultVersion.expected_claude_version
};

const actualVersions = {
  package: packageJson.version,
  ontology: ontology.version,
  pm_ontology: pmOntology.version,
  claude: (claudeMd.match(/v(\d+\.\d+\.\d+)-LOCKED/) || [])[1]
};

const driftReport = {
  generated_at: new Date().toISOString(),
  canonical_versions: canonicalVersions,
  actual_versions: actualVersions,
  active_drifts: [],
  acknowledged_drifts: [],
  observations: [],
  source_mtime_drifts: []
};

const acknowledged = vaultVersion.acknowledged_version_drifts || {};

// 1. Version drift across project files
const versionChecks = [
  { key: 'package_version', canonical: canonicalVersions.package, actual: actualVersions.package, location: 'package.json' },
  { key: 'ontology_version', canonical: canonicalVersions.ontology, actual: actualVersions.ontology, location: 'ONTOLOGY.json' },
  { key: 'pm_ontology_version', canonical: canonicalVersions.pm_ontology, actual: actualVersions.pm_ontology, location: 'PROJECT-MANAGEMENT-ONTOLOGY.json' },
  { key: 'claude_md_frozen_version', canonical: canonicalVersions.claude, actual: actualVersions.claude, location: 'CLAUDE.md' }
];

for (const check of versionChecks) {
  if (check.actual !== check.canonical) {
    const ack = acknowledged[check.key];
    const isAcknowledged = ack && ack.actual_version === check.actual && ack.expected_version === check.canonical;
    const drift = {
      id: check.key,
      category: 'version',
      severity: isAcknowledged ? 'acknowledged' : 'active',
      location: check.location,
      expected: check.canonical,
      actual: check.actual,
      message: `${check.location} is at ${check.actual}, expected ${check.canonical}`
    };
    if (isAcknowledged) {
      drift.rationale = ack.rationale;
      driftReport.acknowledged_drifts.push(drift);
    } else {
      driftReport.active_drifts.push(drift);
    }
  }
}

// 2. Page-level version and source mtime drift
function byLongestPrefixFirst([a], [b]) { return b.length - a.length; }

const sourceRepoRoots = vaultVersion.source_repo_roots || {};
const sourceRepoRootEntries = Object.entries(sourceRepoRoots).sort(byLongestPrefixFirst);

// Some source_document values encode a path nested inside the source repo itself
// (e.g. "project-progress-dashboard/..." lives under D:\Source\socialengage, not the
// vault). Checking the source_document's own prefix is more reliable for these than
// inferring the repo from where the compiled page happens to live in the vault.
const sourceDocumentRepoRoots = vaultVersion.source_document_repo_roots || {};
const sourceDocumentRepoRootEntries = Object.entries(sourceDocumentRepoRoots).sort(byLongestPrefixFirst);

function normalizeRoot(root) {
  return path.isAbsolute(root) ? root : path.resolve(vaultRoot, root);
}

function resolveSourceRepoRoot(relPath, sourceRel) {
  for (const [prefix, root] of sourceDocumentRepoRootEntries) {
    if (sourceRel === prefix || sourceRel.startsWith(`${prefix}/`)) return normalizeRoot(root);
  }
  for (const [prefix, root] of sourceRepoRootEntries) {
    if (relPath === prefix || relPath.startsWith(`${prefix}/`)) return normalizeRoot(root);
  }
  return vaultRoot;
}

// Some source_document values were written with a vault-side folder name that never
// existed in the source repo (e.g. compiled ADAP ADR pages store "Projects/ADAP/ADRs/..."
// but the adpa repo actually keeps them at "docs/07-architecture/..."). Rather than guess
// at a fix, only apply an explicit, verified rewrite from vault-version.json - each entry
// must map to a single unambiguous location in the source repo. Do NOT add an entry here
// for a path pattern that fans out to multiple possible source files (e.g. ADPA's
// per-managed-project BRD/story templates, which are duplicated across ~145 sub-projects
// with no recorded provenance for which one a given vault page came from) - leave those
// as unresolved source_missing drift until the ingestion step records real provenance.
const sourceDocumentPathRewrites = Object.entries(vaultVersion.source_document_path_rewrites || {})
  .sort(byLongestPrefixFirst);

function rewriteSourceDocumentPath(sourceRel) {
  for (const [from, to] of sourceDocumentPathRewrites) {
    if (sourceRel.startsWith(from)) return to + sourceRel.slice(from.length);
  }
  return sourceRel;
}

// A source_document is "self-referencing" when it points back at the very page that
// declares it (i.e. the page was authored directly in the vault, not compiled from an
// external repo). Different generators have written this two ways: some prefix the
// vault-relative path with "wiki/" (resolved from vaultRoot), others store it bare
// (resolved from wikiRoot) - so check both interpretations against the page's own path
// rather than pattern-matching a specific prefix.
function isSelfReferencing(sourceRel, absolutePagePath) {
  const candidates = [path.resolve(vaultRoot, sourceRel), path.resolve(wikiRoot, sourceRel)];
  return candidates.includes(path.resolve(absolutePagePath));
}

const ontologyMtime = fs.statSync(ontologyPath).mtime;
const allMds = scanMds(wikiRoot);

for (const p of allMds) {
  const content = fs.readFileSync(p, 'utf8');
  const fm = parseFrontmatter(content);
  if (!fm || !fm.version) continue;

  const relPath = path.relative(wikiRoot, p).replace(/\\/g, '/');

  if (fm.version !== canonicalVersions.ontology) {
    driftReport.observations.push({
      category: 'page_version',
      severity: 'warning',
      file: relPath,
      message: `Page version ${fm.version} does not match canonical ontology version ${canonicalVersions.ontology}`
    });
  }

  const pageModifiedAt = toIsoDate(fm.modified_at);
  if (pageModifiedAt) {
    const pageModified = new Date(pageModifiedAt);
    if (ontologyMtime > pageModified) {
      driftReport.source_mtime_drifts.push({
        category: 'ontology_newer_than_page',
        severity: 'warning',
        file: relPath,
        message: `ONTOLOGY.json (${ontologyMtime.toISOString()}) is newer than page modified_at (${pageModifiedAt})`
      });
    }
  }

  if (fm.source_document && !isSelfReferencing(fm.source_document, p)) {
    const sourceRel = rewriteSourceDocumentPath(fm.source_document);
    const repoRoot = resolveSourceRepoRoot(relPath, sourceRel);
    const sourcePath = path.join(repoRoot, sourceRel);

    if (!fs.existsSync(sourcePath)) {
      driftReport.source_mtime_drifts.push({
        category: 'source_missing',
        severity: 'warning',
        file: relPath,
        source_document: sourceRel,
        message: `Source document ${sourceRel} not found at ${sourcePath}`
      });
    } else {
      const sourceMtime = fs.statSync(sourcePath).mtime;
      if (pageModifiedAt && sourceMtime > new Date(pageModifiedAt)) {
        driftReport.source_mtime_drifts.push({
          category: 'page_stale',
          severity: 'active',
          file: relPath,
          source_document: sourceRel,
          message: `Source document ${sourceRel} (${sourceMtime.toISOString()}) is newer than page modified_at (${pageModifiedAt})`
        });
      }
    }
  }
}

// Update vault-version.json with drift status
vaultVersion.last_drift_check = driftReport.generated_at;
vaultVersion.drift_status = driftReport.active_drifts.length === 0 ? 'clean' : 'drift';
fs.writeFileSync(versionMetaPath, JSON.stringify(vaultVersion, null, 2) + '\n', 'utf8');

// Generate markdown report
const activeRows = driftReport.active_drifts.map(d =>
  `| **${d.id}** | ${d.category} | ${d.severity} | ${d.location} | ${d.expected} | ${d.actual} | ${d.message} |`
).join('\n') || '| — | — | — | — | — | — | No active version drifts |';

const ackRows = driftReport.acknowledged_drifts.map(d =>
  `| **${d.id}** | ${d.category} | ${d.location} | ${d.expected} | ${d.actual} | ${d.rationale || 'Acknowledged'} |`
).join('\n') || '| — | — | — | — | — | — |';

const sourceRows = driftReport.source_mtime_drifts.slice(0, 100).map(d =>
  `| ${d.file} | ${d.category} | ${d.severity} | ${d.message} |`
).join('\n') || '| — | — | — | — |';

const overflowNote = driftReport.source_mtime_drifts.length > 100
  ? `\n> Showing first 100 of ${driftReport.source_mtime_drifts.length} source mtime observations.`
  : '';

const sourceDriftsByCategory = driftReport.source_mtime_drifts.reduce((acc, d) => {
  acc[d.category] = (acc[d.category] || 0) + 1;
  return acc;
}, {});

const sourceCategoryRows = Object.entries(sourceDriftsByCategory)
  .sort((a, b) => b[1] - a[1])
  .map(([category, count]) => `  - **${category}:** ${count}`)
  .join('\n') || '  - (none)';

const reportMd = `---
title: "Brain Version & Source Drift Detection Report"
artifact_id: "DRIFT-REPORT"
entity_id: "drift-report"
type: "telemetry"
status: "Generated"
domain_cluster: "Self-Learning / Telemetry / Operations"
dmbok_category: "Data Quality Management"
pmbok_category: "Integration Management"
babok_category: "Requirements Analysis & Design Definition (RADD)"
tags:
  - telemetry
  - drift
  - version
  - git
  - project/socialengage
version: "${canonicalVersions.ontology}"
modified_at: "${driftReport.generated_at}"
---

# Brain Version & Source Drift Detection Report

> Generated by \`scripts/brain-drift-detection.mjs\` at ${driftReport.generated_at}

## Canonical Versions

| Dimension | Canonical Version |
|---|---|
| Vault | ${canonicalVersions.vault} |
| Ontology | ${canonicalVersions.ontology} |
| PM Ontology | ${canonicalVersions.pm_ontology} |
| package.json | ${canonicalVersions.package} |
| CLAUDE.md frozen version | ${canonicalVersions.claude} |

## Actual Versions

| File | Actual Version |
|---|---|
| package.json | ${actualVersions.package} |
| ONTOLOGY.json | ${actualVersions.ontology} |
| PROJECT-MANAGEMENT-ONTOLOGY.json | ${actualVersions.pm_ontology} |
| CLAUDE.md | ${actualVersions.claude || 'not parsed'} |

## Active Version Drifts

| ID | Category | Severity | Location | Expected | Actual | Message |
|---|---|---|---|---|---|---|
${activeRows}

## Acknowledged Version Drifts

| ID | Category | Location | Expected | Actual | Rationale |
|---|---|---|---|---|---|
${ackRows}

## Source Mtime Drifts

| File | Category | Severity | Message |
|---|---|---|---|
${sourceRows}
${overflowNote}

## Summary

- **Active drifts:** ${driftReport.active_drifts.length}
- **Acknowledged drifts:** ${driftReport.acknowledged_drifts.length}
- **Page-version observations:** ${driftReport.observations.length}
- **Source-mtime observations:** ${driftReport.source_mtime_drifts.length}
${sourceCategoryRows}
- **Overall status:** ${driftReport.active_drifts.length === 0 ? '🟢 Clean (no unacknowledged drifts)' : '🔴 Drift detected'}
`;

fs.writeFileSync(path.join(systemDir, 'Brain-Version-Drift-Report.md'), reportMd, 'utf8');

console.log('Brain drift detection complete.');
console.log(`  Active drifts: ${driftReport.active_drifts.length}`);
console.log(`  Acknowledged drifts: ${driftReport.acknowledged_drifts.length}`);
console.log(`  Page-version observations: ${driftReport.observations.length}`);
console.log(`  Source-mtime observations: ${driftReport.source_mtime_drifts.length}`);
for (const [category, count] of Object.entries(sourceDriftsByCategory).sort((a, b) => b[1] - a[1])) {
  console.log(`    ${category}: ${count}`);
}
console.log('  Report saved to wiki/System/Brain-Version-Drift-Report.md');

if (failOnDrift && driftReport.active_drifts.length > 0) {
  console.error('Failing commit because unacknowledged drifts were detected.');
  process.exit(1);
}
