/**
 * quarantine-pseudo-concepts.mjs
 * CLI Utility to audit and quarantine pseudo-concept notes (commit SHAs, schema keys, variable names)
 * that violate Topic Admission Guardrails.
 *
 * Usage:
 *   node scripts/quarantine-pseudo-concepts.mjs            # Dry-run audit report
 *   node scripts/quarantine-pseudo-concepts.mjs --execute  # Quarantine invalid notes to raw/quarantined-concepts/
 */

import fs from 'fs';
import path from 'path';
import { auditExistingConceptNotes, quarantineNoiseConceptNotes } from './topic-guardrails.mjs';
import { resolveVaultRoot } from './vault-resolver.mjs';

const VAULT_ROOT = resolveVaultRoot();
const args = process.argv.slice(2);
const execute = args.includes('--execute');

console.log(`\n======================================================`);
console.log(`🛡️ CONCEPT NOTE INTEGRITY & ADMISSION AUDIT`);
console.log(`======================================================\n`);

const { valid, noise } = auditExistingConceptNotes(VAULT_ROOT);

console.log(`📊 Audit Results:`);
console.log(`   ✅ Authentic Architectural Concepts: ${valid.length}`);
console.log(`   ⚠️ Guardrail Violations (Pseudo-Concepts): ${noise.length}\n`);

if (noise.length === 0) {
  console.log(`🎉 Perfect graph integrity! No pseudo-concepts found in the synthesis directory.\n`);
  process.exit(0);
}

console.log(`🔍 Sample Guardrail Violations Flagged for Quarantine:`);
noise.slice(0, 15).forEach((item, idx) => {
  console.log(`   ${(idx + 1).toString().padStart(2, ' ')}. ${item.file}`);
  console.log(`       Reason: ${item.reason}`);
});

if (noise.length > 15) {
  console.log(`   ...and ${noise.length - 15} more.`);
}

if (!execute) {
  console.log(`\n💡 DRY-RUN MODE: No files were moved.`);
  console.log(`   To quarantine these ${noise.length} pseudo-concepts into 'raw/quarantined-concepts/', run:`);
  console.log(`   npm run brain:enrich:quarantine\n`);
} else {
  console.log(`\n🚀 EXECUTING QUARANTINE...`);
  const quarantined = quarantineNoiseConceptNotes(VAULT_ROOT, false);
  console.log(`✅ Successfully moved ${quarantined.length} pseudo-concepts to raw/quarantined-concepts/`);
  console.log(`   Original notes preserved in quarantine folder for inspection/rollback.\n`);
}

console.log(`======================================================\n`);
