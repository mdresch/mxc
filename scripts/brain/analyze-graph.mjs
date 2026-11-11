import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { resolveVaultRoot, resolveWikiRoot } from './vault-resolver.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const vaultRoot = resolveVaultRoot();
const wikiRoot = resolveWikiRoot(vaultRoot);

function scanDir(dir) {
  let files = [];
  fs.readdirSync(dir).forEach(f => {
    const p = path.join(dir, f);
    if (fs.statSync(p).isDirectory()) {
      files = files.concat(scanDir(p));
    } else if (f.endsWith('.md')) {
      files.push(p);
    }
  });
  return files;
}

const allFiles = scanDir(wikiRoot);

const nodes = new Map();
const nodesByBaseName = new Map();
const typeDistribution = {};
const domainDistribution = {};
const dmbokDistribution = {};
const outgoingMap = new Map();
const incomingMap = new Map();

for (const f of allFiles) {
  const content = fs.readFileSync(f, 'utf8');
  const relPath = path.relative(wikiRoot, f).replace(/\\/g, '/');
  const baseName = path.basename(f, '.md');

  // Frontmatter extraction
  const fmMatch = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  const meta = {};
  if (fmMatch) {
    fmMatch[1].split(/\r?\n/).forEach(line => {
      const kv = line.match(/^([a-z_0-9]+):\s*"?([^"\r\n]+)"?/i);
      if (kv) meta[kv[1].trim()] = kv[2].trim();
    });
  }

  let type = meta.type;
  if (!type) {
    if (relPath.includes('_MOCs')) type = 'moc';
    else if (relPath.includes('System')) type = 'system';
    else if (relPath.includes('01 Architecture Decisions')) type = 'adr';
    else if (relPath.includes('02 Business Requirements')) type = 'brd';
    else if (relPath.includes('03 Functional Design')) type = 'fdd';
    else if (relPath.includes('04 User Stories')) type = 'story';
    else if (relPath.includes('06 Synthesis')) type = baseName.startsWith('Concept-') ? 'concept' : 'synthesis';
    else type = 'note';
  }
  type = type.toLowerCase();
  typeDistribution[type] = (typeDistribution[type] || 0) + 1;

  if (meta.domain_cluster) {
    domainDistribution[meta.domain_cluster] = (domainDistribution[meta.domain_cluster] || 0) + 1;
  }
  if (meta.dmbok_category) {
    dmbokDistribution[meta.dmbok_category] = (dmbokDistribution[meta.dmbok_category] || 0) + 1;
  }

  const key = relPath.replace(/\.md$/i, '').toLowerCase();
  nodes.set(key, { baseName, relPath, meta, type });
  outgoingMap.set(key, new Set());
  if (!incomingMap.has(key)) incomingMap.set(key, new Set());

  const baseKey = baseName.toLowerCase();
  if (!nodesByBaseName.has(baseKey)) nodesByBaseName.set(baseKey, new Set());
  nodesByBaseName.get(baseKey).add(key);
}

function resolveNodeKey(target) {
  const normalizedTarget = target
    .replace(/\\/g, '/')
    .replace(/^wiki\//i, '')
    .replace(/\.md$/i, '')
    .replace(/^\/+/, '')
    .toLowerCase();
  if (nodes.has(normalizedTarget)) return normalizedTarget;

  const baseName = path.posix.basename(normalizedTarget);
  const matches = nodesByBaseName.get(baseName);
  return matches?.size === 1 ? matches.values().next().value : null;
}

// Second pass: Extract links
const linkCounts = { totalWikilinks: 0, internalResolved: 0, unresolved: 0 };
const linkRegex = /\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]/g;

for (const f of allFiles) {
  const content = fs.readFileSync(f, 'utf8');
  const sourceKey = path.relative(wikiRoot, f).replace(/\\/g, '/').replace(/\.md$/i, '').toLowerCase();
  let m;
  while ((m = linkRegex.exec(content)) !== null) {
    const rawTarget = m[1].trim();
    const targetKey = resolveNodeKey(rawTarget);
    linkCounts.totalWikilinks++;

    if (targetKey) {
      outgoingMap.get(sourceKey).add(targetKey);
      linkCounts.internalResolved++;
      incomingMap.get(targetKey).add(sourceKey);
    } else {
      linkCounts.unresolved++;
    }

  }
}

// Calculate Metrics
const hubArray = [];
for (const [nodeKey, inSet] of incomingMap.entries()) {
  const node = nodes.get(nodeKey);
  if (node) {
    const outSet = outgoingMap.get(nodeKey) || new Set();
    hubArray.push({
      name: node.baseName,
      type: node.type,
      relPath: node.relPath,
      inDegree: inSet.size,
      outDegree: outSet.size,
      totalDegree: inSet.size + outSet.size
    });
  }
}

hubArray.sort((a, b) => b.totalDegree - a.totalDegree);

// Concept Notes specifically
const conceptNotes = hubArray.filter(h => h.type === 'concept' || h.name.startsWith('Concept-'));

// ADRs and their concept links
let adrsWithConceptLinks = 0;
let totalADRs = 0;
for (const [nodeKey, node] of nodes.entries()) {
  if (node.type === 'adr') {
    totalADRs++;
    const outSet = outgoingMap.get(nodeKey) || new Set();
    const hasConcept = [...outSet].some(target => {
      const targetNode = nodes.get(target);
      return targetNode && (targetNode.type === 'concept' || targetNode.baseName.startsWith('Concept-'));
    });
    if (hasConcept) adrsWithConceptLinks++;
  }
}

// Quarantine Stats
const quarantineDir = path.join(vaultRoot, 'raw', 'quarantined-concepts');
let quarantinedCount = 0;
if (fs.existsSync(quarantineDir)) {
  quarantinedCount = fs.readdirSync(quarantineDir).filter(f => f.endsWith('.md')).length;
}

const report = {
  vaultStats: {
    totalMarkdownFiles: allFiles.length,
    totalWikilinks: linkCounts.totalWikilinks,
    internalResolvedEdges: linkCounts.internalResolved,
    unresolvedReferences: linkCounts.unresolved,
    graphDensity: (linkCounts.internalResolved / (allFiles.length * (allFiles.length - 1))).toFixed(5),
    averageDegree: (linkCounts.internalResolved / allFiles.length).toFixed(2)
  },
  typeDistribution,
  domainDistribution,
  dmbokDistribution,
  enrichmentImpact: {
    canonicalConceptCount: conceptNotes.length,
    quarantinedPseudoConcepts: quarantinedCount,
    adrsWithConceptGrounding: `${adrsWithConceptLinks} / ${totalADRs} (${((adrsWithConceptLinks / totalADRs) * 100).toFixed(1)}%)`,
    totalConceptLinks: conceptNotes.reduce((acc, c) => acc + c.totalDegree, 0)
  },
  topMasterHubs: hubArray.slice(0, 12),
  topConceptHubs: conceptNotes.sort((a, b) => b.totalDegree - a.totalDegree).slice(0, 15)
};

console.log('=== GRAPH ENRICHMENT AUDIT & TOPOLOGY ANALYSIS ===\n');
console.log('Vault Totals:');
console.log(`  Total Notes:          ${report.vaultStats.totalMarkdownFiles}`);
console.log(`  Total Wikilinks:      ${report.vaultStats.totalWikilinks}`);
console.log(`  Resolved Edges:       ${report.vaultStats.internalResolvedEdges}`);
console.log(`  Average Note Degree:  ${report.vaultStats.averageDegree} connections/note\n`);

console.log('Node Type Distribution:');
console.table(report.typeDistribution);

console.log('DAMA-DMBOK Knowledge Area Coverage:');
console.table(report.dmbokDistribution);

console.log('Enrichment Impact & Semantic Health:');
console.log(`  Canonical Concepts:   ${report.enrichmentImpact.canonicalConceptCount}`);
console.log(`  Quarantined Noise:    ${report.enrichmentImpact.quarantinedPseudoConcepts} (git SHAs, variable names isolated)`);
console.log(`  ADR Concept Grounding:${report.enrichmentImpact.adrsWithConceptGrounding}`);
console.log(`  Total Concept Edges:  ${report.enrichmentImpact.totalConceptLinks} active structural connections\n`);

console.log('Top 12 Most Connected Graph Hubs (Degree Centrality):');
console.table(report.topMasterHubs.map(h => ({
  Name: h.name.slice(0, 45),
  Type: h.type,
  InDegree: h.inDegree,
  OutDegree: h.outDegree,
  Total: h.totalDegree
})));

console.log('\nTop 15 Most Influential Canonical Concept Nodes:');
console.table(report.topConceptHubs.map(c => ({
  Concept: c.name.slice(0, 40),
  InDegree: c.inDegree,
  OutDegree: c.outDegree,
  TotalEdges: c.totalDegree
})));

// Save full report JSON
fs.writeFileSync(path.join(vaultRoot, 'raw', 'graph-enrichment-analysis.json'), JSON.stringify(report, null, 2), 'utf8');
console.log('\n✅ Report saved to raw/graph-enrichment-analysis.json');
