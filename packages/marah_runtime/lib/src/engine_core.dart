import 'dart:async';

import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/marah_domain.dart';

import 'presenter.dart';
import 'protocol.dart';
import 'view_models.dart';

/// Gives the event loop a turn during long work: lets frames render on the
/// web and lets queued messages through in a worker.
typedef Yielder = Future<void> Function();

Future<void> _defaultYield() => Future<void>.delayed(Duration.zero);

/// Owns the running game: loading, commands, catching up with the clock,
/// saving and building view models. It runs inside the worker isolate on
/// iOS and Android, and on the main thread (time-sliced) on the web.
///
/// * Operations are serialised: a command never lands in the middle of a
///   catch-up (commands sent during one wait for it to finish).
/// * Saving never silently stops: every failure is pushed as a
///   [SaveStatus], retried with backoff, and later saves still run.
/// * A day boundary is always re-armed, even if a step fails.
class EngineCore {
  EngineCore({
    required this.store,
    required this.emit,
    DateTime Function()? now,
    Yielder? yielder,
    this.sliceBudget = const Duration(milliseconds: 6),
    this.autosaveDelay = const Duration(milliseconds: 1500),
    this.autosaveMaxWait = const Duration(seconds: 10),
    this.maxCatchUpDays = 365,
  }) : _now = now ?? DateTime.now,
       _yield = yielder ?? _defaultYield;

  final GameStore store;

  /// Pushes snapshots, progress and status to the client.
  final void Function(Push) emit;
  final DateTime Function() _now;
  final Yielder _yield;

  /// How long catch-up runs before yielding.
  final Duration sliceBudget;

  /// Quiet time after a change before saving...
  final Duration autosaveDelay;

  /// ...but never longer than this after the first unsaved change.
  final Duration autosaveMaxWait;

  /// The most game days simulated in one catch-up (365 ≈ 52 real days).
  /// Longer absences, or a device clock moved far forward, are skipped:
  /// the world waits instead of running on unattended.
  final int maxCatchUpDays;

  Game? _game;
  int _revision = 0;
  PlayerSnapshot? _last;
  Timer? _autosave;
  DateTime? _dirtySince;
  Timer? _nextDay;
  Timer? _retry;
  int _retryStep = 0;
  bool _saveOk = true;
  bool _paused = false;
  bool _closed = false;
  Future<void> _tail = Future.value();

  Game? get game => _game;

  /// Runs [op] after every earlier operation has finished.
  Future<T> _serial<T>(Future<T> Function() op) {
    if (_closed) return Future.error(StateError('engine closed'));
    final result = _tail.then((_) => op());
    _tail = result.then<void>((_) {}, onError: (Object _) {});
    return result;
  }

  // ------------------------------------------------------------- lifecycle

  Future<OpenStatus> open() => _serial(() async {
    final r = await store.open();
    switch (r) {
      case NoSave():
        return const NoGame();
      case OpenFailed(:final problem, :final detail):
        return GameOpenFailed(problem, detail);
      case Opened(:final state):
        return _start(state);
    }
  });

  Future<OpenStatus> openPrevious() => _serial(() async {
    final r = await store.openPrevious();
    switch (r) {
      case NoSave():
        return const NoGame();
      case OpenFailed(:final problem, :final detail):
        return GameOpenFailed(problem, detail);
      case Opened(:final state):
        return _start(state);
    }
  });

  /// Brings a loaded game up to date. If the simulation itself fails on
  /// this save, the save is backed up and locked instead of being lost.
  Future<OpenStatus> _start(GameState state) async {
    _game = Game(state);
    try {
      await _catchUpNow();
      return const GameOpened();
    } on Object catch (e) {
      _game = null;
      _cancelTimers();
      final failed = await store.reject('could not resume: $e');
      return GameOpenFailed(failed.problem, failed.detail);
    }
  }

  Future<void> newGame(NewGameParams p) => _serial(() async {
    final now = _now();
    _game = Game.create(
      seed: p.seed,
      playerName: p.playerName,
      farmName: p.farmName,
      region: p.region,
      favourite: p.favourite,
      startedAt: now,
    )..state.lastSeenUtcMs = now.toUtc().millisecondsSinceEpoch;
    await store.startOver();
    await _saveNow();
    _publish();
    _scheduleNextDay();
  });

  Future<void> startOver() => _serial(() async {
    _cancelTimers();
    _game = null;
    await store.startOver();
  });

  /// App hidden: save now and stop timers.
  Future<void> pause() => _serial(() async {
    _paused = true;
    _cancelTimers();
    await _saveNow();
  });

  /// App visible again: catch up with the clock.
  Future<void> resume() => _serial(() async {
    _paused = false;
    if (_game != null) await _catchUpNow();
  });

  Future<void> flush() => _serial(_saveNow);

  /// Saves, stops timers and refuses further work.
  Future<void> close() async {
    if (_closed) return;
    try {
      await flush();
    } finally {
      _closed = true;
      _cancelTimers();
    }
  }

  // ------------------------------------------------------------- actions

  Future<Result> dispatch(Command c) => _serial(() async {
    final g = _game;
    if (g == null) return const Err(DomainError(ErrorCode.notFound));
    final Result r;
    try {
      r = g.dispatch(c);
    } on Object catch (e) {
      await _recover(e);
      return const Err(DomainError(ErrorCode.internalError));
    }
    if (r.events.isNotEmpty) {
      _publish();
      _scheduleAutosave();
    }
    return r;
  });

  Future<CamelDetail?> camelDetail(CamelId id) => _serial(() async {
    final g = _game;
    return g == null ? null : Presenter(g.state, g.me.id).camelDetail(id);
  });

  Future<FestivalDetail?> festivalDetail(FestivalId id) => _serial(() async {
    final g = _game;
    return g == null ? null : Presenter(g.state, g.me.id).festivalDetail(id);
  });

  Future<HerdPage?> herdPage(HerdQuery q) => _serial(() async {
    final g = _game;
    return g == null ? null : Presenter(g.state, g.me.id).herdPage(q);
  });

  Future<void> catchUp() => _serial(_catchUpNow);

  /// A bug left the in-memory game half-changed: throw it away and reload
  /// the last save, which is always a consistent state.
  Future<void> _recover(Object error) async {
    _cancelTimers();
    _game = null;
    emit(StateRecovered('$error'));
    final r = await store.open();
    if (r is Opened) {
      _game = Game(r.state);
      _publish();
      _scheduleNextDay();
    }
  }

  // ------------------------------------------------------------- internals

  /// Simulates up to the clock in slices, yielding between them; reports
  /// progress for long catch-ups. Handles device clock jumps: backwards
  /// never rewinds the world, and far forward is capped.
  Future<void> _catchUpNow() async {
    final g = _game;
    if (g == null) return;
    try {
      final s = g.state;
      final nowMs = _now().toUtc().millisecondsSinceEpoch;
      final lastSeen = s.lastSeenUtcMs;
      if (lastSeen != null && nowMs < lastSeen) {
        // Clock moved back: shift the anchor so time continues from here.
        s.clockShiftMs -= lastSeen - nowMs;
      }
      s.lastSeenUtcMs = nowMs;

      var target = s.clock(now: _now).today();
      final behind = target.daysSince(g.today);
      if (behind > maxCatchUpDays) {
        final skipped = behind - maxCatchUpDays;
        s.clockShiftMs += skipped * const Duration(days: 1).inMilliseconds ~/ 7;
        target = g.today + maxCatchUpDays;
        emit(CatchUpCapped(skipped));
      }
      final total = target.daysSince(g.today);
      if (total > 0) {
        final watch = Stopwatch()..start();
        var done = 0;
        while (g.today < target) {
          try {
            g.advanceDays(1);
          } on Object catch (e) {
            await _recover(e);
            return;
          }
          done++;
          if (watch.elapsed >= sliceBudget) {
            if (total > 14) emit(CatchUpProgress(done, total));
            await _yield();
            watch.reset();
          }
        }
        if (total > 14) emit(CatchUpProgress(total, total));
        await _saveNow();
      }
    } finally {
      _publish();
      _scheduleNextDay();
    }
  }

  /// Saves now. A failure is reported and retried; it never stops later
  /// saves and never throws into the caller's operation.
  Future<void> _saveNow() async {
    _autosave?.cancel();
    _dirtySince = null;
    final g = _game;
    if (g == null) return;
    try {
      await store.save(g.state);
      _retry?.cancel();
      _retryStep = 0;
      if (!_saveOk) {
        _saveOk = true;
        emit(const SaveStatus(ok: true));
      }
    } on Object catch (e) {
      _saveOk = false;
      emit(SaveStatus(ok: false, error: e.toString()));
      _scheduleRetry();
    }
  }

  void _scheduleRetry() {
    if (_closed) return;
    const steps = [2, 5, 15, 60];
    final wait = steps[_retryStep.clamp(0, steps.length - 1)];
    _retryStep++;
    _retry?.cancel();
    _retry = Timer(Duration(seconds: wait), () {
      if (!_closed) unawaited(_serial(_saveNow).catchError((Object _) {}));
    });
  }

  void _publish() {
    final g = _game;
    if (g == null) return;
    _revision++;
    final s = Presenter(g.state, g.me.id).snapshot(_revision, previous: _last);
    _last = s;
    emit(SnapshotPush(s));
  }

  void _scheduleAutosave() {
    final now = _now();
    _dirtySince ??= now;
    _autosave?.cancel();
    final waited = now.difference(_dirtySince!);
    final delay = waited >= autosaveMaxWait ? Duration.zero : autosaveDelay;
    _autosave = Timer(delay, () {
      if (!_closed) unawaited(_serial(_saveNow).catchError((Object _) {}));
    });
  }

  void _scheduleNextDay() {
    _nextDay?.cancel();
    final g = _game;
    if (g == null || _paused || _closed) return;
    final wait = g.state.clock(now: _now).untilNextDay();
    _nextDay = Timer(wait + const Duration(milliseconds: 50), () {
      if (!_closed) unawaited(catchUp().catchError((Object _) {}));
    });
  }

  void _cancelTimers() {
    _autosave?.cancel();
    _nextDay?.cancel();
    _retry?.cancel();
  }
}
