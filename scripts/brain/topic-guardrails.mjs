/**
 * topic-guardrails.mjs
 * Authoritative Topic Admission Guardrails (TAG) for the Second Brain Knowledge Graph.
 *
 * Enforces strict architectural and ontological filters to prevent:
 * 1. Git commit SHAs and hex fragments (e.g., 5d4ef0)
 * 2. Reserved frontmatter schema keys (e.g., best_practices, topics)
 * 3. Compound code-level identifiers, event types, or boolean flags (e.g., canprovidefollowercountatpublish)
 * 4. Generic dictionary keywords, language tokens, or commit stopwords (e.g., loop, edit, stored)
 * 5. Low-centrality noise fragments
 */

import fs from 'fs';
import path from 'path';

// Known authoritative architectural acronyms permitted as single tokens
export const AUTHORIZED_ARCHITECTURAL_ACRONYMS = new Set([
  'rbac', 'abac', 'rls', 'rag', 'cdc', 'dlq', 'api', 'jwt', 'mtls',
  'mdm', 'sor', 'etl', 'elt', 'oltp', 'olap', 'cqrs', 'ddd', 'sla', 'slo', 'kpi',
  'base64', 'ipv4', 'ipv6', 'd365', 'auth0', 'tier3', 'neo4j'
]);

// Reserved frontmatter metadata keys in ONTOLOGY.json
export const RESERVED_SCHEMA_KEYS = new Set([
  'best_practices', 'best-practices', 'best practices',
  'anti_patterns', 'anti-patterns', 'anti patterns',
  'operational_kpis', 'operational-kpis', 'operational kpis',
  'standards_alignment', 'standards-alignment', 'standards alignment',
  'source_urls', 'source-urls', 'source urls',
  'topics', 'tags', 'aliases', 'backlinks',
  'authority_level', 'authority-level', 'confidence_score', 'confidence-score',
  'entity_id', 'artifact_id', 'created_at', 'modified_at', 'source_document',
  'version', 'type', 'pm_class', 'pm_subclass', 'pm_relationships', 'domain_cluster',
  'dmbok_category', 'pmbok_category', 'babok_category', 'status',
  'outgoing_link_count', 'backlink_count', 'consequences', 'pages', 'referenced'
]);

// Generic grammatical words, commit stopwords, and language tokens
export const GENERIC_STOPWORDS = new Set([
  'loop', 'edit', 'primary', 'amended', 'stored', 'never', 'directly', 'exist',
  'matched', 'facing', 'registry', 'body', 'country', 'workspace', 'preconfigured',
  'async', 'advanced', 'grounding', 'capabilities', 'evolution', 'resolved',
  'dependency', 'dependencies', 'context', 'problem', 'scale', 'level', 'likely',
  'documents', 'draft', 'cost', 'costs', 'index', 'model', 'multi', 'already',
  'scope', 'requirements', 'assumptions', 'control', 'acceptance', 'state',
  'appendix', 'appendices', 'purpose', 'approval', 'criteria', 'notes', 'summary',
  'overview', 'introduction', 'solution', 'process', 'activity', 'task', 'phase',
  'status', 'description', 'title', 'version', 'date', 'section', 'details',
  'item', 'items', 'user', 'system', 'project', 'amendment', 'refinements',
  'assertion', 'extension', 'leakage', 'policy', 'secret', 'sentiment', 'statement',
  'current', 'background', 'backend', 'considerations', 'executive', 'error',
  'capability', 'decision', 'rules', 'exceptions', 'goals', 'audience', 'future',
  'boolean', 'string', 'number', 'array', 'object', 'function', 'class', 'const', 'let', 'var'
]);

/**
 * Validate whether a proposed topic is a legitimate architectural / ontological concept.
 *
 * @param {string} rawTopic
 * @param {object} context - { isFrameworkAnchor, referenceCount, referencingArtifacts }
 * @returns {{ admissible: boolean, reason: string }}
 */
export function validateTopicAdmission(rawTopic, context = {}) {
  if (!rawTopic || typeof rawTopic !== 'string') {
    return { admissible: false, reason: 'Topic is empty or non-string' };
  }

  const clean = rawTopic.trim().replace(/^\[\[|\]\]$/g, '');
  const lower = clean.toLowerCase();
  const slug = clean.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');

  // Guardrail 1: Framework Anchor Exemption
  if (context.isFrameworkAnchor) {
    return { admissible: true, reason: 'Approved Framework Anchor (ONTOLOGY.json)' };
  }

  // Guardrail 2: Hex Hash / Git Commit SHA (e.g. 5d4ef0, ba95e4, 9ed1f505)
  if (/^[0-9a-f]{6,40}$/i.test(clean) || /^[0-9a-f]{6,40}$/i.test(slug)) {
    return { admissible: false, reason: `Rejected: Matches git commit SHA or hex hash pattern ("${clean}")` };
  }

  // Guardrail 3: Reserved Frontmatter Schema Keys
  if (RESERVED_SCHEMA_KEYS.has(lower) || RESERVED_SCHEMA_KEYS.has(slug) || RESERVED_SCHEMA_KEYS.has(clean)) {
    return { admissible: false, reason: `Rejected: Matches reserved frontmatter metadata schema key ("${clean}")` };
  }

  // Guardrail 4: Generic Stopwords / Git Commit Log Tokens
  if (GENERIC_STOPWORDS.has(lower) || GENERIC_STOPWORDS.has(slug)) {
    return { admissible: false, reason: `Rejected: Matches generic grammatical stopword or commit fragment ("${clean}")` };
  }

  // Guardrail 5: Code Identifiers, Event Contracts, and Function/Method Names
  // Matches compound unspaced tokens like 'connectorhealthchangedevent', 'canprovidefollowercountatpublish', 'implementationlogorderdrift'
  if (/^[a-z0-9_]{16,}$/i.test(clean) && !clean.includes(' ') && !clean.includes('-')) {
    return { admissible: false, reason: `Rejected: Concatenated code-level variable, method, or event identifier ("${clean}")` };
  }
  if (/(event|service|connector|translator|filter|matches|refresh|handler|router|controller)$/i.test(clean) && !clean.includes(' ') && !clean.includes('-')) {
    return { admissible: false, reason: `Rejected: Code-level component or event class name without spacing ("${clean}")` };
  }

  // Guardrail 6: Numeric or Hash-Prefix Patterns (e.g. '0052', '123abc')
  if (/^\d+$/.test(clean) || (/^\d+[a-z]/i.test(clean) && !/^iso|rfc|ieee/i.test(clean))) {
    return { admissible: false, reason: `Rejected: Numeric or numeric-prefix identifier ("${clean}")` };
  }

  // Guardrail 7: Single Lowercase Words Without Architectural Acronym Approval
  if (/^[a-z]{2,15}$/.test(clean)) {
    if (!AUTHORIZED_ARCHITECTURAL_ACRONYMS.has(lower)) {
      return { admissible: false, reason: `Rejected: Single uncapitalized token ("${clean}") not in authorized architectural acronym registry` };
    }
  }

  // Guardrail 8: Minimum Graph Centrality for Vault-Discovered Topics
  if (context.referenceCount !== undefined && context.referenceCount < 2 && !context.isTargeted && !context.isFrameworkAnchor) {
    return { admissible: false, reason: `Rejected: Insufficient graph centrality (${context.referenceCount} reference; minimum 2 required)` };
  }

  return { admissible: true, reason: 'Valid architectural or conceptual topic' };
}

/**
 * Scan Synthesis directory for pseudo-concept notes that fail admission guardrails.
 */
export function auditExistingConceptNotes(vaultRoot) {
  const synthesisDir = path.join(vaultRoot, 'wiki', 'Projects', 'SocialEngage', '06 Synthesis & Lessons Learned');
  if (!fs.existsSync(synthesisDir)) return { valid: [], noise: [] };

  const files = fs.readdirSync(synthesisDir).filter(f => f.startsWith('Concept-') && f.endsWith('.md'));
  const noise = [];
  const valid = [];

  for (const file of files) {
    const topicSlug = file.replace(/^Concept-/, '').replace(/\.md$/, '');
    const topicTitle = topicSlug.replace(/-/g, ' ');
    const check = validateTopicAdmission(topicTitle, { isFrameworkAnchor: false });

    if (!check.admissible) {
      noise.push({
        file,
        path: path.join(synthesisDir, file),
        slug: topicSlug,
        reason: check.reason
      });
    } else {
      valid.push({
        file,
        path: path.join(synthesisDir, file),
        slug: topicSlug
      });
    }
  }

  return { valid, noise };
}

/**
 * Quarantine noise/pseudo-concept notes to raw/quarantined-concepts/
 */
export function quarantineNoiseConceptNotes(vaultRoot, dryRun = true) {
  const { noise } = auditExistingConceptNotes(vaultRoot);
  const quarantineDir = path.join(vaultRoot, 'raw', 'quarantined-concepts');

  if (!dryRun && !fs.existsSync(quarantineDir)) {
    fs.mkdirSync(quarantineDir, { recursive: true });
  }

  const results = [];
  for (const item of noise) {
    const destPath = path.join(quarantineDir, item.file);
    if (!dryRun) {
      fs.renameSync(item.path, destPath);
    }
    results.push({
      file: item.file,
      reason: item.reason,
      quarantinedTo: !dryRun ? destPath : 'dry-run'
    });
  }

  return results;
}
