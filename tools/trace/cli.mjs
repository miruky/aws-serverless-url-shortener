import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { inspectProject, acknowledge, retireNode } from './model.mjs';
import { exportGraph } from './workbench.mjs';

const root = fileURLToPath(new URL('../../', import.meta.url));
const args = process.argv.slice(2);
const option = (name) => (args.includes(name) ? args[args.indexOf(name) + 1] : undefined);
const command = args[0] ?? 'check';
try {
  if (command === 'ack') {
    const record = acknowledge(root, args[1], {
      change: option('--change'),
      reason: option('--reason'),
    });
    console.log(`${args[1]}: 確認を記録しました (${record.fingerprint.slice(0, 12)})`);
  } else if (command === 'retire') {
    retireNode(root, args[1], { change: option('--change'), reason: option('--reason') });
    console.log(`${args[1]}: 退役を記録しました。`);
  } else if (command === 'graph') {
    console.log(exportGraph(root));
  } else if (['check', 'impact', 'json'].includes(command)) {
    const report = inspectProject(root);
    if (command === 'json' || args.includes('--json')) console.log(JSON.stringify(report, null, 2));
    else {
      console.log(
        `${report.nodes.length} 文書 / ${report.graph.nodes.length} ノード / ${report.graph.edges.length} 接続`,
      );
      for (const f of report.findings) {
        console.log(`${f.code} ${f.node ?? f.path ?? ''}: ${f.message}`);
        if (command === 'impact' && f.changedInputs?.length)
          console.log(`  変更: ${f.changedInputs.join(', ')}`);
      }
      if (report.ok) console.log('仕様・設計・実装・テストの確認状態: 合格');
    }
    if (command !== 'impact' && !report.ok) process.exitCode = 1;
  } else
    throw new Error(
      '使い方: trace check | impact | graph | ack ID --change CHG-ID --reason 理由 | retire ID --change CHG-ID --reason 理由',
    );
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
