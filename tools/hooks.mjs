import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
const root = fileURLToPath(new URL('../', import.meta.url));
const top = spawnSync('git', ['rev-parse', '--show-toplevel'], { cwd: root, encoding: 'utf8' });
if (top.status !== 0 || resolve(top.stdout.trim()) !== resolve(root)) {
  console.log('Source archive: no Git checkout to install hooks into.');
} else {
  const result = spawnSync('git', ['config', '--local', 'core.hooksPath', '.githooks'], {
    cwd: root,
    stdio: 'inherit',
  });
  process.exitCode = result.status ?? 1;
}
