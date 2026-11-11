import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { reclassifyVaultDmbokTaxonomy } from './taxonomy-router.mjs';
import { resolveVaultRoot, resolveWikiRoot } from './vault-resolver.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const vaultRoot = resolveVaultRoot();
const wikiRoot = resolveWikiRoot(vaultRoot);

console.log('======================================================');
console.log('🧠 SECOND BRAIN COMPREHENSIVE HEALING PIPELINE');
console.log('======================================================\n');

// ----------------------------------------------------
// 1. SCAN AND INDEX CANONICAL NOTES & ALIASES
// ----------------------------------------------------
console.log('🔍 Step 1: Indexing all canonical notes and aliases across wiki/ ...');

function scanMds(dir) {
  let list = [];
  if (!fs.existsSync(dir)) return list;
  for (const f of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, f.name);
    if (f.isDirectory()) list = list.concat(scanMds(full));
    else if (f.name.endsWith('.md')) list.push(full);
  }
  return list;
}

const allMds = scanMds(wikiRoot);
console.log(`  Found ${allMds.length} total markdown notes.`);

const aliasToCanonical = new Map(); // lowercase alias -> canonical baseName (without .md)

for (const p of allMds) {
  const content = fs.readFileSync(p, 'utf8');
  const base = path.basename(p, '.md');
  const rel = path.relative(wikiRoot, p).replace(/\\/g, '/').replace(/\.md$/, '');

  aliasToCanonical.set(base.toLowerCase(), base);
  aliasToCanonical.set(rel.toLowerCase(), base);

  // Frontmatter parsing
  const fmMatch = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (fmMatch) {
    const lines = fmMatch[1].split(/\r?\n/);
    for (const line of lines) {
      const artMatch = line.match(/^artifact_id:\s*"?([^"\r\n]+)"?/);
      if (artMatch) {
        aliasToCanonical.set(artMatch[1].trim().toLowerCase(), base);
      }
      const aliasMatch = line.match(/^\s*-\s*"?([^"\r\n]+)"?/);
      if (aliasMatch) {
        aliasToCanonical.set(aliasMatch[1].trim().toLowerCase(), base);
      }
    }
  }

  // Epic patterns: epic-6-tenant-admin-ui -> epic-6, epic 6
  const epicMatch = base.match(/^epic-(\d+)/i);
  if (epicMatch) {
    aliasToCanonical.set(`epic-${epicMatch[1]}`.toLowerCase(), base);
    aliasToCanonical.set(`epic ${epicMatch[1]}`.toLowerCase(), base);
  }

  // ADR patterns: 0054-tenant-... -> adr-0054, adr-54, adr 0054, 0054
  const adrMatch = base.match(/^(\d{4})/);
  if (adrMatch) {
    const num = adrMatch[1];
    const intNum = parseInt(num, 10);
    aliasToCanonical.set(`adr-${num}`.toLowerCase(), base);
    aliasToCanonical.set(`adr-${intNum}`.toLowerCase(), base);
    aliasToCanonical.set(`adr ${num}`.toLowerCase(), base);
    aliasToCanonical.set(`adr ${intNum}`.toLowerCase(), base);
  }

  // TDS patterns: TDS-0054-... -> tds-0054, tds-54, tds 0054
  const tdsMatch = base.match(/^tds-(\d{4})/i);
  if (tdsMatch) {
    const num = tdsMatch[1];
    const intNum = parseInt(num, 10);
    aliasToCanonical.set(`tds-${num}`.toLowerCase(), base);
    aliasToCanonical.set(`tds-${intNum}`.toLowerCase(), base);
    aliasToCanonical.set(`tds ${num}`.toLowerCase(), base);
    aliasToCanonical.set(`tds ${intNum}`.toLowerCase(), base);
  }

  // BRD patterns: BRD-0054-... -> brd-0054, brd-54
  const brdMatch = base.match(/^brd-(\d{4})/i);
  if (brdMatch) {
    const num = brdMatch[1];
    const intNum = parseInt(num, 10);
    aliasToCanonical.set(`brd-${num}`.toLowerCase(), base);
    aliasToCanonical.set(`brd-${intNum}`.toLowerCase(), base);
  }

  // FDD patterns: FDD-0054-... -> fdd-0054, fdd-54
  const fddMatch = base.match(/^fdd-(\d{4})/i);
  if (fddMatch) {
    const num = fddMatch[1];
    const intNum = parseInt(num, 10);
    aliasToCanonical.set(`fdd-${num}`.toLowerCase(), base);
    aliasToCanonical.set(`fdd-${intNum}`.toLowerCase(), base);
  }
}

console.log(`  Indexed ${aliasToCanonical.size} alias/artifact resolution rules.\n`);

// ----------------------------------------------------
// 2. HEAL WIKILINKS IN ALL NOTES
// ----------------------------------------------------
console.log('🩹 Step 2: Healing ambiguous/alias wikilinks to canonical note basenames...');

let filesModifiedCount = 0;
let linksHealedCount = 0;

for (const p of allMds) {
  let content = fs.readFileSync(p, 'utf8');
  let fileChanged = false;

  // Replace [[target#heading|label]] or [[target|label]] or [[target]]
  const newContent = content.replace(/\[\[([^\]|#]+)(#[^\]|]+)?(\|[^\]]+)?\]\]/g, (match, rawTarget, section, rawLabel) => {
    const target = rawTarget.trim();
    if (!target) return match;

    const cleanTarget = target.replace(/\\/g, '/').replace(/\.md$/, '').toLowerCase();
    const baseTarget = path.basename(cleanTarget);

    let canonical = aliasToCanonical.get(cleanTarget) || aliasToCanonical.get(baseTarget);
    if (!canonical) return match; // Cannot resolve, leave intact

    // If target already equals canonical, nothing to heal
    if (baseTarget === canonical.toLowerCase()) return match;

    // Build healed link preserving label and section
    const sec = section || '';
    const label = rawLabel ? rawLabel.slice(1) : target;

    linksHealedCount++;
    fileChanged = true;
    return `[[${canonical}${sec}|${label}]]`;
  });

  if (fileChanged) {
    fs.writeFileSync(p, newContent, 'utf8');
    filesModifiedCount++;
  }
}

console.log(`  ✅ Healed ${linksHealedCount} wikilinks across ${filesModifiedCount} files.\n`);

// ----------------------------------------------------
// 3. NORMALIZE FRONTMATTER DMBOK TAXONOMY STRINGS
// ----------------------------------------------------
console.log('🏷️ Step 3: Normalizing DMBOK frontmatter taxonomy to ONTOLOGY.json (v1.0.0-LOCKED)...');

let taxonomyFixCount = 0;
const dmbokFixes = [
  { bad: /dmbok_category:\s*"Data Security & Governance"/g, good: 'dmbok_category: "Data Security"' },
  { bad: /dmbok_category:\s*"Data Warehousing & Analytics \(DW-BI\)"/g, good: 'dmbok_category: "Data Warehousing & Analytics (DW/BI)"' },
  { bad: /dmbok_category:\s*"Data Warehousing & Business Intelligence"/g, good: 'dmbok_category: "Data Warehousing & Analytics (DW/BI)"' },
  { bad: /dmbok_category:\s*"Data Operations"/g, good: 'dmbok_category: "Data Storage & Operations"' }
];

for (const p of allMds) {
  let content = fs.readFileSync(p, 'utf8');
  let changed = false;

  for (const fix of dmbokFixes) {
    if (fix.bad.test(content)) {
      content = content.replace(fix.bad, fix.good);
      changed = true;
      taxonomyFixCount++;
    }
  }

  if (changed) {
    fs.writeFileSync(p, content, 'utf8');
  }
}

console.log(`  ✅ Normalized ${taxonomyFixCount} non-standard taxonomy attributes.\n`);

// ----------------------------------------------------
// 4. PREVENT GENERIC DATA GOVERNANCE DEFAULTING
// ----------------------------------------------------
console.log('🧭 Step 4: Reclassifying generic "Data Governance" notes via Taxonomy Router...');
const reclassResult = reclassifyVaultDmbokTaxonomy(vaultRoot, false);
console.log(`  ✅ Reclassified ${reclassResult.reclassified} notes from generic Data Governance to specific DMBOK areas.`);
if (reclassResult.reclassified > 0) {
  for (const [area, count] of Object.entries(reclassResult.breakdown)) {
    console.log(`     - ${area}: ${count} notes`);
  }
}
console.log('');

console.log('🎉 Healing Pass complete.');
