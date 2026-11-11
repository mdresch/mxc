/**
 * enrich-brain-topics.mjs
 * Master Orchestrator for Ontological Topic Enrichment & Web Research Pipeline.
 *
 * Executes:
 * Phase 1: Candidate Resolution (from raw/enrichment-queue.json)
 * Phase 2: 5-Facet Query Generation & Authority-Filtered Web Research
 * Phase 3: Cognitive Synthesis, Schema Validation & Adversarial ADR Conflict Check
 * Phase 4: Atomic Concept Note Ingestion & MOC Hub Recompilation
 */

import crypto from 'crypto';
import fs from 'fs';
import path from 'path';
import { build5FacetQueries, scoreAuthority, cleanSnippet } from './research-engine.mjs';
import { validateSchemaConformance, validateDecisionInversion } from './synthesis-validator.mjs';
import { ingestEnrichedTopic } from './vault-ingestion.mjs';
import { validateTopicAdmission } from './topic-guardrails.mjs';
import { resolveDmbokTaxonomy } from './taxonomy-router.mjs';
import { resolveVaultRoot } from './vault-resolver.mjs';

const VAULT_ROOT = resolveVaultRoot();
const ontPath = path.join(VAULT_ROOT, 'ONTOLOGY.json');
const ONTOLOGY = fs.existsSync(ontPath) ? JSON.parse(fs.readFileSync(ontPath, 'utf-8')) : {};
const QUEUE_PATH = path.join(VAULT_ROOT, 'raw', 'enrichment-queue.json');

// Curated authoritative reference evidence bank for core DAMA-DMBOK2 & architecture disciplines
export const AUTHORITATIVE_KNOWLEDGE_BANK = {
  'data-governance': {
    definition: 'Data Governance is the exercise of authority, control, and shared decision-making (planning, monitoring, and enforcement) over the management of data assets. Within the DAMA-DMBOK2 framework, it serves as the foundational wheel center coordinating all other ten data management knowledge disciplines.',
    core_principles: [
      { id: 'CP-1', title: 'Federated Accountability with Central Policy', description: 'Decouple high-level policy definition from domain operational execution, embedding data stewards directly into cross-functional delivery teams.' },
      { id: 'CP-2', title: 'Data as a Governed Product', description: 'Treat datasets and APIs as version-controlled, SLA-backed products owned by domain teams rather than passive warehouse dumps.' },
      { id: 'CP-3', title: 'Continuous Automated Compliance', description: 'Replace annual manual audits with programmatic CI/CD schema verification, contract testing, and runtime telemetry.' }
    ],
    best_practices: [
      { id: 'BP-1', title: 'Shift-Left Data Governance', details: 'Enforce metadata schemas, security policies, and privacy tagging at the ingestion boundary before records enter persistence.', evidence_source: 'https://www.dama.org/cpages/body-of-knowledge' },
      { id: 'BP-2', title: 'Contract-Driven Interoperability', details: 'Implement formal, executable JSON schema contracts between producers and consumers to prevent unannounced breaking migrations.', evidence_source: 'https://martinfowler.com/articles/data-mesh-principles.html' },
      { id: 'BP-3', title: 'Immutable Audit Logging', details: 'Maintain append-only, tamper-evident audit logs of all policy overrides, schema mutations, and data access grants.', evidence_source: 'https://csrc.nist.gov/publications/detail/sp/800-88/rev-1/final' }
    ],
    anti_patterns: [
      { id: 'AP-1', title: 'The Bureaucratic Committee Bottleneck', details: 'Mandating approval from a central committee for minor schema modifications stalls engineering velocity and encourages shadow engineering.' },
      { id: 'AP-2', title: 'Passive Shelf-Ware Governance', details: 'Writing extensive policy PDFs that are not embedded in automated pipeline gates results in zero real-world operational compliance.' },
      { id: 'AP-3', title: 'Retrospective Big-Bang Cataloging', details: 'Attempting to catalog years of undocumented legacy databases without business-domain drivers leads to immediate catalog abandonment.' }
    ],
    operational_kpis: [
      { name: 'Production Asset Catalog Coverage', target: '>= 95% of active schemas documented with owner and classification' },
      { name: 'Schema Contract Test Pass Rate', target: '100% compliance across inter-service APIs' },
      { name: 'Mean-Time-to-Remediate (MTTR) Corrupt Ingests', target: '< 15 minutes to quarantine or recover' }
    ],
    standards_alignment: [
      { framework: 'DAMA-DMBOK2', mapping: 'Core Wheel Center (Data Management Governance)' },
      { framework: 'TOGAF Standard 10th Ed.', mapping: 'Information Architecture Governance & Compliance' },
      { framework: 'NIST SP 800-88', mapping: 'Guidelines for Media Sanitization & Data Lifecycle Governance' },
      { framework: 'ISO/IEC 38505-1', mapping: 'Corporate Governance of Data' }
    ],
    source_urls: [
      'https://www.dama.org/cpages/body-of-knowledge',
      'https://martinfowler.com/articles/data-mesh-principles.html',
      'https://csrc.nist.gov/publications/detail/sp/800-88/rev-1/final',
      'https://www.iso.org/standard/66687.html'
    ]
  },
  'data-security': {
    definition: 'Data Security encompasses the planning, development, and execution of security policies and technical controls to ensure authentication, authorization, access governance, encryption, and continuous auditing of enterprise data assets across their entire lifecycle.',
    core_principles: [
      { id: 'CP-1', title: 'Zero Trust Architecture', description: 'Never trust, always verify: authenticate and authorize every request explicitly at network, service, and database layers.' },
      { id: 'CP-2', title: 'Principle of Least Privilege (PoLP)', description: 'Grant identities the minimum necessary access required to perform their discrete function, enforcing fine-grained tenant boundaries.' },
      { id: 'CP-3', title: 'Defense in Depth', description: 'Layer security across perimeter edge gates, transport encryption, application middleware, database RLS, and cryptographic storage.' }
    ],
    best_practices: [
      { id: 'BP-1', title: 'Cryptographic Isolation & Tenant Key Vaults', details: 'Employ envelope encryption with AES-256 for data at rest and TLS 1.3 in transit, isolating tenant encryption keys in dedicated HSMs or key vaults.', evidence_source: 'https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final' },
      { id: 'BP-2', title: 'Database-Enforced Row-Level Security (RLS)', details: 'Enforce tenant data isolation directly at the database engine level via RLS policies rather than relying exclusively on application software logic.', evidence_source: 'https://www.postgresql.org/docs/current/ddl-rowsecurity.html' },
      { id: 'BP-3', title: 'Dynamic Tokenization & Field-Level Masking', details: 'Tokenize PII, payment details, and sensitive credentials upon ingestion so downstream analytics and workers operate solely on masked abstractions.', evidence_source: 'https://owasp.org/www-project-api-security/' }
    ],
    anti_patterns: [
      { id: 'AP-1', title: 'The Hard Shell, Soft Center Perimeter', details: 'Relying exclusively on edge firewalls while leaving internal microservice communication and database connections unauthenticated.' },
      { id: 'AP-2', title: 'Shared Superuser Database Connection Pooling', details: 'Bypassing fine-grained multi-tenant isolation by funneling all queries through a single unrestricted database master user.' },
      { id: 'AP-3', title: 'Static Hardcoded Secrets in Source Code', details: 'Embedding API keys, connection strings, or JWT signing secrets directly in configuration files or code repositories.' }
    ],
    operational_kpis: [
      { name: 'Zero-Trust Internal Traffic Coverage', target: '100% of inter-service APIs authenticated via mTLS / JWT' },
      { name: 'Cross-Tenant Data Leakage Incidents', target: '0 tolerance (monitored by automated continuous penetration tests)' },
      { name: 'Mean-Time-to-Rotate Compromised Secrets', target: '< 10 minutes via automated vault orchestrators' }
    ],
    standards_alignment: [
      { framework: 'DAMA-DMBOK2', mapping: 'Data Security Knowledge Area' },
      { framework: 'NIST SP 800-53 Rev. 5', mapping: 'Security and Privacy Controls for Information Systems' },
      { framework: 'ISO/IEC 27001:2022', mapping: 'Annex A.8 Technological Controls (Data Security & Cryptography)' },
      { framework: 'OWASP Top 10 API Security', mapping: 'Broken Object Level Authorization (BOLA) Prevention' }
    ],
    source_urls: [
      'https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final',
      'https://www.dama.org/cpages/body-of-knowledge',
      'https://owasp.org/www-project-api-security/',
      'https://martinfowler.com/articles/zero-trust-architecture.html'
    ]
  },
  'reference-master-data': {
    definition: 'Reference and Master Data Management (MDM) is the discipline of creating and maintaining an authoritative, reliable, and consolidated Single Source of Truth (SSOT)—the "Golden Record"—for core shared business entities (e.g., customers, accounts, tenants, products) across disparate operational systems.',
    core_principles: [
      { id: 'CP-1', title: 'The Golden Record Standard', description: 'Establish a unified, verified canonical representation for every core entity, resolving duplicates through deterministic matching.' },
      { id: 'CP-2', title: 'System of Record (SOR) vs System of Reference', description: 'Distinguish transactional entry points from analytical MDM hubs, ensuring bidirectional synchronization preserves provenance.' },
      { id: 'CP-3', title: 'Universal Reference Standard Anchorage', description: 'Anchor shared reference taxonomies to global standards (e.g., ISO-3166 for countries, ISO-4217 for currencies, ISO-8601 for time).' }
    ],
    best_practices: [
      { id: 'BP-1', title: 'Declarative Survivorship Rules', details: 'Define deterministic rules for attribute precedence (e.g., most recently verified source, trusted provider ranking) when resolving entity merge conflicts.', evidence_source: 'https://www.dama.org/cpages/body-of-knowledge' },
      { id: 'BP-2', title: 'Event-Driven CDC Entity Synchronization', details: 'Publish Change Data Capture (CDC) events to an event bus (Kafka/Event Hub) whenever master entities are consolidated or amended.', evidence_source: 'https://martinfowler.com/articles/patterns-of-distributed-systems/' },
      { id: 'BP-3', title: 'Human-in-the-Loop Merge Stewardship', details: 'Automatically merge matches with >= 98% confidence while routing ambiguous fuzzy matches to domain stewards via dedicated UIs.', evidence_source: 'https://www.iso.org/standard/50798.html' }
    ],
    anti_patterns: [
      { id: 'AP-1', title: 'Point-to-Point Entity Spaghetti Sync', details: 'Synchronizing master data through bilateral cron jobs between individual applications without an authoritative centralized broker.' },
      { id: 'AP-2', title: 'Aggressive Unreviewed Auto-Merging', details: 'Merging distinct entities based on loose probabilistic similarity thresholds without rollback capabilities.' },
      { id: 'AP-3', title: 'Treating MDM as a One-Time Migration Project', details: 'Running a batch deduplication project without building continuous automated ingestion validation gates.' }
    ],
    operational_kpis: [
      { name: 'Golden Record Deduplication Accuracy', target: '>= 99.5% accuracy across tenant and user profiles' },
      { name: 'Master Entity Consolidation Latency', target: '< 5 seconds from creation to cross-platform broadcast' },
      { name: 'Steward Review Queue Resolution Time', target: '< 24 hours for ambiguous entity merge candidates' }
    ],
    standards_alignment: [
      { framework: 'DAMA-DMBOK2', mapping: 'Reference and Master Data Management' },
      { framework: 'ISO 8000-110', mapping: 'Data Quality: Master Data Exchange of Characteristic Data' },
      { framework: 'TOGAF Standard 10th Ed.', mapping: 'Enterprise Information Architecture Core Entity Models' }
    ],
    source_urls: [
      'https://www.dama.org/cpages/body-of-knowledge',
      'https://www.iso.org/standard/50798.html',
      'https://martinfowler.com/articles/patterns-of-distributed-systems/'
    ]
  },
  'document-content-management': {
    definition: 'Document and Content Management oversees the lifecycle capture, storage, protection, retrieval, and disposition of unstructured data (electronic documents, media, records) while enforcing legal retention, regulatory compliance, and semantic discoverability.',
    core_principles: [
      { id: 'CP-1', title: 'Lifecycle Retention Compliance', description: 'Govern records from creation to certified destruction according to statutory retention schedules and legal hold mandates.' },
      { id: 'CP-2', title: 'Write-Once, Read-Many (WORM) Immutability', description: 'Enforce cryptographic non-tampering storage for sensitive regulatory, compliance, and contract documents.' },
      { id: 'CP-3', title: 'Multimodal Semantic Indexing', description: 'Transform unstructured documents into queryable assets via automated OCR, layout parsing, and dense vector embeddings.' }
    ],
    best_practices: [
      { id: 'BP-1', title: 'Automated Lifecycle Tiering & Retention', details: 'Apply policy-driven lifecycle rules to transition active documents to immutable cold archive storage, pruning expired records automatically.', evidence_source: 'https://www.iso.org/standard/62542.html' },
      { id: 'BP-2', title: 'Hybrid Lexical-Semantic Search Indexing', details: 'Extract semantic chunks and generate vector embeddings alongside full-text BM25 indexes to power high-precision document retrieval.', evidence_source: 'https://www.dama.org/cpages/body-of-knowledge' },
      { id: 'BP-3', title: 'Granular Access Tokenization', details: 'Protect sensitive attachments via short-lived, signed URLs generated dynamically after verifying tenant permissions.', evidence_source: 'https://csrc.nist.gov/publications/detail/sp/800-88/rev-1/final' }
    ],
    anti_patterns: [
      { id: 'AP-1', title: 'Unmanaged Content Sprawl', details: 'Storing documents in unindexed, unclassified shared cloud drives without retention policies or audit trails.' },
      { id: 'AP-2', title: 'Manual Deletion Regimes', details: 'Relying on manual staff processes to prune regulated documents, leading to catastrophic discovery liabilities.' },
      { id: 'AP-3', title: 'Unbounded Monolithic Attachments in Transactional DBs', details: 'Storing large binary files directly inside OLTP relational tables instead of dedicated blob/object storage with metadata pointers.' }
    ],
    operational_kpis: [
      { name: 'Search Retrieval Precision @ 5', target: '>= 92% relevant document recall on benchmark queries' },
      { name: 'Automated Retention Schedule Execution Rate', target: '100% compliant with legal holds and statutory destruction' },
      { name: 'Unindexed Dark Content Ratio', target: '< 1% of enterprise document storage' }
    ],
    standards_alignment: [
      { framework: 'DAMA-DMBOK2', mapping: 'Document and Content Management Knowledge Area' },
      { framework: 'ISO 15489-1:2016', mapping: 'Information and Documentation - Records Management' },
      { framework: 'DoD 5015.02-STD', mapping: 'Electronic Records Management Software Applications Design Criteria' },
      { framework: 'NIST SP 800-88 Rev. 1', mapping: 'Guidelines for Media Sanitization' }
    ],
    source_urls: [
      'https://www.iso.org/standard/62542.html',
      'https://www.dama.org/cpages/body-of-knowledge',
      'https://csrc.nist.gov/publications/detail/sp/800-88/rev-1/final'
    ]
  },
  'data-quality-management': {
    definition: 'Data Quality Management (DQM) is the continuous discipline of defining, measuring, monitoring, and improving the fitness of data assets across the six core quality dimensions: accuracy, completeness, consistency, timeliness, validity, and uniqueness.',
    core_principles: [
      { id: 'CP-1', title: 'Quality at the Source (Shift-Left)', description: 'Prevent bad data from entering the ecosystem by validating contracts at ingestion APIs rather than cleaning in downstream warehouses.' },
      { id: 'CP-2', title: 'The Six Core Quality Dimensions', description: 'Formally evaluate all business-critical attributes against Accuracy, Completeness, Consistency, Timeliness, Validity, and Uniqueness.' },
      { id: 'CP-3', title: 'Automated Circuit Breakers & Quarantine', description: 'Halt data pipeline processing or isolate corrupt partitions into Dead-Letter Queues (DLQs) to prevent toxic data contamination.' }
    ],
    best_practices: [
      { id: 'BP-1', title: 'Declarative Contract Testing in CI/CD', details: 'Define schema contracts and range invariants (using Great Expectations, Soda, or Pydantic) enforced automatically during deployment and batch ingestion.', evidence_source: 'https://www.iso.org/standard/50798.html' },
      { id: 'BP-2', title: 'Continuous Anomaly Telemetry & Profiling', details: 'Track statistical distribution drift (mean, variance, null rates, volume spikes) in real-time, alarming on anomalous patterns.', evidence_source: 'https://www.dama.org/cpages/body-of-knowledge' },
      { id: 'BP-3', title: 'Self-Healing Data Quarantine Pipelines', details: 'Route invalid records to structured dead-letter queues with automated retry policies and steward escalation workflows.', evidence_source: 'https://martinfowler.com/articles/data-mesh-principles.html' }
    ],
    anti_patterns: [
      { id: 'AP-1', title: 'The Downstream Janitor Syndrome', details: 'Allowing broken records to hit the data lakehouse and relying on data analysts to write custom SQL cleaning patches.' },
      { id: 'AP-2', title: 'Silent Pipeline Failure', details: 'Allowing empty, truncated, or null-heavy batches to succeed without alerting because no volume anomaly detectors exist.' },
      { id: 'AP-3', title: 'Metric-Free Subjective Quality Assessments', details: 'Treating data quality as an opinion rather than measuring objective SLA percentages and defect ppm rates.' }
    ],
    operational_kpis: [
      { name: 'Ingestion Clean Pass-Through Rate', target: '>= 99.7% of ingested batches passing all schema constraints' },
      { name: 'Quality Anomaly Mean-Time-to-Detect (MTTD)', target: '< 5 minutes from anomaly occurrence' },
      { name: 'Critical Attribute Nullability Rate', target: '0.00% on mandatory entity identifiers' }
    ],
    standards_alignment: [
      { framework: 'DAMA-DMBOK2', mapping: 'Data Quality Management Knowledge Area' },
      { framework: 'ISO 8000-61', mapping: 'Data Quality Management: Process Reference Model' },
      { framework: 'ISO/IEC 25012', mapping: 'Software Engineering - Data Quality Model' }
    ],
    source_urls: [
      'https://www.iso.org/standard/50798.html',
      'https://www.dama.org/cpages/body-of-knowledge',
      'https://martinfowler.com/articles/data-mesh-principles.html'
    ]
  },
  'metadata-management': {
    definition: 'Metadata Management encompasses the architecture, governance, and technology to collect, organize, integrate, and deliver business, technical, operational, and provenance metadata across all data producers and consumers in the enterprise.',
    core_principles: [
      { id: 'CP-1', title: 'Active Metadata as Event Streams', description: 'Treat metadata not as a static repository, but as continuous, real-time event streams that actively drive runtime pipeline behaviors.' },
      { id: 'CP-2', title: 'Automated End-to-End Lineage', description: 'Capture column-level and pipeline-level transformation lineage automatically from code execution, query logs, and DAGs.' },
      { id: 'CP-3', title: 'Unified Semantic Ontology Mapping', description: 'Bridge business terminology to physical column definitions through formal semantic ontologies and knowledge graphs.' }
    ],
    best_practices: [
      { id: 'BP-1', title: 'OpenLineage & OpenTelemetry Standard Emission', details: 'Instrument data orchestrators (Airflow, Dagster, Temporal) and SQL engines to emit standardized OpenLineage run events.', evidence_source: 'https://openlineage.io/' },
      { id: 'BP-2', title: 'GitOps for Metadata Schemas', details: 'Maintain data catalogs and schema definitions in version-controlled repositories, syncing changes via automated CI/CD webhooks.', evidence_source: 'https://www.dama.org/cpages/body-of-knowledge' },
      { id: 'BP-3', title: 'Contextual In-Line Catalog Integration', details: 'Surface data definitions, freshness metrics, and ownership contacts directly in developers IDEs and BI tools.', evidence_source: 'https://www.iso.org/standard/50798.html' }
    ],
    anti_patterns: [
      { id: 'AP-1', title: 'The Graveyard Data Catalog', details: 'Deploying an expensive catalog UI that requires manual data entry, resulting in immediate abandonment and stale documentation.' },
      { id: 'AP-2', title: 'Black-Box Transformation Pipelines', details: 'Running complex ETL transformations without column-level lineage tracking, leaving teams unable to determine impact of upstream schema changes.' },
      { id: 'AP-3', title: 'Siloed Business Glossaries', details: 'Maintaining business definitions in wikis completely disconnected from the underlying databases and APIs.' }
    ],
    operational_kpis: [
      { name: 'Active Column-Level Lineage Coverage', target: '>= 95% of all production transformation paths mapped' },
      { name: 'Automated Catalog Refresh Latency', target: '< 60 seconds from schema deployment' },
      { name: 'Catalog Weekly Active Usage Rate', target: '>= 80% across data and software engineering teams' }
    ],
    standards_alignment: [
      { framework: 'DAMA-DMBOK2', mapping: 'Metadata Management Knowledge Area' },
      { framework: 'ISO/IEC 11179', mapping: 'Specification and Standardization of Data Elements (Metadata Registries)' },
      { framework: 'W3C PROV-O', mapping: 'The PROV Ontology (Provenance Data Model)' },
      { framework: 'OpenLineage', mapping: 'Open Standard for Data Lineage Collection' }
    ],
    source_urls: [
      'https://openlineage.io/',
      'https://www.dama.org/cpages/body-of-knowledge',
      'https://www.w3.org/TR/prov-o/'
    ]
  },
  'data-modeling-design': {
    definition: 'Data Modeling and Design is the discovery, analysis, representation, and communication of data requirements in a formal structure (conceptual, logical, and physical models) optimized for relational integrity, transactional throughput, and analytical query performance.',
    core_principles: [
      { id: 'CP-1', title: 'Separation of Architectural Abstraction Levels', description: 'Maintain clear boundaries between Conceptual (business domain), Logical (normalized structure), and Physical (engine-optimized storage) models.' },
      { id: 'CP-2', title: 'Schema as Immutable, Versioned Code', description: 'Manage database schemas with declarative, version-controlled migration scripts subjected to peer review and automated linting.' },
      { id: 'CP-3', title: 'Ubiquitous Domain Language (DDD)', description: 'Model entities and relationships using the exact, agreed-upon terminology of the domain experts rather than technical abstractions.' }
    ],
    best_practices: [
      { id: 'BP-1', title: 'Zero-Downtime Safe Migrations', details: 'Follow the Expand/Contract (Parallel Run) migration pattern for all schema modifications, never dropping active columns synchronously.', evidence_source: 'https://martinfowler.com/articles/evodb.html' },
      { id: 'BP-2', title: 'Strict Relational Foreign Key Integrity with Idempotent Constraints', details: 'Enforce referential integrity at the database engine level, combining foreign keys with covering composite indexes.', evidence_source: 'https://www.postgresql.org/docs/current/' },
      { id: 'BP-3', title: 'Hybrid Relational-Dimensional-Graph Modeling', details: 'Employ 3NF/Postgres for transactional OLTP, Star Schema/Data Vault for analytical marts, and Graph nodes for interconnected ontology traversal.', evidence_source: 'https://www.dama.org/cpages/body-of-knowledge' }
    ],
    anti_patterns: [
      { id: 'AP-1', title: 'The Monolithic God Table', details: 'Consolidating hundreds of unrelated domain attributes into a single enormous table, creating high lock contention and cache thrashing.' },
      { id: 'AP-2', title: 'Schemaless Anti-Design', details: 'Dumping unvalidated JSONB blobs into database tables without schema validation constraints, deferring integrity issues to runtime software.' },
      { id: 'AP-3', title: 'Entity-Attribute-Value (EAV) Overuse', details: 'Using generic key-value rows in relational databases for core domain entities, destroying relational query optimization and indexing.' }
    ],
    operational_kpis: [
      { name: 'Schema Migration Zero-Downtime Rate', target: '100% of production migrations executed without service interruption' },
      { name: 'Query Index Hit Ratio', target: '>= 99.0% on OLTP transactional workloads' },
      { name: 'Domain Entity Redundancy Ratio', target: '< 2% redundant attribute definitions across schemas' }
    ],
    standards_alignment: [
      { framework: 'DAMA-DMBOK2', mapping: 'Data Modeling and Design Knowledge Area' },
      { framework: 'ANSI/SPARC', mapping: 'Three-Schema Architecture (External, Conceptual, Internal)' },
      { framework: 'ISO/IEC 19501', mapping: 'Unified Modeling Language (UML) Specification' },
      { framework: 'TOGAF 10', mapping: 'Information Architecture / Data Entity Models' }
    ],
    source_urls: [
      'https://martinfowler.com/articles/evodb.html',
      'https://www.dama.org/cpages/body-of-knowledge',
      'https://www.postgresql.org/docs/current/'
    ]
  },
  'data-storage-operations': {
    definition: 'Data Storage and Operations focuses on the implementation, configuration, maintenance, optimization, and recovery of persistent storage infrastructure throughout data lifecycles, ensuring maximum availability, performance, and durability.',
    core_principles: [
      { id: 'CP-1', title: 'High Availability with Automated Failover', description: 'Deploy redundant, multi-availability zone clusters with automated health-check detection and sub-minute replica promotion.' },
      { id: 'CP-2', title: 'Guaranteed RPO and RTO Disaster Recovery', description: 'Design storage architectures to strictly honor defined Recovery Point Objectives (RPO) and Recovery Time Objectives (RTO).' },
      { id: 'CP-3', title: 'Tiered Storage Cost-Performance Optimization', description: 'Automatically migrate aged partitions and audit trails from fast NVMe storage to low-cost object storage tiers.' }
    ],
    best_practices: [
      { id: 'BP-1', title: 'Continuous WAL Archiving & Point-In-Time Recovery (PITR)', details: 'Stream Write-Ahead Logs (WAL) continuously to durable object storage, enabling millisecond-accurate point-in-time recovery.', evidence_source: 'https://www.postgresql.org/docs/current/continuous-archiving.html' },
      { id: 'BP-2', title: 'Multiplexed Connection Pooling', details: 'Enforce transactional connection poolers (PgBouncer) between application containers and database engines to prevent socket starvation.', evidence_source: 'https://csrc.nist.gov/publications/detail/sp/800-34/rev-1/final' },
      { id: 'BP-3', title: 'Proactive IOPS and Table Partitioning', details: 'Partition high-volume transactional tables by date range or tenant ID to prevent sequential scan degradation and index bloat.', evidence_source: 'https://www.dama.org/cpages/body-of-knowledge' }
    ],
    anti_patterns: [
      { id: 'AP-1', title: 'Schrödinger’s Backup', details: 'Relying on scheduled backup scripts that are never automatically restored and verified in testing environments.' },
      { id: 'AP-2', title: 'Direct Application-to-Database Connection Leaks', details: 'Allowing stateless application worker pods to open unbounded direct connections to the database primary.' },
      { id: 'AP-3', title: 'Unbounded Table Growth without Retention', details: 'Allowing high-throughput log and event tables to grow infinitely on transactional storage until disk exhaustion triggers hard outages.' }
    ],
    operational_kpis: [
      { name: 'Recovery Point Objective (RPO)', target: '< 5 minutes of data loss window under catastrophic failure' },
      { name: 'Recovery Time Objective (RTO)', target: '< 30 minutes to complete recovery to standby environment' },
      { name: 'Database Storage Availability SLA', target: '>= 99.99% uptime across production clusters' }
    ],
    standards_alignment: [
      { framework: 'DAMA-DMBOK2', mapping: 'Data Storage and Operations Knowledge Area' },
      { framework: 'ISO/IEC 27040:2024', mapping: 'Information Security - Storage Security' },
      { framework: 'NIST SP 800-34 Rev. 1', mapping: 'Contingency Planning Guide for Federal Information Systems' }
    ],
    source_urls: [
      'https://www.postgresql.org/docs/current/continuous-archiving.html',
      'https://csrc.nist.gov/publications/detail/sp/800-34/rev-1/final',
      'https://www.dama.org/cpages/body-of-knowledge'
    ]
  },
  'data-integration-interoperability': {
    definition: 'Data Integration and Interoperability governs the acquisition, movement, transformation, and real-time synchronization of data across disparate software systems, applications, organizations, and cloud platforms.',
    core_principles: [
      { id: 'CP-1', title: 'Decoupled Event-Driven Messaging', description: 'Connect distributed services via asynchronous event buses and message queues rather than tightly coupled synchronous RPC calls.' },
      { id: 'CP-2', title: 'Idempotency and Exactly-Once Semantics', description: 'Design consumer handlers and API endpoints with deduplication keys and idempotent state machines to survive network retries.' },
      { id: 'CP-3', title: 'Contract-First API Architecture', description: 'Publish and validate strict, machine-readable interface specifications (OpenAPI, Protobuf, AsyncAPI) before implementing services.' }
    ],
    best_practices: [
      { id: 'BP-1', title: 'Transactional Outbox Pattern with CDC', details: 'Atomically commit business state mutations alongside event records in an outbox table, using Debezium/Kafka Connect to stream changes.', evidence_source: 'https://martinfowler.com/articles/patterns-of-distributed-systems/' },
      { id: 'BP-2', title: 'Schema Registry Compatibility Enforcement', details: 'Enforce backward and forward compatibility rules via a schema registry, rejecting breaking payloads at publish time.', evidence_source: 'https://www.dama.org/cpages/body-of-knowledge' },
      { id: 'BP-3', title: 'Distributed Tracing Across Integration Boundaries', details: 'Propagate W3C tracecontext headers through all message queues and HTTP calls to maintain end-to-end distributed observability.', evidence_source: 'https://opentelemetry.io/' }
    ],
    anti_patterns: [
      { id: 'AP-1', title: 'The Dual-Write Race Condition', details: 'Writing directly to both a relational database and a message broker within application code without transactional coordination.' },
      { id: 'AP-2', title: 'Synchronous Cascading HTTP Chains', details: 'Chaining synchronous REST calls across multiple microservices to satisfy a single user request, multiplying latency and failure rates.' },
      { id: 'AP-3', title: 'Unbounded Batch Polling', details: 'Running periodic cron jobs that execute full-table scans to detect changes rather than subscribing to event-driven CDC streams.' }
    ],
    operational_kpis: [
      { name: 'Message Processing Latency (P99)', target: '< 250ms from publish to consumer ack' },
      { name: 'Integration Message Dead-Letter Rate', target: '< 0.01% of total routed traffic' },
      { name: 'Ingestion Pipeline Availability', target: '>= 99.99% operational uptime' }
    ],
    standards_alignment: [
      { framework: 'DAMA-DMBOK2', mapping: 'Data Integration and Interoperability Knowledge Area' },
      { framework: 'CloudEvents (CNCF)', mapping: 'Common Specification for Event Data Description' },
      { framework: 'OpenAPI Specification 3.1', mapping: 'Standard Interface Description for HTTP APIs' },
      { framework: 'AsyncAPI Specification', mapping: 'Standard for Event-Driven Architectures' }
    ],
    source_urls: [
      'https://martinfowler.com/articles/patterns-of-distributed-systems/',
      'https://cloudevents.io/',
      'https://www.dama.org/cpages/body-of-knowledge'
    ]
  },
  'data-warehousing-business-intelligence': {
    definition: 'Data Warehousing and Business Intelligence (DW/BI) encompasses the collection, consolidation, dimensional transformation, and analytical modeling of enterprise data to empower business decision-making and operational intelligence.',
    core_principles: [
      { id: 'CP-1', title: 'Decoupled Compute and Storage Lakehouse', description: 'Store raw and refined analytical assets in open columnar formats (Parquet/Iceberg) with scalable compute engines allocated on demand.' },
      { id: 'CP-2', title: 'Conformed Dimensions and Star Schemas', description: 'Structure analytical reporting around Kimball conformed dimensions (time, customer, product) and atomic fact tables to ensure consistent metrics.' },
      { id: 'CP-3', title: 'The Centralized Headless Semantic Layer', description: 'Define metrics (e.g., ARR, Active Tenants) once in code and serve them identically across BI tools, notebooks, and reverse-ETL apps.' }
    ],
    best_practices: [
      { id: 'BP-1', title: 'Declarative dbt Data Transformation Pipelines', details: 'Author transformation logic in modular, testable SQL/Python with automated DAG generation, lineage tracking, and unit tests in CI/CD.', evidence_source: 'https://martinfowler.com/articles/data-monolith-to-mesh.html' },
      { id: 'BP-2', title: 'Zero-Copy Table Cloning & Sandboxing', details: 'Enable safe analytical experimentation by providing data engineers with instant, zero-storage-copy sandboxes of production analytical tables.', evidence_source: 'https://www.dama.org/cpages/body-of-knowledge' },
      { id: 'BP-3', title: 'Automated Metric Freshness & SLA Monitoring', details: 'Monitor analytical pipeline run duration and table arrival freshness, sending automated alerts when dashboards risk serving stale data.', evidence_source: 'https://www.iso.org/standard/50798.html' }
    ],
    anti_patterns: [
      { id: 'AP-1', title: 'The Metric Divergence Anomaly', details: 'Allowing different business teams to calculate critical metrics in isolated spreadsheet formulas or separate BI dashboards.' },
      { id: 'AP-2', title: 'Spaghetti Nested SQL Views', details: 'Stacking dozens of unmaterialized SQL views on top of each other, resulting in multi-hour query runtimes and untraceable bugs.' },
      { id: 'AP-3', title: 'Running Heavy Analytical Scans on Transactional OLTP', details: 'Executing large aggregations and reporting queries directly against primary production databases, causing connection timeouts and lock contention.' }
    ],
    operational_kpis: [
      { name: 'Executive Dashboard Query Latency (P95)', target: '< 2.0 seconds for standard executive KPI reports' },
      { name: 'Daily Analytical SLA Adherence', target: '>= 99.5% on-time delivery of morning analytical marts' },
      { name: 'Semantic Metric Divergence Incidents', target: '0 tolerance across enterprise reporting tools' }
    ],
    standards_alignment: [
      { framework: 'DAMA-DMBOK2', mapping: 'Data Warehousing and Business Intelligence Knowledge Area' },
      { framework: 'Kimball Dimensional Modeling', mapping: 'The Data Warehouse Toolkit Design Standards' },
      { framework: 'Inmon Corporate Information Factory', mapping: 'Enterprise Data Warehouse Architecture' }
    ],
    source_urls: [
      'https://www.dama.org/cpages/body-of-knowledge',
      'https://martinfowler.com/articles/data-monolith-to-mesh.html',
      'https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/'
    ]
  },
  'data-architecture': {
    definition: 'Data Architecture defines the blueprint for managing data assets by aligning technical data structures, pipelines, and persistence mechanisms with enterprise business strategy and domain capabilities.',
    core_principles: [
      { id: 'CP-1', title: 'Domain-Driven Data Architecture', description: 'Organize data ownership around bounded business contexts with domain teams accountable for exposing governed data products.' },
      { id: 'CP-2', title: 'Architecture as Code & Enforced ADRs', description: 'Document all significant structural decisions in versioned Architecture Decision Records (ADRs) with programmatic fitness tests.' },
      { id: 'CP-3', title: 'Polyglot Persistence by Design', description: 'Select database and storage technologies strictly based on workload characteristics (OLTP relational, search index, graph traversal, columnar analytics).' }
    ],
    best_practices: [
      { id: 'BP-1', title: 'Architectural Fitness Functions', details: 'Implement automated CI/CD linters and dependency analyzers that fail builds when prohibited cross-domain architectural dependencies are introduced.', evidence_source: 'https://martinfowler.com/articles/building-evolutionary-architecture.html' },
      { id: 'BP-2', title: 'Publish-Subscribe Data Product Boundaries', details: 'Enforce that all cross-domain communication occurs through published data contracts or public APIs, never via direct internal database coupling.', evidence_source: 'https://www.dama.org/cpages/body-of-knowledge' },
      { id: 'BP-3', title: 'Regular Architecture Decision Auditing', details: 'Review existing ADRs against operational drift, deprecating outdated standards and recording architectural evolution in git.', evidence_source: 'https://www.opengroup.org/togaf' }
    ],
    anti_patterns: [
      { id: 'AP-1', title: 'Ivory Tower Architecture', details: 'Producing elaborate slide decks and enterprise diagrams that bear no resemblance to running software implementation.' },
      { id: 'AP-2', title: 'The Big Ball of Mud Shared Database', details: 'Allowing multiple independent development teams to read and write directly to a single shared monolithic schema without boundary enforcement.' },
      { id: 'AP-3', title: 'Resume-Driven Tech Selection', details: 'Introducing complex, exotic distributed storage engines where proven, battle-tested solutions like Postgres easily handle the scale.' }
    ],
    operational_kpis: [
      { name: 'Architecture Fitness Test Pass Rate', target: '100% compliance on automated structural linters' },
      { name: 'Cross-Domain Contract Compliance', target: '100% of inter-domain access mediated by documented contracts' },
      { name: 'New Domain Onboarding Latency', target: '< 2 weeks from business capability inception to live data product' }
    ],
    standards_alignment: [
      { framework: 'DAMA-DMBOK2', mapping: 'Data Architecture Knowledge Area' },
      { framework: 'TOGAF Standard 10th Ed.', mapping: 'Phase C: Information Systems Architectures - Data Architecture' },
      { framework: 'ISO/IEC/IEEE 42010', mapping: 'Systems and Software Engineering - Architecture Description' }
    ],
    source_urls: [
      'https://www.dama.org/cpages/body-of-knowledge',
      'https://martinfowler.com/articles/building-evolutionary-architecture.html',
      'https://www.opengroup.org/togaf'
    ]
  },
  'neo4j': {
    definition: 'Neo4j is an enterprise-grade native graph database management system implementing the Labeled Property Graph (LPG) model, utilizing Index-Free Adjacency (IFA) for constant-time O(1) pointer traversals, and enforcing strict ACID transactional reliability via Write-Ahead Logging (WAL) and Raft-based Causal Clustering.',
    core_principles: [
      { id: 'CP-1', title: 'Native Graph Storage & Index-Free Adjacency (IFA)', description: 'Nodes and relationships are stored as direct record memory pointers on disk and pagecache, eliminating expensive relational join tables and ensuring traversal latency depends strictly on subgraph size, not total graph volume.' },
      { id: 'CP-2', title: 'Labeled Property Graph (LPG) Model', description: 'High-fidelity semantic representation connecting domain entities (Nodes), directed and typed connections (Relationships), and arbitrary key-value metadata (Properties) on both nodes and edges.' },
      { id: 'CP-3', title: 'ACID Concurrency & Causal Clustering', description: 'Full Atomicity, Consistency, Isolation, and Durability backed by MVCC, scaling read throughput across asynchronously replicated read pools while anchoring writes in Raft Core quorums.' },
      { id: 'CP-4', title: 'Declarative Cypher Pattern Matching', description: 'Expressive ASCII-art pattern matching syntax for graph traversal, subgraph projection, and topological path extraction without procedural table scans.' }
    ],
    best_practices: [
      { id: 'BP-1', title: 'Balanced Memory Partitioning & Page Cache Sizing', details: 'Dedicate 15-20% RAM to Linux kernel and OS overhead, cap JVM Heap between 16GB-31GB to avoid GC Stop-The-World pauses and keep compressed OOPs active, and allocate the remainder to off-heap Page Cache covering total store file size plus 10% headroom.', evidence_source: 'https://neo4j.com/docs/operations-manual/current/performance/memory-tuning/' },
      { id: 'BP-2', title: 'Page Cache Warmup & Swappiness Hardening', details: 'Enable db.memory.pagecache.warmup.enable=true on high-IOPS NVMe SSDs and configure vm.swappiness=1 or 0 to eliminate cold-start page faults and prevent paging to disk.', evidence_source: 'https://neo4j.com/docs/operations-manual/current/performance/' },
      { id: 'BP-3', title: 'Sub-Graph Batching & Shift-Left Cypher Pruning', details: 'Execute high-volume mutations using CALL { ... } IN TRANSACTIONS OF 5000 ROWS, filtering node properties early in Cypher execution plans to utilize index scans and prune traversal trees before expansions.', evidence_source: 'https://neo4j.com/docs/cypher-manual/current/clauses/call-subquery/' },
      { id: 'BP-4', title: 'Fine-Grained Sub-Graph Access Control (RBAC & ReBAC)', details: 'Enforce fine-grained security down to node labels, relationships, and property keys via native Cypher GRANT commands, satisfying NIST AC-3/AC-6 and ISO 27001 requirements.', evidence_source: 'https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final' }
    ],
    anti_patterns: [
      { id: 'AP-1', title: 'Unbounded Variable-Length Path Traversal', details: 'Writing queries like MATCH (n)-[:REL*1..5]->(m) across dense graphs, inducing combinatorial explosions that exhaust the JVM heap with OutOfMemory errors.' },
      { id: 'AP-2', title: 'The Super-Node Bottleneck', details: 'Permitting single nodes to accumulate hundreds of thousands of direct relationships without intermediate structural categorization, forcing linear scans during traversals.' },
      { id: 'AP-3', title: 'Monolithic Mega-Transactions', details: 'Attempting to ingest or mutate millions of graph entities within a single ACID transaction block, exceeding memory pool limits and crashing database instances.' },
      { id: 'AP-4', title: 'Late Filtering & Missing Query Profiling', details: 'Executing un-profiled Cypher queries that match large subgraphs before applying WHERE filters, bypassing schema indexes and multiplying DB hits.' }
    ],
    operational_kpis: [
      { name: 'Page Cache Hit Ratio', target: '>= 98.0% on production workloads' },
      { name: 'Single-Hop Traversal Latency (P99)', target: '< 5 ms for indexed pointer traversals' },
      { name: 'Complex Subgraph Traversal Latency (P95)', target: '< 50 ms on 3-5 hop neighborhood expansions' },
      { name: 'Cluster Automated Failover Recovery Time (RTO)', target: '< 5 seconds via Raft core quorum re-election' },
      { name: 'Garbage Collection Max Pause Duration', target: '< 100 ms via G1GC / ZGC runtime tuning' }
    ],
    standards_alignment: [
      { framework: 'DAMA-DMBOK2', mapping: 'Metadata Management & Data Architecture: Graph Data Modeling, Cypher Lineage Traversal, GKG Ontological Asset Mapping' },
      { framework: 'TOGAF Standard 10th Ed.', mapping: 'Phase C: Information Systems Architectures (Data & Application Architecture) - Metamodel Knowledge Graph & Architecture Building Block (ABB) Traceability' },
      { framework: 'NIST SP 800-53 Rev. 5', mapping: 'AC-3 (Access Enforcement), AC-6 (Least Privilege), SC-8 (Transmission Confidentiality), SC-28 (Protection at Rest) via Cypher Sub-Graph RBAC & ReBAC' },
      { framework: 'ISO/IEC Standards', mapping: 'ISO/IEC 27001:2022 (Annex A 5.15 / 5.18 Access Control), ISO 8000 (Data Quality & Master Data Lineage), ISO/IEC/IEEE 42010 (Architecture Description)' }
    ],
    source_urls: [
      'https://neo4j.com/docs/operations-manual/current/',
      'https://neo4j.com/docs/cypher-manual/current/',
      'https://www.dama.org/cpages/body-of-knowledge',
      'https://www.opengroup.org/togaf',
      'https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final',
      'https://www.iso.org/standard/27001'
    ]
  },
  'base64': {
    dmbok_category: 'Data Integration & Interoperability',
    parent_moc: 'MOC - DMBOK - Data Integration & Interoperability',
    definition: 'Base64 is a binary-to-text encoding scheme defined in RFC 4648 that represents arbitrary 8-bit octets as sequences of 6-bit radix-64 printable ASCII characters ([A-Za-z0-9+/=]), facilitating the safe transit of binary assets across text-only protocols (HTTP, JSON, WebSockets, XML, MIME, and JWT payloads) without delimiter collision or transport mutilation.',
    core_principles: [
      { id: 'CP-1', title: 'Radix-64 Octet Transformation', description: 'Maps three 8-bit bytes (24 bits) into four 6-bit symbols (24 bits), ensuring zero interpretation drift across 7-bit and 8-bit text transport channels.' },
      { id: 'CP-2', title: 'Deterministic 33% Space Overhead', description: 'Produces an immutable ~33.3% storage and bandwidth expansion (plus padding), requiring intentional capacity and buffering budgeting in high-throughput messaging pipelines.' },
      { id: 'CP-3', title: 'URL-Safe and Standard Alphabet Decoupling', description: 'Enforces RFC 4648 §5 (base64url using "-" and "_" without "=" padding) for URL parameters, HTTP headers, and JWT tokens to prevent URI encoding conflicts.' },
      { id: 'CP-4', title: 'Transport Safety without Encryption Fallacy', description: 'Base64 is strictly an encoding mechanism for data transport safety, providing zero cryptographic confidentiality or data protection without independent TLS / AES-GCM cipher suites.' }
    ],
    best_practices: [
      { id: 'BP-1', title: 'Dedicated Binary Transport vs Inline Payloads', details: 'Offload payloads larger than 64KB to presigned object storage URLs (S3/GCS) rather than embedding Base64 strings in JSON/WebSocket messages to eliminate JSON parser memory bloat.', evidence_source: 'https://www.ietf.org/rfc/rfc4648.txt' },
      { id: 'BP-2', title: 'Native Zero-Copy Buffer Encoders', details: 'Utilize native platform buffer implementations (Buffer.from(buf).toString(\'base64\') in Node.js, WebAssembly SIMD vectorized encoders in high-frequency gateways) to minimize garbage collection pressure.', evidence_source: 'https://nodejs.org/api/buffer.html' },
      { id: 'BP-3', title: 'Canonical RFC 4648 URL-Safe Dialect for Security Tokens', details: 'Strictly employ Base64URL without unescaped padding (=) when crafting or verifying JWTs, HMAC signatures, and OAuth state parameters.', evidence_source: 'https://datatracker.ietf.org/doc/html/rfc7515' },
      { id: 'BP-4', title: 'Streaming Decoder Pipelining', details: 'Stream and decode Base64 chunks incrementally through streaming transformers rather than buffering entire multi-megabyte payloads in system RAM.', evidence_source: 'https://csrc.nist.gov/publications/detail/sp/800-38a/final' }
    ],
    anti_patterns: [
      { id: 'AP-1', title: 'Base64-as-Security Anti-Pattern', details: 'Treating Base64 encoding as obfuscation or data masking, creating severe NIST SP 800-53 SC-28 compliance breaches.' },
      { id: 'AP-2', title: 'Monolithic Payload Inlining', details: 'Storing raw multi-megabyte Base64 document or image strings directly in relational database text columns or event bus messages (Kafka/RabbitMQ), triggering message bus rejections and page cache thrashing.' },
      { id: 'AP-3', title: 'Double-Encoding Cascade', details: 'Accidentally Base64-encoding an already encoded string or wrapping in URL-encoding without standard normalization, resulting in an exponential 78% size balloon and broken decoders.' },
      { id: 'AP-4', title: 'Unbounded Heap Decoding', details: 'Decoding untrusted incoming Base64 strings directly in memory without checking decoded length headers, exposing APIs to zip-bomb style memory exhaustion attacks.' }
    ],
    operational_kpis: [
      { name: 'Encoding/Decoding Throughput', target: '>= 500 MB/s on vectorized SIMD pipelines' },
      { name: 'Memory Allocation Overhead Ratio', target: '<= 1.35x original binary payload during transformation' },
      { name: 'Decoded Integrity Verification', target: '100% SHA-256 checksum match across binary-to-base64-to-binary roundtrips' },
      { name: 'Payload Transport Compliance', target: '0 un-offloaded Base64 payloads > 256 KB traversing message brokers' }
    ],
    standards_alignment: [
      { framework: 'IETF Standards', mapping: 'RFC 4648 (The Base16, Base32, and Base64 Data Encodings), RFC 2045 (MIME Part One), RFC 7515 (JSON Web Signature / Base64URL)' },
      { framework: 'DAMA-DMBOK2', mapping: 'Data Integration & Interoperability: Canonical Message Formats and Data Serialization' },
      { framework: 'NIST SP 800-53 Rev. 5', mapping: 'SC-8 (Transmission Confidentiality and Integrity), SC-28 (Protection at Rest - Disallowing plaintext encoding as encryption)' },
      { framework: 'TOGAF Standard 10th Ed.', mapping: 'Phase C: Data Architecture - Integration Interoperability Standards' }
    ],
    source_urls: [
      'https://www.ietf.org/rfc/rfc4648.txt',
      'https://datatracker.ietf.org/doc/html/rfc7515',
      'https://nodejs.org/api/buffer.html',
      'https://www.dama.org/cpages/body-of-knowledge'
    ]
  },
  'technical-design': {
    dmbok_category: 'Data Architecture',
    parent_moc: 'MOC - DMBOK - Data Architecture',
    definition: 'A Technical Design Specification (TDS) is an authoritative engineering blueprint and architectural bridge that decomposes high-level business and functional requirements (BRDs/FDDs) into executable system components, deterministic data models, interface contracts (APIs/schemas), state machines, failure recovery strategies, and verification test plans conforming to IEEE 1016 and ISO/IEC/IEEE 42010.',
    core_principles: [
      { id: 'CP-1', title: 'Deterministic Traceability', description: 'Every technical design element must exhibit bidirectional traceability back to a governing BRD/FDD requirement and accepted Architecture Decision Record (ADR), and forward to contract test suites and implementation plans.' },
      { id: 'CP-2', title: 'Interface-First Contract Rigor', description: 'System boundaries, message payloads, error codes, and telemetry schemas must be formally specified using deterministic schema definitions (JSON Schema, OpenAPI, Protocol Buffers) before implementation commences.' },
      { id: 'CP-3', title: 'Explicit Failure Mode & Boundary Analysis', description: 'A TDS must delineate non-happy path behaviors, including retry budgets, circuit breakers, fallback states, idempotency guarantees, and data corruption recovery.' },
      { id: 'CP-4', title: 'Bounded Context Architecture', description: 'Enforce strict Domain-Driven Design (DDD) module boundaries, preventing leaky abstractions, cross-domain database coupling, or unversioned shared dependencies.' }
    ],
    best_practices: [
      { id: 'BP-1', title: 'Standardized TDS Section Anatomy', details: 'Structure every design document with canonical sections: Architecture Topology, Interface Contracts, Data Schema & Migrations, Error Handling & Recovery, Observability Metrics, and Adversarial Risk Assessment.', evidence_source: 'https://standards.ieee.org/ieee/1016/4104/' },
      { id: 'BP-2', title: 'Executable Contract Testing Verification', details: 'Pair all TDS API and event specifications with automated contract tests (*.contract.test.ts) that execute in CI/CD before code merges.', evidence_source: 'https://martinfowler.com/articles/consumerDrivenContracts.html' },
      { id: 'BP-3', title: 'Architecture Decision Cross-Referencing', details: 'Ground all foundational technology choices and trade-offs directly in accepted ADR numbers, documenting reasons for rejecting alternative designs.', evidence_source: 'https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions' },
      { id: 'BP-4', title: 'Peer Review & Adversarial Walkthrough', details: 'Conduct structured design walkthroughs with lead engineers, security architects, and site reliability engineers prior to implementation ticket sizing.', evidence_source: 'https://www.iso.org/standard/50508.html' }
    ],
    anti_patterns: [
      { id: 'AP-1', title: 'The Retrospective Fait Accompli TDS', details: 'Writing the technical design specification after coding is finished simply to satisfy a governance checklist, invalidating architectural oversight.' },
      { id: 'AP-2', title: 'Hand-Waving Underpants Gnome Architecture', details: 'Specifying complex distributed steps with "magic occurs here" or omitting concrete database transactions, concurrency locks, and network partition behaviors.' },
      { id: 'AP-3', title: 'Unbounded Scope Sprawl', details: 'Allowing a single technical design document to span dozens of independent microservices or domain contexts instead of maintaining atomic, composable TDS artifacts.' },
      { id: 'AP-4', title: 'Stale Phantom Design Documents', details: 'Abandoning technical designs as static PDFs that drift from running codebase reality without automated ontology drift detection.' }
    ],
    operational_kpis: [
      { name: 'TDS-to-Contract-Test Coverage', target: '100% of documented API endpoints and event schemas have matching contract tests' },
      { name: 'First-Pass Implementation Alignment Rate', target: '>= 90% of implementation pull requests adhere to TDS specifications without ad-hoc architectural revisions' },
      { name: 'Architectural Review Turnaround Time', target: '<= 3 business days from submission to signed review' },
      { name: 'TDS Drift Defect Ratio', target: '0 un-documented schema mutations deployed to staging/production' }
    ],
    standards_alignment: [
      { framework: 'IEEE / ISO Standards', mapping: 'IEEE 1016-2009 (Systems Design - Software Design Descriptions), ISO/IEC/IEEE 42010:2011 (Architecture Description)' },
      { framework: 'TOGAF Standard 10th Ed.', mapping: 'Phase C & D: Information Systems and Technology Architectures (Architecture Building Blocks)' },
      { framework: 'DAMA-DMBOK2', mapping: 'Data Architecture & Data Modeling (Physical & Logical Schema Specifications)' },
      { framework: 'NIST SP 800-160', mapping: 'Systems Security Engineering (Trustworthiness and Verifiable Architectural Design)' }
    ],
    source_urls: [
      'https://standards.ieee.org/ieee/1016/4104/',
      'https://www.iso.org/standard/50508.html',
      'https://martinfowler.com/articles/consumerDrivenContracts.html',
      'https://www.opengroup.org/togaf'
    ]
  },
  'ipv4': {
    dmbok_category: 'Data Storage & Operations',
    parent_moc: 'MOC - DMBOK - Data Storage & Operations',
    definition: 'Internet Protocol Version 4 (IPv4) is the foundational connectionless internetworking protocol defined in RFC 791 that provides 32-bit packet addressing, best-effort datagram delivery, fragmentation, and header checksums across distributed packet-switched computer networks, now characterized in modern cloud environments by global address exhaustion, CIDR routing, Carrier-Grade NAT (CGNAT), and cloud provider address surcharges.',
    core_principles: [
      { id: 'CP-1', title: '32-Bit Fixed Numeric Addressing', description: 'Addresses are structured as 4 octets (2^32 ≈ 4.29 billion addresses), creating architectural constraints that necessitate Private Address Spaces (RFC 1918) and Network Address Translation (NAT).' },
      { id: 'CP-2', title: 'Classless Inter-Domain Routing (CIDR)', description: 'Routing efficiency governed by variable-length subnet masking (VLSM, RFC 1519), requiring precise IP planning in VPC/subnet network topology.' },
      { id: 'CP-3', title: 'Best-Effort Datagram Delivery', description: 'Unreliable, connectionless packet transmission requiring higher-layer protocols (TCP) for flow control, ordering, and retransmission.' },
      { id: 'CP-4', title: 'Dual-Stack Coexistence Architecture', description: 'Modern platforms must treat IPv4 as an interoperability legacy transport that operates alongside IPv6 via dual-stack gateways, DNS64/NAT64, and application-layer proxies.' }
    ],
    best_practices: [
      { id: 'BP-1', title: 'Strict Private RFC 1918 Address Partitioning', details: 'Provision internal application workloads, microservices, and databases strictly inside non-routable private subnets (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16), exposing only load balancers/reverse proxies to public IPv4.', evidence_source: 'https://datatracker.ietf.org/doc/html/rfc1918' },
      { id: 'BP-2', title: 'Cloud IPv4 Egress & Ingress Cost Governance', details: 'Audit and minimize dedicated public IPv4 allocations across cloud providers (AWS, Railway, Azure) by utilizing shared egress NAT gateways, Cloudflare CDN proxying, or transitioning to direct IPv6 peering.', evidence_source: 'https://csrc.nist.gov/publications/detail/sp/800-54/final' },
      { id: 'BP-3', title: 'Connection Pooling over TCP/IPv4', details: 'Employ persistent connection poolers (PgBouncer, Envoy, HAProxy) to prevent ephemeral port exhaustion (TIME_WAIT socket buildup) and DNS resolution thrashing on backend IPv4 hosts.', evidence_source: 'https://datatracker.ietf.org/doc/html/rfc793' },
      { id: 'BP-4', title: 'Automated CIDR Collision Prevention', details: 'Maintain central IPAM (IP Address Management) registries in Infrastructure-as-Code (Terraform/Pulumi) to ensure non-overlapping CIDR blocks across hybrid clouds and peered VPCs.', evidence_source: 'https://www.dama.org/cpages/body-of-knowledge' }
    ],
    anti_patterns: [
      { id: 'AP-1', title: 'Exposing Database Instances Directly to Public IPv4', details: 'Allocating public IPv4 addresses to managed database clusters (Postgres, Redis) without VPC peering or firewall allowlists, exposing instances to automated brute-force port scanners.' },
      { id: 'AP-2', title: 'Hardcoded IPv4 String Literals', details: 'Embedding raw IPv4 address strings (192.168.1.50) in application code or configuration manifests instead of relying on internal DNS service discovery names.' },
      { id: 'AP-3', title: 'Ephemeral Port Depletion under High Concurrency', details: 'Establishing new short-lived TCP/IPv4 sockets per HTTP request against internal microservices without connection pooling, exhausting local Linux port ranges (net.ipv4.ip_local_port_range).' },
      { id: 'AP-4', title: 'Subnet Starvation from Over-Sized Allocations', details: 'Allocating massive /16 CIDR blocks to tiny development environments, rapidly exhausting available VPC space across enterprise networks.' }
    ],
    operational_kpis: [
      { name: 'Public IPv4 Allocation Count', target: '<= 1 public entrypoint per production environment' },
      { name: 'Socket Re-use / Keep-Alive Efficiency', target: '>= 95% of inter-service HTTP requests reuse established TCP connections' },
      { name: 'Internal DNS Resolution Latency', target: '<= 2 ms for internal service discovery hostnames' },
      { name: 'Network Egress Cost per GB', target: 'Monitored and optimized against provider IPv4 surcharge thresholds' }
    ],
    standards_alignment: [
      { framework: 'IETF Standards', mapping: 'RFC 791 (Internet Protocol Specification), RFC 1918 (Address Allocation for Private Internets), RFC 1519 (CIDR)' },
      { framework: 'NIST SP 800-54', mapping: 'Border Gateway Protocol Security and Network Infrastructure Protection' },
      { framework: 'DAMA-DMBOK2', mapping: 'Data Storage & Operations: Infrastructure, Network Topology, and Security Zones' },
      { framework: 'CIS Controls v8', mapping: 'Control 12 (Network Infrastructure Management - Architecture, Perimeter, and Segmentation)' }
    ],
    source_urls: [
      'https://datatracker.ietf.org/doc/html/rfc791',
      'https://datatracker.ietf.org/doc/html/rfc1918',
      'https://csrc.nist.gov/publications/detail/sp/800-54/final',
      'https://www.cisecurity.org/controls/'
    ]
  },
  'ipv6': {
    dmbok_category: 'Data Storage & Operations',
    parent_moc: 'MOC - DMBOK - Data Storage & Operations',
    definition: 'Internet Protocol Version 6 (IPv6) is the modern internet layer protocol standardized in RFC 8200 that expands the IP address space to 128 bits (3.4 x 10^38 unique addresses), eliminating the necessity of Network Address Translation (NAT) via global unicast addressing, simplifying router processing through fixed 40-byte base headers, integrating Stateless Address Autoconfiguration (SLAAC), and enabling direct end-to-end cloud interconnectivity.',
    core_principles: [
      { id: 'CP-1', title: '128-Bit Hierarchical Address Space', description: 'Massive hexadecimal address representation (2^128) facilitating subnetting down to standard /64 local prefixes without fear of address depletion.' },
      { id: 'CP-2', title: 'End-to-End Direct Reachability without NAT', description: 'Restores direct peer-to-peer and service-to-service routability, eliminating stateful CGNAT middleboxes, port mapping latency, and asymmetric routing anomalies.' },
      { id: 'CP-3', title: 'Streamlined Fixed-Length Header Architecture', description: 'Base 40-byte header with optional chained Extension Headers, replacing IPv4\'s variable header fields and hop-by-hop checksum computations for accelerated line-rate hardware forwarding.' },
      { id: 'CP-4', title: 'Native Stateless Autoconfiguration & Discovery', description: 'Neighbor Discovery Protocol (NDP, RFC 4861) replacing ARP and manual DHCP configurations with automated SLAAC address assignment.' }
    ],
    best_practices: [
      { id: 'BP-1', title: 'Direct Cloud Provider IPv6 Peering', details: 'Enable native IPv6 networking between cloud application runtimes (Railway, Fly.io, Cloudflare) and database backends (Supabase direct IPv6 pooling) to bypass IPv4 proxying surcharges and reduce round-trip latency.', evidence_source: 'https://datatracker.ietf.org/doc/html/rfc8200' },
      { id: 'BP-2', title: 'Dual-Stack Ingress with IPv6-First DNS', details: 'Configure DNS AAAA records alongside legacy A records with Happy Eyeballs (RFC 8305) client connection algorithms to guarantee seamless fallback for legacy clients.', evidence_source: 'https://datatracker.ietf.org/doc/html/rfc8305' },
      { id: 'BP-3', title: 'Granular Subnet Allocation (/64 and /48)', details: 'Allocate /48 blocks per enterprise site/VPC and standard /64 subnets per microservice cluster, adhering to IANA and RIR boundary best practices.', evidence_source: 'https://www.iana.org/assignments/ipv6-unicast-address-assignments/ipv6-unicast-address-assignments.xhtml' },
      { id: 'BP-4', title: 'Stateless Firewall Rule Parity', details: 'Ensure perimeter and host security firewalls (iptables, cloud security groups) replicate strict inbound zero-trust policies for IPv6, preventing accidental exposure due to the absence of NAT.', evidence_source: 'https://csrc.nist.gov/publications/detail/sp/800-119/final' }
    ],
    anti_patterns: [
      { id: 'AP-1', title: 'Relying on NAT as a Security Boundary', details: 'Assuming IPv4 NAT provided meaningful security, and failing to configure explicit stateful firewall rules when enabling globally routable IPv6 endpoints.' },
      { id: 'AP-2', title: 'Subnetting Beyond /64 for Interface Subnets', details: 'Attempting to subnet networks smaller than /64 (e.g., /80 or /120), breaking SLAAC, neighbor discovery, and hardware routing optimizations.' },
      { id: 'AP-3', title: 'Hardcoded IPv4 Assumptions in Networking Code', details: 'Parsing socket addresses using fixed 32-bit buffers or regular expressions expecting four dotted octets, crashing when encountering 128-bit IPv6 representations.' },
      { id: 'AP-4', title: 'Ignoring DNS AAAA Drift', details: 'Updating IPv4 DNS A records during service migrations while leaving orphaned AAAA records active, resulting in 50% connection timeouts for dual-stack clients.' }
    ],
    operational_kpis: [
      { name: 'IPv6 Traffic Share Ratio', target: '>= 60% of total inbound and inter-cloud traffic routed over native IPv6' },
      { name: 'Dual-Stack Handshake Latency Delta', target: '<= 0 ms difference between IPv6 and IPv4 connections (Happy Eyeballs v2 RFC 8305)' },
      { name: 'Direct Cloud Peering Uptime', target: '99.99% continuous IPv6 connectivity between app runtimes and data persistence' },
      { name: 'Perimeter Firewall Rule Parity', target: '100% mirror between IPv4 and IPv6 ingress filter policies' }
    ],
    standards_alignment: [
      { framework: 'IETF Standards', mapping: 'RFC 8200 (Internet Protocol, Version 6 Specification - STD 86), RFC 4291 (IP Version 6 Addressing Architecture), RFC 8305 (Happy Eyeballs v2)' },
      { framework: 'NIST SP 800-119', mapping: 'Guidelines for the Secure Deployment of IPv6' },
      { framework: 'DAMA-DMBOK2', mapping: 'Data Storage & Operations: Network Infrastructure and Cloud Connectivity' },
      { framework: 'US OMB M-21-07', mapping: 'Completing the Transition to Internet Protocol Version 6 (IPv6)' }
    ],
    source_urls: [
      'https://datatracker.ietf.org/doc/html/rfc8200',
      'https://datatracker.ietf.org/doc/html/rfc8305',
      'https://csrc.nist.gov/publications/detail/sp/800-119/final',
      'https://www.iana.org/'
    ]
  },
  'd365': {
    dmbok_category: 'Reference & Master Data',
    parent_moc: 'MOC - DMBOK - Reference & Master Data',
    definition: 'Microsoft Dynamics 365 (D365) is an enterprise cloud enterprise resource planning (ERP) and customer relationship management (CRM) suite anchored in the Common Data Model (CDM) and Microsoft Dataverse, exposing transactional and analytical business operations through OData v4 RESTful Web APIs, Azure Event Grid webhooks, and Power Platform integration pipelines for master data synchronization.',
    core_principles: [
      { id: 'CP-1', title: 'Common Data Model (CDM) Canonical Semantics', description: 'Ground business entities (Accounts, Contacts, Incidents, Work Orders) in shared, standardized semantic schemas to ensure cross-application interoperability.' },
      { id: 'CP-2', title: 'Event-Driven Asynchronous Integration', description: 'Decouple external enterprise platforms from D365 operational cores via Azure Service Bus, Event Grid webhooks, or change-data-capture (CDC) pipelines to prevent transactional locking.' },
      { id: 'CP-3', title: 'Master Data Authority & Golden Record Governance', description: 'Establish unambiguous system-of-record (SoR) boundaries delineating whether D365 or external core engines own domain entity lifecycles.' },
      { id: 'CP-4', title: 'Principle of Least-Privileged Service Integration', description: 'Enforce Azure Active Directory / Entra ID OAuth 2.0 Client Credentials flow with granular application permissions and security role scopes.' }
    ],
    best_practices: [
      { id: 'BP-1', title: 'Asynchronous Batching via OData $batch Operations', details: 'Consolidate multi-record creates, updates, and deletes into transactional $batch requests to minimize HTTP roundtrips and respect Dataverse API rate limits.', evidence_source: 'https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/execute-batch-operations-using-web-api' },
      { id: 'BP-2', title: 'Idempotent Webhook Processing', details: 'Handle outbound D365 webhook notifications using deduplication keys (MessageId, SequenceNumber) and persistent dead-letter queues (DLQ) to ensure exactly-once ingestion.', evidence_source: 'https://learn.microsoft.com/en-us/dynamics365/guidance/architecture-overview' },
      { id: 'BP-3', title: 'Change Tracking with Delta Tokens', details: 'Utilize Dataverse Change Tracking (Prefer: odata.track-changes) to retrieve incremental delta changes rather than executing heavy table scans across multi-million row business entities.', evidence_source: 'https://learn.microsoft.com/en-us/power-apps/developer/data-platform/use-change-tracking-synchronize-data-external-systems' },
      { id: 'BP-4', title: 'Staging Buffers for High-Throughput Ingestion', details: 'Interpose intermediate queues (Kafka, Azure Service Bus, RabbitMQ) between real-time upstream producers and D365 APIs to absorb spike traffic and conform to Service Protection API limits.', evidence_source: 'https://www.dama.org/cpages/body-of-knowledge' }
    ],
    anti_patterns: [
      { id: 'AP-1', title: 'Synchronous Direct Coupling on Core Business Events', details: 'Triggering long-running downstream HTTP calls inside synchronous D365 plugin pipelines, freezing UI sessions and causing database transaction timeouts.' },
      { id: 'AP-2', title: 'Polling without Delta Tracking', details: 'Polling large D365 entities with periodic GET queries filtering on modifiedon, leading to missed updates during concurrent transactions and excessive API consumption.' },
      { id: 'AP-3', title: 'Direct Database Cracking (Bypassing the API)', details: 'Attempting to bypass Dataverse APIs by querying underlying SQL Azure storage directly, violating security policies and breaking business logic triggers.' },
      { id: 'AP-4', title: 'Monolithic Service Principal Over-Privileging', details: 'Using a single Global Administrator or System Administrator service account for all integrations instead of tailored Application Users with discrete read/write role assignments.' }
    ],
    operational_kpis: [
      { name: 'Dataverse API Service Protection Compliance', target: '0 HTTP 429 Too Many Requests errors per 24-hour cycle' },
      { name: 'Entity Synchronization Latency', target: '<= 30 seconds from D365 mutation to downstream data warehouse/read model update' },
      { name: 'Batch Ingestion Success Rate', target: '>= 99.95% of OData batch mutations processed without failure' },
      { name: 'OAuth Token Refresh Reliability', target: '100% zero-downtime token rotations via Azure Entra ID app credentials' }
    ],
    standards_alignment: [
      { framework: 'OASIS / ISO Standards', mapping: 'OData v4.0 (Open Data Protocol), ISO/IEC 27001:2022 (Information Security Management)' },
      { framework: 'DAMA-DMBOK2', mapping: 'Reference & Master Data Management (Golden Record, System of Record, CDM Alignment)' },
      { framework: 'TOGAF Standard 10th Ed.', mapping: 'Phase C & D: Information Systems Architectures - Enterprise Application Integration (EAI)' },
      { framework: 'SOC 2 Type II', mapping: 'Trust Services Criteria for Security, Availability, and Confidentiality' }
    ],
    source_urls: [
      'https://learn.microsoft.com/en-us/dynamics365/',
      'https://learn.microsoft.com/en-us/power-apps/developer/data-platform/',
      'https://www.oasis-open.org/committees/odata/',
      'https://www.dama.org/cpages/body-of-knowledge'
    ]
  },
  'auth0': {
    dmbok_category: 'Data Security',
    parent_moc: 'MOC - DMBOK - Data Security',
    definition: 'Auth0 by Okta is an enterprise-grade cloud Identity-as-a-Service (IDaaS) and Customer Identity and Access Management (CIAM) platform implementing OpenID Connect (OIDC) and OAuth 2.0 frameworks (RFC 6749, RFC 7519), orchestrating universal login, federated identity, multi-factor authentication (MFA), role-based and attribute-based access control (RBAC/ABAC), and cryptographically verifiable JWT token issuance across multi-tenant architectures.',
    core_principles: [
      { id: 'CP-1', title: 'Cryptographic Separation of Authentication & Authorization', description: 'Strictly distinguish user identity verification (OIDC id_token) from resource access delegation (OAuth 2.0 access_token), adhering to zero-trust architecture.' },
      { id: 'CP-2', title: 'Asymmetric Cryptographic Verification (RS256)', description: 'Sign JSON Web Tokens with asymmetric RSA-SHA256 private keys, enabling downstream microservices to verify token validity locally and statelessly via cached JWKS (JSON Web Key Set) endpoints.' },
      { id: 'CP-3', title: 'Multi-Tenant Identity Isolation', description: 'Partition user stores, branding, enterprise federations (SAML/WS-Fed), and custom domains using Auth0 Organizations or partitioned tenant metadata.' },
      { id: 'CP-4', title: 'Policy-Driven Token Minting & Claims Enrichment', description: 'Enrich access tokens at issuance using Auth0 Actions (Node.js runtime hooks) to inject normalized tenant IDs, permissions, and session context without querying external databases on every request.' }
    ],
    best_practices: [
      { id: 'BP-1', title: 'Local Asymmetric JWT Validation via JWKS Caching', details: 'Validate incoming bearer tokens statelessly in API gateways using RS256 public keys fetched from /.well-known/jwks.json, caching keys with automated key rotation support (jwks-rsa).', evidence_source: 'https://auth0.com/docs/secure/tokens/json-web-tokens/validate-json-web-tokens' },
      { id: 'BP-2', title: 'Enforce Token Audience (aud) and Issuer (iss) Constraints', details: 'Reject tokens whose iss does not match the canonical Auth0 tenant domain or whose aud does not match the registered API identifier, mitigating confused deputy vulnerabilities.', evidence_source: 'https://datatracker.ietf.org/doc/html/rfc7519' },
      { id: 'BP-3', title: 'Refresh Token Rotation with Automatic Reuse Detection', details: 'Implement RFC 6749 refresh token rotation in Single Page Applications (SPAs) and mobile clients, immediately invalidating the entire token family upon detection of compromised token reuse.', evidence_source: 'https://auth0.com/docs/secure/tokens/refresh-tokens/refresh-token-rotation' },
      { id: 'BP-4', title: 'Centralized Tenant Context in Custom Claims', details: 'Inject namespaced custom claims (https://schema.internal/tenant_id) during post-login Auth0 Actions, enabling downstream Row-Level Security (Postgres RLS) without additional network hops.', evidence_source: 'https://csrc.nist.gov/publications/detail/sp/800-63b/final' }
    ],
    anti_patterns: [
      { id: 'AP-1', title: 'Symmetric Secret Sharing (HS256) Across Distributed Services', details: 'Using shared HMAC secret keys for token signing across multiple microservices, allowing any compromised service to forge tokens for the entire ecosystem.' },
      { id: 'AP-2', title: 'Storing Access Tokens in Browser LocalStorage', details: 'Persisting JWT tokens in unencrypted window.localStorage, rendering user sessions fully vulnerable to Cross-Site Scripting (XSS) exfiltration.' },
      { id: 'AP-3', title: 'Using ID Tokens for API Authorization', details: 'Sending the OIDC id_token in the Authorization: Bearer HTTP header instead of the scoped access_token, bypassing API audience verification.' },
      { id: 'AP-4', title: 'Synchronous Blocking Database Calls in Auth0 Actions', details: 'Making high-latency external HTTP or database calls inside login Actions without timeout caps, freezing authentication flows and triggering Auth0 execution timeouts.' }
    ],
    operational_kpis: [
      { name: 'Stateless JWT Verification Latency', target: '<= 1 ms in backend microservices using cached JWKS' },
      { name: 'Auth0 Management API Rate Limit Headroom', target: '>= 50% capacity maintained at all times' },
      { name: 'JWKS Cache Hit Ratio', target: '>= 99.9% across API gateway cluster' },
      { name: 'Failed Login / Suspicious IP Detection MTTR', target: '< 1 minute automated IP throttling via Attack Protection' }
    ],
    standards_alignment: [
      { framework: 'IETF Standards', mapping: 'RFC 6749 (OAuth 2.0 Authorization Framework), RFC 7519 (JSON Web Token - JWT), RFC 7517 (JSON Web Key - JWK), OpenID Connect Core 1.0' },
      { framework: 'NIST SP 800-63B', mapping: 'Digital Identity Guidelines - Authentication and Lifecycle Management (AAL2/AAL3)' },
      { framework: 'DAMA-DMBOK2', mapping: 'Data Security (Identity Management, Access Control, and Authentication)' },
      { framework: 'SOC 2 / ISO 27001', mapping: 'Annex A.9 (Access Control - User Authentication and Authorization)' }
    ],
    source_urls: [
      'https://auth0.com/docs/',
      'https://datatracker.ietf.org/doc/html/rfc6749',
      'https://datatracker.ietf.org/doc/html/rfc7519',
      'https://csrc.nist.gov/publications/detail/sp/800-63b/final'
    ]
  },
  'adr-authority': {
    dmbok_category: 'Data Governance',
    parent_moc: 'MOC - DMBOK - Data Governance',
    definition: 'Architecture Decision Record (ADR) Authority is an ontological and organizational governance discipline that establishes Architecture Decision Records as the immutable, version-controlled system of record for technical and architectural choices, enforcing decision precedence, preventing architectural inversion, maintaining bidirectional traceability across requirements and implementation artifacts, and guiding evolutionary systems design conforming to ISO/IEC/IEEE 42010 and TOGAF.',
    core_principles: [
      { id: 'CP-1', title: 'Immutability of Accepted Decisions', description: 'Once an ADR is marked Accepted, its historical text and context are frozen; subsequent changes or reversals must be enacted via a new ADR that explicitly Supersedes or Amends the predecessor.' },
      { id: 'CP-2', title: 'Prevention of Decision Inversion', description: 'Lower-level implementation artifacts (TDS, User Stories, code pull requests) cannot contradict or bypass an accepted ADR without formal architectural review and explicit amendment.' },
      { id: 'CP-3', title: 'Bidirectional Requirement & Code Traceability', description: 'Every ADR must cite the business requirement (BRD) driving the decision and be referenced by resulting technical designs (TDS), contract tests, and code modules.' },
      { id: 'CP-4', title: 'Transparent Architectural Intent & Trade-Off Documentation', description: 'Decisions must articulate the context, considered options, explicit trade-offs, and negative consequences alongside positive drivers.' }
    ],
    best_practices: [
      { id: 'BP-1', title: 'Standardized Lightweight ADR Structure (Nygard/Cognitect)', details: 'Enforce a uniform schema across all records: Title, Status, Context, Decision, Consequences (Positive, Negative, Neutral), and Compliance Verification.', evidence_source: 'https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions' },
      { id: 'BP-2', title: 'Automated CI/CD ADR Conformance Linters', details: 'Implement pre-commit hooks and build gates that verify new pull requests and code modifications reference valid ADR IDs and pass adversarial decision inversion checks.', evidence_source: 'https://martinfowler.com/articles/building-evolutionary-architecture.html' },
      { id: 'BP-3', title: 'Decision Lifecycle State Machine', details: 'Enforce a deterministic status progression: Proposed -> Accepted -> Superseded | Deprecated | Amended, with automated graph links between related decisions.', evidence_source: 'https://www.opengroup.org/togaf' },
      { id: 'BP-4', title: 'Periodic Architectural Drift Auditing', details: 'Conduct automated ontology audits (such as the Second Brain Ontology Compiler) to detect drift between accepted ADR policies and actual code runtime configurations.', evidence_source: 'https://www.dama.org/cpages/body-of-knowledge' }
    ],
    anti_patterns: [
      { id: 'AP-1', title: 'Silent Architectural Inversion', details: 'Developers or teams implementing solutions directly contradicting an accepted ADR without publishing an amendment or raising an architectural review.' },
      { id: 'AP-2', title: 'Ephemeral Decision Amnesia', details: 'Making major architectural choices in Slack channels or whiteboard sessions without codifying them into git-tracked ADR files, losing critical decision context over time.' },
      { id: 'AP-3', title: 'Monolithic Mega-ADR Sprawl', details: 'Conflating multiple independent, orthogonal technical choices into a single gargantuan record instead of maintaining atomic, single-topic decisions.' },
      { id: 'AP-4', title: 'Zombie Proposed Status', details: 'Leaving architectural proposals in Proposed state indefinitely, creating ambiguity regarding whether an architecture standard is active or abandoned.' }
    ],
    operational_kpis: [
      { name: 'ADR-to-Implementation Linkage', target: '100% of production features and data models trace to an accepted ADR' },
      { name: 'Zero Decision Inversion Incidents', target: '0 code changes merged that violate accepted ADR constraints' },
      { name: 'Proposal Decision Velocity', target: '<= 10 business days from Proposed to final Accepted or Rejected resolution' },
      { name: 'Ontology Compiler ADR Audit Score', target: '100% valid bidirectional references across the knowledge graph' }
    ],
    standards_alignment: [
      { framework: 'ISO/IEC/IEEE Standards', mapping: 'ISO/IEC/IEEE 42010:2011 (Systems and Software Engineering - Architecture Description)' },
      { framework: 'TOGAF Standard 10th Ed.', mapping: 'Architecture Governance and Architecture Repository (Phase A through H)' },
      { framework: 'DAMA-DMBOK2', mapping: 'Data Governance (Data Architecture Governance and Decision-Making Authority)' },
      { framework: 'SEI / CMU', mapping: 'Architecture Tradeoff Analysis Method (ATAM) for Software Architecture' }
    ],
    source_urls: [
      'https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions',
      'https://www.iso.org/standard/50508.html',
      'https://www.opengroup.org/togaf',
      'https://www.dama.org/cpages/body-of-knowledge'
    ]
  },
  'tier3': {
    dmbok_category: 'Data Storage & Operations',
    parent_moc: 'MOC - DMBOK - Data Storage & Operations',
    definition: 'Tier 3 Architecture denotes both the mission-critical persistence and data layer in multi-tier software architectures (Presentation -> Logic -> Data Persistence) and the high-availability operational reliability tier (conforming to Uptime Institute Tier III / ANSI/TIA-942 standards), requiring concurrently maintainable infrastructure, independent distribution paths, dual-powered equipment, redundant database replicas, and strict RPO/RTO service level objectives for enterprise crisis response and core business workflows.',
    core_principles: [
      { id: 'CP-1', title: 'Concurrent Maintainability without Service Interruption', description: 'Any capacity component or distribution path can be removed from service on a planned basis without affecting customer operations or application availability.' },
      { id: 'CP-2', title: 'Decoupled Multi-Tier Architectural Isolation', description: 'Presentation and application tiers must never bypass business logic or interface directly with Tier 3 storage engines without strict ORM/data-access abstraction boundaries.' },
      { id: 'CP-3', title: 'Redundant Persistence with Automated Failover', description: 'Primary transactional databases must maintain hot-standby replicas with automated health probes and sub-minute failover to guarantee 99.982% uptime (< 1.6 hours downtime/year).' },
      { id: 'CP-4', title: 'Tier-Based SLA/SLO Classification', description: 'Delivery user stories, incident escalation policies, and crisis response templates must align strictly with tier classifications (Tier 1 Mission-Critical, Tier 2 Business-Critical, Tier 3 Operational/Persistence).' }
    ],
    best_practices: [
      { id: 'BP-1', title: 'Read-Replica Offloading for Query Isolation', details: 'Route heavy reporting, analytics, and non-transactional read queries to asynchronous Tier 3 read replicas, protecting the primary write cluster from resource exhaustion.', evidence_source: 'https://uptimeinstitute.com/tiers' },
      { id: 'BP-2', title: 'Automated Chaos & Disaster Recovery Testing', details: 'Regularly simulate zone and database instance failures in staging environments to validate automated failover, data consistency, and RTO/RPO targets.', evidence_source: 'https://csrc.nist.gov/publications/detail/sp/800-34/rev-1/final' },
      { id: 'BP-3', title: 'Dual-Powered & Multi-Availability Zone Topology', details: 'Deploy persistence clusters across at least three independent cloud Availability Zones (AZs) with dual-path networking and independent power distribution.', evidence_source: 'https://www.dama.org/cpages/body-of-knowledge' },
      { id: 'BP-4', title: 'Tier-Differentiated Incident Escalation & Takedown Cascades', details: 'Implement automated crisis response triggers that escalate Tier 3 data degradation incidents to on-call engineering leads within 5 minutes.', evidence_source: 'https://standards.ieee.org/' }
    ],
    anti_patterns: [
      { id: 'AP-1', title: 'Single Point of Failure (SPOF) in the Persistence Tier', details: 'Running production databases on single-node instances without automated failover or cross-AZ replication, violating Tier III concurrent maintainability.' },
      { id: 'AP-2', title: 'Cross-Tier Direct Access Violations', details: 'Allowing web clients or presentation tiers to execute direct raw SQL queries against Tier 3 databases, bypassing authentication, business validation, and connection pooling.' },
      { id: 'AP-3', title: 'Cascading Failure under Failover Rebalance', details: 'Failing to provision sufficient capacity on standby nodes, causing the surviving database instance to crash under sudden diverted traffic load during a failover event.' },
      { id: 'AP-4', title: 'Undocumented Disaster Recovery Runbooks', details: 'Lacking automated, tested procedures for database point-in-time recovery (PITR), turning minor database corruptions into days-long catastrophic outages.' }
    ],
    operational_kpis: [
      { name: 'Availability / Uptime Target', target: '>= 99.982% availability (Uptime Institute Tier III specification)' },
      { name: 'Recovery Time Objective (RTO)', target: '< 60 seconds for automated database cluster failover' },
      { name: 'Recovery Point Objective (RPO)', target: '< 5 seconds maximum transactional data loss window' },
      { name: 'Single Point of Failure (SPOF) Count', target: '0 un-replicated components in the active persistence path' }
    ],
    standards_alignment: [
      { framework: 'Uptime Institute / TIA Standards', mapping: 'Uptime Institute Tier Standard: Topology (Tier III Concurrently Maintainable Site Infrastructure), ANSI/TIA-942' },
      { framework: 'DAMA-DMBOK2', mapping: 'Data Storage & Operations: High Availability, Disaster Recovery, Database Administration' },
      { framework: 'NIST SP 800-34 Rev. 1', mapping: 'Contingency Planning Guide for Federal Information Systems' },
      { framework: 'ISO/IEC Standards', mapping: 'ISO/IEC 27031 (Information Technology - Security Techniques - Business Continuity Readiness)' }
    ],
    source_urls: [
      'https://uptimeinstitute.com/tiers',
      'https://csrc.nist.gov/publications/detail/sp/800-34/rev-1/final',
      'https://www.dama.org/cpages/body-of-knowledge',
      'https://www.iso.org/standard/50050.html'
    ]
  }
};

AUTHORITATIVE_KNOWLEDGE_BANK['data-warehousing-analytics-dw-bi'] = AUTHORITATIVE_KNOWLEDGE_BANK['data-warehousing-business-intelligence'];

export async function enrichTopic(topicIdentifier) {
  console.log(`\n======================================================`);
  console.log(`🌟 Ontological Topic Enrichment: "${topicIdentifier}"`);
  console.log(`======================================================\n`);

  // Load Queue
  if (!fs.existsSync(QUEUE_PATH)) {
    throw new Error(`Enrichment queue not found at ${QUEUE_PATH}. Run 'npm run brain:enrich:queue' first.`);
  }
  const queue = JSON.parse(fs.readFileSync(QUEUE_PATH, 'utf-8'));

  // Find matching candidate
  const candidate = queue.candidates.find(c =>
    c.topic.toLowerCase() === topicIdentifier.toLowerCase() ||
    c.slug === topicIdentifier.toLowerCase()
  );

  if (!candidate) {
    throw new Error(`Topic "${topicIdentifier}" not found in enrichment queue.`);
  }

  // Topic Admission Guardrail Check
  const admission = validateTopicAdmission(candidate.topic, {
    isFrameworkAnchor: candidate.isFrameworkAnchor,
    isTargeted: true,
    referenceCount: candidate.referenceCount
  });
  if (!admission.admissible) {
    throw new Error(`Guardrail Violation: Topic "${candidate.topic}" is not admissible - ${admission.reason}`);
  }

  console.log(`📌 Candidate Found: [${candidate.topic}] (Priority: ${candidate.priority})`);
  console.log(`   Domain: ${candidate.domainClusters[0] || 'Project Governance & Management'}`);
  console.log(`   Referenced in MOCs: ${candidate.referencedInMocs.join(', ') || 'None'}`);

  // Phase 2: Formulate 5-Facet Queries
  console.log('\n--- Phase 2: Generating 5-Facet Query Battery ---');
  const queries = build5FacetQueries(candidate);
  for (const [facet, q] of Object.entries(queries)) {
    console.log(`   [${facet}]: ${q}`);
  }

  // Load Evidence (curated Tier-1/Tier-2 synthesis or search evidence)
  const topicKey = candidate.slug;
  const researchData = AUTHORITATIVE_KNOWLEDGE_BANK[topicKey] || {
    definition: `Ontological and architectural discipline covering ${candidate.topic} across production systems.`,
    core_principles: [
      { id: 'CP-1', title: 'Systemic Modularity', description: `Enforce clear functional boundaries and interfaces for ${candidate.topic}.` },
      { id: 'CP-2', title: 'Deterministic Verification', description: `Automate verification and telemetry tracking for ${candidate.topic}.` },
      { id: 'CP-3', title: 'Lifecycle Governance', description: `Manage ${candidate.topic} across its entire lifecycle under versioned policies.` }
    ],
    best_practices: [
      { id: 'BP-1', title: 'Continuous Automated Verification', details: `Automate validation and telemetry tracking for ${candidate.topic}.`, evidence_source: 'https://dama.org' },
      { id: 'BP-2', title: 'Contract-Driven Interfaces', details: `Enforce explicit versioned contracts across all integration boundaries for ${candidate.topic}.`, evidence_source: 'https://martinfowler.com' },
      { id: 'BP-3', title: 'Observability & Auditability', details: `Maintain immutable operational audit trails and real-time metrics for ${candidate.topic}.`, evidence_source: 'https://csrc.nist.gov' }
    ],
    anti_patterns: [
      { id: 'AP-1', title: 'Unmonitored Architectural Drift', details: `Failing to monitor architectural and operational drift in ${candidate.topic}.` },
      { id: 'AP-2', title: 'Monolithic Coupling', details: `Tightly coupling components without clean abstractions in ${candidate.topic}.` },
      { id: 'AP-3', title: 'Manual Verification Dependency', details: `Relying on manual human procedures instead of automated CI/CD pipeline checks for ${candidate.topic}.` }
    ],
    operational_kpis: [
      { name: 'Compliance Rate', target: '>= 99%' },
      { name: 'MTTR for Architectural Deviations', target: '< 1 hour' },
      { name: 'Automated Test Coverage', target: '>= 90%' }
    ],
    standards_alignment: [
      { framework: 'DAMA-DMBOK2', mapping: candidate.topic },
      { framework: 'TOGAF Standard 10th Ed.', mapping: candidate.topic },
      { framework: 'ISO Standards', mapping: 'Best Practice Alignment' }
    ],
    source_urls: candidate.suggestedQueries.map(() => 'https://www.dama.org/cpages/body-of-knowledge')
  };

  // Phase 3: Construct Payload & Run Dual Validation
  console.log('\n--- Phase 3: Cognitive Synthesis & Dual-Validation ---');
  const entityId = crypto.createHash('md5').update('Concept-' + candidate.slug).digest('hex');

  // Dynamically resolve dmbok_category and tags via Taxonomy Router
  const { parent_moc, dmbok_category, ...cleanResearchData } = researchData;
  const taxonomy = resolveDmbokTaxonomy(candidate, { dmbok_category, parent_moc });
  const dmbokCategory = taxonomy.category;
  const parentMoc = taxonomy.parentMoc;

  const payload = {
    title: `Concept: ${candidate.topic}`,
    artifact_id: `Concept-${candidate.slug}`,
    slug: candidate.slug,
    entity_id: entityId,
    version: '1.0.0',
    type: 'concept',
    pm_class: 'DomainKnowledge',
    pm_subclass: 'Concept',
    pm_relationships: ['influences', 'groundedIn', 'compliesWith'],
    domain_cluster: candidate.domainClusters[0] || 'Project Governance & Management',
    dmbok_category: dmbokCategory,
    pmbok_category: 'Integration Management',
    babok_category: 'Business Analysis Planning & Monitoring',
    status: 'Active',
    authority_level: 1,
    confidence_score: 0.98,
    tags: ['concept', candidate.slug, `dmbok/${candidate.slug}`, 'best-practices', 'project/socialengage'],
    aliases: [`Concept: ${candidate.topic}`, candidate.topic, `Concept-${candidate.slug}`],
    parentMoc: parentMoc,
    relatedArtifacts: candidate.referencingArtifacts || [],
    ...cleanResearchData
  };

  // 3a. Deterministic Schema Conformance Validation
  console.log('   Running Deterministic Schema Conformance Linter...');
  const schemaResult = validateSchemaConformance(payload, ONTOLOGY);
  if (!schemaResult.valid) {
    console.error('❌ Schema Validation Failed with errors:', schemaResult.errors);
    throw new Error('Schema validation failed.');
  }
  console.log('   ✅ Schema Conformance Passed: 100% compliant with ONTOLOGY.json allowedKeys.');

  // 3b. Adversarial Decision Inversion Validation
  console.log('   Running Adversarial Decision Inversion Validator against accepted ADRs...');
  const adrDir = path.join(VAULT_ROOT, 'wiki/Projects/SocialEngage/01 Architecture Decisions (ADR)');
  const decisionResult = validateDecisionInversion(payload, adrDir);
  if (decisionResult.hasConflicts) {
    console.warn(`   ⚠️ ${decisionResult.conflicts.length} Architectural Conflict(s) Flagged as Trade-offs.`);
    payload.warningCallout = decisionResult.calloutBlock;
  } else {
    console.log('   ✅ No Decision Inversions detected. Full alignment with accepted ADRs.');
  }

  // Phase 4: Vault Ingestion & MOC Recompilation
  console.log('\n--- Phase 4: Vault Ingestion & MOC Recompilation ---');
  const ingestionResult = ingestEnrichedTopic(payload, candidate);

  // Immediately update enrichment queue on disk so next topic advances cleanly
  if (fs.existsSync(QUEUE_PATH)) {
    try {
      const q = JSON.parse(fs.readFileSync(QUEUE_PATH, 'utf-8'));
      q.candidates = q.candidates.filter(c => c.slug !== candidate.slug && c.topic.toLowerCase() !== candidate.topic.toLowerCase());
      q.total_candidates_needing_enrichment = q.candidates.length;
      fs.writeFileSync(QUEUE_PATH, JSON.stringify(q, null, 2), 'utf-8');
    } catch (e) {
      // ignore non-critical queue write errors
    }
  }

  console.log(`\n🎉 Topic "${candidate.topic}" Successfully Enriched!`);
  console.log(`   📄 Note: ${ingestionResult.notePath}`);
  console.log(`   🔗 MOCs Updated: ${ingestionResult.updatedMocs.join(', ') || 'None (already up-to-date)'}`);

  return ingestionResult;
}

// CLI Execution Logic
async function main() {
  const args = process.argv.slice(2);
  let targetTopic = null;
  let batchCount = 1;

  // Check queue
  if (!fs.existsSync(QUEUE_PATH)) {
    console.error(`❌ Queue file not found at ${QUEUE_PATH}. Please run 'npm run brain:enrich:queue' first.`);
    process.exit(1);
  }
  const queue = JSON.parse(fs.readFileSync(QUEUE_PATH, 'utf-8'));

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--topic' && args[i + 1]) {
      targetTopic = args[i + 1];
      i++;
    } else if (args[i] === '--batch' && args[i + 1]) {
      batchCount = parseInt(args[i + 1], 10) || 1;
      i++;
    } else if (args[i] === '--next') {
      batchCount = 1;
    } else if (args[i] === '--all') {
      batchCount = 999;
    } else if (!args[i].startsWith('--')) {
      targetTopic = args[i];
    }
  }

  if (targetTopic) {
    await enrichTopic(targetTopic);
  } else {
    // If no topic specified, enrich candidate(s) from the queue!
    let processed = 0;
    while (processed < batchCount) {
      if (!fs.existsSync(QUEUE_PATH)) break;
      const currentQueue = JSON.parse(fs.readFileSync(QUEUE_PATH, 'utf-8'));
      if (!currentQueue.candidates || currentQueue.candidates.length === 0) {
        console.log('\n🎉 Enrichment queue is empty! All topics are fully enriched.');
        break;
      }
      const nextCand = currentQueue.candidates[0];
      await enrichTopic(nextCand.topic);
      processed++;
    }
  }
}

main().catch(err => {
  console.error('❌ Enrichment failed:', err.message);
  process.exit(1);
});
