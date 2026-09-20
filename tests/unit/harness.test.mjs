import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync, utimesSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { inspectProject, acknowledge, retireNode } from '../../tools/trace/model.mjs';

function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), 'workspace-trace-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  for (const dir of ['docs/requirements', 'docs/basic', 'docs/details', 'docs/changes', 'src', 'tests']) mkdirSync(join(root, dir), { recursive: true });
  writeFileSync(join(root, 'trace.config.json'), JSON.stringify({ schemaVersion: 1, documents: ['docs/requirements', 'docs/basic', 'docs/details'], managedRoots: ['src', 'tests'], managedFiles: [], lockFile: 'trace.lock.json' }));
  writeFileSync(join(root, 'docs/requirements/main.md'), '---\nid: REQ-ONE\nkind: requirement\ndepends_on: []\n---\n# 要件\n必要な挙動。\n');
  writeFileSync(join(root, 'docs/basic/main.md'), '---\nid: BASIC-ONE\nkind: basic\ndepends_on: [REQ-ONE]\n---\n# 基本設計\n構造。\n');
  writeFileSync(join(root, 'docs/details/main.md'), '---\nid: DETAIL-ONE\nkind: detail\ndepends_on: [BASIC-ONE]\nartifacts:\n  - {path: src/main.mjs, role: implementation}\n  - {path: tests/main.test.mjs, role: test, verifies: [REQ-ONE]}\n---\n# 詳細設計\n関数。\n');
  writeFileSync(join(root, 'src/main.mjs'), 'export const value = 1;\n');
  writeFileSync(join(root, 'tests/main.test.mjs'), 'test fixture\n');
  writeFileSync(join(root, 'docs/changes/CHG-ONE.md'), '---\nid: CHG-ONE\nkind: change\nscope: [DETAIL-ONE]\n---\n# 変更\n要件を確認する。\n');
  return root;
}
const codes = report => report.findings.map(x => x.code);
function acceptAll(root) {
  for (const id of ['REQ-ONE', 'BASIC-ONE', 'DETAIL-ONE']) acknowledge(root, id, { change: 'CHG-ONE', reason: '対象の要件と実装・テストの対応関係を確認し、今回の変更内容と矛盾しないことを確認した。' });
}

test('new documents require explicit review', t => {
  const r = inspectProject(fixture(t));
  assert.equal(r.ok, false);
  assert.equal(r.findings.filter(x => x.code === 'REVIEW_REQUIRED').length, 3);
});
test('acknowledged graph passes', t => { const root=fixture(t); acceptAll(root); assert.equal(inspectProject(root).ok, true); });
test('requirement edit makes every downstream document stale', t => {
  const root=fixture(t); acceptAll(root);
  const p=join(root,'docs/requirements/main.md'); writeFileSync(p,readFileSync(p,'utf8')+'追加要件。\n');
  assert.deepEqual(inspectProject(root).findings.filter(x=>x.code==='STALE_REVIEW').map(x=>x.node).sort(), ['BASIC-ONE','DETAIL-ONE','REQ-ONE']);
});
test('implementation edit makes requirements and both design levels stale', t => {
  const root=fixture(t); acceptAll(root); writeFileSync(join(root,'src/main.mjs'),'export const value = 2;\n');
  assert.equal(inspectProject(root).findings.filter(x=>x.code==='STALE_REVIEW').length,3);
});
test('timestamps alone do not create freshness', t=> { const root=fixture(t); acceptAll(root); utimesSync(join(root,'src/main.mjs'),new Date(),new Date()); assert.equal(inspectProject(root).ok,true); });
test('acknowledging one node leaves the other stale nodes unresolved',t=>{
  const root=fixture(t); acceptAll(root); writeFileSync(join(root,'src/main.mjs'),'export const value = 3;\n');
  acknowledge(root,'DETAIL-ONE',{change:'CHG-ONE',reason:'この詳細設計について変更後の実装とテストを確認し、文書の記載は変更不要と判断した。'});
  assert.equal(inspectProject(root).findings.filter(x=>x.code==='STALE_REVIEW').length,2);
});
test('dangling dependencies fail',t=>{const root=fixture(t); const p=join(root,'docs/basic/main.md'); writeFileSync(p,readFileSync(p,'utf8').replace('REQ-ONE','REQ-MISSING')); assert.ok(codes(inspectProject(root)).includes('DANGLING_REFERENCE'));});
test('cycles fail',t=>{const root=fixture(t);const p=join(root,'docs/requirements/main.md');writeFileSync(p,readFileSync(p,'utf8').replace('depends_on: []','depends_on: [BASIC-ONE]'));assert.ok(codes(inspectProject(root)).includes('CYCLE'));});
test('duplicate document IDs fail',t=>{const root=fixture(t);writeFileSync(join(root,'docs/requirements/duplicate.md'),readFileSync(join(root,'docs/requirements/main.md')));assert.ok(codes(inspectProject(root)).includes('DUPLICATE_ID'));});
test('unmapped code files fail',t=>{const root=fixture(t);writeFileSync(join(root,'src/forgotten.mjs'),'export const forgotten = true;');assert.ok(codes(inspectProject(root)).includes('UNMANAGED_FILE'));});
test('missing implementation files fail',t=>{const root=fixture(t);rmSync(join(root,'src/main.mjs'));assert.ok(codes(inspectProject(root)).includes('MISSING_ARTIFACT'));});
test('path traversal is rejected',t=>{const root=fixture(t);const p=join(root,'docs/details/main.md');writeFileSync(p,readFileSync(p,'utf8').replace('src/main.mjs','../escape.mjs'));assert.ok(codes(inspectProject(root)).includes('UNSAFE_PATH'));});
test('a reason and a real change record are required',t=>{const root=fixture(t);assert.throws(()=>acknowledge(root,'REQ-ONE',{change:'CHG-ONE',reason:'ok'}));assert.throws(()=>acknowledge(root,'REQ-ONE',{change:'CHG-NONE',reason:'対象文書と変更内容を確認し、依存関係が正しく保たれていることを確認した。'}));});
test('a requirement must have a verifying test',t=>{const root=fixture(t);const p=join(root,'docs/details/main.md');writeFileSync(p,readFileSync(p,'utf8').replace('verifies: [REQ-ONE]','verifies: []'));assert.ok(codes(inspectProject(root)).includes('UNVERIFIED_REQUIREMENT'));});
test('graph has requirement, design, implementation and test nodes',t=>{const root=fixture(t);const r=inspectProject(root);assert.equal(r.graph.nodes.length,5);assert.ok(r.graph.edges.some(e=>e.kind==='verified-by'));});
test('retiring a renamed node removes only its obsolete review',t=>{const root=fixture(t);acceptAll(root);const p=join(root,'docs/details/main.md');writeFileSync(p,readFileSync(p,'utf8').replace('id: DETAIL-ONE','id: DETAIL-NEW'));assert.ok(codes(inspectProject(root)).includes('REMOVED_NODE_REVIEW'));retireNode(root,'DETAIL-ONE',{change:'CHG-ONE',reason:'文書を新しいIDへ移し、参照と担当ファイルを新しい文書へ引き継いだことを確認した。'});const r=inspectProject(root);assert.equal(codes(r).includes('REMOVED_NODE_REVIEW'),false);assert.equal(r.nodes.find(n=>n.id==='REQ-ONE').status,'current');});
test('an active node cannot be retired',t=>{const root=fixture(t);acceptAll(root);assert.throws(()=>retireNode(root,'DETAIL-ONE',{change:'CHG-ONE',reason:'現在の文書が残っているため、この削除は受け入れられないことを確認するためのテスト。'}));});
test('retirement requires a documented reason',t=>{const root=fixture(t);acceptAll(root);assert.throws(()=>retireNode(root,'DETAIL-ONE',{change:'CHG-ONE',reason:'ok'}));});
test('an unrelated green scope cannot approve changed implementation',t=>{
  const root=fixture(t);acceptAll(root);
  const config=JSON.parse(readFileSync(join(root,'trace.config.json'),'utf8'));config.requireTdd=true;writeFileSync(join(root,'trace.config.json'),JSON.stringify(config));
  writeFileSync(join(root,'docs/details/other.md'),'---\nid: DETAIL-OTHER\nkind: detail\ndepends_on: [BASIC-ONE]\n---\n# 別の設計\n');
  writeFileSync(join(root,'docs/changes/CHG-OTHER.md'),'---\nid: CHG-OTHER\nkind: change\nscope: [DETAIL-OTHER]\n---\n# 別の変更\n');
  mkdirSync(join(root,'evidence/tdd/CHG-OTHER'),{recursive:true});
  writeFileSync(join(root,'evidence/tdd/CHG-OTHER/green.json'),JSON.stringify({phase:'green',status:0,counts:{tests:1,pass:1,fail:0,skipped:0,cancelled:0},scopeHashes:{}}));
  writeFileSync(join(root,'src/main.mjs'),'export const value = 99;\n');
  assert.throws(()=>acknowledge(root,'DETAIL-ONE',{change:'CHG-OTHER',reason:'別の範囲のテストが成功していても、この実装を確認したことにはできない。'}));
});

test('planned requirements retain review tracking without pretending to have executed tests', t => {
  const root=fixture(t),p=join(root,'docs/requirements/main.md'),d=join(root,'docs/details/main.md');
  writeFileSync(p,readFileSync(p,'utf8').replace('kind: requirement','kind: requirement\nlifecycle: planned\nplanned_tests: [T-LINKS]'));
  writeFileSync(d,readFileSync(d,'utf8').replace('verifies: [REQ-ONE]','verifies: []'));
  const r=inspectProject(root,{requireReviews:false});
  assert.equal(r.ok,true,JSON.stringify(r.findings));
  assert.equal(r.nodes.find(n=>n.id==='REQ-ONE').lifecycle,'planned');
  assert.equal(r.graph.nodes.find(n=>n.id==='REQ-ONE').lifecycle,'planned');
  assert.equal(r.nodes.find(n=>n.id==='REQ-ONE').status,'unreviewed');
});
test('planned requirements need explicit planned tests', t => {
  const root=fixture(t),p=join(root,'docs/requirements/main.md');
  writeFileSync(p,readFileSync(p,'utf8').replace('kind: requirement','kind: requirement\nlifecycle: planned'));
  assert.ok(codes(inspectProject(root)).includes('MISSING_PLANNED_TESTS'));
});
test('changing a planned requirement to implemented requires actual test registration', t => {
  const root=fixture(t),p=join(root,'docs/requirements/main.md'),d=join(root,'docs/details/main.md');
  writeFileSync(p,readFileSync(p,'utf8').replace('kind: requirement','kind: requirement\nlifecycle: implemented\nplanned_tests: [T-LINKS]'));
  writeFileSync(d,readFileSync(d,'utf8').replace('verifies: [REQ-ONE]','verifies: []'));
  assert.ok(codes(inspectProject(root)).includes('UNVERIFIED_REQUIREMENT'));
});
test('unknown lifecycle cannot silently skip verification', t => {
  const root=fixture(t),p=join(root,'docs/requirements/main.md');
  writeFileSync(p,readFileSync(p,'utf8').replace('kind: requirement','kind: requirement\nlifecycle: verified'));
  assert.ok(codes(inspectProject(root)).includes('INVALID_LIFECYCLE'));
});
