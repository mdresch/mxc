/**
 * taxonomy-router.mjs
 * Deterministic Multi-Signal DAMA-DMBOK2 Taxonomy Router.
 *
 * Prevents generic defaulting to "Data Governance" by implementing:
 * 1. Exact Framework Anchor Matching (DMBOK_AREAS)
 * 2. High-Precision Title/Topic Keyword Rules (DMBOK_KEYWORD_RULES)
 * 3. Domain Cluster -> DAMA-DMBOK2 Knowledge Area Mapping Matrix (DOMAIN_TO_DMBOK_MAP)
 * 4. Contextual Keyword Rules (Tags & Referencing Artifacts)
 * 5. Vault-wide Audit & Reclassification Pass for heal-brain.mjs
 */

import fs from 'fs';
import path from 'path';

// Canonical 11 DAMA-DMBOK2 Knowledge Areas per ONTOLOGY.json (v1.1.0-LOCKED)
export const DMBOK_AREAS = new Set([
  'Data Governance',
  'Data Security',
  'Reference & Master Data',
  'Document & Content Management',
  'Data Warehousing & Analytics (DW/BI)',
  'Data Quality Management',
  'Metadata Management',
  'Data Modeling & Design',
  'Data Storage & Operations',
  'Data Architecture',
  'Data Integration & Interoperability'
]);

// Deterministic Mapping: 14 Domain Clusters -> Canonical DMBOK Knowledge Areas
export const DOMAIN_TO_DMBOK_MAP = {
  // Security & Identity
  'Security, Identity & Multi-Tenancy': 'Data Security',

  // Messaging, Connectors & Integration
  'Eventing & Messaging Architecture': 'Data Integration & Interoperability',
  'Ingestion, Connectors & Rate Limits': 'Data Integration & Interoperability',

  // Persistence, Cloud Infra & Storage
  'Data Model, Storage & Archival': 'Data Storage & Operations',
  'Platform Architecture & Foundations': 'Data Storage & Operations',

  // Analytics, DW & Reporting
  'Derived Data, Health & Analytics': 'Data Warehousing & Analytics (DW/BI)',

  // Knowledge, Search & Content
  'RAG & Vector Semantic Search': 'Document & Content Management',
  'Document & Content Management': 'Document & Content Management',

  // Semantic Enrichment, Ontologies & Metadata
  'AI, NLP & Semantic Enrichment': 'Metadata Management',
  'Strategic Intent & Cognitive Learning': 'Metadata Management',

  // Master Data & CRM/ERP Systems
  'Outbound Publishing, Engagement & CRM': 'Reference & Master Data',

  // Architecture & Engineering Specifications
  'Delivery & User Stories': 'Data Architecture',

  // True Governance & Reasoning Architecture (Legitimate home for Data Governance)
  'Project Governance & Management': 'Data Governance',
  'AI Governance & Reasoning Architecture': 'Data Governance'
};

// Lexical & Contextual Keyword Classifier Rules
export const DMBOK_KEYWORD_RULES = [
  {
    category: 'Data Security',
    regex: /\b(auth0?|oauth|oidc|jwt|token|saml|rbac|abac|crypto|cipher|encryption|secret|tls|mtls|vulnerability|firewall|credentials?|zero-trust)\b/i
  },
  {
    category: 'Data Storage & Operations',
    regex: /\b(ipv4|ipv6|subnet|cidr|dns|nat|socket|port|tier3|postgres|mysql|redis|storage|disk|nvme|cache|cluster|failover|rto|rpo|high-availability|replica|backup)\b/i
  },
  {
    category: 'Data Integration & Interoperability',
    regex: /\b(base64|encoding|codec|kafka|rabbitmq|event|queue|webhook|rest|grpc|protobuf|avro|xml|json|api|connector|middleware|pubsub)\b/i
  },
  {
    category: 'Reference & Master Data',
    regex: /\b(d365|dynamics|salesforce|sap|erp|crm|dataverse|cdm|golden-record|master-data|customer|vendor|mdm|entity-resolution)\b/i
  },
  {
    category: 'Data Architecture',
    regex: /\b(technical-design|tds|blueprint|erd|uml|metamodel|togaf|c4-model|bounded-context|ddd|pipeline|lifecycle|architecture)\b/i
  },
  {
    category: 'Metadata Management',
    regex: /\b(neo4j|ontology|taxonomy|schema-registry|lineage|catalog|semantic|knowledge-graph|gkg|graph-database|rdf|owl)\b/i
  },
  {
    category: 'Data Quality Management',
    regex: /\b(quality|data-quality|profiling|cleansing|dedup|anomaly-detection|accuracy|completeness|consistency|validity)\b/i
  },
  {
    category: 'Data Warehousing & Analytics (DW/BI)',
    regex: /\b(olap|warehouse|bi|analytics|dashboard|metric|kpi|telemetry|cube|star-schema|snowflake|clickhouse|bigquery)\b/i
  },
  {
    category: 'Document & Content Management',
    regex: /\b(document|rag|vector|embedding|chunking|unstructured|pdf|markdown|cms|dms)\b/i
  },
  {
    category: 'Data Governance',
    regex: /\b(adr-authority|adr|governance|policy|stewardship|compliance|audit|gdpr|hipaa|sox|charter|decision-making)\b/i
  }
];

/**
 * Resolves the canonical DAMA-DMBOK2 category and parent MOC for a given candidate topic or note.
 *
 * @param {object} candidate - { topic, slug, title, isFrameworkAnchor, domainClusters, referencingArtifacts }
 * @param {object} [researchData={}] - { dmbok_category, parent_moc }
 * @returns {{ category: string, parentMoc: string, resolutionSource: string }}
 */
export function resolveDmbokTaxonomy(candidate, researchData = {}) {
  // 1. Explicit author / evidence bank assignment
  if (researchData?.dmbok_category && DMBOK_AREAS.has(researchData.dmbok_category)) {
    return {
      category: researchData.dmbok_category,
      parentMoc: researchData.parent_moc || `MOC - DMBOK - ${researchData.dmbok_category}`,
      resolutionSource: 'explicit_research_data'
    };
  }

  // 2. Direct Framework Anchor check
  if (candidate?.isFrameworkAnchor && DMBOK_AREAS.has(candidate.topic)) {
    return {
      category: candidate.topic,
      parentMoc: `MOC - DMBOK - ${candidate.topic}`,
      resolutionSource: 'framework_anchor'
    };
  }

  // 3. High-Precision Title/Topic Keyword Extraction
  const titleTopicText = `${candidate?.topic || ''} ${candidate?.slug || ''} ${candidate?.title || ''}`;
  for (const rule of DMBOK_KEYWORD_RULES) {
    if (rule.regex.test(titleTopicText)) {
      return {
        category: rule.category,
        parentMoc: `MOC - DMBOK - ${rule.category}`,
        resolutionSource: `high_precision_title_keyword (${rule.category})`
      };
    }
  }

  // 4. Domain Cluster Mapping Matrix
  const domains = candidate?.domainClusters || (candidate?.domain_cluster ? [candidate.domain_cluster] : []);
  for (const dom of domains) {
    if (DOMAIN_TO_DMBOK_MAP[dom]) {
      const mapped = DOMAIN_TO_DMBOK_MAP[dom];
      return {
        category: mapped,
        parentMoc: `MOC - DMBOK - ${mapped}`,
        resolutionSource: `domain_cluster_map (${dom})`
      };
    }
  }

  // 5. Broader Contextual Keyword Extraction (Tags, referencing artifacts)
  const broaderText = [
    ...(candidate?.referencingArtifacts || []),
    ...(candidate?.tags || [])
  ].join(' ');

  for (const rule of DMBOK_KEYWORD_RULES) {
    if (rule.regex.test(broaderText)) {
      return {
        category: rule.category,
        parentMoc: `MOC - DMBOK - ${rule.category}`,
        resolutionSource: `context_keyword_rule (${rule.category})`
      };
    }
  }

  // 6. Intelligent Fallback: Data Architecture (rather than generic Data Governance)
  return {
    category: 'Data Architecture',
    parentMoc: 'MOC - DMBOK - Data Architecture',
    resolutionSource: 'fallback_architecture'
  };
}

/**
 * Reclassifies notes across the vault that were historically defaulted to "Data Governance"
 * when their title, domain_cluster, or keywords indicate a specific DMBOK discipline.
 *
 * @param {string} vaultRoot
 * @param {boolean} [dryRun=false]
 * @returns {{ audited: number, reclassified: number, breakdown: object }}
 */
export function reclassifyVaultDmbokTaxonomy(vaultRoot, dryRun = false) {
  const wikiDir = path.join(vaultRoot, 'wiki');
  if (!fs.existsSync(wikiDir)) return { audited: 0, reclassified: 0, breakdown: {} };

  function getMarkdownFiles(dir) {
    let results = [];
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory() && entry.name !== '.git' && entry.name !== 'node_modules') {
        results = results.concat(getMarkdownFiles(fullPath));
      } else if (entry.isFile() && entry.name.endsWith('.md')) {
        results.push(fullPath);
      }
    }
    return results;
  }

  const allMds = getMarkdownFiles(wikiDir);
  let reclassified = 0;
  const breakdown = {};

  for (const filePath of allMds) {
    const content = fs.readFileSync(filePath, 'utf-8');
    const dmbokMatch = content.match(/dmbok_category:\s*"([^"]+)"/);
    const domainMatch = content.match(/domain_cluster:\s*"([^"]+)"/);
    const titleMatch = content.match(/title:\s*"([^"]+)"/);
    const baseName = path.basename(filePath, '.md');

    if (dmbokMatch && domainMatch) {
      const currentDmbok = dmbokMatch[1];
      const currentDomain = domainMatch[1];
      const title = titleMatch ? titleMatch[1] : baseName;

      // Only reclassify if currently tagged as generic "Data Governance"
      if (currentDmbok === 'Data Governance') {
        const resolved = resolveDmbokTaxonomy({
          title,
          slug: baseName,
          topic: baseName,
          domain_cluster: currentDomain
        });

        if (resolved.category !== 'Data Governance') {
          const newContent = content.replace(
            /dmbok_category:\s*"Data Governance"/,
            `dmbok_category: "${resolved.category}"`
          );

          if (!dryRun && newContent !== content) {
            fs.writeFileSync(filePath, newContent, 'utf-8');
          }

          reclassified++;
          breakdown[resolved.category] = (breakdown[resolved.category] || 0) + 1;
        }
      }
    }
  }

  return { audited: allMds.length, reclassified, breakdown };
}

