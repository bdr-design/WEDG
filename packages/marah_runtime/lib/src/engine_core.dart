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
    this.maxCatchUpDays = 365,
    this.maxRecoveriesPerDay = 2,
  }) : _now = now ?? DateTime.now,
       _yield = yielder ?? _defaultYield;

  final GameStore store;

  /// Pushes snapshots, progress and status to the client.
  final void Function(Push) emit;
  final DateTime Function() _now;
  final Yielder _yield;

  /// How long catch-up runs before yielding.
  final Duration sliceBudget;

  /// After this many recoveries on the same game day the engine stops the
  /// world instead of looping on the same bug.
  final int maxRecoveriesPerDay;

  /// The most game days simulated in one catch-up (365 ≈ 52 real days).
  /// Longer absences, or a device clock moved far forward, are skipped:
  /// the world waits instead of running on unattended.
  final int maxCatchUpDays;

  Game? _game;
  int _revision = 0;
  PlayerSnapshot? _last;
  Timer? _nextDay;
  bool _halted = false;
  int _recoveryDay = -1;
  int _recoveries = 0;
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

  /// Brings a loaded game up to date and saves it; only then is the save
  /// proven good and copied as the fallback. If this version of the game
  /// fails on the save (a bug), nothing is changed or locked.
  Future<OpenStatus> _start(GameState state) async {
    _game = Game(state);
    _halted = false;
    try {
      await _catchUpNow();
    } on Object catch (e) {
      _game = null;
      _cancelTimers();
      return GameOpenFailed(LoadProblem.engineError, 'could not resume: $e');
    }
    if (_game == null) {
      return const GameOpenFailed(
        LoadProblem.engineError,
        'could not resume: the world stopped',
      );
    }
    await _saveNow();
    if (_saveOk && !await store.markGood()) emit(const BackupWarning());
    return const GameOpened();
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
    _halted = false;
    await store.startOver();
    await _saveNow();
    if (_saveOk && !await store.markGood()) emit(const BackupWarning());
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

  /// The game's minute of the day by the engine's own clock.
  int minuteOfDay() {
    final g = _game;
    return g == null ? 0 : g.state.clock(now: _now).minuteOfDay();
  }

  /// A rushed truck's hour, stamped from the engine's own clock (the second
  /// review's N2): a command's hour is accepted if it is this hour or the
  /// one before (the price shown is the price paid), refused after it (a
  /// stale confirm after the day turned too), and stamped when it has none.
  (Command?, Err?) _stampHour(Command c) {
    // the hunting season's buttons: the game's minute is always the
    // engine's own (the hours of the hunt and the trap, task T18)
    switch (c) {
      case SpotFalcon(:final actor, :final at):
        return (SpotFalcon(actor, at, minute: minuteOfDay()), null);
      case ReleaseLure(:final actor, :final at, :final lure):
        return (ReleaseLure(actor, at, lure, minute: minuteOfDay()), null);
      case CastFalcon(
        :final actor,
        :final falcon,
        :final at,
        :final inCar,
        :final moving,
      ):
        return (
          CastFalcon(
            actor,
            falcon,
            at,
            inCar: inCar,
            moving: moving,
            minute: minuteOfDay(),
          ),
          null,
        );
      default:
        break;
    }
    final now = minuteOfDay() ~/ 60;
    int? asked;
    switch (c) {
      case RushTruck(:final hour):
        asked = hour;
      case BuyListing(now: true, :final hour):
        asked = hour;
      default:
        return (c, null);
    }
    if (asked != null && asked != now && asked != now - 1) {
      return (null, Err(DomainError(ErrorCode.priceChanged, {'hour': now})));
    }
    final h = asked ?? now;
    return (
      switch (c) {
        RushTruck(:final actor, :final camel) => RushTruck(
          actor,
          camel,
          hour: h,
        ),
        BuyListing(:final actor, :final listing) => BuyListing(
          actor,
          listing,
          now: true,
          hour: h,
        ),
        _ => c,
      },
      null,
    );
  }

  Future<Result> dispatch(Command c0) => _serial(() async {
    final g = _game;
    if (g == null) return const Err(DomainError(ErrorCode.notFound));
    final (stamped, refused) = _stampHour(c0);
    if (refused != null) return refused;
    final c = stamped!;
    final Result r;
    try {
      r = g.dispatch(c);
    } on Object catch (e) {
      await _recover(e);
      return const Err(DomainError(ErrorCode.internalError));
    }
    if (r.events.isNotEmpty) {
      // Saved before the player hears it worked (about 11 ms at 10k head),
      // so a later recovery never loses an acknowledged command.
      await _saveNow();
      _publish();
    }
    return r;
  });

  Future<CamelDetail?> camelDetail(CamelId id) => _serial(() async {
    final g = _game;
    return g == null ? null : Presenter(g.state, g.me.id).camelDetail(id);
  });

  /// One month of البنك, opened (BankSummary carries every month's net and
  /// biggest kind only).
  Future<MonthMoney?> bankMonth(String month) => _serial(() async {
    final g = _game;
    return g == null ? null : Presenter(g.state, g.me.id).bankMonth(month);
  });

  Future<FestivalDetail?> festivalDetail(FestivalId id) => _serial(() async {
    final g = _game;
    return g == null ? null : Presenter(g.state, g.me.id).festivalDetail(id);
  });

  Future<HerdPage?> herdPage(HerdQuery q) => _serial(() async {
    final g = _game;
    return g == null ? null : Presenter(g.state, g.me.id).herdPage(q);
  });

  /// Catches up with the clock: the days, and the stages of today's rounds
  /// whose hour has come; a snapshot only when something changed.
  Future<void> catchUp() => _serial(() => _catchUpNow(always: false));

  // ------------------------------------------------------------- away

  bool _cancelAway = false;

  /// Ends a stretch away at the day it is on («وقّف هنا»). Not an operation:
  /// it is set at once, outside the queue, and the loop reads it between its
  /// slices (the worker hands it over beside 'stored').
  void stopAway() => _cancelAway = true;

  /// Goes away to [target] (the one mechanism: docs/proposals/
  /// rush_and_calendar.md section 5): the days simulated one by one on the
  /// same pipeline as any played day, yielding every slice, the stops read
  /// after each day, [extra] conditions a caller adds; at the first stop,
  /// the target, or «وقّف هنا», the clock's anchor is moved so that now is
  /// [landingMinute] of the day reached, the game saved once and that save
  /// marked good (a jump cannot be undone by opening the save before it).
  /// Returns the stretch (where it stopped, what happened), or the refusal.
  Future<({AwayRun? run, DomainError? refused})> away(
    GameDay target, {
    int landingMinute = 360,
    List<AwayCondition> extra = const [],
    List<AwayCounter> counters = const [],
    Map<String, Object?> card = const {},
  }) => _serial(() async {
    final g = _game;
    if (g == null || _halted) {
      return (run: null, refused: const DomainError(ErrorCode.notFound));
    }
    final no = AwayRun.refusal(g, target);
    if (no != null) return (run: null, refused: no);
    _cancelAway = false;
    _nextDay?.cancel();
    final run = AwayRun(
      g,
      AwayPlan(target, extra: extra, counters: counters, card: card),
    );
    final watch = Stopwatch()..start();
    var lastPush = Stopwatch()..start();
    while (!run.done) {
      try {
        run.step();
      } on Object catch (e) {
        await _recover(e);
        return (run: null, refused: const DomainError(ErrorCode.internalError));
      }
      if (watch.elapsed >= sliceBudget) {
        if (lastPush.elapsedMilliseconds >= 250) {
          emit(AwayProgress(run.doneDays, run.total, g.today));
          lastPush = Stopwatch()..start();
        }
        await _yield();
        watch.reset();
      }
      if (!run.done && _cancelAway) run.cancel();
    }
    _cancelAway = false;
    emit(AwayProgress(run.doneDays, run.total, g.today));
    land(g.state, g.today, landingMinute);
    emit(AwayProgress(run.doneDays, run.total, g.today, saving: true));
    await _saveNow();
    if (_saveOk && !await store.markGood()) emit(const BackupWarning());
    _publish();
    _scheduleNextDay();
    return (run: run, refused: null);
  });

  /// A night at camp («نام لين الفجر», task T18): one away call to
  /// tomorrow with the camp's own stops and lines, landing at the working
  /// hour's start (Trips). Refused when he is not on a trip of days.
  Future<({AwayRun? run, DomainError? refused})> tripNight() async {
    final g = _game;
    final plan = g == null ? null : Trips.night(g);
    if (g == null || plan == null) {
      return (
        run: null,
        refused: const DomainError(ErrorCode.huntRefused, {
          'reason': 'notOnTrip',
        }),
      );
    }
    final t = g.me.falconry?.trip;
    return away(
      plan.target,
      landingMinute: Trips.landingMinute(t, plan.target),
      extra: plan.extra,
      counters: plan.counters,
      card: plan.card,
    );
  }

  /// The hunting season's catalog (asked once by the phone).
  Future<Map<String, Object?>?> falconCatalog() => _serial(() async {
    final g = _game;
    return g == null ? null : falconCatalogOf(g.state, g.me.id);
  });

  /// The trip's lines for the card before leaving.
  Future<Map<String, Object?>?> tripCard(
    TripKind kind,
    Ground ground,
    int nights,
  ) => _serial(() async {
    final g = _game;
    return g == null ? null : Trips.card(g, kind, ground, nights);
  });

  /// Moves [s]'s clock anchor so that now is [minute] of [day], in the
  /// clock's own microseconds (a game day is 86,400,000,000 / 7 µs, whole
  /// by integer division; in milliseconds it is not whole).
  void land(GameState s, GameDay day, int minute) {
    final dayUs = Duration.microsecondsPerDay ~/ 7;
    final elapsedUs =
        day.daysSince(s.startedOn) * dayUs + (minute * dayUs + 1439) ~/ 1440;
    final nowUs = _now().toUtc().microsecondsSinceEpoch;
    s
      ..clockShiftMs = (nowUs - elapsedUs) ~/ 1000 - s.startedAtUtcMs
      ..lastSeenUtcMs = nowUs ~/ 1000;
  }

  /// A bug left the in-memory game half-changed: throw it away and reload
  /// the last save, which is always consistent. If the same day keeps
  /// failing, stop the world instead of looping.
  Future<void> _recover(Object error) async {
    _cancelTimers();
    final day = _game?.today.value ?? -1;
    _game = null;
    if (day == _recoveryDay) {
      _recoveries++;
    } else {
      _recoveryDay = day;
      _recoveries = 1;
    }
    emit(StateRecovered('$error'));
    final r = await store.open();
    if (r is! Opened) {
      _halted = true;
      emit(EngineHalted('could not reload the last save: $r'));
      return;
    }
    _game = Game(r.state);
    if (_recoveries > maxRecoveriesPerDay) {
      _halted = true;
      emit(
        EngineHalted('day ${r.state.world.day.value} keeps failing: $error'),
      );
    }
    _publish();
    _scheduleNextDay();
  }

  // ------------------------------------------------------------- internals

  /// Simulates up to the clock in slices, yielding between them; reports
  /// progress for long catch-ups. Handles device clock jumps: backwards
  /// never rewinds the world, and far forward is capped.
  Future<void> _catchUpNow({bool always = true}) async {
    final g = _game;
    if (g == null || _halted) {
      _publish();
      return;
    }
    var changed = false;
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
        changed = true;
      }
      // the stages of today's rounds whose hour has come (the owner, 13 Nov
      // 2026: the round's day told stage by stage through the day)
      if (g.nextTelling != null) {
        try {
          final before = g.toldStages;
          g.tellTo(s.clock(now: _now).minuteOfDay());
          if (g.toldStages != before) changed = true;
        } on Object catch (e) {
          await _recover(e);
          return;
        }
      }
      if (changed) await _saveNow();
    } finally {
      if (always || changed) _publish();
      _scheduleNextDay();
    }
  }

  /// Saves now. A failure is reported and retried; it never stops later
  /// saves and never throws into the caller's operation.
  Future<void> _saveNow() async {
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

  void _scheduleNextDay() {
    _nextDay?.cancel();
    final g = _game;
    if (g == null || _paused || _closed || _halted) return;
    final clock = g.state.clock(now: _now);
    var wait = clock.untilNextDay();
    // or the next stage of a round today, if it comes first
    final stage = g.nextTelling;
    if (stage != null) {
      final until = clock.untilMinute(stage);
      if (until < wait) wait = until;
    }
    _nextDay = Timer(wait + const Duration(milliseconds: 50), () {
      if (!_closed) unawaited(catchUp().catchError((Object _) {}));
    });
  }

  void _cancelTimers() {
    _nextDay?.cancel();
    _retry?.cancel();
  }
}
