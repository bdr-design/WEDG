import 'dart:async';
import 'dart:convert';

import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_runtime/marah_runtime.dart';

import 'commands_json.dart';
import 'worker_backend.dart';

/// The rules engine as the 3D prototype's Web Worker runs it
/// (docs/plan-gameplay.md, G2): marah_runtime's EngineCore (the clock's
/// catch-up, commands in order, saving, the screens' view models) behind a
/// message protocol in JSON text. bin/worker.dart connects it to the worker's
/// `self`; the tests drive it directly, on the VM and in node.
///
/// page -> worker (JSON text):
/// * `{op: 'start', id, server: {base, token}, newGame: {seed, playerName,
///   farmName, region, favourite}, timeScale}`: opens the game kept by the
///   iPhone app's server (the worker reads and writes it itself, so the page
///   never holds the save's text), or with `store: {key: text}` instead of
///   `server`, the game the page keeps (the browser tests). A new game when
///   there is none. A second start closes the first engine (saved, its clock
///   stopped) before the next opens; in the page's keeping it then opens the
///   save as the worker last wrote it. A start that cannot read the save
///   (saveUnreadable) leaves no engine: the page may start again.
/// * `{op: 'dispatch', id, command: {type, ...}}` (commands_json.dart).
/// * `{op: 'bankMonth', id, month: 'YYYY-MM'}`: one month of البنك, opened
///   (`month`: SnapshotJson.moneyMonth, or null when no money moved in it).
/// * `{op: 'flush' | 'pause' | 'resume' | 'openPrevious', id}`;
///   `{op: 'startOver', id, newGame}`.
/// * `{op: 'stored', seq, ok, error}`: the page kept write `seq`, or could not
///   (only when it keeps the save). Answered at once, never queued (every
///   other op waits its turn, in order).
///
/// worker -> page: JSON text `{type: 'ready' | 'reply' | 'snapshot' | 'save' |
/// 'wrote' | 'catchUp' | 'notice' | 'error', ...}` ('wrote': a write's key,
/// characters, milliseconds and outcome, for the frame meter); and, when the
/// page keeps the save, its writes through [postStore] (`{type: 'store', seq,
/// key, value}`, a null value deletes; sent as an object, so the save is not
/// written as JSON a second time).
class WorkerHost {
  WorkerHost({
    required this.post,
    required this.postStore,
    this.http,
    this.saveTimeout = const Duration(seconds: 15),
    DateTime Function()? wallClock,
  }) : _wall = wallClock ?? DateTime.now;

  /// A request to the app's server that has not answered by then is cut off
  /// and the write counts as failed (one that never answered held up every
  /// later write, and every command waited behind it).
  final Duration saveTimeout;

  final void Function(String json) post;
  final void Function(int seq, String key, String? value) postStore;

  /// How the worker reaches the app's server (fetch in bin/worker.dart);
  /// without it only the page can keep the save.
  final HttpCall? http;
  final DateTime Function() _wall;

  EngineCore? _core;
  WorkerBackend? _backend;
  PageSaveIo? _pageIo;
  Timer? _ticker;
  Duration? _tick;
  Future<void> _tail = Future.value();
  int _seq = 0;

  /// The game's own clock: a real day is a game week (approved by the owner;
  /// RealTimeClock).
  static const gameDay = Duration(
    microseconds: Duration.microsecondsPerDay ~/ 7,
  );

  /// The fastest clock a test may ask for (a game day in about 12 ms).
  static const maxTimeScale = 1e6;

  /// The save version of the one-camel start (the owner, 13 Nov 2026: a
  /// game starts with one nursing camel and her calf). The prototype's saves
  /// from before it are games of the old start (three camels and SAR 600,000,
  /// the whole farm built): replaced by a new game, which the owner asked to
  /// see (the old one, and its fallback copy, are not kept). The app itself
  /// keeps every save (SaveCodec migrates it).
  static const oneCamelStart = 7;

  /// The version an encoded save was written in, read from its head (the
  /// envelope names it first; the whole text is megabytes at 10,000 head).
  static int? savedVersion(String text) {
    final head = text.length > 400 ? text.substring(0, 400) : text;
    final m = RegExp(r'"version"\s*:\s*(\d+)').firstMatch(head);
    return m == null ? null : int.parse(m.group(1)!);
  }

  void ready() => _send({'type': 'ready'});

  /// One message from the page.
  void receive(Object? data) {
    final Map<String, Object?> m;
    try {
      final decoded = jsonDecode(data! as String);
      m = (decoded as Map).cast<String, Object?>();
    } on Object {
      return _send({'type': 'error', 'id': null, 'error': 'badMessage'});
    }
    if (m['op'] == 'stored') return _stored(m);
    // «وقّف هنا»: handed over at once, outside the queue, which a jump holds
    // until it ends (EngineCore.stopAway; the loop reads it between slices)
    if (m['op'] == 'stopAway') {
      _core?.stopAway();
      return _reply(m['id'], {'ok': true});
    }
    _tail = _tail.then((_) => _handle(m));
  }

  void _send(Map<String, Object?> m) => post(jsonEncode(m));
  void _reply(Object? id, Map<String, Object?> m) =>
      _send({'type': 'reply', 'id': id, ...m});

  void _stored(Map<String, Object?> m) {
    final seq = m['seq'];
    if (seq is! num) return;
    _pageIo?.stored(
      seq.toInt(),
      ok: m['ok'] == true,
      error: m['error'] is String ? m['error']! as String : null,
    );
  }

  Future<void> _handle(Map<String, Object?> m) async {
    final id = m['id'];
    try {
      final op = m['op'];
      if (op == 'start') return await _start(id, m);
      final core = _core;
      if (core == null) {
        return _reply(id, {'ok': false, 'error': 'noEngine'});
      }
      switch (op) {
        case 'dispatch':
          final game = core.game;
          if (game == null) {
            return _reply(id, {'ok': false, 'error': 'noGame'});
          }
          final j = m['command'];
          final cmd = j is Map
              ? commandFromJson(game.me.id, j.cast<String, Object?>())
              : null;
          if (cmd == null) {
            return _reply(id, {'ok': false, 'error': 'badCommand'});
          }
          final r = await core.dispatch(cmd);
          _reply(id, {
            'ok': r.ok,
            'error': r is Err
                ? {'code': r.error.code.name, 'params': r.error.params}
                : null,
            'events': [for (final e in r.events) e.toJson()],
          });
        case 'bankMonth':
          final month = m['month'];
          if (month is! String || !RegExp(r'^\d{4}-\d{2}$').hasMatch(month)) {
            return _reply(id, {'ok': false, 'error': 'badMonth'});
          }
          final got = await core.bankMonth(month);
          _reply(id, {
            'ok': true,
            'month': got == null ? null : SnapshotJson.moneyMonth(got),
          });
        case 'festival':
          // a festival's page, for the phone's المزاين app
          final fid = m['festival'];
          final d = fid is String
              ? await core.festivalDetail(FestivalId(fid))
              : null;
          _reply(id, {
            'ok': d != null,
            'festival': d == null ? null : SnapshotJson.festivalDetail(d),
          });
        case 'away':
          // the calendar's jump (EngineCore.away): to a day, landing at a
          // minute of it (06:00 unless asked)
          final to = m['target'];
          final minute = m['landingMinute'] ?? 360;
          if (to is! num || minute is! num || minute < 0 || minute >= 1440) {
            return _reply(id, {'ok': false, 'error': 'badAway'});
          }
          _ticker?.cancel();
          final res = await core.away(
            GameDay(to.toInt()),
            landingMinute: minute.toInt(),
          );
          _startTicker();
          final run = res.run;
          _reply(id, {
            'ok': run != null,
            'error': res.refused == null
                ? null
                : {
                    'code': res.refused!.code.name,
                    'params': res.refused!.params,
                  },
            'away': run?.toJson(),
          });
        case 'flush':
          await core.flush();
          _reply(id, {'ok': true});
        case 'pause':
          _ticker?.cancel();
          await core.pause();
          _reply(id, {'ok': true});
        case 'resume':
          await core.resume();
          _startTicker();
          _reply(id, {'ok': true});
        case 'openPrevious':
          _reply(id, {
            'ok': true,
            'status': _status(await core.openPrevious()),
          });
        case 'startOver':
          final NewGameParams p;
          try {
            p = _params(m['newGame']);
          } on FormatException catch (e) {
            return _reply(id, {
              'ok': false,
              'error': 'badNewGame',
              'detail': e.message,
            });
          }
          await core.startOver();
          await core.newGame(p);
          _reply(id, {'ok': true, 'status': 'new'});
        default:
          _reply(id, {'ok': false, 'error': 'unknownOp'});
      }
    } on Object catch (e) {
      _send({'type': 'error', 'id': id, 'error': '$e'});
    }
  }

  Future<void> _start(Object? id, Map<String, Object?> m) async {
    // everything checked before anything changes: a bad start leaves the
    // engine that runs, if any, as it was
    final server = m['server'];
    final rawStore = m['store'] ?? const <String, Object?>{};
    if (server != null &&
        (server is! Map ||
            server['base'] is! String ||
            server['token'] is! String ||
            http == null)) {
      return _reply(id, {'ok': false, 'error': 'badServer'});
    }
    if (rawStore is! Map ||
        rawStore.entries.any((e) => e.key is! String || e.value is! String)) {
      return _reply(id, {'ok': false, 'error': 'badStore'});
    }
    final scale = m['timeScale'] ?? 1;
    if (scale is! num || !scale.isFinite || scale < 1 || scale > maxTimeScale) {
      return _reply(id, {'ok': false, 'error': 'badTimeScale'});
    }
    final NewGameParams? fresh;
    try {
      fresh = m['newGame'] == null ? null : _params(m['newGame']);
    } on FormatException catch (e) {
      return _reply(id, {
        'ok': false,
        'error': 'badNewGame',
        'detail': e.message,
      });
    }

    // the engine that ran stops first: saved, its clock and retries stopped,
    // so it never writes over the next one's save
    _ticker?.cancel();
    await _core?.close();
    _core = null;

    final SaveIo io;
    if (server is Map) {
      _pageIo = null;
      io = _Measured(
        ServerSaveIo(
          http!,
          base: server['base']! as String,
          token: server['token']! as String,
          timeout: saveTimeout,
        ),
        _send,
      );
    } else {
      // a second start in the page's keeping opens the save as the worker last
      // wrote it: the page's copy, taken as it sent the start, can miss the
      // writes still on their way (a command just before was lost)
      final previous = _pageIo != null ? _backend?.kept : null;
      io = _Measured(
        _pageIo = PageSaveIo(
          previous ?? rawStore.cast<String, String>(),
          postStore,
          nextSeq: () => ++_seq,
        ),
        _send,
      );
    }
    final Map<String, String> kept;
    try {
      kept = await io.load();
    } on Object catch (e) {
      return _reply(id, {
        'ok': false,
        'error': 'saveUnreadable',
        'detail': '$e',
      });
    }
    final backend = _backend = WorkerBackend(kept, io);
    // a faster clock for trying things in tests; a save played on one is
    // ahead of the real clock, and waits for it at a normal speed
    final s = scale.toDouble();
    final t0 = _wall();
    DateTime now() => s == 1 ? _wall() : t0.add(_wall().difference(t0) * s);
    _tick = s == 1 ? null : gameDay * (1 / s);
    final core = _core = EngineCore(
      store: SaveStore(backend),
      emit: _push,
      now: now,
    );
    final old = kept['marah.save'];
    final oldStart =
        old != null && (savedVersion(old) ?? oneCamelStart) < oneCamelStart;
    final opened = oldStart ? const NoGame() : await core.open();
    var status = _status(opened);
    if (opened is NoGame) {
      await core.newGame(
        fresh ??
            _params(<String, Object?>{'seed': now().millisecondsSinceEpoch}),
      );
      status = 'new';
    }
    _startTicker();
    _reply(id, {'ok': !status.startsWith('failed'), 'status': status});
  }

  /// EngineCore waits for the next game day in real time; under a faster
  /// clock the worker wakes it every 90 game minutes (Balance.stageMinutes:
  /// the closest two stages are that far apart), so each day starts within
  /// that of its time and a round's day is told stage by stage on the fast
  /// clock too. A wake with nothing to do sends no snapshot.
  void _startTicker() {
    _ticker?.cancel();
    final tick = _tick;
    final core = _core;
    if (tick == null || core == null) return;
    final step = tick * (90 / Game.minutesInDay);
    final every = step < const Duration(milliseconds: 10)
        ? const Duration(milliseconds: 10)
        : step;
    // one catch-up at a time: a tick that comes while the last one (its
    // day, save and snapshot) is still running is skipped, never queued
    var busy = false;
    _ticker = Timer.periodic(every, (_) {
      if (busy) return;
      busy = true;
      unawaited(
        core
            .catchUp()
            .catchError((Object _) {})
            .whenComplete(() => busy = false),
      );
    });
  }

  static String _status(OpenStatus s) => switch (s) {
    GameOpened() => 'opened',
    NoGame() => 'none',
    GameOpenFailed(:final problem, :final detail) =>
      'failed ${problem.name}: $detail',
  };

  /// A new game's settings, the defaults for any left out.
  static NewGameParams _params(Object? raw) {
    if (raw != null && raw is! Map)
      throw const FormatException('not an object');
    final p = raw == null ? const <String, Object?>{} : (raw as Map);
    T pick<T>(String k, T fallback) {
      final v = p[k];
      if (v == null) return fallback;
      if (v is! T) throw FormatException('$k: ${v.runtimeType}');
      return v;
    }

    final seed = pick<num>('seed', DateTime.now().millisecondsSinceEpoch);
    if (seed != seed.roundToDouble() || seed.abs() > 9007199254740991) {
      throw FormatException('seed: $seed');
    }
    E byName<E extends Enum>(List<E> values, String k, E fallback) {
      final n = pick<String>(k, fallback.name);
      for (final v in values) {
        if (v.name == n) return v;
      }
      throw FormatException('$k: $n');
    }

    return NewGameParams(
      seed: seed.toInt(),
      playerName: pick<String>('playerName', 'اللاعب'),
      farmName: pick<String>('farmName', 'العزبة'),
      region: byName(Region.values, 'region', Region.qassim),
      favourite: byName(ColorCategory.values, 'favourite', ColorCategory.wodh),
    );
  }

  void _push(Push p) => _send(switch (p) {
    SnapshotPush(:final snapshot) => {
      'type': 'snapshot',
      // (the game's minute of the day by the engine's clock: the truck's rush
      // is priced by its hour, T15)
      'snapshot': {
        ...SnapshotJson.snapshot(snapshot),
        'minute': _core?.minuteOfDay() ?? 0,
        'minuteAt': _wall().millisecondsSinceEpoch,
      },
    },
    SaveStatus(:final ok, :final error) => {
      'type': 'save',
      'ok': ok,
      'error': error,
    },
    AwayProgress(:final done, :final total, :final day) => {
      'type': 'away',
      'done': done,
      'total': total,
      'day': day.value,
    },
    CatchUpProgress(:final done, :final total) => {
      'type': 'catchUp',
      'done': done,
      'total': total,
    },
    CatchUpCapped(:final skippedDays) => {
      'type': 'notice',
      'kind': 'catchUpCapped',
      'skippedDays': skippedDays,
    },
    StateRecovered(:final reason) => {
      'type': 'notice',
      'kind': 'recovered',
      'reason': reason,
    },
    BackupWarning() => {'type': 'notice', 'kind': 'backup'},
    EngineHalted(:final reason) => {
      'type': 'notice',
      'kind': 'halted',
      'reason': reason,
    },
    EngineDown(:final reason) => {
      'type': 'notice',
      'kind': 'down',
      'reason': reason,
    },
  });
}

/// Reports each write to the page ('wrote'): what the frame meter shows of
/// the save, wherever it is kept.
class _Measured implements SaveIo {
  _Measured(this.io, this.send);
  final SaveIo io;
  final void Function(Map<String, Object?>) send;

  @override
  Future<Map<String, String>> load() => io.load();

  @override
  Future<void> keep(String key, String? value) async {
    final sw = Stopwatch()..start();
    try {
      await io.keep(key, value);
      send(_note(key, value, sw, null));
    } on Object catch (e) {
      send(_note(key, value, sw, '$e'));
      rethrow;
    }
  }

  static Map<String, Object?> _note(
    String key,
    String? value,
    Stopwatch sw,
    String? error,
  ) => {
    'type': 'wrote',
    'key': key,
    'chars': value?.length ?? 0,
    'ms': sw.elapsedMicroseconds / 1000,
    'ok': error == null,
    'error': error,
  };
}
