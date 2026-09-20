import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { greenIsCurrent, scopeSnapshot } from '../../tools/trace/model.mjs';

test('a fabricated green summary without an execution log cannot approve a source change', t => {
  const root=mkdtempSync(join(tmpdir(),'shortener-evidence-'));
  t.after(()=>rmSync(root,{recursive:true,force:true}));
  for(const path of ['docs/details','docs/changes','src','evidence/tdd/CHG-ONE'])mkdirSync(join(root,path),{recursive:true});
  writeFileSync(join(root,'trace.config.json'),JSON.stringify({schemaVersion:1,documents:['docs/details'],managedRoots:['src'],managedFiles:[],lockFile:'trace.lock.json'}));
  writeFileSync(join(root,'src/main.py'),'value = 1\n');
  writeFileSync(join(root,'docs/details/main.md'),'---\nid: DETAIL-ONE\nkind: detail\ndepends_on: []\nartifacts:\n  - {path: src/main.py, role: implementation}\n---\n# Detail\n');
  writeFileSync(join(root,'docs/changes/CHG-ONE.md'),'---\nid: CHG-ONE\nkind: change\nscope: [DETAIL-ONE]\n---\n# Change\n');
  writeFileSync(join(root,'evidence/tdd/CHG-ONE/green.json'),JSON.stringify({phase:'green',status:0,counts:{tests:1,pass:1,fail:0},scopeHashes:scopeSnapshot(root,['DETAIL-ONE'])}));
  assert.equal(greenIsCurrent(root,'CHG-ONE',['src/main.py']),false);
});
