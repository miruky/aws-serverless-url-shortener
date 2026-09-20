import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { inspectProject } from './trace/model.mjs';

export function inspectIndex(root) {
  const snapshot = mkdtempSync(join(tmpdir(), 'shortener-index-'));
  try {
    const result = spawnSync('git', ['checkout-index', '--all', `--prefix=${snapshot}/`], {
      cwd: root,
      encoding: 'utf8',
    });
    if (result.status !== 0) throw new Error(result.stderr || 'Could not read Git index');
    return inspectProject(snapshot);
  } finally {
    rmSync(snapshot, { recursive: true, force: true });
  }
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const report = inspectIndex(process.cwd());
    for (const finding of report.findings)
      console.error(`${finding.code} ${finding.node ?? finding.path ?? ''}: ${finding.message}`);
    if (!report.ok) process.exitCode = 1;
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
