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
/// autosaving and building view models. It runs inside the worker isolate
/// on iOS and Android, and on the main thread (time-sliced) on the web.
///
/// Operations are serialised: one finishes before the next starts, so a
/// command can never land in the middle of a catch-up.
class EngineCore {
  EngineCore({
    required this.store,
    required this.emit,
    DateTime Function()? now,
    Yielder? yielder,
    this.sliceBudget = const Duration(milliseconds: 6),
    this.autosaveDelay = const Duration(milliseconds: 1500),
  }) : _now = now ?? DateTime.now,
       _yield = yielder ?? _defaultYield;

  final SaveStore store;

  /// Pushes snapshots, progress and status to the client.
  final void Function(Push) emit;
  final DateTime Function() _now;
  final Yielder _yield;

  /// How long catch-up runs before yielding (1 ms on the web main thread).
  final Duration sliceBudget;
  final Duration autosaveDelay;

  Game? _game;
  int _revision = 0;
  Timer? _autosave;
  Timer? _nextDay;
  bool _paused = false;
  Future<void> _tail = Future.value();

  Game? get game => _game;

  /// Runs [op] after every earlier operation has finished.
  Future<T> _serial<T>(Future<T> Function() op) {
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
        _game = Game(state);
        await _catchUpNow();
        return const GameOpened();
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
        await store.startOver();
        _game = Game(state);
        await store.save(state);
        await _catchUpNow();
        return const GameOpened();
    }
  });

  Future<void> newGame(NewGameParams p) => _serial(() async {
    final now = _now();
    _game = Game.create(
      seed: p.seed,
      playerName: p.playerName,
      farmName: p.farmName,
      region: p.region,
      favourite: p.favourite,
      startedAt: now,
    );
    await store.startOver();
    await store.save(_game!.state);
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
    final g = _game;
    if (g != null) await store.save(g.state);
    await store.flush();
  });

  /// App visible again: catch up with the clock.
  Future<void> resume() => _serial(() async {
    _paused = false;
    if (_game != null) await _catchUpNow();
  });

  Future<void> flush() => _serial(() async {
    _autosave?.cancel();
    final g = _game;
    if (g != null) await store.save(g.state);
    await store.flush();
  });

  Future<void> close() async {
    await flush();
    _cancelTimers();
  }

  // ------------------------------------------------------------- actions

  Future<Result> dispatch(Command c) => _serial(() async {
    final g = _game;
    if (g == null) return const Err(DomainError(ErrorCode.notFound));
    final r = g.dispatch(c);
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

  Future<void> catchUp() => _serial(_catchUpNow);

  // ------------------------------------------------------------- internals

  /// Simulates up to the clock in slices, yielding between them so the
  /// event loop stays responsive; reports progress for long catch-ups.
  Future<void> _catchUpNow() async {
    final g = _game;
    if (g == null) return;
    final target = g.state.clock(now: _now).today();
    final total = target.daysSince(g.today);
    if (total > 0) {
      final watch = Stopwatch()..start();
      var done = 0;
      while (g.today < target) {
        g.advanceDays(1);
        done++;
        if (watch.elapsed >= sliceBudget) {
          if (total > 14) emit(CatchUpProgress(done, total));
          await _yield();
          watch.reset();
        }
      }
      if (total > 14) emit(CatchUpProgress(total, total));
      await store.save(g.state);
    }
    _publish();
    _scheduleNextDay();
  }

  void _publish() {
    final g = _game;
    if (g == null) return;
    _revision++;
    emit(SnapshotPush(Presenter(g.state, g.me.id).snapshot(_revision)));
  }

  void _scheduleAutosave() {
    _autosave?.cancel();
    _autosave = Timer(autosaveDelay, () {
      final g = _game;
      if (g != null) unawaited(_serial(() => store.save(g.state)));
    });
  }

  void _scheduleNextDay() {
    _nextDay?.cancel();
    final g = _game;
    if (g == null || _paused) return;
    final wait = g.state.clock(now: _now).untilNextDay();
    _nextDay = Timer(wait + const Duration(milliseconds: 50), () {
      unawaited(catchUp());
    });
  }

  void _cancelTimers() {
    _autosave?.cancel();
    _nextDay?.cancel();
  }
}
