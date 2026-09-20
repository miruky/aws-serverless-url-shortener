import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
const root = fileURLToPath(new URL('../', import.meta.url));
const args = process.argv.slice(2);
const python = resolve(
  root,
  process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python',
);
const node = process.execPath;
function run(command, values = []) {
  const result = spawnSync(command, values, { cwd: root, stdio: 'inherit' });
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status ?? 1);
}
try {
  switch (args[0] ?? 'help') {
    case 'setup':
      run('uv', ['sync', '--locked', '--extra', 'dev']);
      run('npm', ['ci']);
      run(python, ['tools/bootstrap_guard.py']);
      run(node, ['tools/hooks.mjs']);
      break;
    case 'doctor':
      console.log(
        `Node ${process.version}; Python environment: ${existsSync(python) ? 'present' : 'missing (run ./dev setup)'}`,
      );
      if (!existsSync(python)) process.exitCode = 1;
      break;
    case 'trace':
      run(node, ['tools/trace/cli.mjs', ...args.slice(1)]);
      break;
    case 'docs':
      run(node, ['tools/docs-server.mjs']);
      break;
    case 'tdd':
      run(node, ['tools/tdd.mjs', ...args.slice(1)]);
      break;
    case 'serve':
      run(python, ['-m', 'src.local_server', ...args.slice(1)]);
      break;
    case 'package':
      run(python, ['tools/package.py']);
      break;
    case 'prepare':
      run(python, ['tools/prepare_deployment.py', ...args.slice(1)]);
      break;
    case 'test':
      run(python, ['-m', 'pytest', ...args.slice(1)]);
      break;
    case 'check':
      run(python, ['-m', 'ruff', 'check', 'src', 'tests', 'tools']);
      run(python, ['-m', 'ruff', 'format', '--check', 'src', 'tests', 'tools']);
      run(python, ['-m', 'mypy', 'src']);
      run(python, ['-m', 'pytest']);
      run('npm', ['run', 'format:check']);
      run('npm', ['test']);
      run(resolve(root, '.venv/bin/cfn-lint'), [
        'infrastructure/product.yaml',
        'infrastructure/artifacts.yaml',
      ]);
      const guard = existsSync(resolve(root, '.harness/bin/cfn-guard'))
        ? resolve(root, '.harness/bin/cfn-guard')
        : 'cfn-guard';
      run(guard, [
        'validate',
        '--rules',
        'infrastructure/rules/product.guard',
        '--rules',
        'infrastructure/rules/dynamodb_pitr_enabled.guard',
        '--data',
        'infrastructure/product.yaml',
        '--output-format',
        'json',
      ]);
      run(guard, [
        'validate',
        '--rules',
        'infrastructure/rules/artifacts.guard',
        '--data',
        'infrastructure/artifacts.yaml',
        '--output-format',
        'json',
      ]);
      run(node, ['tools/trace/cli.mjs', 'check']);
      run('npm', ['run', 'test:e2e']);
      run(python, ['tools/package.py']);
      const gitRoot = spawnSync('git', ['rev-parse', '--show-toplevel'], {
        cwd: root,
        encoding: 'utf8',
      });
      if (gitRoot.status === 0 && resolve(gitRoot.stdout.trim()) === resolve(root))
        run('git', ['diff', '--check']);
      else console.log('Source archive: Git diff checks do not apply.');
      break;
    default:
      console.log(
        'Usage: ./dev setup | doctor | serve | docs | test | package | prepare --region REGION | trace impact | tdd red --change CHG-ID | check',
      );
  }
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
