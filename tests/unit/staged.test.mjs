import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,writeFileSync,rmSync} from 'node:fs';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {spawnSync} from 'node:child_process';
import {acknowledge,inspectProject} from '../../tools/trace/model.mjs';
import {inspectIndex} from '../../tools/check-staged.mjs';

test('unstaged review cannot approve stale staged documentation',t=>{
  const root=mkdtempSync(join(tmpdir(),'shortener-staged-'));
  t.after(()=>rmSync(root,{recursive:true,force:true}));
  for(const path of ['docs/details','docs/changes','src'])mkdirSync(join(root,path),{recursive:true});
  writeFileSync(join(root,'trace.config.json'),JSON.stringify({schemaVersion:1,documents:['docs/details'],managedRoots:['src'],managedFiles:[],lockFile:'trace.lock.json'}));
  writeFileSync(join(root,'docs/details/main.md'),'---\nid: DETAIL-ONE\nkind: detail\ndepends_on: []\nartifacts:\n  - {path: src/main.py, role: implementation}\n---\n# Detail\n');
  writeFileSync(join(root,'docs/changes/CHG-ONE.md'),'---\nid: CHG-ONE\nkind: change\nscope: [DETAIL-ONE]\n---\n# Change\n');
  writeFileSync(join(root,'src/main.py'),'value = 1\n');
  const review=()=>acknowledge(root,'DETAIL-ONE',{change:'CHG-ONE',reason:'変更された実装の値を文書と照合し、この範囲の設計に矛盾がないことを確認した。'});
  const git=(...args)=>assert.equal(spawnSync('git',args,{cwd:root,encoding:'utf8'}).status,0);
  git('init','--quiet');review();git('add','.');
  assert.equal(inspectIndex(root).ok,true);
  writeFileSync(join(root,'src/main.py'),'value = 2\n');git('add','src/main.py');review();
  assert.equal(inspectProject(root).ok,true);
  assert.equal(inspectIndex(root).ok,false);
  git('add','trace.lock.json');assert.equal(inspectIndex(root).ok,true);
});
