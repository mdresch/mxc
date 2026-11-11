#!/usr/bin/env node
/**
 * Claim a story worktree for agentic parallel execution (Tier A or B).
 * Atomic claim: git worktree add -b fails if branch exists.
 *
 * Usage:
 *   node scripts/provision-story-worktree.mjs 1.1.1
 *   node scripts/provision-story-worktree.mjs 1.2.1 --tier B
 */

import { existsSync } from 'fs';
import { execSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const args = process.argv.slice(2).filter((a) => !a.startsWith('--'));
const tier = process.argv.includes('--tier') ? process.argv[process.argv.indexOf('--tier') + 1] : 'A';
const wbs = args[0];

if (!wbs || !/^\d+\.\d+\.\d+$/.test(wbs)) {
  console.error('Usage: node scripts/provision-story-worktree.mjs <WBS e.g. 1.1.1> [--tier A|B]');
  process.exit(1);
}

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const baseBranch = process.env.MXC_STORY_BASE_BRANCH || 'feat/hyperv-v2-rebased';
const branch = `feat/story-${wbs}`;
const worktreePath = path.resolve(repoRoot, '..', `mxc-story-${wbs}`);

try {
  execSync('git rev-parse --is-inside-work-tree', { cwd: repoRoot, stdio: 'pipe' });
} catch {
  console.error('Not a git repository:', repoRoot);
  process.exit(1);
}

if (existsSync(worktreePath)) {
  console.error(`Worktree path already exists: ${worktreePath}`);
  console.error('Inspect read-only (implement-story Step 0). Do not reclaim without confirming abandonment.');
  process.exit(2);
}

try {
  execSync(`git worktree add "${worktreePath}" -b "${branch}" "${baseBranch}"`, {
    cwd: repoRoot,
    stdio: 'inherit',
  });
} catch (e) {
  console.error(`Claim failed — branch "${branch}" may already exist (another agent claimed this WBS).`);
  process.exit(3);
}

console.log('\n--- Claim OK ---');
console.log(`  WBS:      ${wbs}`);
console.log(`  Tier:     ${tier}`);
console.log(`  Branch:   ${branch}`);
console.log(`  Worktree: ${worktreePath}`);
console.log(`  Base:     ${baseBranch}`);
console.log('\nNext: update docs/registers/Project-Status-Register.md §5 and Implementation-Story-Queue.md');
console.log('Then: implement-story Steps 1–8 from the worktree.\n');
