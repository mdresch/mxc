import fs from 'fs';
import path from 'path';
import { resolveVaultRoot, resolveWikiRoot } from './vault-resolver.mjs';

function scanFiles(dir) {
  let list = [];
  if (!fs.existsSync(dir)) return list;
  for (const f of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, f.name);
    if (f.isDirectory()) list = list.concat(scanFiles(full));
    else list.push(full);
  }
  return list;
}

const vaultRoot = resolveVaultRoot();
const wikiRoot = resolveWikiRoot(vaultRoot);
const allFiles = scanFiles(wikiRoot);
// Also include root files like ONTOLOGY.json if they exist
const ontPath = path.join(vaultRoot, 'ONTOLOGY.json');
if (fs.existsSync(ontPath)) allFiles.push(ontPath);

const fileSet = new Set();
const baseNameMap = new Map();

for (const p of allFiles) {
  const ext = path.extname(p);
  const baseWithoutExt = path.basename(p, ext).toLowerCase();
  const baseWithExt = path.basename(p).toLowerCase();
  
  fileSet.add(baseWithoutExt);
  fileSet.add(baseWithExt);
  
  const rel = path.relative('wiki', p).replace(/\\/g, '/').toLowerCase();
  fileSet.add(rel);
  fileSet.add(rel.replace(/\.(md|canvas|json)$/, ''));
  fileSet.add(`wiki/${rel}`);
  fileSet.add(`wiki/${rel.replace(/\.(md|canvas|json)$/, '')}`);
  
  baseNameMap.set(baseWithoutExt, p);

  if (ext === '.md') {
    try {
      const content = fs.readFileSync(p, 'utf8');
      const fmMatch = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
      if (fmMatch) {
        const fm = fmMatch[1];
        const aliasesMatch = fm.match(/aliases:\s*\n((?:\s*-\s*.*(?:\r?\n|$))*)/);
        if (aliasesMatch && aliasesMatch[1]) {
          const lines = aliasesMatch[1].split(/\r?\n/);
          for (const l of lines) {
            const m = l.match(/^\s*-\s*["']?(.*?)["']?\s*$/);
            if (m && m[1]) {
              fileSet.add(m[1].trim().toLowerCase());
            }
          }
        }
      }
    } catch (e) {}
  }
}

const allMds = allFiles.filter(f => f.endsWith('.md'));
const broken = new Map();

for (const p of allMds) {
  const content = fs.readFileSync(p, 'utf8');
  const matches = content.matchAll(/\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]/g);
  for (const m of matches) {
    const target = m[1].trim();
    if (!target) continue;
    const cleanTarget = target.replace(/\\/g, '/').toLowerCase();
    const cleanTargetNoExt = cleanTarget.replace(/\.(md|canvas|json)$/, '');
    const baseTarget = path.basename(cleanTarget);
    const baseTargetNoExt = path.basename(cleanTargetNoExt);

    if (
      !fileSet.has(cleanTarget) &&
      !fileSet.has(cleanTargetNoExt) &&
      !fileSet.has(baseTarget) &&
      !fileSet.has(baseTargetNoExt) &&
      !fs.existsSync(target) &&
      !fs.existsSync(path.join('wiki', target))
    ) {
      if (!broken.has(target)) broken.set(target, []);
      broken.get(target).push(path.relative('wiki', p).replace(/\\/g, '/'));
    }
  }
}

console.log('Total unique broken targets:', broken.size);
const sorted = [...broken.entries()].sort((a, b) => b[1].length - a[1].length);
console.log('Top 25 most frequent missing targets:');
sorted.slice(0, 25).forEach(([t, refs]) => {
  console.log(`  ${t} (${refs.length} refs) e.g. in ${refs[0]}`);
});
