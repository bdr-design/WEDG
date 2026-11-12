// The page's side (design/prototype3d/engine.js) with the compiled worker, in node: a fake Worker runs
// engine_worker.js in its own context, with the page's globals faked around engine.js. Checks both ways the save is
// kept (the page's localStorage in the browser tests; the app's server, which the worker reaches itself), a request
// that never answers, and the pause when the page is hidden.
//   node test_js/engine_page.mjs <engine_worker.js>
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const workerCode = fs.readFileSync(path.resolve(process.argv[2]), 'utf8');

// the app's server, as the worker's fetch sees it
const files = {};
let hang = false, requests = 0;
function fetchInWorker(url, init) {
  return new Promise((resolve, reject) => {
    requests++;
    if (init.headers['x-marah-save'] !== 'tok') return resolve({ status: 403, text: async () => '' });
    if (hang) { init.signal.addEventListener('abort', () => reject(new Error('aborted'))); return; }
    const key = decodeURIComponent(url.split('/save/')[1] || '');
    if (init.method === 'GET') return resolve({ status: 200, text: async () => JSON.stringify(files) });
    if (init.method === 'PUT') files[key] = init.body; else delete files[key];
    resolve({ status: 204, text: async () => '' });
  });
}

class FakeWorker {
  constructor() {
    const ctx = { console, setTimeout, clearTimeout, setInterval, clearInterval, AbortController, fetch: fetchInWorker, Date, Math, JSON };
    ctx.self = ctx;
    ctx.postMessage = (data) => setTimeout(() => { if (!this.dead) this.onmessage?.({ data }); }, 0);
    vm.createContext(ctx);
    vm.runInContext(workerCode, ctx);
    this.ctx = ctx;
  }
  postMessage(data) { if (!this.dead) setTimeout(() => this.ctx.onmessage({ data }), 0); }
  terminate() { this.dead = true; this.onmessage = null; }
}

const storage = new Map();
const listeners = [];
globalThis.Worker = FakeWorker;
globalThis.localStorage = { getItem: (k) => storage.get(k) ?? null, setItem: (k, v) => storage.set(k, String(v)), removeItem: (k) => storage.delete(k) };
globalThis.document = { hidden: false, addEventListener: (t, f) => listeners.push(f), removeEventListener: (t, f) => { const i = listeners.indexOf(f); if (i >= 0) listeners.splice(i, 1); } };
const setPage = (search) => { globalThis.location = { search, origin: 'http://127.0.0.1:9' }; };
const hide = (hidden) => { globalThis.document.hidden = hidden; for (const f of listeners) f(); };

const { startEngine } = await import(pathToFileURL(path.join(here, '../../../design/prototype3d/engine.js')).href);

// 1. the browser tests' way: localStorage
setPage('');
const a = await startEngine({ newGame: { seed: 5 } });
assert.strictEqual(a.status, 'new');
assert.ok(a.snapshot && a.snapshot.herd.total === 3, 'a snapshot came');
assert.ok(storage.get('marah.proto.marah.save'), 'kept in localStorage');
assert.strictEqual((await a.dispatch({ type: 'orderSupply', supply: 'water', units: 1 })).ok, true);
assert.strictEqual((await a.dispatch({ type: 'orderSupply', supply: 'water', units: 1.5 })).error, 'badCommand');
assert.strictEqual((await a.startOver({ region: 'mars' })).error, 'badNewGame', 'resolved, not thrown');
assert.ok(a.stats.writes > 0 && a.stats.failedWrites === 0 && a.stats.snapshotChars > 1000);
assert.strictEqual(await startEngine(), a, 'one engine at a time');
await a.stop();
const b = await startEngine();
assert.strictEqual(b.status, 'opened', 'opened again from what the page kept');
assert.ok(storage.get('marah.proto.marah.save').includes('"supply":"water"'));

// 2. the app's way: the worker reads and writes the server's files; the page never sees the save
await b.stop();      // (its last save goes to the page's storage first)
setPage('?save=tok');
for (const [k, v] of storage) if (k.startsWith('marah.proto.')) files[k.slice('marah.proto.'.length)] = v;
storage.clear();
const c = await startEngine();
assert.strictEqual(c.status, 'opened', 'opened from the server');
assert.strictEqual((await c.dispatch({ type: 'orderSupply', supply: 'barley', units: 2 })).ok, true);
assert.ok(files['marah.save'].includes('"supply":"barley"'), 'written to the server');
assert.strictEqual(storage.size, 0, 'nothing in the page\'s storage');
// hidden: saved and stopped; shown: caught up
hide(true); hide(false);
await c.flush();      // (queued behind the pause and the resume)
// 3. a request that never answers is cut off (15 s) and reported; the next save goes through
hang = true;
const t0 = Date.now();
await c.dispatch({ type: 'orderSupply', supply: 'barley', units: 1 });
assert.ok(Date.now() - t0 < 20000, 'the command was not held for ever');
assert.ok(c.stats.failedWrites > 0, 'the failed write was reported');
hang = false;
assert.strictEqual((await c.flush()).ok, true);
assert.ok(requests > 4);
// a worker that no longer answers: stop() gives up on its save after 20 s, the calls still waiting fail, and a new
// engine may start
c.worker.dead = true;
const pending = c.dispatch({ type: 'setShepherds', count: 1 }).then(() => 'answered', () => 'failed');
const t1 = Date.now();
await c.stop();
assert.ok(Date.now() - t1 < 25000, 'stop() did not wait for ever');
assert.strictEqual(await pending, 'failed');
assert.notStrictEqual(await startEngine(), c, 'a new engine after stop()');
console.log(`engine page: ok (snapshot ${c.stats.snapshotChars} chars, ${c.stats.writes} writes, ${c.stats.failedWrites} failed and retried)`);
process.exit(0);
