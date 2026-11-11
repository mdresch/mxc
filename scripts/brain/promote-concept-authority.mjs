/**
 * promote-concept-authority.mjs
 * Phase 5 (STEP-5.4): ADPA/ECS Human-in-the-Loop Authority Promotion Script.
 *
 * Upgrades a machine-generated Concept note (authority_level: 1) to an
 * authoritative, human-reviewed standard (authority_level: 2).
 */

import fs from 'fs';
import path from 'path';
import { resolveVaultRoot, resolveWikiRoot } from './vault-resolver.mjs';

const VAULT_ROOT = resolveVaultRoot();
const baseWiki = resolveWikiRoot(VAULT_ROOT);
const SYNTHESIS_DIR = path.join(baseWiki, 'Projects', 'SocialEngage', '06 Synthesis & Lessons Learned');

const args = process.argv.slice(2);
let targetSlug = args[0] || 'data-governance';
let reviewer = args[1] || 'Lead Architect';

// Normalize target
targetSlug = targetSlug.replace(/^Concept-/i, '').replace(/\.md$/i, '').toLowerCase();
if (!targetSlug || /[<>:"/\\|?*\x00-\x1f]/.test(targetSlug)) {
  console.error('❌ Invalid concept slug. Use a file name without path separators or reserved characters.');
  process.exit(1);
}

const fileName = `Concept-${targetSlug}.md`;
const filePath = path.join(SYNTHESIS_DIR, fileName);
const relativePath = path.relative(SYNTHESIS_DIR, filePath);
if (relativePath.startsWith('..') || path.isAbsolute(relativePath)) {
  console.error('❌ Concept path must remain inside the synthesis directory.');
  process.exit(1);
}

if (!fs.existsSync(filePath)) {
  console.error(`❌ Concept note not found: ${filePath}`);
  process.exit(1);
}

let content = fs.readFileSync(filePath, 'utf-8');

// Update authority_level to 2
content = content.replace(/authority_level:\s*\d+/, 'authority_level: 2');
content = content.replace(/confidence_score:\s*[\d.]+/, 'confidence_score: 1.0');
content = content.replace(/modified_at:\s*"[^"]*"/, `modified_at: "${new Date().toISOString()}"`);

// Add human-approved tag if not present
if (!content.includes('"human-approved"')) {
  content = content.replace(/tags:\s*\n/, 'tags:\n  - "human-approved"\n');
}

// Append Audit Log section at bottom
const auditEntry = `\n\n## 8. ADPA/ECS Governance & Authority Audit
- **Authority Elevation**: Promoted from Level 1 (Machine-Generated) to Level 2 (Human-Verified Architectural Standard).
- **Reviewed By**: ${reviewer}
- **Timestamp**: ${new Date().toISOString()}
- **Status**: Approved for production architectural grounding.
`;

if (!content.includes('## 8. ADPA/ECS Governance & Authority Audit')) {
  content += auditEntry;
}

fs.writeFileSync(filePath, content, 'utf-8');

console.log(`✅ Successfully promoted Concept note to Authority Level 2:`);
console.log(`   📄 File: ${filePath}`);
console.log(`   👤 Reviewed by: ${reviewer}`);
console.log(`   🛡️ Authority Level: 2 (Human-Verified Architectural Standard)`);
