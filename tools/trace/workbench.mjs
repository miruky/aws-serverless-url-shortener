import { createServer } from 'node:http';
import { readFileSync, writeFileSync, mkdirSync, copyFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { inspectProject } from './model.mjs';

const style = `*{box-sizing:border-box}body{margin:0;font:14px/1.65 system-ui,sans-serif;background:#f3f4f6;color:#17202a}header{padding:20px 28px;background:#fff;border-bottom:1px solid #d5dbe2;display:flex;justify-content:space-between;gap:20px}h1{font-size:20px;margin:0}p{margin:3px 0}main{padding:22px;display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:18px}#graph{height:60vh;min-height:380px;background:#fff;border:1px solid #d5dbe2}aside,section{background:white;border:1px solid #d5dbe2;padding:18px;min-width:0}h2{font-size:15px;margin:0 0 10px}button,input,select{font:inherit;padding:9px;border:1px solid #aeb8c5;border-radius:4px;background:#fff}button{cursor:pointer}button:focus-visible,input:focus-visible{outline:3px solid #2258b0;outline-offset:3px}.ok{color:#1f663e}.bad{color:#a53430}.toolbar{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}.legend{font-size:12px;color:#526274}#findings{max-height:44vh;overflow:auto;padding-left:20px}code{overflow-wrap:anywhere}table{width:100%;border-collapse:collapse;font-size:12px}td,th{border-bottom:1px solid #e2e7ed;text-align:left;padding:9px;overflow-wrap:anywhere}#table{grid-column:1/-1}#detail{white-space:pre-wrap;overflow-wrap:anywhere}a{color:#244ca6}@media(max-width:850px){header{display:block}main{grid-template-columns:1fr}#graph{height:50vh}#table{overflow:auto}}`;

function client(live, initial) {
  return `const live=${JSON.stringify(live)};let report=${JSON.stringify(initial).replace(/</g, '\\u003c')};let cy;let documentsOnly=true;const labels={requirement:'要件',basic:'基本設計',detail:'詳細設計',implementation:'実装',test:'テスト',configuration:'設定'};const status={current:'確認済み',stale:'要再確認',unreviewed:'未確認',file:'ファイル',missing:'欠落'};
function draw(next,resetView=false){report=next;const summary=document.querySelector('#summary');summary.textContent=report.ok?'すべて確認済み':report.findings.length+'件の確認が必要';summary.className=report.ok?'ok':'bad';document.querySelector('#counts').textContent=report.nodes.length+'文書・'+report.graph.nodes.length+'ノード・'+report.graph.edges.length+'接続';const list=document.querySelector('#findings');list.replaceChildren();for(const f of report.findings){const li=document.createElement('li');li.textContent=(f.node||f.path||'')+' '+f.message;list.append(li)}const visibleNodes=report.graph.nodes.filter(n=>!documentsOnly||!n.id.startsWith('file:'));const visibleIds=new Set(visibleNodes.map(n=>n.id));const elements=[...visibleNodes.map(n=>({data:{...n,label:(n.id.startsWith('file:')?n.path.split('/').slice(-2).join('/'):n.id)+'\\n'+(labels[n.kind]||n.kind)}})),...report.graph.edges.filter(e=>visibleIds.has(e.from)&&visibleIds.has(e.to)).map(e=>({data:{id:e.id,source:e.from,target:e.to,kind:e.kind}}))];const oldZoom=resetView?undefined:cy?.zoom(),oldPan=resetView?undefined:cy?.pan();if(cy)cy.destroy();cy=cytoscape({container:document.querySelector('#graph'),elements,layout:{name:'breadthfirst',directed:true,padding:24,spacingFactor:1.25},style:[{selector:'node',style:{label:'data(label)','font-size':10,'text-wrap':'wrap','text-max-width':130,'text-valign':'center','text-halign':'center',width:130,height:45,shape:'round-rectangle','background-color':'#e6ebf2','border-width':1,'border-color':'#8b9bad',color:'#17202a'}},{selector:'node[kind="requirement"]',style:{'background-color':'#cfe3f8'}},{selector:'node[kind="basic"]',style:{'background-color':'#dcebd7'}},{selector:'node[kind="detail"]',style:{'background-color':'#f0e6cb'}},{selector:'node[status="stale"],node[status="unreviewed"]',style:{'border-color':'#bd4a3e','border-width':3}},{selector:'node[kind="test"]',style:{'background-color':'#e9def5'}},{selector:'edge',style:{width:1.2,'curve-style':'bezier','target-arrow-shape':'triangle','line-color':'#9eacbb','target-arrow-color':'#9eacbb'}},{selector:'edge[kind="verified-by"]',style:{'line-style':'dashed','line-color':'#b8aac7','target-arrow-color':'#b8aac7'}},{selector:'.dim',style:{opacity:.13}},{selector:'.highlight',style:{'border-color':'#174ba3','border-width':4}}]});if(oldZoom){cy.zoom(oldZoom);cy.pan(oldPan)}cy.on('tap','node',e=>{const n=e.target.data();document.querySelector('#detail').textContent=(labels[n.kind]||n.kind)+' / '+status[n.status]+'\\n'+n.path+'\\n\\n'+(report.nodes.find(x=>x.id===n.id)?.changedInputs?.join('\\n')||'変更入力なし');});const tbody=document.querySelector('tbody');tbody.replaceChildren();for(const n of report.nodes){const tr=document.createElement('tr');for(const value of[n.id,labels[n.kind],status[n.status],n.lifecycle==='planned'?'計画・未実装':'実装あり（検証は別）',n.path,report.graph.edges.filter(e=>e.kind==='depends-on'&&e.to===n.id).map(e=>e.from).join(', ')||'—',n.changedInputs.length]){const td=document.createElement('td');td.textContent=String(value);tr.append(td)}tbody.append(tr)}}
document.querySelector('#files').onclick=()=>{documentsOnly=!documentsOnly;document.querySelector('#files').textContent=documentsOnly?'ファイルも表示':'文書だけに戻す';draw(report,true)};document.querySelector('#fit').onclick=()=>cy.fit(undefined,24);document.querySelector('#filter').oninput=e=>{const value=e.target.value.toLowerCase();cy.nodes().removeClass('dim highlight');if(value)cy.nodes().forEach(n=>n.toggleClass('dim',!(n.data('id')+' '+n.data('path')).toLowerCase().includes(value)))};document.querySelector('#stale').onclick=()=>{cy.nodes().removeClass('dim highlight');cy.nodes().forEach(n=>n.toggleClass('dim',!['stale','unreviewed','missing'].includes(n.data('status'))))};let signature='';async function refresh(){if(!live)return;try{const next=await fetch('/api/status',{cache:'no-store'}).then(r=>r.json());const sig=JSON.stringify(next.nodes.map(n=>[n.id,n.fingerprint,n.status]))+JSON.stringify(next.findings);if(sig!==signature){signature=sig;draw(next)}}catch{document.querySelector('#summary').textContent='ローカル接続を確認してください'}}draw(report);if(live)setInterval(refresh,2500);`;
}
function publicReport(report) {
  return {
    ok: report.ok,
    findings: report.findings,
    nodes: report.nodes.map(
      ({ id, kind, lifecycle, path, title, fingerprint, status, changedInputs }) => ({
        id,
        kind,
        lifecycle,
        path,
        title,
        fingerprint,
        status,
        changedInputs,
      }),
    ),
    graph: report.graph,
  };
}
function html(report, live) {
  return `<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>仕様のワークベンチ</title><style>${style}</style><header><div><h1>仕様のワークベンチ</h1><p>要件・設計・実装・テストの対応関係</p></div><div><strong id="summary"></strong><p id="counts"></p></div></header><main><div><div class="toolbar"><input id="filter" aria-label="ノードを絞り込む" placeholder="ID・ファイル名を検索"><button id="fit">全体を表示</button><button id="files">ファイルも表示</button><button id="stale">要確認を強調</button></div><div id="graph" role="img" aria-label="仕様の依存関係グラフ。下の表でも確認できます。"></div><p class="legend">赤枠：要確認 ／ 実線：依存・担当 ／ 破線：要件を検証するテスト。ノードを選択すると詳細を表示。</p></div><aside><h2>検出された変更</h2><ul id="findings"></ul><h2>選択したノード</h2><div id="detail">ノードを選択してください。</div><p>本文または影響先を確認した後、変更票と理由を付けて確認記録を更新します。自動承認は行いません。</p></aside><section id="table"><h2>文書の一覧</h2><table><thead><tr><th>ID</th><th>種類</th><th>文書の確認</th><th>実装段階</th><th>ファイル</th><th>依存先</th><th>変更入力</th></tr></thead><tbody></tbody></table></section></main><script src="/cytoscape.min.js"></script><script>${client(live, publicReport(report))}</script></html>`;
}
export function exportGraph(root) {
  const report = inspectProject(root),
    directory = resolve(root, '.harness');
  mkdirSync(directory, { recursive: true });
  writeFileSync(
    resolve(directory, 'graph.json'),
    JSON.stringify(publicReport(report), null, 2) + '\n',
  );
  writeFileSync(
    resolve(directory, 'graph.html'),
    html(report, false).replace('src="/cytoscape.min.js"', 'src="cytoscape.min.js"'),
  );
  copyFileSync(
    resolve(root, 'node_modules/cytoscape/dist/cytoscape.min.js'),
    resolve(directory, 'cytoscape.min.js'),
  );
  return '.harness/graph.html';
}
export function startWorkbench(root, port = 4322) {
  const server = createServer((req, res) => {
    const listeningPort = server.address()?.port ?? port;
    if (
      !['127.0.0.1:' + listeningPort, 'localhost:' + listeningPort].includes(
        req.headers.host ?? '',
      ) ||
      (req.headers.origin &&
        !['http://127.0.0.1:' + listeningPort, 'http://localhost:' + listeningPort].includes(
          req.headers.origin,
        ))
    ) {
      res.writeHead(403);
      res.end();
      return;
    }
    if (req.method !== 'GET') {
      res.writeHead(405);
      res.end();
      return;
    }
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('Referrer-Policy', 'no-referrer');
    try {
      if (req.url === '/cytoscape.min.js') {
        res.setHeader('Content-Type', 'text/javascript; charset=utf-8');
        res.end(readFileSync(resolve(root, 'node_modules/cytoscape/dist/cytoscape.min.js')));
      } else if (req.url === '/api/status') {
        res.setHeader('Content-Type', 'application/json');
        res.end(JSON.stringify(publicReport(inspectProject(root))));
      } else if (req.url === '/') {
        res.setHeader('Content-Type', 'text/html; charset=utf-8');
        res.end(html(inspectProject(root), true));
      } else {
        res.writeHead(404);
        res.end('Not found');
      }
    } catch {
      res.writeHead(500);
      res.end('ローカルの仕様ファイルを確認してください。');
    }
  });
  server.listen(port, '127.0.0.1', () =>
    console.log(`仕様のワークベンチ: http://127.0.0.1:${server.address().port}`),
  );
  return server;
}
