import 'dart:async';

import 'package:marah_domain/marah_domain.dart';

import 'engine_core.dart';
import 'protocol.dart';
import 'view_models.dart';

/// The only way the UI talks to the game. Every call is asynchronous and
/// all work happens away from the UI thread (see ADR 0002).
abstract interface class EngineClient {
  /// The latest state of the player's world, after every change.
  Stream<PlayerSnapshot> get snapshots;

  /// Progress while a long absence is being caught up.
  Stream<CatchUpProgress> get progress;

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

/// Shared stream plumbing for client implementations.
mixin PushStreams {
  final _snapshots = StreamController<PlayerSnapshot>.broadcast();
  final _progress = StreamController<CatchUpProgress>.broadcast();
  int _lastRevision = 0;

  Stream<PlayerSnapshot> get snapshots => _snapshots.stream;
  Stream<CatchUpProgress> get progress => _progress.stream;

  void deliver(Push p) {
    switch (p) {
      case SnapshotPush(:final snapshot):
        if (snapshot.revision <= _lastRevision) return; // stale
        _lastRevision = snapshot.revision;
        _snapshots.add(snapshot);
      case CatchUpProgress():
        _progress.add(p);
    }
  }

  Future<void> closeStreams() async {
    await _snapshots.close();
    await _progress.close();
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
