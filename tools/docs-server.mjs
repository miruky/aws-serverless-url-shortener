import { fileURLToPath } from 'node:url';
import { startWorkbench } from './trace/workbench.mjs';
const port = Number(process.env.DOCS_PORT ?? 4323);
if (!Number.isInteger(port) || port < 0 || port > 65535) throw new Error('Invalid docs port');
const server = startWorkbench(fileURLToPath(new URL('../', import.meta.url)), port);
for (const signal of ['SIGINT', 'SIGTERM'])
  process.on(signal, () => {
    server.closeAllConnections();
    server.close();
  });
