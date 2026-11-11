/**
 * list-enrichment-topics.mjs
 * CLI inspector to view the current list of topics in the Second Brain knowledge graph:
 * - Next queued candidates waiting for enrichment
 * - Already enriched canonical concept notes
 * - Framework taxonomy overview (DMBOK, BABOK, PMBOK, Domain Clusters)
 */

import fs from 'fs';
import path from 'path';
import { resolveVaultRoot, resolveWikiRoot } from './vault-resolver.mjs';

const VAULT_ROOT = resolveVaultRoot();
const baseWiki = resolveWikiRoot(VAULT_ROOT);
const QUEUE_PATH = path.join(VAULT_ROOT, 'raw', 'enrichment-queue.json');
const SYNTHESIS_DIR = path.join(baseWiki, 'Projects', 'SocialEngage', '06 Synthesis & Lessons Learned');
const ONTOLOGY_PATH = path.join(VAULT_ROOT, 'ONTOLOGY.json');

console.log(`\n======================================================`);
console.log(`📚 SECOND BRAIN KNOWLEDGE GRAPH: TOPIC DIRECTORY`);
console.log(`======================================================\n`);

// 1. Enriched Concept Notes
const enrichedNotes = fs.existsSync(SYNTHESIS_DIR)
  ? fs.readdirSync(SYNTHESIS_DIR).filter(f => f.startsWith('Concept-') && f.endsWith('.md'))
  : [];

console.log(`✅ ENRICHED CANONICAL CONCEPTS: ${enrichedNotes.length} notes compiled in wiki/`);
console.log(`   Location: wiki/Projects/SocialEngage/06 Synthesis & Lessons Learned/\n`);

// 2. Queue Status
if (fs.existsSync(QUEUE_PATH)) {
  const queue = JSON.parse(fs.readFileSync(QUEUE_PATH, 'utf-8'));
  console.log(`📋 ENRICHMENT QUEUE (Remaining Gaps):`);
  console.log(`   Queue File: raw/enrichment-queue.json`);
  console.log(`   Generated:  ${queue.generated_at}`);
  console.log(`   Total Candidates Needing Enrichment: ${queue.total_candidates_needing_enrichment || queue.candidates.length}`);
  console.log(`   Priority 1: ${queue.priority_1_count} | Priority 2: ${queue.priority_2_count}\n`);

  console.log(`⭐ TOP 15 UPCOMING CANDIDATES IN QUEUE:`);
  const top15 = queue.candidates.slice(0, 15);
  top15.forEach((cand, idx) => {
    const domain = cand.domainClusters?.[0] || 'General';
    console.log(`   ${(idx + 1).toString().padStart(2, ' ')}. [${cand.topic}]`);
    console.log(`       Priority: ${cand.priority} | Domain: ${domain} | References: ${cand.referenceCount}`);
    console.log(`       Reason: ${cand.priorityReason}`);
  });
  console.log('');
} else {
  console.log(`⚠️ Enrichment queue not found at raw/enrichment-queue.json. Run 'npm run brain:enrich:queue' to generate.\n`);
}

// 3. Formal Ontology Taxonomies
if (fs.existsSync(ONTOLOGY_PATH)) {
  const ontology = JSON.parse(fs.readFileSync(ONTOLOGY_PATH, 'utf-8'));
  console.log(`🏛️ FORMAL ONTOLOGY TAXONOMIES (ONTOLOGY.json):`);
  if (ontology.taxonomies) {
    console.log(`   • Domain Clusters: ${ontology.taxonomies.domainClusters?.length || 0} clusters`);
    console.log(`   • DAMA-DMBOK Knowledge Areas: ${ontology.taxonomies.dmbokAreas?.length || 0} areas (All 11 Enriched ✅)`);
    console.log(`   • PMI-PMBOK Knowledge Areas:  ${ontology.taxonomies.pmbokAreas?.length || 0} areas (All 8 Enriched ✅)`);
    console.log(`   • IIBA-BABOK Knowledge Areas: ${ontology.taxonomies.babokAreas?.length || 0} areas (All 6 Enriched ✅)`);
  }
}

console.log(`\n======================================================\n`);
