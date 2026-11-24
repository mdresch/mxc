import { existsSync, readdirSync } from 'fs';
import { spawnSync } from 'child_process';
import path from 'path';

const contractsDir = path.resolve('tests/contracts');
if (!existsSync(contractsDir)) {
  console.log('No tests/contracts directory found. Skipping contract tests.');
  process.exit(0);
}

const testFiles = readdirSync(contractsDir)
  .filter(f => f.endsWith('.test.js'))
  .map(f => path.join('tests/contracts', f));

if (testFiles.length === 0) {
  console.log('No contract tests found in tests/contracts. Skipping.');
  process.exit(0);
}

console.log(`Running ${testFiles.length} contract test suites with node:test...`);
const res = spawnSync('node', ['--test', ...testFiles], { stdio: 'inherit' });
process.exit(res.status ?? 0);

