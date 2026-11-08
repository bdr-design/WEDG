import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/marah_domain.dart';

import 'view_models.dart';

/// Parameters for a new world.
class NewGameParams {
  const NewGameParams({
    required this.seed,
    required this.playerName,
    required this.farmName,
    required this.region,
    required this.favourite,
  });

  final int seed;
  final String playerName;
  final String farmName;
  final Region region;
  final ColorCategory favourite;
}

/// What opening the game found.
sealed class OpenStatus {
  const OpenStatus();
}

final class NoGame extends OpenStatus {
  const NoGame();
}

final class GameOpened extends OpenStatus {
  const GameOpened();
}

/// The save could not be read. It is backed up and untouched; the player
/// chooses to try the previous save or start over.
final class GameOpenFailed extends OpenStatus {
  const GameOpenFailed(this.problem, this.detail);
  final LoadProblem problem;
  final String detail;
}

/// Messages the engine pushes to the UI without being asked.
sealed class Push {
  const Push();
}

final class SnapshotPush extends Push {
  const SnapshotPush(this.snapshot);
  final PlayerSnapshot snapshot;
}

/// Catching up a long absence: [done] of [total] game days simulated.
final class CatchUpProgress extends Push {
  const CatchUpProgress(this.done, this.total);
  final int done;
  final int total;
}

// ----------------------------------------------------------- isolate wire

/// UI → worker. Each request has an id; the worker answers with a [Reply]
/// or a [Failure] carrying the same id.
sealed class Request {
  const Request(this.id);
  final int id;
}

final class OpenReq extends Request {
  const OpenReq(super.id);
}

final class OpenPreviousReq extends Request {
  const OpenPreviousReq(super.id);
}

final class NewGameReq extends Request {
  const NewGameReq(super.id, this.params);
  final NewGameParams params;
}

final class StartOverReq extends Request {
  const StartOverReq(super.id);
}

final class DispatchReq extends Request {
  const DispatchReq(super.id, this.command);
  final Command command;
}

final class CamelDetailReq extends Request {
  const CamelDetailReq(super.id, this.camel);
  final CamelId camel;
}

final class FestivalDetailReq extends Request {
  const FestivalDetailReq(super.id, this.festival);
  final FestivalId festival;
}

final class PauseReq extends Request {
  const PauseReq(super.id);
}

final class ResumeReq extends Request {
  const ResumeReq(super.id);
}

final class FlushReq extends Request {
  const FlushReq(super.id);
}

final class ShutdownReq extends Request {
  const ShutdownReq(super.id);
}

/// Worker → UI.
sealed class WorkerMessage {
  const WorkerMessage();
}

final class Reply extends WorkerMessage {
  const Reply(this.id, this.value);
  final int id;
  final Object? value;
}

final class Failure extends WorkerMessage {
  const Failure(this.id, this.error, this.stack);
  final int id;
  final String error;
  final String stack;
}

final class Pushed extends WorkerMessage {
  const Pushed(this.push);
  final Push push;
}
