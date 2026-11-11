import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { resolveVaultRoot, resolveWikiRoot } from './vault-resolver.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const vaultRoot = resolveVaultRoot();
const baseWiki = resolveWikiRoot(vaultRoot);
const adrDirs = [
  path.join(baseWiki, 'Projects', 'EnterpriseWorkHierarchy', '01 Architecture Decisions (ADR)'),
  path.join(baseWiki, 'Projects', 'SocialEngage', '01 Architecture Decisions (ADR)'),
  path.join(baseWiki, 'Projects', 'ADAP', 'ADRs'),
  path.join(baseWiki, 'Projects', 'ADAP', 'Architecture-Specs', 'RFCs')
].filter(d => fs.existsSync(d));
const conceptDir = path.join(baseWiki, 'Projects', 'SocialEngage', '06 Synthesis & Lessons Learned');

const args = process.argv.slice(2);
const isDryRun = !args.includes('--execute') && !args.includes('--write');

console.log('=== ADR Conceptual Grounding Engine ===');
console.log(`Mode: ${isDryRun ? '🔍 DRY RUN' : '⚡ LIVE EXECUTION'}\n`);

// 1. Index Canonical Concept Notes
const conceptFiles = fs.readdirSync(conceptDir).filter(f => f.startsWith('Concept-') && f.endsWith('.md'));
const concepts = conceptFiles.map(f => {
  const content = fs.readFileSync(path.join(conceptDir, f), 'utf8');
  const base = f.replace(/\.md$/, '');
  const titleMatch = content.match(/^title:\s*"Concept:\s*([^"]+)"/m) || content.match(/^#\s*Concept:\s*(.*)/m);
  const title = titleMatch ? titleMatch[1].trim() : base.replace(/^Concept-/, '');
  const slug = base.replace(/^Concept-/, '').toLowerCase();
  return { file: f, base, title, slug };
});

console.log(`Indexed ${concepts.length} canonical concepts.`);

// Exact Domain Cluster Mapping
const domainClusterToConcept = {
  'Platform Architecture & Foundations': 'platform-architecture-foundations',
  'Ingestion, Connectors & Rate Limits': 'ingestion-connectors-rate-limits',
  'Data Model, Storage & Archival': 'data-model-storage-archival',
  'Security, Identity & Multi-Tenancy': 'security-identity-multi-tenancy',
  'Derived Data, Health & Analytics': 'derived-data-health-analytics',
  'AI, NLP & Semantic Enrichment': 'ai-nlp-semantic-enrichment',
  'Eventing & Messaging Architecture': 'eventing-messaging-architecture',
  'RAG & Vector Semantic Search': 'rag-vector-semantic-search',
  'Outbound Publishing, Engagement & CRM': 'outbound-publishing-engagement-crm',
  'Self-Learning, Telemetry & Operations': 'self-learning-telemetry-operations',
  'Project Governance & Management': 'project-governance-management',
  'Delivery & User Stories': 'delivery-user-stories'
};

const dmbokToConcept = {
  'Data Governance': 'data-governance',
  'Data Architecture': 'data-architecture',
  'Data Modeling & Design': 'data-modeling-design',
  'Data Storage & Operations': 'data-storage-operations',
  'Data Security': 'data-security',
  'Data Integration & Interoperability': 'data-integration-interoperability',
  'Document & Content Management': 'document-content-management',
  'Reference & Master Data': 'reference-master-data',
  'Data Warehousing & BI (DW/BI)': 'data-warehousing-analytics-dw-bi',
  'Data Warehousing & Analytics (DW/BI)': 'data-warehousing-analytics-dw-bi',
  'Metadata Management': 'metadata-management',
  'Data Quality Management': 'data-quality-management'
};

// 2. High-Precision Concept Resolver
function findBestConcept(title, domainCluster, dmbokCategory, content) {
  const text = `${title} ${content.slice(0, 1000)}`.toLowerCase();

  // 1. High-precision architectural keyword overrides
  if (/\brbac\b/i.test(text) || /\brole-based\b/i.test(text)) {
    const c = concepts.find(c => c.slug === 'rbac');
    if (c) return c;
  }
  if (/\brls\b/i.test(text) || text.includes('row-level security') || text.includes('tenant isolation')) {
    const c = concepts.find(c => c.slug === 'security-identity-multi-tenancy');
    if (c) return c;
  }
  if (text.includes('envelope encryption') || text.includes('key vault')) {
    const c = concepts.find(c => c.slug === 'data-security');
    if (c) return c;
  }
  if (/\brag\b/i.test(text) || text.includes('vector search') || text.includes('embedding')) {
    const c = concepts.find(c => c.slug === 'rag-vector-semantic-search');
    if (c) return c;
  }
  if (text.includes('polypost') || text.includes('composer') || text.includes('social care')) {
    const c = concepts.find(c => c.slug === 'outbound-publishing-engagement-crm');
    if (c) return c;
  }

  // 2. Exact Domain Cluster Mapping
  if (domainCluster && domainClusterToConcept[domainCluster]) {
    const targetSlug = domainClusterToConcept[domainCluster];
    const c = concepts.find(c => c.slug === targetSlug);
    if (c) return c;
  }

  // 3. Exact DMBOK Category Mapping
  if (dmbokCategory && dmbokToConcept[dmbokCategory]) {
    const targetSlug = dmbokToConcept[dmbokCategory];
    const c = concepts.find(c => c.slug === targetSlug);
    if (c) return c;
  }

  // 4. Fallback: platform architecture foundations
  return concepts.find(c => c.slug === 'platform-architecture-foundations') || concepts[0];
}

// 3. Process All ADRs
let allAdrFiles = [];
for (const dir of adrDirs) {
  if (fs.existsSync(dir)) {
    const files = fs.readdirSync(dir).filter(f => f.endsWith('.md')).sort();
    for (const f of files) {
      allAdrFiles.push({ dir, file: f, path: path.join(dir, f) });
    }
  }
}
console.log(`Found ${allAdrFiles.length} ADR notes across ${adrDirs.length} project folders to evaluate.\n`);

let updatedCount = 0;
const mappingSamples = [];

for (const item of allAdrFiles) {
  const filePath = item.path;
  const f = item.file;
  let content = fs.readFileSync(filePath, 'utf8');

  // Extract frontmatter
  const fmMatch = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!fmMatch) continue;

  const meta = {};
  fmMatch[1].split(/\r?\n/).forEach(line => {
    const kv = line.match(/^([a-z_0-9]+):\s*"?([^"\r\n]+)"?/i);
    if (kv) meta[kv[1].trim()] = kv[2].trim();
  });

  const title = meta.title || f;
  const domainCluster = meta.domain_cluster || '';
  const dmbokCategory = meta.dmbok_category || '';

  const matchedConcept = findBestConcept(title, domainCluster, dmbokCategory, content);
  if (!matchedConcept) continue;

  const conceptLink = `[[${matchedConcept.base}|Concept: ${matchedConcept.title}]]`;

  mappingSamples.push({
    adr: f.slice(0, 38),
    domain: domainCluster.slice(0, 30),
    concept: matchedConcept.base
  });

  // Inject into frontmatter if not present
  let newFm = fmMatch[1];
  if (!newFm.includes('concept_grounding:')) {
    newFm = newFm.trim() + `\nconcept_grounding: "${conceptLink}"\n`;
  } else {
    newFm = newFm.replace(/concept_grounding:\s*"[^"]*"/, `concept_grounding: "${conceptLink}"`);
  }

  // Inject into Traceability Callout if present
  let body = content.slice(fmMatch[0].length);
  if (body.includes('> [!NOTE] 🔗') && (body.includes('Traceability') || body.includes('Mesh') || body.includes('Quad'))) {
    body = body.replace(/> \[!NOTE\] 🔗[^\n]*\n([\s\S]*?)(?=\n\n|\n#[^#]|$)/, (fullCallout) => {
      const cleanCallout = fullCallout.replace(/\n>\s*-\s*🧠\s*\*\*Conceptual & Standards Grounding:[^\n]*/g, '');
      return cleanCallout.trimEnd() + `\n> - 🧠 **Conceptual & Standards Grounding:** ${conceptLink}`;
    });
  } else if (!body.includes('Conceptual & Standards Grounding')) {
    // If no callout, inject callout before title
    const titleMatch = body.match(/^(\s*#\s+ADR.*)/m);
    if (titleMatch) {
      const callout = `\n> [!NOTE] 🔗 **Conceptual & Standards Grounding**\n> - 🧠 **Governing Enterprise Concept:** ${conceptLink} *(Aligned with DMBOK2, TOGAF & NIST)*\n\n`;
      body = body.replace(titleMatch[1], callout + titleMatch[1]);
    }
  }

  const updatedContent = `---\n${newFm.trim()}\n---${body}`;

  if (!isDryRun) {
    fs.writeFileSync(filePath, updatedContent, 'utf8');
  }
  updatedCount++;
}

console.log('Sample High-Precision Concept Mappings:');
console.table(mappingSamples.slice(0, 15));

console.log(`\n✅ Summary: Grounded ${updatedCount} / ${allAdrFiles.length} ADRs to Canonical Concepts.`);
if (isDryRun) {
  console.log('👉 To execute live updates, run: node scripts/ground-adrs-to-concepts.mjs --execute');
} else {
  console.log('🎉 LIVE UPDATES COMPLETE: All ADRs across SocialEngage and ADPA now possess direct bidirectional concept grounding!');
}
