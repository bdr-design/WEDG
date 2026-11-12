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
  console.log(`worker smoke: ok (${got.length} messages, save ${kept['marah.save'].length} chars)`);
  process.exit(0);
})().catch((e) => { console.error('worker smoke: FAILED', e); process.exit(1); });
