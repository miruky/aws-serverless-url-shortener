import {
  existsSync,
  readdirSync,
  readFileSync,
  writeFileSync,
  mkdirSync,
  lstatSync,
} from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { homedir } from 'node:os';
import { hashText, readChange, scopeSnapshot, safePath } from './trace/model.mjs';

export function assessRun(result, phase) {
  let counts,
    testNames = [];
  if (result.runner === 'pytest') {
    const reports = result.report?.reports ?? [];
    const calls = reports.filter((r) => r.when === 'call');
    testNames = calls.map((r) => r.id).sort();
    counts = {
      tests: calls.length,
      pass: calls.filter((r) => r.outcome === 'passed').length,
      fail: calls.filter((r) => r.outcome === 'failed').length,
      skipped: reports.filter((r) => r.outcome === 'skipped').length,
      cancelled: 0,
    };
    if (
      reports.some((r) => r.when !== 'call' && r.outcome !== 'passed') ||
      new Set(testNames).size !== testNames.length
    )
      return {
        ok: false,
        counts,
        testNames,
        reason: 'setup/teardownエラー・skip・重複テストは証拠にできません。',
      };
    if (
      phase === 'red' &&
      !calls.some(
        (r) => r.outcome === 'failed' && ['AssertionError', 'Failed'].includes(r.exception),
      )
    )
      return { ok: false, counts, testNames, reason: '実行されたアサーションの失敗がありません。' };
  } else {
    counts = Object.fromEntries(
      [...result.output.matchAll(/^# (tests|pass|fail|skipped|cancelled) (\d+)\s*$/gm)].map((m) => [
        m[1],
        Number(m[2]),
      ]),
    );
    if (
      phase === 'red' &&
      (!/ERR_ASSERTION/.test(result.output) ||
        /ERR_MODULE_NOT_FOUND|MODULE_NOT_FOUND|SyntaxError:|Cannot find package/.test(
          result.output,
        ))
    )
      return { ok: false, counts, testNames, reason: '起動・構文エラーをRedにできません。' };
  }
  const valid = counts.tests > 0 && !counts.skipped && !counts.cancelled;
  const ok =
    valid &&
    (phase === 'red'
      ? result.status === 1 && counts.fail > 0
      : result.status === 0 && counts.fail === 0 && counts.pass === counts.tests);
  return {
    ok,
    counts,
    testNames,
    reason: ok ? '' : '実行件数・終了コード・合否が期待値と一致しません。',
  };
}

function collectTests(root, paths, runner) {
  const files = [];
  function walk(path) {
    const absolute = safePath(root, path);
    if (lstatSync(absolute).isDirectory()) {
      for (const name of readdirSync(absolute).sort())
        if (name !== '__pycache__') walk(`${path}/${name}`);
    } else if (
      runner === 'pytest' ? /(^|\/)test_[^/]+\.py$/.test(path) : path.endsWith('.test.mjs')
    )
      files.push(path);
  }
  paths.forEach(walk);
  if (!files.length) throw new Error('対象テストがありません。');
  return files.sort();
}

export function runTdd(root, phase, change, baseline) {
  if (!['red', 'green'].includes(phase)) throw new Error('red または green を指定してください。');
  const meta = readChange(root, change),
    runner = meta.tdd?.runner ?? 'node';
  if (!['node', 'pytest'].includes(runner)) throw new Error('Unsupported runner');
  const files = collectTests(root, meta.tdd?.test_roots ?? ['tests/unit'], runner);
  const helpers = runner === 'pytest' ? ['tests/conftest.py', 'tools/pytest_evidence.py'] : [];
  const hashes = Object.fromEntries(
    [...files, ...helpers]
      .sort()
      .map((path) => [path, hashText(readFileSync(safePath(root, path)))]),
  );
  const directory = resolve(root, 'evidence/tdd', change);
  const reportPath = resolve(root, '.harness', `${randomUUID()}.json`);
  mkdirSync(resolve(root, '.harness'), { recursive: true });
  const executable =
    runner === 'pytest'
      ? resolve(
          root,
          process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python',
        )
      : process.execPath;
  if (baseline && (phase !== 'red' || runner !== 'pytest' || !/^[a-f0-9]{40}$/.test(baseline)))
    throw new Error('Baseline is supported for pytest Red with a full commit SHA only.');
  const command =
    runner === 'pytest'
      ? baseline
        ? ['tools/baseline.py', baseline, ...files]
        : ['-m', 'pytest', '-p', 'tools.pytest_evidence', '-q', ...files]
      : ['--test', '--test-reporter=tap', ...files];
  const env = {
    ...process.env,
    HARNESS_PYTEST_REPORT: reportPath,
    AWS_ACCESS_KEY_ID: 'testing',
    AWS_SECRET_ACCESS_KEY: 'testing',
    AWS_SESSION_TOKEN: 'testing',
    AWS_EC2_METADATA_DISABLED: 'true',
    AWS_DEFAULT_REGION: 'us-east-1',
    URLS_TABLE_NAME: 'test-urls',
  };
  const result = spawnSync(executable, command, {
    cwd: root,
    env,
    encoding: 'utf8',
    timeout: 120000,
    maxBuffer: 16 * 1024 * 1024,
  });
  const output = (result.stdout ?? '') + (result.stderr ?? '');
  const report = existsSync(reportPath) ? JSON.parse(readFileSync(reportPath, 'utf8')) : undefined;
  const assessment = assessRun({ status: result.status, output, runner, report }, phase);
  const safeOutput = output.replaceAll(root, '<repo>').replaceAll(homedir(), '<home>');
  if (!assessment.ok) {
    console.error(safeOutput.slice(-6000));
    throw new Error(assessment.reason);
  }
  let red;
  if (phase === 'green') {
    red = JSON.parse(readFileSync(resolve(directory, 'red.json'), 'utf8'));
    if (
      red.phase !== 'red' ||
      red.status !== 1 ||
      !red.counts.fail ||
      red.runner !== runner ||
      JSON.stringify(red.testHashes) !== JSON.stringify(hashes) ||
      JSON.stringify(red.testNames) !== JSON.stringify(assessment.testNames)
    )
      throw new Error(
        'Redのテスト・実行条件と一致しません。変更後の同じテストでRedを取り直してください。',
      );
    if (hashText(readFileSync(resolve(directory, 'red.log'))) !== red.outputHash)
      throw new Error('Redログが変わっています。');
  }
  const record = {
    schemaVersion: 1,
    phase,
    change,
    runner,
    command,
    status: result.status,
    capturedAt: new Date().toISOString(),
    counts: assessment.counts,
    testNames: assessment.testNames,
    testHashes: hashes,
    scopeHashes: scopeSnapshot(root, meta.scope),
    changeHash: hashText(readFileSync(safePath(root, `docs/changes/${change}.md`))),
    outputHash: hashText(safeOutput),
    ...(baseline ? { baselineRevision: baseline } : {}),
    ...(red ? { redOutputHash: red.outputHash, baselineRevision: red.baselineRevision } : {}),
  };
  mkdirSync(directory, { recursive: true });
  const previous = resolve(directory, `${phase}.json`);
  if (existsSync(previous)) {
    const old = readFileSync(previous),
      id = hashText(old).slice(0, 16);
    mkdirSync(resolve(directory, 'history'), { recursive: true });
    writeFileSync(resolve(directory, 'history', `${phase}-${id}.json`), old);
    if (existsSync(resolve(directory, `${phase}.log`)))
      writeFileSync(
        resolve(directory, 'history', `${phase}-${id}.log`),
        readFileSync(resolve(directory, `${phase}.log`)),
      );
  }
  writeFileSync(resolve(directory, `${phase}.log`), safeOutput);
  writeFileSync(resolve(directory, `${phase}.json`), JSON.stringify(record, null, 2) + '\n');
  console.log(
    `${phase}: ${record.counts.tests} tests, ${record.counts.fail} failures; evidence saved.`,
  );
  return record;
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const args = process.argv.slice(2);
    runTdd(
      fileURLToPath(new URL('../', import.meta.url)),
      args[0],
      args[args.indexOf('--change') + 1],
      args.includes('--baseline') ? args[args.indexOf('--baseline') + 1] : undefined,
    );
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
