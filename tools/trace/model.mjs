import {
  readFileSync,
  writeFileSync,
  readdirSync,
  lstatSync,
  existsSync,
  renameSync,
} from 'node:fs';
import { createHash } from 'node:crypto';
import { resolve, relative, dirname, sep } from 'node:path';
import YAML from 'yaml';

export const hashText = (value) => createHash('sha256').update(value).digest('hex');
const levels = { requirement: 0, basic: 1, detail: 2 };
const idPattern = /^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+$/;
const roles = ['implementation', 'test', 'configuration'];
const slash = (value) => value.split(sep).join('/');
const unique = (values) => [...new Set(values)];

export function safePath(root, path) {
  if (
    typeof path !== 'string' ||
    !path ||
    path.includes('\\') ||
    path.includes('\0') ||
    path.startsWith('/') ||
    path.split('/').some((x) => x === '..' || x === '.')
  )
    throw new Error('Unsafe relative path');
  const absolute = resolve(root, path);
  if (!absolute.startsWith(resolve(root) + sep)) throw new Error('Path outside project');
  let cursor = root;
  for (const part of path.split('/')) {
    cursor = resolve(cursor, part);
    if (existsSync(cursor) && lstatSync(cursor).isSymbolicLink())
      throw new Error('Symlinks are not allowed');
  }
  return absolute;
}

function walk(root, path, findings = []) {
  let absolute;
  try {
    absolute = safePath(root, path);
  } catch {
    findings.push({ code: 'UNSAFE_PATH', path, message: '安全な相対パスではありません。' });
    return [];
  }
  if (!existsSync(absolute)) return [];
  const stat = lstatSync(absolute);
  if (stat.isSymbolicLink()) {
    findings.push({
      code: 'UNSAFE_PATH',
      path,
      message: 'シンボリックリンクは管理対象にできません。',
    });
    return [];
  }
  if (stat.isFile()) return [slash(path)];
  return readdirSync(absolute)
    .sort()
    .filter((name) => name !== '__pycache__')
    .flatMap((name) => walk(root, `${path}/${name}`, findings));
}

export function readMarkdown(root, path) {
  const text = readFileSync(safePath(root, path), 'utf8');
  const match = text.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
  if (!match) throw new Error('Markdown front matter missing');
  const data = YAML.parse(match[1], { uniqueKeys: true, maxAliasCount: 0 });
  if (!data || typeof data !== 'object' || Array.isArray(data))
    throw new Error('Invalid front matter');
  return { data, text };
}

export function readConfig(root) {
  const config = JSON.parse(readFileSync(resolve(root, 'trace.config.json'), 'utf8'));
  if (
    config.schemaVersion !== 1 ||
    !Array.isArray(config.documents) ||
    !Array.isArray(config.managedRoots) ||
    !Array.isArray(config.managedFiles)
  )
    throw new Error('Invalid trace configuration');
  safePath(root, config.lockFile);
  return config;
}

function markdownLinks(root, findings) {
  const roots = [
    'docs',
    'README.md',
    'AGENTS.md',
    'CONTRIBUTING.md',
    'SECURITY.md',
    'CHANGELOG.md',
  ];
  for (const path of unique(roots.flatMap((path) => walk(root, path, findings))).filter((p) =>
    p.endsWith('.md'),
  )) {
    const text = readFileSync(safePath(root, path), 'utf8').replace(/```[\s\S]*?```/g, '');
    for (const m of text.matchAll(/!?\[[^\]]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)/g)) {
      const href = m[1].replace(/^<|>$/g, '');
      if (/^(https?:|mailto:|#)/i.test(href)) continue;
      let target;
      try {
        target = resolve(root, dirname(path), decodeURIComponent(href.split('#')[0]));
      } catch {
        target = '';
      }
      if (!target || !target.startsWith(resolve(root) + sep) || !existsSync(target))
        findings.push({
          code: 'BROKEN_MARKDOWN_LINK',
          path,
          message: `ローカルリンクの参照先がありません: ${href}`,
        });
    }
  }
}

export function inspectProject(root, { requireReviews = true } = {}) {
  root = resolve(root);
  const findings = [];
  let config;
  try {
    config = readConfig(root);
  } catch {
    return {
      ok: false,
      findings: [{ code: 'INVALID_CONFIG', message: 'trace.config.jsonが不正です。' }],
      nodes: [],
      graph: { nodes: [], edges: [] },
    };
  }
  const map = new Map();
  const artifactMap = new Map();
  const paths = unique(config.documents.flatMap((p) => walk(root, p, findings))).filter((p) =>
    p.endsWith('.md'),
  );
  for (const path of paths) {
    let data, text;
    try {
      ({ data, text } = readMarkdown(root, path));
    } catch {
      findings.push({
        code: 'INVALID_DOCUMENT',
        path,
        message: 'Markdownのメタデータを読めません。',
      });
      continue;
    }
    if (
      !idPattern.test(data.id ?? '') ||
      !(data.kind in levels) ||
      !Array.isArray(data.depends_on)
    ) {
      findings.push({
        code: 'INVALID_DOCUMENT',
        path,
        message: 'id、kind、depends_onが不正です。',
      });
      continue;
    }
    if (map.has(data.id)) {
      findings.push({
        code: 'DUPLICATE_ID',
        node: data.id,
        path,
        message: '文書IDが重複しています。',
      });
      continue;
    }
    const lifecycle = data.lifecycle ?? 'implemented';
    if (!['planned', 'implemented'].includes(lifecycle))
      findings.push({
        code: 'INVALID_LIFECYCLE',
        node: data.id,
        path,
        message: 'lifecycleはplannedまたはimplementedです。実行証拠は別に確認します。',
      });
    const plannedTests = data.planned_tests ?? [];
    if (
      data.kind === 'requirement' &&
      lifecycle === 'planned' &&
      (!Array.isArray(plannedTests) ||
        !plannedTests.length ||
        plannedTests.some((id) => typeof id !== 'string' || !id.trim()))
    )
      findings.push({
        code: 'MISSING_PLANNED_TESTS',
        node: data.id,
        path,
        message: '未実装要件には計画テストIDが必要です。',
      });
    const node = {
      id: data.id,
      kind: data.kind,
      lifecycle,
      plannedTests,
      title: text.match(/^# (.+)$/m)?.[1] ?? data.id,
      path,
      dependsOn: data.depends_on,
      artifacts: [],
      ownHash: hashText(text),
    };
    map.set(node.id, node);
    if (data.artifacts !== undefined && !Array.isArray(data.artifacts)) {
      findings.push({
        code: 'INVALID_ARTIFACT',
        node: node.id,
        path,
        message: 'artifactsは配列にしてください。',
      });
      continue;
    }
    for (const artifact of data.artifacts ?? []) {
      if (!artifact || typeof artifact !== 'object' || !roles.includes(artifact.role)) {
        findings.push({
          code: 'INVALID_ARTIFACT',
          node: node.id,
          path,
          message: '成果物の役割が不正です。',
        });
        continue;
      }
      try {
        safePath(root, artifact.path);
      } catch {
        findings.push({
          code: 'UNSAFE_PATH',
          node: node.id,
          path: artifact.path,
          message: '成果物は安全な相対パスで指定してください。',
        });
        continue;
      }
      if (artifactMap.has(artifact.path)) {
        findings.push({
          code: 'DUPLICATE_OWNER',
          node: node.id,
          path: artifact.path,
          message: '成果物の担当文書が重複しています。',
        });
        continue;
      }
      const absolute = safePath(root, artifact.path);
      if (!existsSync(absolute) || !lstatSync(absolute).isFile()) {
        findings.push({
          code: 'MISSING_ARTIFACT',
          node: node.id,
          path: artifact.path,
          message: '成果物が存在しません。',
        });
      }
      const a = {
        ...artifact,
        verifies: Array.isArray(artifact.verifies) ? artifact.verifies : [],
        owner: node.id,
        hash:
          existsSync(absolute) && lstatSync(absolute).isFile()
            ? hashText(readFileSync(absolute))
            : null,
      };
      artifactMap.set(a.path, a);
      node.artifacts.push(a);
    }
  }
  if (!map.size) findings.push({ code: 'NO_DOCUMENTS', message: '管理する文書がありません。' });
  for (const node of map.values())
    for (const dep of node.dependsOn) {
      if (!map.has(dep))
        findings.push({
          code: 'DANGLING_REFERENCE',
          node: node.id,
          path: node.path,
          message: `上位文書がありません: ${dep}`,
        });
      else if (levels[map.get(dep).kind] > levels[node.kind])
        findings.push({
          code: 'REVERSED_LAYER',
          node: node.id,
          path: node.path,
          message: `上位に下位層の文書を指定しています: ${dep}`,
        });
    }
  const visiting = new Set(),
    visited = new Set();
  function cycle(id) {
    if (visiting.has(id)) {
      findings.push({ code: 'CYCLE', node: id, message: '文書参照に循環があります。' });
      return;
    }
    if (visited.has(id) || !map.has(id)) return;
    visiting.add(id);
    for (const dep of map.get(id).dependsOn) cycle(dep);
    visiting.delete(id);
    visited.add(id);
  }
  for (const id of map.keys()) cycle(id);
  const ancestors = (id) => {
    const result = new Set();
    function go(current) {
      for (const dep of map.get(current)?.dependsOn ?? [])
        if (map.has(dep) && !result.has(dep)) {
          result.add(dep);
          go(dep);
        }
    }
    go(id);
    result.delete(id);
    return result;
  };
  const descendantIds = (id) =>
    [...map.keys()].filter((other) => other === id || ancestors(other).has(id));
  const verified = new Set();
  for (const a of artifactMap.values())
    for (const id of a.verifies) {
      if (a.role !== 'test' || map.get(id)?.kind !== 'requirement')
        findings.push({
          code: 'INVALID_VERIFICATION',
          node: a.owner,
          path: a.path,
          message: `検証先が要件ではありません: ${id}`,
        });
      else verified.add(id);
    }
  for (const node of map.values())
    if (node.kind === 'requirement' && node.lifecycle !== 'planned' && !verified.has(node.id))
      findings.push({
        code: 'UNVERIFIED_REQUIREMENT',
        node: node.id,
        message: '対応するテストが登録されていません。',
      });
  const inventory = unique([
    ...config.managedRoots.flatMap((p) => walk(root, p, findings)),
    ...config.managedFiles.filter((p) => {
      try {
        return existsSync(safePath(root, p));
      } catch {
        return true;
      }
    }),
  ]);
  for (const path of inventory)
    if (!artifactMap.has(path))
      findings.push({
        code: 'UNMANAGED_FILE',
        path,
        message: '詳細設計に対応がない管理対象ファイルです。',
      });
  markdownLinks(root, findings);
  let lock = { schemaVersion: 1, reviews: {} };
  if (existsSync(resolve(root, config.lockFile)))
    try {
      lock = JSON.parse(readFileSync(resolve(root, config.lockFile), 'utf8'));
      if (lock.schemaVersion !== 1 || !lock.reviews || typeof lock.reviews !== 'object')
        throw new Error();
    } catch {
      findings.push({ code: 'INVALID_LOCK', message: '確認記録を読めません。' });
      lock = { schemaVersion: 1, reviews: {} };
    }
  for (const id of Object.keys(lock.reviews))
    if (!map.has(id))
      findings.push({
        code: 'REMOVED_NODE_REVIEW',
        node: id,
        message: '削除されたノードの確認記録が残っています。明示的な削除レビューが必要です。',
      });
  const nodes = [...map.values()].map((node) => {
    const inputs = { [`doc:${node.id}`]: node.ownHash };
    for (const id of ancestors(node.id)) inputs[`doc:${id}`] = map.get(id).ownHash;
    const descendants = descendantIds(node.id);
    const relevantRequirements = new Set([node.id, ...ancestors(node.id)]);
    for (const a of artifactMap.values()) {
      if (
        descendants.includes(a.owner) ||
        (a.role === 'test' && a.verifies.some((id) => relevantRequirements.has(id)))
      )
        inputs[`file:${a.path}`] = a.hash;
    }
    const sorted = Object.fromEntries(
      Object.entries(inputs).sort(([a], [b]) => a.localeCompare(b)),
    );
    const fingerprint = hashText(JSON.stringify(sorted));
    const previous = lock.reviews[node.id];
    const status = !previous
      ? 'unreviewed'
      : previous.fingerprint === fingerprint
        ? 'current'
        : 'stale';
    const changedInputs = unique([
      ...Object.keys(sorted),
      ...Object.keys(previous?.inputs ?? {}),
    ]).filter((key) => sorted[key] !== previous?.inputs?.[key]);
    if (requireReviews && status !== 'current')
      findings.push({
        code: previous ? 'STALE_REVIEW' : 'REVIEW_REQUIRED',
        node: node.id,
        path: node.path,
        message: previous
          ? '入力が変更されています。文書の更新または理由付きの再確認が必要です。'
          : '初回の確認が必要です。',
        changedInputs,
      });
    return {
      ...node,
      inputs: sorted,
      fingerprint,
      status,
      changedInputs,
      reviewed: previous ?? null,
    };
  });
  const graph = {
    nodes: nodes.map(({ id, kind, lifecycle, title, path, status }) => ({
      id,
      kind,
      lifecycle,
      title,
      path,
      status,
    })),
    edges: [],
  };
  for (const node of nodes)
    for (const dep of node.dependsOn)
      if (map.has(dep))
        graph.edges.push({
          id: `dep:${dep}:${node.id}`,
          from: dep,
          to: node.id,
          kind: 'depends-on',
        });
  for (const a of artifactMap.values()) {
    graph.nodes.push({
      id: `file:${a.path}`,
      kind: a.role,
      title: a.path,
      path: a.path,
      status: a.hash ? 'file' : 'missing',
    });
    graph.edges.push({
      id: `owns:${a.owner}:${a.path}`,
      from: a.owner,
      to: `file:${a.path}`,
      kind: 'owns',
    });
    for (const id of a.verifies)
      if (map.has(id))
        graph.edges.push({
          id: `test:${id}:${a.path}`,
          from: id,
          to: `file:${a.path}`,
          kind: 'verified-by',
        });
  }
  return {
    ok: findings.length === 0,
    root,
    config,
    findings,
    nodes,
    artifacts: [...artifactMap.values()],
    graph,
  };
}

export function scopeSnapshot(root, scope) {
  const report = inspectProject(root, { requireReviews: false });
  if (!Array.isArray(scope) || scope.some((id) => !report.nodes.some((n) => n.id === id)))
    throw new Error('Unknown scope');
  const paths = new Set(
    scope.flatMap((id) =>
      Object.keys(report.nodes.find((n) => n.id === id).inputs)
        .filter((k) => k.startsWith('file:'))
        .map((k) => k.slice(5)),
    ),
  );
  return Object.fromEntries(
    [...paths]
      .sort()
      .map((path) => [
        path,
        existsSync(safePath(root, path)) ? hashText(readFileSync(safePath(root, path))) : null,
      ]),
  );
}

export function readChange(root, change) {
  if (!/^CHG-[A-Z0-9-]+$/.test(change ?? '')) throw new Error('変更票IDが必要です。');
  const { data } = readMarkdown(root, `docs/changes/${change}.md`);
  if (data.id !== change || data.kind !== 'change' || !Array.isArray(data.scope))
    throw new Error('変更票のメタデータが不正です。');
  return data;
}

export function greenIsCurrent(root, change, requiredPaths = []) {
  try {
    const meta = readChange(root, change);
    const directory = `evidence/tdd/${change}`;
    const evidence = JSON.parse(readFileSync(safePath(root, `${directory}/green.json`), 'utf8'));
    const red = JSON.parse(readFileSync(safePath(root, `${directory}/red.json`), 'utf8'));
    if (
      evidence.phase !== 'green' ||
      evidence.status !== 0 ||
      evidence.counts.tests < 1 ||
      evidence.counts.fail !== 0 ||
      evidence.counts.pass !== evidence.counts.tests ||
      evidence.counts.skipped ||
      evidence.counts.cancelled
    )
      return false;
    if (
      red.phase !== 'red' ||
      red.status !== 1 ||
      !red.counts.fail ||
      red.runner !== evidence.runner
    )
      return false;
    if (
      evidence.outputHash !== hashText(readFileSync(safePath(root, `${directory}/green.log`))) ||
      red.outputHash !== hashText(readFileSync(safePath(root, `${directory}/red.log`))) ||
      evidence.redOutputHash !== red.outputHash
    )
      return false;
    if (evidence.changeHash !== hashText(readFileSync(safePath(root, `docs/changes/${change}.md`))))
      return false;
    if (
      !Object.keys(evidence.testHashes ?? {}).length ||
      JSON.stringify(evidence.testHashes) !== JSON.stringify(red.testHashes)
    )
      return false;
    for (const [path, hash] of Object.entries(evidence.testHashes))
      if (hashText(readFileSync(safePath(root, path))) !== hash) return false;
    return (
      requiredPaths.every((path) => Object.hasOwn(evidence.scopeHashes ?? {}, path)) &&
      JSON.stringify(evidence.scopeHashes) === JSON.stringify(scopeSnapshot(root, meta.scope))
    );
  } catch {
    return false;
  }
}

export function acknowledge(root, id, { change, reason } = {}) {
  if (typeof reason !== 'string' || reason.trim().length < 24)
    throw new Error('確認した内容を24文字以上の具体的な理由で記録してください。');
  readChange(root, change);
  const report = inspectProject(root, { requireReviews: false });
  if (!report.ok)
    throw new Error(
      `構造エラーを先に解消してください: ${report.findings.map((x) => x.code).join(', ')}`,
    );
  const node = report.nodes.find((n) => n.id === id);
  if (!node) throw new Error('Unknown document ID');
  const changedCodePaths = node.changedInputs
    .filter(
      (key) =>
        key.startsWith('file:') &&
        ['implementation', 'test'].includes(
          report.artifacts.find((a) => a.path === key.slice(5))?.role,
        ),
    )
    .map((key) => key.slice(5));
  if (
    report.config.requireTdd &&
    changedCodePaths.length &&
    !greenIsCurrent(root, change, changedCodePaths)
  )
    throw new Error('変更された実装・テストを含むGreen記録がありません、または古くなっています。');
  const path = safePath(root, report.config.lockFile);
  const lock = existsSync(path)
    ? JSON.parse(readFileSync(path, 'utf8'))
    : { schemaVersion: 1, reviews: {}, history: [] };
  const record = {
    fingerprint: node.fingerprint,
    inputs: node.inputs,
    change,
    reason: reason.trim(),
    reviewer: 'local-review',
    reviewedAt: new Date().toISOString(),
  };
  lock.reviews[id] = record;
  lock.history = [...(lock.history ?? []), { id, ...record, inputs: undefined }];
  const temp = `${path}.tmp`;
  writeFileSync(temp, JSON.stringify(lock, null, 2) + '\n');
  renameSync(temp, path);
  return record;
}

export function retireNode(root, id, { change, reason } = {}) {
  if (!idPattern.test(id ?? '') || typeof reason !== 'string' || reason.trim().length < 24)
    throw new Error('削除するID、変更票、具体的な理由が必要です。');
  readChange(root, change);
  const report = inspectProject(root, { requireReviews: false });
  if (report.nodes.some((node) => node.id === id))
    throw new Error(
      '現存する文書は退役できません。参照を整理してから文書を移動・削除してください。',
    );
  const blocking = report.findings.filter((f) => f.code !== 'REMOVED_NODE_REVIEW');
  if (blocking.length)
    throw new Error(
      `参照と成果物の整合を先に直してください: ${blocking.map((f) => f.code).join(', ')}`,
    );
  const path = safePath(root, report.config.lockFile);
  const lock = JSON.parse(readFileSync(path, 'utf8'));
  if (!Object.hasOwn(lock.reviews, id)) throw new Error('退役対象の確認記録がありません。');
  const previous = lock.reviews[id];
  delete lock.reviews[id];
  const record = {
    id,
    action: 'retire',
    previousFingerprint: previous.fingerprint,
    change,
    reason: reason.trim(),
    reviewer: 'local-review',
    reviewedAt: new Date().toISOString(),
  };
  lock.history = [...(lock.history ?? []), record];
  writeFileSync(`${path}.tmp`, JSON.stringify(lock, null, 2) + '\n');
  renameSync(`${path}.tmp`, path);
  return record;
}
