import 'dart:async';
import 'dart:io';
import 'dart:isolate';

import 'package:marah_domain/marah_domain.dart';
import 'package:marah_store/marah_store.dart';

import 'engine_client.dart';
import 'engine_core.dart';
import 'protocol.dart';
import 'view_models.dart';

/// Runs the engine in one long-lived worker isolate (iOS, Android,
/// desktop). The game state lives only in the worker; requests go in with
/// ids, replies and pushes come back. JSON encoding, file writes and
/// catch-up all happen in the worker.
class IsolateEngineClient with PushStreams implements EngineClient {
  IsolateEngineClient._(
    this._isolate,
    this._send,
    this._inbox,
    this._errors,
    this._exits,
  );

  final Isolate _isolate;
  final SendPort _send;
  final ReceivePort _inbox;
  final ReceivePort _errors;
  final ReceivePort _exits;
  final Map<int, Completer<Object?>> _pending = {};
  int _nextId = 0;
  bool _dead = false;
  bool _closing = false;

  /// Starts the worker. [saveDirectory] is an app-private folder resolved on
  /// the UI isolate (path_provider) and passed in as a plain string.
  static Future<IsolateEngineClient> spawn({
    required String saveDirectory,
  }) async {
    final inbox = ReceivePort();
    final errors = ReceivePort();
    final exits = ReceivePort();
    final isolate = await Isolate.spawn(
      _workerMain,
      (inbox.sendPort, saveDirectory),
      onError: errors.sendPort,
      onExit: exits.sendPort,
      debugName: 'marah-engine',
    );
    final first = Completer<SendPort>();
    late final IsolateEngineClient client;
    inbox.listen((Object? message) {
      if (message is SendPort) {
        first.complete(message);
      } else if (message is WorkerMessage) {
        client._receive(message);
      }
    });
    final send = await first.future;
    client = IsolateEngineClient._(isolate, send, inbox, errors, exits);
    errors.listen((Object? e) => client._fail('worker error: $e'));
    exits.listen((_) => client._fail('worker exited'));
    return client;
  }

  void _receive(WorkerMessage m) {
    switch (m) {
      case Reply(:final id, :final value):
        _pending.remove(id)?.complete(value);
      case Failure(:final id, :final error, :final stack):
        _pending
            .remove(id)
            ?.completeError(EngineFailure(error), StackTrace.fromString(stack));
      case Pushed(:final push):
        deliver(push);
    }
  }

  void _fail(String why) {
    if (_dead) return;
    _dead = true;
    for (final c in _pending.values) {
      c.completeError(EngineStopped(why));
    }
    _pending.clear();
    if (!_closing) notice(EngineDown(why));
  }

  Future<T> _ask<T>(Request Function(int id) build) {
    if (_dead || _closing) {
      return Future.error(const EngineStopped('engine stopped'));
    }
    final id = ++_nextId;
    final c = Completer<Object?>();
    _pending[id] = c;
    _send.send(build(id));
    return c.future.then((v) => v as T);
  }

  @override
  Future<OpenStatus> open() => _ask(OpenReq.new);
  @override
  Future<OpenStatus> openPrevious() => _ask(OpenPreviousReq.new);
  @override
  Future<void> newGame(NewGameParams params) =>
      _ask((id) => NewGameReq(id, params));
  @override
  Future<void> startOver() => _ask(StartOverReq.new);
  @override
  Future<Result> dispatch(Command command) =>
      _ask((id) => DispatchReq(id, command));
  @override
  Future<CamelDetail?> camelDetail(CamelId id) =>
      _ask((rid) => CamelDetailReq(rid, id));
  @override
  Future<FestivalDetail?> festivalDetail(FestivalId id) =>
      _ask((rid) => FestivalDetailReq(rid, id));
  @override
  Future<HerdPage?> herdPage(HerdQuery query) =>
      _ask((rid) => HerdPageReq(rid, query));
  @override
  Future<void> pause() => _ask(PauseReq.new);
  @override
  Future<void> resume() => _ask(ResumeReq.new);
  @override
  Future<void> flush() => _ask(FlushReq.new);

  @override
  Future<void> dispose() async {
    if (_closing) return;
    EngineFailure? shutdownError;
    if (!_dead) {
      try {
        await _ask<void>(ShutdownReq.new);
      } on EngineFailure catch (e) {
        shutdownError = e; // the final save failed: report it below
      } on EngineStopped {
        // Already gone.
      }
    }
    _closing = true;
    _fail('disposed');
    _inbox.close();
    _errors.close();
    _exits.close();
    _isolate.kill(priority: Isolate.beforeNextEvent);
    await closeStreams();
    if (shutdownError != null) throw shutdownError;
  }
}

/// Worker entry point: owns the engine and answers requests in order.
Future<void> _workerMain((SendPort, String) args) async {
  final (toUi, saveDirectory) = args;
  final inbox = ReceivePort();
  toUi.send(inbox.sendPort);

  final core = EngineCore(
    store: SqliteGameStore('$saveDirectory${Platform.pathSeparator}marah.db'),
    emit: (p) => toUi.send(Pushed(p)),
  );

  await for (final Object? message in inbox) {
    if (message is! Request) continue;
    final id = message.id;
    try {
      final value = await _handle(core, message);
      toUi.send(Reply(id, value));
      if (message is ShutdownReq) {
        inbox.close();
        Isolate.exit();
      }
    } on Object catch (e, s) {
      toUi.send(Failure(id, e.toString(), s.toString()));
    }
  }
}

Future<Object?> _handle(EngineCore core, Request message) async {
  switch (message) {
    case OpenReq():
      return core.open();
    case OpenPreviousReq():
      return core.openPrevious();
    case NewGameReq(:final params):
      await core.newGame(params);
    case StartOverReq():
      await core.startOver();
    case DispatchReq(:final command):
      return core.dispatch(command);
    case CamelDetailReq(:final camel):
      return core.camelDetail(camel);
    case FestivalDetailReq(:final festival):
      return core.festivalDetail(festival);
    case HerdPageReq(:final query):
      return core.herdPage(query);
    case PauseReq():
      await core.pause();
    case ResumeReq():
      await core.resume();
    case FlushReq():
      await core.flush();
    case ShutdownReq():
      await core.close();
  }
  return null;
}

/// The worker answered a request with an error.
class EngineFailure implements Exception {
  const EngineFailure(this.message);
  final String message;
  @override
  String toString() => 'EngineFailure: $message';
}
