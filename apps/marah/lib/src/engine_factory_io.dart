import 'package:marah_runtime/io.dart';
import 'package:marah_runtime/marah_runtime.dart';
import 'package:path_provider/path_provider.dart';

/// iOS / Android / desktop: the game lives in a worker isolate and saves to
/// an app-private file. Only the folder path is looked up here.
Future<EngineClient> startEngine() async {
  final dir = await getApplicationSupportDirectory();
  return IsolateEngineClient.spawn(saveDirectory: dir.path);
}
