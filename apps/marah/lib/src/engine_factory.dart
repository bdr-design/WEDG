import 'package:marah_runtime/io.dart';
import 'package:marah_runtime/marah_runtime.dart';
import 'package:path_provider/path_provider.dart';

/// Starts the engine in its worker isolate (iOS and Android; ADR 0002).
/// The game lives in the worker and saves to an app-private folder; only
/// the folder path is looked up here. The web is paused (ADR 0002).
Future<EngineClient> startEngine() async {
  final dir = await getApplicationSupportDirectory();
  return IsolateEngineClient.spawn(saveDirectory: dir.path);
}
