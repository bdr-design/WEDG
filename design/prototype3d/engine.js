// The game's rules engine in a Web Worker (docs/plan-gameplay.md, G2): packages/marah_* compiled to JavaScript by
// tool/proto_engine (engine_worker.js, built, not committed: python3 tool/proto_engine/build_worker.py), so the world's
// frames never wait for it. The worker sends the screens' view models (marah_runtime's SnapshotJson) and every save
// write; the page keeps the save and says when each write has landed, so a write that fails reaches the engine, which
// reports it and tries again:
//  - in the iPhone app (tool/proto_app), as files through the app's server, the key to them in the page's address
//    (?save=): the page's own storage would be lost, its origin (the port) changes every launch;
//  - anywhere else (the browser tests), in localStorage.
const KEYS = ['marah.save', 'marah.save.prev', 'marah.save.broken'];

function appSaves(token) {
  const headers = { 'x-marah-save': token };
  return {
    where: 'app',
    async load() {
      const r = await fetch('/save', { headers, cache: 'no-store' });
      if (!r.ok) throw new Error(`the save could not be read (${r.status})`);
      return r.json();
    },
    async put(key, value) {
      const r = await fetch('/save/' + encodeURIComponent(key), value == null ? { method: 'DELETE', headers } : { method: 'PUT', headers, body: value });
      if (!r.ok) throw new Error(`${key} not written (${r.status})`);
    },
  };
}

function browserSaves(prefix = 'marah.proto.') {
  return {
    where: 'browser',
    async load() {
      const all = {};
      for (const k of KEYS) { const v = localStorage.getItem(prefix + k); if (v != null) all[k] = v; }
      return all;
    },
    async put(key, value) {
      if (value == null) localStorage.removeItem(prefix + key); else localStorage.setItem(prefix + key, value);
    },
  };
}

/** Starts the engine and opens the saved game, or a new one with [newGame] ({seed, playerName, farmName, region,
 *  favourite}; the engine's defaults for any left out). [onSnapshot] gets each new view of the game. Resolves to
 *  {status ('opened' | 'new' | 'failed …': a save it could not read, kept as .broken), dispatch(command), flush(),
 *  openPrevious(), startOver(newGame), stats, worker}. Every call resolves to the worker's reply ({ok, ...}). */
export async function startEngine({ url = './engine_worker.js', newGame = {}, timeScale, onSnapshot, onNotice } = {}) {
  const token = new URLSearchParams(location.search).get('save');
  const saves = token ? appSaves(token) : browserSaves();
  const t0 = performance.now();
  const store = await saves.load();
  // what it costs, for the frame meter (#fps) and the tests: the page's side only (the worker's own time is its
  // thread's, not the frame's)
  const stats = {
    where: saves.where, loadMs: performance.now() - t0, startMs: 0, snapshots: 0, snapshotBytes: 0, maxSnapshotBytes: 0,
    parseMs: 0, maxParseMs: 0, writes: 0, writeBytes: 0, writeMs: 0, maxWriteMs: 0, failedWrites: 0, catchUp: null, today: null,
  };
  const worker = new Worker(url);
  const waiting = new Map();
  let nextId = 1, writes = Promise.resolve(), last = null;
  let ready;
  const isReady = new Promise((resolve, reject) => { ready = { resolve, reject }; });
  const call = (op, extra) => new Promise((resolve, reject) => {
    const id = nextId++;
    waiting.set(id, { resolve, reject });
    worker.postMessage(JSON.stringify({ op, id, ...extra }));
  });
  const settle = (m) => {
    const w = waiting.get(m.id);
    if (!w) return false;
    waiting.delete(m.id);
    if (m.type === 'error') w.reject(new Error(m.error)); else w.resolve(m);
    return true;
  };
  worker.onerror = (e) => {
    const err = new Error(`the engine stopped: ${e.message || 'could not load'}`);
    ready.reject(err);
    for (const w of waiting.values()) w.reject(err);
    waiting.clear();
    onNotice?.({ kind: 'down', reason: err.message });
  };
  worker.onmessage = (e) => {
    const tp = performance.now();
    // JSON text, but a save's write comes as an object: its text (megabytes on a big farm) is not JSON a second time
    const m = typeof e.data === 'string' ? JSON.parse(e.data) : e.data;
    switch (m.type) {
      case 'ready': ready.resolve(); break;
      case 'reply': settle(m); break;
      case 'error': if (!settle(m)) console.warn('engine:', m.error); break;
      case 'snapshot': {
        const ms = performance.now() - tp;
        stats.snapshots++; stats.snapshotBytes = e.data.length; stats.maxSnapshotBytes = Math.max(stats.maxSnapshotBytes, e.data.length);
        stats.parseMs = ms; stats.maxParseMs = Math.max(stats.maxParseMs, ms); stats.today = m.snapshot.date;
        last = m.snapshot;
        onSnapshot?.(m.snapshot);
        break;
      }
      case 'store': {
        // in order, one at a time: a later write never lands before an earlier one
        writes = writes.then(async () => {
          const tw = performance.now();
          let ok = true, error = null;
          try { await saves.put(m.key, m.value); } catch (err) { ok = false; error = String(err.message || err); stats.failedWrites++; }
          const ms = performance.now() - tw;
          stats.writes++; stats.writeBytes = m.value ? m.value.length : 0; stats.writeMs = ms; stats.maxWriteMs = Math.max(stats.maxWriteMs, ms);
          worker.postMessage(JSON.stringify({ op: 'stored', seq: m.seq, ok, error }));
        });
        break;
      }
      case 'catchUp': stats.catchUp = [m.done, m.total]; break;
      case 'save': if (!m.ok) onNotice?.({ kind: 'saveFailed', reason: m.error }); break;
      case 'notice': onNotice?.(m); break;
    }
  };
  await isReady;
  const opened = await call('start', { store, newGame, ...(timeScale ? { timeScale } : {}) });
  stats.startMs = performance.now() - t0;
  if (opened.ok === false && !opened.status) throw new Error(`the engine did not start: ${opened.error}`);
  // into the background: saved, and the clock stopped; back in front: caught up (iOS may suspend the page any moment
  // after it is hidden)
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) call('pause').then(() => writes).catch(() => {});
    else call('resume').catch(() => {});
  });
  return {
    status: opened.status,
    stats,
    worker,
    get snapshot() { return last; },
    /** A command as JSON ({type, ...}: tool/proto_engine/lib/commands_json.dart); resolves to {ok, error, events}. */
    dispatch: (command) => call('dispatch', { command }),
    /** Saves now and waits until the save has landed. */
    flush: async () => { const r = await call('flush'); await writes; return r; },
    /** After a save that could not be read: the last one that was. */
    openPrevious: () => call('openPrevious'),
    startOver: (game = {}) => call('startOver', { newGame: game }),
  };
}
