import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { inspectProject } from '../../tools/trace/model.mjs';

test('a broken README link is checked as part of documentation quality', t=>{
  const root=mkdtempSync(join(tmpdir(),'shortener-readme-'));
  t.after(()=>rmSync(root,{recursive:true,force:true}));
  writeFileSync(join(root,'trace.config.json'),JSON.stringify({schemaVersion:1,documents:[],managedRoots:[],managedFiles:['README.md'],lockFile:'trace.lock.json'}));
  writeFileSync(join(root,'README.md'),'# Start\n[Missing guide](docs/missing.md)\n');
  assert.ok(inspectProject(root).findings.some(f=>f.code==='BROKEN_MARKDOWN_LINK'&&f.path==='README.md'));
});
