import 'dart:async';

import 'package:marah_domain/marah_domain.dart';

import 'engine_core.dart';
import 'protocol.dart';
import 'view_models.dart';

/// The only way the UI talks to the game. Every call is asynchronous and
/// all work happens away from the UI thread (see ADR 0002).
abstract interface class EngineClient {
  /// The latest state of the player's world. A new listener immediately
  /// receives the most recent snapshot, then every later one.
  Stream<PlayerSnapshot> get snapshots;

  /// The most recent snapshot, if any.
  PlayerSnapshot? get latest;

  /// Progress while a long absence is being caught up.
  Stream<CatchUpProgress> get progress;

  /// Saving problems and recoveries, skipped absences, and engine failure.
  Stream<Push> get notices;

  Future<OpenStatus> open();
  Future<OpenStatus> openPrevious();
  Future<void> newGame(NewGameParams params);
  Future<void> startOver();
  Future<Result> dispatch(Command command);
  Future<CamelDetail?> camelDetail(CamelId id);
  Future<FestivalDetail?> festivalDetail(FestivalId id);

  /// Call when the app is hidden: saves and stops timers.
  Future<void> pause();

  /// Call when the app is shown again: catches up with the clock.
  Future<void> resume();
  Future<void> flush();
  Future<void> dispose();
}

class EngineStopped implements Exception {
  const EngineStopped(this.reason);
  final String reason;
  @override
  String toString() => 'EngineStopped: $reason';
}

/// Shared stream plumbing for client implementations.
mixin PushStreams {
  final _snapshots = StreamController<PlayerSnapshot>.broadcast();
  final _progress = StreamController<CatchUpProgress>.broadcast();
  final _notices = StreamController<Push>.broadcast();
  PlayerSnapshot? _latest;

  PlayerSnapshot? get latest => _latest;

  Stream<PlayerSnapshot> get snapshots => Stream.multi((c) {
    final last = _latest;
    if (last != null) c.add(last);
    final sub = _snapshots.stream.listen(c.add, onDone: c.close);
    c.onCancel = sub.cancel;
  });

  Stream<CatchUpProgress> get progress => _progress.stream;
  Stream<Push> get notices => _notices.stream;

  void deliver(Push p) {
    switch (p) {
      case SnapshotPush(:final snapshot):
        final last = _latest;
        if (last != null && snapshot.revision <= last.revision) return;
        _latest = snapshot;
        if (!_snapshots.isClosed) _snapshots.add(snapshot);
      case CatchUpProgress():
        if (!_progress.isClosed) _progress.add(p);
      case SaveStatus() || CatchUpCapped() || EngineDown():
        if (!_notices.isClosed) _notices.add(p);
    }
  }

  void notice(Push p) {
    if (!_notices.isClosed) _notices.add(p);
  }

  Future<void> closeStreams() async {
    await _snapshots.close();
    await _progress.close();
    await _notices.close();
  }
}

/// Runs the engine in the current isolate, time-sliced so the event loop
/// keeps running. Used on the web, where isolates are not available, and in
/// tests.
class InlineEngineClient with PushStreams implements EngineClient {
  InlineEngineClient(EngineCoreFactory create) {
    core = create(deliver);
  }

  late final EngineCore core;

  @override
  Future<OpenStatus> open() => core.open();
  @override
  Future<OpenStatus> openPrevious() => core.openPrevious();
  @override
  Future<void> newGame(NewGameParams params) => core.newGame(params);
  @override
  Future<void> startOver() => core.startOver();
  @override
  Future<Result> dispatch(Command command) => core.dispatch(command);
  @override
  Future<CamelDetail?> camelDetail(CamelId id) => core.camelDetail(id);
  @override
  Future<FestivalDetail?> festivalDetail(FestivalId id) =>
      core.festivalDetail(id);
  @override
  Future<void> pause() => core.pause();
  @override
  Future<void> resume() => core.resume();
  @override
  Future<void> flush() => core.flush();
  @override
  Future<void> dispose() async {
    await core.close();
    await closeStreams();
  }
}

typedef EngineCoreFactory = EngineCore Function(void Function(Push) emit);
