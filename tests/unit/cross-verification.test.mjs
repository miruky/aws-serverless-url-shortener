import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,writeFileSync,rmSync} from 'node:fs';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {acknowledge,inspectProject} from '../../tools/trace/model.mjs';

test('a verifying test owned by another design still invalidates the requirement',t=>{
  const root=mkdtempSync(join(tmpdir(),'shortener-cross-'));
  t.after(()=>rmSync(root,{recursive:true,force:true}));
  for(const path of ['docs/requirements','docs/details','docs/changes','tests'])mkdirSync(join(root,path),{recursive:true});
  writeFileSync(join(root,'trace.config.json'),JSON.stringify({schemaVersion:1,documents:['docs/requirements','docs/details'],managedRoots:['tests'],managedFiles:[],lockFile:'trace.lock.json'}));
  writeFileSync(join(root,'docs/requirements/api.md'),'---\nid: REQ-API\nkind: requirement\ndepends_on: []\n---\n# API\n');
  writeFileSync(join(root,'docs/details/api.md'),'---\nid: DETAIL-API\nkind: detail\ndepends_on: [REQ-API]\n---\n# API design\n');
  writeFileSync(join(root,'docs/details/browser.md'),'---\nid: DETAIL-BROWSER\nkind: detail\ndepends_on: []\nartifacts:\n  - {path: tests/browser.mjs, role: test, verifies: [REQ-API]}\n---\n# Browser\n');
  writeFileSync(join(root,'tests/browser.mjs'),'old test\n');
  writeFileSync(join(root,'docs/changes/CHG-ONE.md'),'---\nid: CHG-ONE\nkind: change\nscope: [DETAIL-API, DETAIL-BROWSER]\n---\n# Change\n');
  for(const id of ['REQ-API','DETAIL-API','DETAIL-BROWSER'])acknowledge(root,id,{change:'CHG-ONE',reason:'この要件を検証するブラウザテストと実装の契約を照合し、文書の内容を確認した。'});
  writeFileSync(join(root,'tests/browser.mjs'),'changed test\n');
  const stale=inspectProject(root).nodes.filter(n=>n.status==='stale').map(n=>n.id).sort();
  assert.deepEqual(stale,['DETAIL-API','DETAIL-BROWSER','REQ-API']);
});
