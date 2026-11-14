// The game's rules engine in a Web Worker (docs/plan-gameplay.md, G2): packages/marah_* compiled to JavaScript by
// tool/proto_engine (engine_worker.js, built, not committed: python3 tool/proto_engine/build_worker.py), so the world's
// frames never wait for it. The worker sends the screens' view models (marah_runtime's SnapshotJson). The save:
//  - in the iPhone app (tool/proto_app), files behind the app's own server. The worker reads and writes them itself,
//    with the key to them that the page's address carries (?save=), so the page's thread never holds the save's text
//    (6.7 MB at 10,000 head). The page's own storage would be lost: its origin (the port) changes every launch;
//  - anywhere else (the browser tests), localStorage, kept by the page: the worker hands it each write and waits for
//    the page to say it landed.
// Either way a write that fails reaches the engine, which reports it and tries again; the worker reports each write's
// size and time for the frame meter.
const KEYS = ['marah.save', 'marah.save.prev', 'marah.save.broken'];
const PREFIX = 'marah.proto.';

let running = null;

/** Starts the engine and opens the saved game, or a new one with [newGame] ({seed, playerName, farmName, region,
 *  favourite}; the engine's defaults for any left out). [onSnapshot] gets each new view of the game. Resolves to
 *  {status ('opened' | 'new' | 'failed …': a save it could not read, kept as .broken), dispatch(command), flush(),
 *  openPrevious(), startOver(newGame), stop(), stats, worker}. Every call resolves to the worker's reply ({ok, ...}).
 *  One engine at a time: called again before stop(), it gives the same one (two would write the same save). */
export function startEngine(options = {}) {
  if (!running) running = start(options).catch((err) => { running = null; throw err; });
  return running;
}

async function start({ url = './engine_worker.js', newGame = {}, timeScale, onSnapshot, onNotice, onAway } = {}) {
  const token = new URLSearchParams(location.search).get('save');
  const t0 = performance.now();
  // what it costs, for the frame meter (#fps) and the tests. Sizes are characters of JSON text. The parse is the
  // page's thread; a write's time is the worker's request (or the page's storage), not the frame's.
  const stats = {
    where: token ? 'app' : 'browser', startMs: 0, snapshots: 0, snapshotChars: 0, maxSnapshotChars: 0, parseMs: 0,
    maxParseMs: 0, writes: 0, writeChars: 0, writeMs: 0, maxWriteMs: 0, failedWrites: 0, catchUp: null, today: null,
  };
  const worker = new Worker(url);
  const waiting = new Map();
  let nextId = 1, last = null;
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
  // every call still waiting fails, and a new engine may start
  const down = (reason) => {
    const err = new Error(reason);
    ready.reject(err);
    for (const w of waiting.values()) w.reject(err);
    waiting.clear();
    running = null;
    return err;
  };
  worker.onerror = (e) => {
    worker.terminate();      // (an error event does not end a worker: left running, it and a new one would both write)
    const err = down(`the engine stopped: ${e.message || 'could not load'}`);
    onNotice?.({ kind: 'down', reason: err.message });
  };
  worker.onmessage = (e) => {
    const tp = performance.now();
    // JSON text, but a write for the page to keep comes as an object: its text is not JSON a second time
    const m = typeof e.data === 'string' ? JSON.parse(e.data) : e.data;
    switch (m.type) {
      case 'ready': ready.resolve(); break;
      case 'reply': settle(m); break;
      case 'error': if (!settle(m)) console.warn('engine:', m.error); break;
      case 'snapshot': {
        const ms = performance.now() - tp;
        stats.snapshots++; stats.snapshotChars = e.data.length; stats.maxSnapshotChars = Math.max(stats.maxSnapshotChars, e.data.length);
        stats.parseMs = ms; stats.maxParseMs = Math.max(stats.maxParseMs, ms); stats.today = m.snapshot.date;
        last = m.snapshot;
        onSnapshot?.(m.snapshot);
        break;
      }
      case 'store': {
        // the browser tests only: localStorage, which answers at once
        let ok = true, error = null;
        try {
          if (m.value == null) localStorage.removeItem(PREFIX + m.key); else localStorage.setItem(PREFIX + m.key, m.value);
        } catch (err) { ok = false; error = String(err.message || err); }
        worker.postMessage(JSON.stringify({ op: 'stored', seq: m.seq, ok, error }));
        break;
      }
      case 'wrote':
        stats.writes++; stats.writeChars = m.chars; stats.writeMs = m.ms; stats.maxWriteMs = Math.max(stats.maxWriteMs, m.ms);
        if (!m.ok) stats.failedWrites++;
        break;
      case 'catchUp': stats.catchUp = [m.done, m.total]; break;
      case 'away': stats.away = [m.done, m.total, m.day]; onAway?.(m); break;      // (the calendar's jump under way: a few a second)
      case 'save': if (!m.ok) onNotice?.({ kind: 'saveFailed', reason: m.error }); break;
      case 'notice': onNotice?.(m); break;
    }
  };
  await isReady;
  const where = token ? { server: { base: location.origin, token } } : { store: browserStore() };
  const opened = await call('start', { ...where, newGame, ...(timeScale ? { timeScale } : {}) });
  stats.startMs = performance.now() - t0;
  if (opened.ok === false && !opened.status) throw new Error(`the engine did not start: ${opened.error} ${opened.detail ?? ''}`);
  // into the background: saved, and the clock stopped; back in front: caught up (iOS may suspend the page any moment
  // after it is hidden)
  const onVisibility = () => { call(document.hidden ? 'pause' : 'resume').catch(() => {}); };
  document.addEventListener('visibilitychange', onVisibility);
  return {
    status: opened.status,
    stats,
    worker,
    get snapshot() { return last; },
    /** A command as JSON ({type, ...}: tool/proto_engine/lib/commands_json.dart); resolves to {ok, error, events}. */
    dispatch: (command) => call('dispatch', { command }),
    /** One month of البنك ('YYYY-MM'), when it is opened: resolves to {ok, month: {month, in, out, lines} or null}. */
    bankMonth: (month) => call('bankMonth', { month }),
    /** A festival's page (المزاين), when it is opened: resolves to {ok, festival: SnapshotJson.festivalDetail or null}. */
    festival: (id) => call('festival', { festival: id }),
    /** The calendar's jump (EngineCore.away): to game day [target], landing at [landingMinute] of the day it ends
     *  on; resolves to {ok, error, away: {from, to, target, stop, summary}}. Progress comes to onAway. */
    away: (target, landingMinute = 360) => call('away', { target, landingMinute }),
    /** «وقّف هنا»: handed over at once (the worker takes it outside its queue); the jump ends at the day it is on. */
    stopAway: () => call('stopAway'),
    /** Saves now; resolves when the save has been kept. */
    flush: () => call('flush'),
    /** After a save that could not be read: the last one that was. */
    openPrevious: () => call('openPrevious'),
    startOver: (game = {}) => call('startOver', { newGame: game }),
    /** Saves (waiting 20 s at most: a save that does not answer is cut off at 15 s), stops the worker, and lets a
     *  new engine start. */
    stop: async () => {
      document.removeEventListener?.('visibilitychange', onVisibility);
      try {
        await Promise.race([call('pause'), new Promise((resolve) => setTimeout(resolve, 20000))]);
      } catch { /* stopped all the same */ } finally {
        worker.terminate();
        down('the engine was stopped');
      }
    },
  };
}

function browserStore() {
  const all = {};
  try {
    for (const k of KEYS) { const v = localStorage.getItem(PREFIX + k); if (v != null) all[k] = v; }
  } catch { /* storage blocked: a new game each time */ }
  return all;
}
