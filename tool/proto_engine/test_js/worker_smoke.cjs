// The compiled worker (build_worker.py) in node, `self` faked as a page would see it: it boots, starts a game, sends
// the save's writes as objects and waits for each to be kept, answers a command, and opens again from what was kept.
// The protocol itself is tested in Dart (test/worker_host_test.dart); this checks the JavaScript wiring.
//   node test_js/worker_smoke.cjs <engine_worker.js>
const path = require('path');
const assert = require('assert');

const got = [];
const kept = {};
let onmessage = null;
globalThis.self = globalThis;
Object.defineProperty(globalThis, 'onmessage', { configurable: true, set(f) { onmessage = f; }, get() { return onmessage; } });
globalThis.postMessage = (data) => {
  if (typeof data === 'string') { got.push(JSON.parse(data)); return; }
  // a save's write: an object, its text as it is, kept and answered like engine.js does
  assert.strictEqual(data.type, 'store');
  assert.ok(Number.isInteger(data.seq) && typeof data.key === 'string', 'a numbered write');
  if (data.value == null) delete kept[data.key]; else kept[data.key] = data.value;
  got.push({ type: 'store', key: data.key });
  setTimeout(() => send({ op: 'stored', seq: data.seq, ok: true }), 1);
};
const send = (m) => onmessage({ data: typeof m === 'string' ? m : JSON.stringify(m) });
const until = async (pred, ms = 20000) => {
  const end = Date.now() + ms;
  while (Date.now() < end) { const hit = got.find(pred); if (hit) return hit; await new Promise((r) => setTimeout(r, 5)); }
  throw new Error('waited in vain; last messages: ' + JSON.stringify(got.slice(-5)).slice(0, 600));
};
const reply = (id) => until((m) => (m.type === 'reply' || m.type === 'error') && m.id === id);

(async () => {
  require(path.resolve(process.argv[2]));
  await until((m) => m.type === 'ready');
  send({ op: 'start', id: 1, newGame: { seed: 7 } });
  send({ op: 'dispatch', id: 2, command: { type: 'orderSupply', supply: 'water', units: 1 } });
  assert.strictEqual((await reply(1)).status, 'new');
  assert.strictEqual((await reply(2)).ok, true);
  const snap = (await until((m) => m.type === 'snapshot')).snapshot;
  assert.strictEqual(snap.herd.total, 3);
  assert.ok(kept['marah.save'] && kept['marah.save.prev'], 'the save and its fallback kept');
  send('{not json');
  assert.ok(got.some((m) => m.type === 'error' && m.error === 'badMessage'));
  send({ op: 'start', id: 3, store: { ...kept } });
  assert.strictEqual((await reply(3)).status, 'opened');
  send({ op: 'pause', id: 4 });
  assert.strictEqual((await reply(4)).ok, true);
  assert.ok(kept['marah.save'].includes('"supply":"water"'), 'the order is in the save');

  // the app's server: the worker fetches and writes the files itself (fetch faked here, aborts honoured); one request
  // that never answers is cut off and the next goes through
  const files = { ...kept };
  let hang = false, fetched = 0;
  globalThis.fetch = (url, init) => new Promise((resolve, reject) => {
    fetched++;
    assert.strictEqual(init.headers['x-marah-save'], 'tok', 'the key goes with every request');
    if (hang) { init.signal.addEventListener('abort', () => reject(new Error('aborted'))); return; }
    const key = decodeURIComponent(url.split('/save/')[1] || '');
    if (init.method === 'GET') return resolve({ status: 200, text: async () => JSON.stringify(files) });
    if (init.method === 'PUT') files[key] = init.body; else delete files[key];
    resolve({ status: 204, text: async () => '' });
  });
  send({ op: 'start', id: 5, server: { base: 'http://127.0.0.1:9', token: 'tok' } });
  assert.strictEqual((await reply(5)).status, 'opened');      // (the first engine saved to the page as it closed)
  const before = got.filter((m) => m.type === 'store').length;
  send({ op: 'dispatch', id: 6, command: { type: 'orderSupply', supply: 'barley', units: 2 } });
  assert.strictEqual((await reply(6)).ok, true);
  assert.ok(files['marah.save'].includes('"supply":"barley"'), 'written to the server');
  assert.strictEqual(got.filter((m) => m.type === 'store').length, before, 'nothing handed to the page');
  assert.ok(got.some((m) => m.type === 'wrote' && m.ok), 'each write reported for the meter');
  hang = true;
  send({ op: 'dispatch', id: 7, command: { type: 'orderSupply', supply: 'barley', units: 1 } });
  await reply(7);
  await until((m) => m.type === 'save' && m.ok === false, 30000);
  hang = false;
  send({ op: 'flush', id: 8 });
  assert.strictEqual((await reply(8)).ok, true);
  await until((m) => m.type === 'save' && m.ok === true, 30000);
  assert.ok(fetched > 3);
  send({ op: 'pause', id: 9 });
  await reply(9);
  console.log(`worker smoke: ok (${got.length} messages, save ${kept['marah.save'].length} chars)`);
  process.exit(0);
})().catch((e) => { console.error('worker smoke: FAILED', e); process.exit(1); });
