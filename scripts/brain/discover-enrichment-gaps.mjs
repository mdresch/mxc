/**
 * discover-enrichment-gaps.mjs
 * Phase 1: Topic Discovery & Priority Queue Generator for the Second Brain Knowledge Graph.
 *
 * Scans all frontmatter topics, ontology categories, and MOC hubs in wiki/,
 * checks for missing or stub concept notes, scores candidates by graph centrality,
 * and emits raw/enrichment-queue.json.
 */

import fs from 'fs';
import path from 'path';
import { validateTopicAdmission } from './topic-guardrails.mjs';
import { resolveVaultRoot, resolveWikiRoot } from './vault-resolver.mjs';

const VAULT_ROOT = resolveVaultRoot();
const WIKI_DIR = resolveWikiRoot(VAULT_ROOT);
const MOCS_DIR = path.join(WIKI_DIR, '_MOCs');
const SYNTHESIS_DIR = path.join(WIKI_DIR, 'Projects', 'SocialEngage', '06 Synthesis & Lessons Learned');
const SYSTEM_DIR = path.join(WIKI_DIR, 'System');
const RAW_DIR = path.join(VAULT_ROOT, 'raw');
if (!fs.existsSync(RAW_DIR)) fs.mkdirSync(RAW_DIR, { recursive: true });
const OUTPUT_QUEUE = path.join(RAW_DIR, 'enrichment-queue.json');
const ONTOLOGY_PATH = path.join(VAULT_ROOT, 'ONTOLOGY.json');

// Helper to recursively get all markdown files
function getMarkdownFiles(dir) {
  let results = [];
  if (!fs.existsSync(dir)) return results;
  const list = fs.readdirSync(dir);
  for (const file of list) {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat.isDirectory()) {
      results = results.concat(getMarkdownFiles(fullPath));
    } else if (file.endsWith('.md')) {
      results.push(fullPath);
    }
  }
  return results;
}

// Normalize topic to a comparable slug
function slugify(text) {
  return text.toLowerCase()
    .replace(/\[\[|\]\]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

// Basic YAML frontmatter parser for our schema
function parseFrontmatter(content) {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return { frontmatter: {}, body: content };
  
  const yamlBlock = match[1];
  const body = content.slice(match[0].length);
  const data = {};

  let currentKey = null;
  let inArray = false;

  for (const line of yamlBlock.split(/\r?\n/)) {
    const arrayItemMatch = line.match(/^\s*-\s*(.+)$/);
    const keyValMatch = line.match(/^([a-zA-Z0-9_]+):\s*(.*)$/);

    if (keyValMatch) {
      currentKey = keyValMatch[1];
      const val = keyValMatch[2].trim();
      if (val === '') {
        data[currentKey] = [];
        inArray = true;
      } else {
        inArray = false;
        data[currentKey] = val.replace(/^["']|["']$/g, '');
      }
    } else if (arrayItemMatch && inArray && currentKey) {
      const item = arrayItemMatch[1].trim().replace(/^["']|["']$/g, '');
      if (Array.isArray(data[currentKey])) {
        data[currentKey].push(item);
      }
    }
  }

  return { frontmatter: data, body };
}

export async function runTopicDiscovery() {
  console.log('🔍 Starting Ontological Topic Discovery in:', WIKI_DIR);

  const ontology = JSON.parse(fs.readFileSync(ONTOLOGY_PATH, 'utf-8'));
  const allMdFiles = getMarkdownFiles(WIKI_DIR);
  console.log(`📄 Found ${allMdFiles.length} markdown files in wiki/`);

  // 1. Index all existing Concept and System notes
  const existingConcepts = new Map(); // slug -> metadata
  for (const file of allMdFiles) {
    const content = fs.readFileSync(file, 'utf-8');
    const { frontmatter, body } = parseFrontmatter(content);
    const wordCount = body.split(/\s+/).filter(w => w.length > 0).length;
    const baseName = path.basename(file, '.md');
    const slug = slugify(baseName);

    if (frontmatter.type === 'concept' || file.includes('06 Synthesis') || file.includes('System')) {
      existingConcepts.set(slug, {
        file: path.relative(VAULT_ROOT, file).replace(/\\/g, '/'),
        title: frontmatter.title || baseName,
        wordCount,
        authorityLevel: parseInt(frontmatter.authority_level || '1', 10),
        isStub: wordCount < 200,
        lastEnrichedAt: frontmatter.last_enriched_at || frontmatter.created_at || null,
        domainCluster: frontmatter.domain_cluster || 'General',
        tags: Array.isArray(frontmatter.tags) ? frontmatter.tags : []
      });
    }
  }
  console.log(`🧠 Indexed ${existingConcepts.size} existing concept/system notes.`);

  // Tiered Staleness Policy (30d / 60d / 90d / 0d Drift)
  function getStalenessPolicy(domainCluster, tags = []) {
    if (tags.some(t => t === 'drift' || t === 'semantic-drift')) {
      return { ttlDays: 0, tier: 'Event-Driven (Drift)' };
    }
    const rapidDrift = new Set([
      'AI, NLP & Semantic Enrichment',
      'RAG & Vector Semantic Search',
      'Ingestion, Connectors & Rate Limits'
    ]);
    const architecture = new Set([
      'Security, Identity & Multi-Tenancy',
      'Eventing & Messaging Architecture',
      'Data Model, Storage & Archival',
      'Derived Data, Health & Analytics'
    ]);

    if (rapidDrift.has(domainCluster)) return { ttlDays: 30, tier: 'Rapid-Drift (30d)' };
    if (architecture.has(domainCluster)) return { ttlDays: 60, tier: 'Architecture (60d)' };
    return { ttlDays: 90, tier: 'Foundational Governance (90d)' };
  }

  // 2. Structural & Generic Stopwords to ignore in frontmatter
  const genericStopWords = new Set([
    'pages', 'referenced', 'context', 'problem', 'scale', 'level', 'likely',
    'documents', 'draft', 'cost', 'costs', 'index', 'model', 'multi', 'already',
    'scope', 'requirements', 'assumptions', 'control', 'dependencies', 'acceptance',
    'state', 'appendix', 'purpose', 'approval', 'criteria', 'notes', 'summary',
    'overview', 'introduction', 'solution', 'process', 'activity', 'task', 'phase',
    'status', 'description', 'title', 'version', 'date', 'section', 'details',
    'item', 'items', 'user', 'system', 'project', 'amendment', 'refinements',
    'assertion', 'extension', 'leakage', 'policy', 'secret', 'sentiment', 'statement'
  ]);

  const topicRegistry = new Map(); // topicName -> { count, occurrences: [], domainClusters: Set, mocs: Set }

  function registerTopic(topicName, fileRelPath, frontmatter, isMoc, isFrameworkAnchor = false) {
    const cleanTopic = topicName.trim();
    if (!cleanTopic || cleanTopic.length < 3) return;

    // Apply strict Topic Admission Guardrail
    const admissionCheck = validateTopicAdmission(cleanTopic, { isFrameworkAnchor });
    if (!admissionCheck.admissible) {
      return;
    }

    if (!topicRegistry.has(cleanTopic)) {
      topicRegistry.set(cleanTopic, {
        topic: cleanTopic,
        slug: slugify(cleanTopic),
        count: 0,
        isFrameworkAnchor,
        occurrences: [],
        domainClusters: new Set(),
        mocs: new Set()
      });
    }

    const entry = topicRegistry.get(cleanTopic);
    entry.count += 1;
    if (fileRelPath) {
      entry.occurrences.push({
        artifact_id: frontmatter.artifact_id || path.basename(fileRelPath, '.md'),
        file: fileRelPath,
        type: frontmatter.type || 'unknown'
      });
    }
    const domain = frontmatter?.domain_cluster;
    if (domain && domain !== 'General') entry.domainClusters.add(domain);
    if (isMoc && frontmatter?.title) entry.mocs.add(frontmatter.title);
  }

  // 2a. Register formal Ontology Framework Categories (DMBOK, BABOK, PMBOK, Domain Clusters)
  if (ontology.taxonomies) {
    const allTaxonomyCategories = [
      ...(ontology.taxonomies.dmbokAreas || []),
      ...(ontology.taxonomies.domainClusters || []),
      ...(ontology.taxonomies.pmbokAreas || []),
      ...(ontology.taxonomies.babokAreas || [])
    ];

    for (const cat of allTaxonomyCategories) {
      registerTopic(cat, null, { type: 'ontology_category' }, false, true);
    }
  }

  // 2b. Scan all Markdown files in wiki/
  for (const file of allMdFiles) {
    const relPath = path.relative(VAULT_ROOT, file).replace(/\\/g, '/');
    const content = fs.readFileSync(file, 'utf-8');
    const { frontmatter } = parseFrontmatter(content);

    const isMoc = file.includes('_MOCs');
    const topics = Array.isArray(frontmatter.topics) ? frontmatter.topics : [];

    // Register frontmatter topics
    for (const rawTopic of topics) {
      registerTopic(rawTopic, relPath, frontmatter, isMoc, false);
    }

    // If it's an MOC, extract the core conceptual title (e.g. MOC - DMBOK - Data Governance -> Data Governance)
    if (isMoc) {
      const base = path.basename(file, '.md');
      const cleanMocTitle = base.replace(/^MOC\s*-\s*/, '').replace(/^(DMBOK|PMBOK|BABOK)\s*-\s*/, '').trim();
      if (cleanMocTitle && !cleanMocTitle.includes('Master Hub') && !cleanMocTitle.includes('Matrix')) {
        registerTopic(cleanMocTitle, relPath, frontmatter, true, true);
      }
    }
  }

  console.log(`📊 Discovered ${topicRegistry.size} candidate topics across the ontology and vault graph.`);

  // 3. Match against existing concepts and prioritize gaps
  const candidates = [];

  for (const [topicName, data] of topicRegistry.entries()) {
    const slug = data.slug;
    const directMatch = existingConcepts.get(slug) ||
                        existingConcepts.get(`concept-${slug}`) ||
                        existingConcepts.get(slug.replace(/^concept-/, ''));

    const isMissing = !directMatch;
    const isStub = directMatch && directMatch.isStub;

    let isStale = false;
    let stalenessInfo = null;
    if (directMatch && directMatch.lastEnrichedAt) {
      const policy = getStalenessPolicy(directMatch.domainCluster, directMatch.tags);
      const daysOld = Math.floor((Date.now() - new Date(directMatch.lastEnrichedAt).getTime()) / (1000 * 60 * 60 * 24));
      if (daysOld > policy.ttlDays) {
        isStale = true;
        stalenessInfo = { daysOld, ttlDays: policy.ttlDays, tier: policy.tier };
      }
    }

    if (isMissing || isStub || isStale) {
      let priority = 2;
      let reason = 'Observed in graph metadata';

      if (isStale) {
        priority = 1;
        reason = `Stale note (${stalenessInfo.daysOld}d old > ${stalenessInfo.ttlDays}d TTL, Tier: ${stalenessInfo.tier})`;
      } else if (data.isFrameworkAnchor) {
        priority = 1;
        reason = `Core Ontology/MOC Framework Discipline (${topicName})`;
      } else if (data.mocs.size > 0) {
        priority = 1;
        reason = `Directly indexed in MOC: ${Array.from(data.mocs).join(', ')}`;
      } else if (data.count >= 3) {
        priority = 1;
        reason = `High graph centrality (${data.count} referencing nodes)`;
      } else if (isStub) {
        priority = 1;
        reason = `Existing note is a shallow stub (${directMatch.wordCount} words)`;
      }

      // Generate suggested 5-facet query battery
      const domainCtx = data.domainClusters.size > 0 ? Array.from(data.domainClusters)[0] : 'Software Architecture & Data Governance';
      const suggestedQueries = [
        `"${topicName}" definition "${domainCtx}" core principles architecture`,
        `"${topicName}" "best practices" production architecture 2025 OR 2026`,
        `"${topicName}" ("DMBOK" OR "TOGAF" OR "NIST" OR "ISO") standard`,
        `"${topicName}" "anti-patterns" OR "common pitfalls" enterprise`,
        `"${topicName}" key metrics KPIs benchmarks operational SLO`
      ];

      candidates.push({
        topic: topicName,
        slug: data.slug,
        isFrameworkAnchor: data.isFrameworkAnchor,
        priority,
        priorityReason: reason,
        referenceCount: data.count,
        domainClusters: Array.from(data.domainClusters),
        referencedInMocs: Array.from(data.mocs),
        referencingArtifacts: data.occurrences.slice(0, 10).map(o => o.artifact_id),
        existingNoteStatus: isMissing ? 'Missing' : isStale ? `Stale (${stalenessInfo.daysOld}d > ${stalenessInfo.ttlDays}d)` : `Stub (${directMatch.wordCount} words)`,
        suggestedQueries
      });
    }
  }

  // Sort candidates: Priority 1 first, Framework anchors first within P1, then by referenceCount descending
  candidates.sort((a, b) => {
    if (a.priority !== b.priority) return a.priority - b.priority;
    if (a.isFrameworkAnchor && !b.isFrameworkAnchor) return -1;
    if (!a.isFrameworkAnchor && b.isFrameworkAnchor) return 1;
    return b.referenceCount - a.referenceCount;
  });

  // Ensure raw directory exists
  if (!fs.existsSync(RAW_DIR)) {
    fs.mkdirSync(RAW_DIR, { recursive: true });
  }

  const outputPayload = {
    generated_at: new Date().toISOString(),
    total_markdown_scanned: allMdFiles.length,
    total_topics_analyzed: topicRegistry.size,
    total_candidates_needing_enrichment: candidates.length,
    priority_1_count: candidates.filter(c => c.priority === 1).length,
    priority_2_count: candidates.filter(c => c.priority === 2).length,
    candidates
  };

  fs.writeFileSync(OUTPUT_QUEUE, JSON.stringify(outputPayload, null, 2), 'utf-8');
  console.log(`✅ Emitted ${candidates.length} prioritized enrichment candidates to ${OUTPUT_QUEUE}`);

  // Print Top Candidates
  const p1s = candidates.filter(c => c.priority === 1).slice(0, 15);
  if (p1s.length > 0) {
    console.log('\n⭐ TOP PRIORITY 1 TOPIC GAPS:');
    p1s.forEach((c, idx) => {
      console.log(`  ${idx + 1}. [${c.topic}] - Refs: ${c.referenceCount} | Reason: ${c.priorityReason}`);
    });
  } else {
    console.log('\n🎉 ALL PRIORITY 1 TOPICS FULLY ENRICHED (All Framework Disciplines & Core Architecture Complete)!');
  }

  const p2s = candidates.filter(c => c.priority === 2).slice(0, 15);
  if (p2s.length > 0) {
    console.log(`\n📋 REMAINING PRIORITY 2 TOPIC GAPS (${candidates.filter(c => c.priority === 2).length} total):`);
    p2s.forEach((c, idx) => {
      console.log(`  ${idx + 1}. [${c.topic}] - Refs: ${c.referenceCount} | Reason: ${c.priorityReason}`);
    });
  } else if (candidates.length === 0) {
    console.log('\n🎉 100% GRAPH CONVERGENCE: ZERO TOPIC GAPS REMAINING ACROSS THE ENTIRE VAULT!');
  }

  return outputPayload;
}

runTopicDiscovery().catch(err => {
  console.error('❌ Error during topic discovery:', err);
  process.exit(1);
});
