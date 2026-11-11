/**
 * vault-ingestion.mjs
 * Phase 4: Vault Ingestion & MOC Recompilation Module.
 *
 * Implements:
 * - Action 1: Atomic Concept Note Generator (STEP-4.1)
 * - Action 2: MOC Hub Recompiler (STEP-4.2)
 * - Action 3: Bidirectional Semantic Edge Linker & Metric Incrementer (STEP-4.3)
 * - Standalone CLI Runner & Queue Dequeuer
 */

import fs from 'fs';
import path from 'path';
import { resolveDmbokTaxonomy } from './taxonomy-router.mjs';
import { resolveVaultRoot, resolveWikiRoot } from './vault-resolver.mjs';

const VAULT_ROOT = resolveVaultRoot();
const BASE_WIKI = resolveWikiRoot(VAULT_ROOT);
const SYNTHESIS_DIR = path.join(BASE_WIKI, 'Projects', 'SocialEngage', '06 Synthesis & Lessons Learned');
const MOCS_DIR = path.join(BASE_WIKI, '_MOCs');
const QUEUE_PATH = path.join(VAULT_ROOT, 'raw', 'enrichment-queue.json');

/**
 * STEP-4.1: Construct Complete Markdown Concept Note adhering to ONTOLOGY.json
 */
export function generateConceptNoteMarkdown(payload) {
  const frontmatterObj = {
    title: payload.title,
    artifact_id: payload.artifact_id,
    entity_id: payload.entity_id,
    version: payload.version || '1.1.0',
    source_document: `Projects/SocialEngage/06 Synthesis & Lessons Learned/${payload.artifact_id}.md`,
    created_at: payload.created_at || new Date().toISOString(),
    modified_at: new Date().toISOString(),
    authority_level: payload.authority_level || 1,
    confidence_score: payload.confidence_score || 0.95,
    type: 'concept',
    pm_class: 'DomainKnowledge',
    pm_subclass: 'Concept',
    pm_relationships: payload.pm_relationships || ['influences', 'groundedIn', 'compliesWith'],
    domain_cluster: payload.domain_cluster || 'Platform Architecture & Foundations',
    dmbok_category: payload.dmbok_category || resolveDmbokTaxonomy(payload).category,
    pmbok_category: payload.pmbok_category || 'Integration Management',
    babok_category: payload.babok_category || 'Business Analysis Planning & Monitoring',
    status: payload.status || 'Active',
    aliases: [
      payload.title,
      payload.title.replace(/^Concept:\s*/, ''),
      payload.artifact_id,
      ...(payload.aliases || [])
    ].filter((v, i, a) => a.indexOf(v) === i),
    tags: [
      'concept',
      payload.slug,
      `dmbok/${(payload.dmbok_category || 'data-architecture').toLowerCase().replace(/[^a-z0-9]+/g, '-')}`,
      'best-practices',
      'project/socialengage'
    ],
    source_urls: payload.source_urls || [],
    last_enriched_at: new Date().toISOString(),
    best_practices: (payload.best_practices || []).map(b => typeof b === 'string' ? b : b.title),
    anti_patterns: (payload.anti_patterns || []).map(a => typeof a === 'string' ? a : a.title),
    operational_kpis: (payload.operational_kpis || []).map(k => typeof k === 'string' ? k : `${k.name}: ${k.target}`),
    standards_alignment: (payload.standards_alignment || []).map(s => typeof s === 'string' ? s : `${s.framework} - ${s.mapping}`)
  };

  // Build Frontmatter YAML
  const yamlLines = ['---'];
  for (const [key, value] of Object.entries(frontmatterObj)) {
    if (Array.isArray(value)) {
      yamlLines.push(`${key}:`);
      for (const item of value) {
        yamlLines.push(`  - "${item.replace(/"/g, '\\"')}"`);
      }
    } else if (typeof value === 'number') {
      yamlLines.push(`${key}: ${value}`);
    } else {
      yamlLines.push(`${key}: "${String(value).replace(/"/g, '\\"')}"`);
    }
  }
  yamlLines.push('---');

  // Build Document Body
  const bodySections = [];

  bodySections.push(`# ${payload.title}\n`);

  if (payload.warningCallout) {
    bodySections.push(payload.warningCallout + '\n');
  }

  bodySections.push(`## 1. Ontological Definition & Purpose
${payload.definition}
`);

  if (payload.core_principles && payload.core_principles.length > 0) {
    bodySections.push(`## 2. Core Architectural Principles`);
    for (const cp of payload.core_principles) {
      bodySections.push(`- **${cp.title || cp.id}**: ${cp.description || cp.details}`);
    }
    bodySections.push('');
  }

  if (payload.best_practices && payload.best_practices.length > 0) {
    bodySections.push(`## 3. Industry Best Practices (2025/2026 Consensus)`);
    for (const bp of payload.best_practices) {
      const title = typeof bp === 'string' ? bp : bp.title;
      const details = typeof bp === 'string' ? '' : ` — ${bp.details}`;
      const src = (typeof bp === 'object' && bp.evidence_source) ? ` *(Source: [${bp.evidence_source}](${bp.evidence_source}))*` : '';
      bodySections.push(`- **${title}**${details}${src}`);
    }
    bodySections.push('');
  }

  if (payload.anti_patterns && payload.anti_patterns.length > 0) {
    bodySections.push(`## 4. Known Anti-Patterns & Operational Pitfalls`);
    for (const ap of payload.anti_patterns) {
      const title = typeof ap === 'string' ? ap : ap.title;
      const details = typeof ap === 'string' ? '' : ` — ${ap.details}`;
      const mit = (typeof ap === 'object' && ap.mitigation) ? ` *(Mitigation: ${ap.mitigation})*` : '';
      bodySections.push(`- ⚠️ **${title}**${details}${mit}`);
    }
    bodySections.push('');
  }

  if (payload.operational_kpis && payload.operational_kpis.length > 0) {
    bodySections.push(`## 5. Quantitative KPIs, SLOs & Measurement`);
    for (const kpi of payload.operational_kpis) {
      const name = typeof kpi === 'string' ? kpi : kpi.name;
      const target = typeof kpi === 'string' ? '' : ` (Target: \`${kpi.target}\`)`;
      const sig = (typeof kpi === 'object' && kpi.significance) ? ` — ${kpi.significance}` : '';
      bodySections.push(`- **${name}**${target}${sig}`);
    }
    bodySections.push('');
  }

  if (payload.standards_alignment && payload.standards_alignment.length > 0) {
    bodySections.push(`## 6. Enterprise Framework Alignment`);
    for (const std of payload.standards_alignment) {
      const fw = typeof std === 'string' ? std : std.framework;
      const map = typeof std === 'string' ? '' : `: ${std.mapping}`;
      bodySections.push(`- **${fw}**${map}`);
    }
    bodySections.push('');
  }

  // Local Vault Traceability & Semantic Relations
  const parentMocName = payload.parentMoc || 'MOC - DMBOK - Data Architecture';
  bodySections.push(`## 7. Local Vault Traceability & Semantic Relations
- **Master Framework Map**: [[${parentMocName}]]
- **Ontological Engine**: [[wiki/System/Ontological-Topic-Enrichment-and-Web-Research-Engine|Ontological Topic Enrichment & Web Research Engine]]
- **Governing Architecture Decision**: [[Projects/SocialEngage/01 Architecture Decisions (ADR)/0142-vault-ontological-topic-enrichment-and-web-research-pipeline|ADR-0142]]
`);

  if (payload.relatedArtifacts && payload.relatedArtifacts.length > 0) {
    bodySections.push(`### Referenced in Vault Nodes:`);
    for (const art of payload.relatedArtifacts) {
      bodySections.push(`- [[${art}]]`);
    }
    bodySections.push('');
  }

  return yamlLines.join('\n') + '\n\n' + bodySections.join('\n');
}

/**
 * STEP-4.1 (Action 1): Write Atomic Concept Note to Disk
 */
export function writeConceptNote(payload) {
  if (!fs.existsSync(SYNTHESIS_DIR)) {
    fs.mkdirSync(SYNTHESIS_DIR, { recursive: true });
  }

  const fileName = `${payload.artifact_id}.md`;
  const targetPath = path.join(SYNTHESIS_DIR, fileName);
  const markdownContent = generateConceptNoteMarkdown(payload);

  fs.writeFileSync(targetPath, markdownContent, 'utf-8');
  console.log(`📝 Concept Note compiled: ${targetPath}`);

  return {
    filePath: targetPath,
    relativePath: path.relative(VAULT_ROOT, targetPath).replace(/\\/g, '/')
  };
}

/**
 * STEP-4.2 (Action 2 & Action 3): Update MOC Hubs & Increment Link Metrics
 */
export function updateMocHubs(conceptArtifactId, conceptTitle, candidate, payload = {}) {
  const updatedMocs = [];
  const mocsToUpdate = new Set(candidate.referencedInMocs || []);

  // Include parentMoc if present
  if (payload.parentMoc) {
    mocsToUpdate.add(payload.parentMoc);
  }
  if (candidate.parentMoc) {
    mocsToUpdate.add(candidate.parentMoc);
  }

  // If candidate belongs to a DMBOK category, also include that MOC
  if (candidate.topic && candidate.isFrameworkAnchor) {
    const dmbokMocName = `MOC - DMBOK - ${candidate.topic}`;
    const potentialFile = path.join(MOCS_DIR, `${dmbokMocName}.md`);
    if (fs.existsSync(potentialFile)) {
      mocsToUpdate.add(dmbokMocName);
    }
  } else if (payload.dmbok_category || candidate.dmbok_category) {
    const cat = payload.dmbok_category || candidate.dmbok_category;
    const dmbokMocName = `MOC - DMBOK - ${cat}`;
    const potentialFile = path.join(MOCS_DIR, `${dmbokMocName}.md`);
    if (fs.existsSync(potentialFile)) {
      mocsToUpdate.add(dmbokMocName);
    }
  }

  for (const mocName of mocsToUpdate) {
    const mocBaseName = mocName.replace(/\.md$/, '');
    const mocFile = path.join(MOCS_DIR, `${mocBaseName}.md`);
    if (!fs.existsSync(mocFile)) {
      console.warn(`⚠️ MOC file not found: ${mocFile}`);
      continue;
    }

    let content = fs.readFileSync(mocFile, 'utf-8');
    const conceptLink = `[[Projects/SocialEngage/06 Synthesis & Lessons Learned/${conceptArtifactId}|${conceptTitle}]]`;

    if (content.includes(conceptArtifactId)) {
      console.log(`ℹ️ MOC ${mocBaseName} already links to ${conceptArtifactId}`);
      continue;
    }

    // Insert under an Enriched Concepts section or before Referenced pages
    if (content.includes('## Enriched Concepts & Deep Research Topics')) {
      content = content.replace(
        '## Enriched Concepts & Deep Research Topics\n',
        `## Enriched Concepts & Deep Research Topics\n- ${conceptLink}\n`
      );
    } else if (content.includes('## Referenced pages')) {
      content = content.replace(
        '## Referenced pages\n',
        `## Enriched Concepts & Deep Research Topics\n- ${conceptLink}\n\n## Referenced pages\n`
      );
    } else {
      content += `\n\n## Enriched Concepts & Deep Research Topics\n- ${conceptLink}\n`;
    }

    // Action 3: Increment outgoing_link_count in frontmatter
    let outgoingInc = false;
    content = content.replace(/outgoing_link_count:\s*(\d+)/, (match, count) => {
      outgoingInc = true;
      const newCount = parseInt(count, 10) + 1;
      return `outgoing_link_count: ${newCount}`;
    });

    // Action 3: Add to backlinks list and increment backlink_count if present
    content = content.replace(/backlink_count:\s*(\d+)/, (match, count) => {
      const newCount = parseInt(count, 10) + 1;
      return `backlink_count: ${newCount}`;
    });

    if (content.includes('backlinks:\n') && !content.includes(`  - ${conceptArtifactId}\n`)) {
      content = content.replace('backlinks:\n', `backlinks:\n  - ${conceptArtifactId}\n`);
    }

    fs.writeFileSync(mocFile, content, 'utf-8');
    console.log(`🔗 Updated MOC hub: ${mocBaseName} with link to ${conceptArtifactId}`);
    if (outgoingInc) {
      console.log(`   📈 Incremented outgoing_link_count in ${mocBaseName}`);
    }
    updatedMocs.push(mocBaseName);
  }

  return updatedMocs;
}

/**
 * Execute Full Phase 4 Ingestion Pipeline for a Validated Concept Payload
 */
export function ingestEnrichedTopic(payload, candidate) {
  console.log(`🚀 Ingesting Enriched Topic into Knowledge Graph: "${payload.title}"`);

  // Action 1: Write the Atomic Concept Note
  const writeResult = writeConceptNote(payload);

  // Action 2 & 3: Recompile and Link in Parent MOC Hubs & Increment Link Metrics
  const updatedMocs = updateMocHubs(payload.artifact_id, payload.title, candidate, payload);

  console.log(`✅ Ingestion Complete: 1 Note Created, ${updatedMocs.length} MOCs Updated.`);

  return {
    success: true,
    notePath: writeResult.relativePath,
    updatedMocs
  };
}

/**
 * Master Execution Function for Phase 4: Vault Ingestion & MOC Linker
 */
export async function runVaultIngestion(options = {}) {
  const {
    topic = null,
    validatedPayloadPath = null,
    queuePath = QUEUE_PATH
  } = options;

  console.log('\n======================================================');
  console.log('📝 Phase 4: Vault Ingestion & MOC Linker');
  console.log('======================================================\n');

  // Load candidate from queue
  let candidate = null;
  let queue = null;
  if (fs.existsSync(queuePath)) {
    queue = JSON.parse(fs.readFileSync(queuePath, 'utf-8'));
    if (topic) {
      candidate = queue.candidates.find(c =>
        c.topic.toLowerCase() === topic.toLowerCase() ||
        c.slug === topic.toLowerCase()
      );
    } else {
      candidate = queue.candidates[0];
    }
  }

  const targetSlug = candidate ? candidate.slug : (topic || 'neo4j').toLowerCase().replace(/[^a-z0-9]+/g, '-');
  const payloadFile = validatedPayloadPath || path.join(VAULT_ROOT, 'raw', `validated-concept-${targetSlug}.json`);

  if (!fs.existsSync(payloadFile)) {
    throw new Error(`Validated concept payload not found at ${payloadFile}. Please run Phase 3 first.`);
  }

  const payload = JSON.parse(fs.readFileSync(payloadFile, 'utf-8'));

  if (!candidate) {
    candidate = {
      topic: payload.title.replace(/^Concept:\s*/, ''),
      slug: payload.slug,
      priority: 1,
      referenceCount: payload.relatedArtifacts?.length || 5,
      domainClusters: [payload.domain_cluster],
      referencedInMocs: [payload.parentMoc],
      referencingArtifacts: payload.relatedArtifacts || []
    };
  }

  // Action 1: Write canonical Concept-<topic>.md
  console.log('--- Action 1: Write Canonical Concept Note ---');
  const writeResult = writeConceptNote(payload);

  // Action 2 & 3: Recompile parent MOC Hub & Update Link Metrics
  console.log('\n--- Action 2 & 3: Recompile Parent MOC Hub & Update Link Metrics ---');
  const updatedMocs = updateMocHubs(payload.artifact_id, payload.title, candidate, payload);

  // Update Enrichment Queue on Disk (dequeue target)
  if (queue && fs.existsSync(queuePath)) {
    const initialCount = queue.candidates.length;
    queue.candidates = queue.candidates.filter(c =>
      c.slug !== targetSlug &&
      c.topic.toLowerCase() !== targetSlug.toLowerCase()
    );
    queue.total_candidates_needing_enrichment = queue.candidates.length;
    queue.priority_1_count = queue.candidates.filter(c => c.priority === 1).length;
    queue.priority_2_count = queue.candidates.filter(c => c.priority === 2).length;
    fs.writeFileSync(queuePath, JSON.stringify(queue, null, 2), 'utf-8');
    console.log(`\n📋 Queue Updated: Dequeued '${targetSlug}' (${initialCount} -> ${queue.candidates.length} candidates remaining).`);
    console.log(`   Priority 1 Gaps Remaining: ${queue.priority_1_count}`);
  }

  console.log(`\n🎉 Phase 4 Ingestion Complete:`);
  console.log(`   📄 Canonical Concept Note: ${writeResult.relativePath}`);
  console.log(`   🔗 Recompiled MOCs: ${updatedMocs.join(', ') || 'None'}`);

  return {
    success: true,
    notePath: writeResult.relativePath,
    updatedMocs,
    queueRemaining: queue ? queue.candidates.length : 0
  };
}

// CLI Execution Support
const isDirectCli = process.argv[1] && (
  process.argv[1].endsWith('vault-ingestion.mjs') ||
  process.argv[1].endsWith('vault-ingestion')
);

if (isDirectCli) {
  const args = process.argv.slice(2);
  let targetTopic = null;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--topic' && args[i + 1]) {
      targetTopic = args[i + 1];
      i++;
    }
  }

  runVaultIngestion({ topic: targetTopic }).catch(err => {
    console.error('❌ Phase 4 Ingestion Failed:', err.message);
    process.exit(1);
  });
}
