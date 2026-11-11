import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Deterministically locates the Obsidian Second Brain vault root.
 * Resolution priority:
 * 1. Command-line flag --vault <path> or --vault-root <path>
 * 2. Environment variables OBSIDIAN_VAULT_ROOT or SECOND_BRAIN_ROOT
 * 3. Parent directory if run directly inside obsidian-second-brain/scripts/
 * 4. Sibling repository (C:/.../Source/Repos/obsidian-second-brain)
 * 5. Current project root fallback
 */
export function resolveVaultRoot() {
  // 1. CLI flag
  const args = process.argv.slice(2);
  const vIdx = args.findIndex(a => a === '--vault' || a === '--vault-root');
  if (vIdx >= 0 && args[vIdx + 1]) {
    const custom = path.resolve(args[vIdx + 1]);
    if (fs.existsSync(custom)) return custom;
  }

  // 2. Environment variables
  if (process.env.OBSIDIAN_VAULT_ROOT && fs.existsSync(process.env.OBSIDIAN_VAULT_ROOT)) {
    return path.resolve(process.env.OBSIDIAN_VAULT_ROOT);
  }
  if (process.env.SECOND_BRAIN_ROOT && fs.existsSync(process.env.SECOND_BRAIN_ROOT)) {
    return path.resolve(process.env.SECOND_BRAIN_ROOT);
  }

  // 3. Parent if inside obsidian-second-brain/scripts
  const parentDir = path.resolve(__dirname, '..');
  if (fs.existsSync(path.join(parentDir, 'wiki')) && fs.existsSync(path.join(parentDir, 'ONTOLOGY.json'))) {
    return parentDir;
  }

  // 4. Sibling repos check (Source/Repos/obsidian-second-brain)
  // From sidpa-template/scripts/brain -> ../../../obsidian-second-brain
  const siblingBrain3 = path.resolve(__dirname, '../../../obsidian-second-brain');
  if (fs.existsSync(siblingBrain3) && fs.existsSync(path.join(siblingBrain3, 'wiki'))) {
    return siblingBrain3;
  }
  // From sidpa-template/scripts -> ../../obsidian-second-brain
  const siblingBrain2 = path.resolve(__dirname, '../../obsidian-second-brain');
  if (fs.existsSync(siblingBrain2) && fs.existsSync(path.join(siblingBrain2, 'wiki'))) {
    return siblingBrain2;
  }

  // 5. Fallback to repository root
  return path.resolve(__dirname, '../..');
}

export function resolveWikiRoot(vaultRoot = resolveVaultRoot()) {
  const wiki = path.join(vaultRoot, 'wiki');
  return fs.existsSync(wiki) ? wiki : path.join(vaultRoot, 'docs');
}

