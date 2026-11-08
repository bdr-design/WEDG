import 'dart:io';

import 'package:marah_data/marah_data.dart';

/// Saves as files in an app-private directory, written atomically: the new
/// text goes to `<key>.tmp`, is flushed to disk, then renamed over the old
/// file, so a crash mid-write never leaves a half-written save.
///
/// Runs inside the worker isolate with plain `dart:io`; the directory path
/// is resolved once on the UI isolate and passed in.
class FileBackend implements SaveBackend {
  FileBackend(this.directory);

  final String directory;

  File _file(String key) => File('$directory${Platform.pathSeparator}$key');

  @override
  Future<String?> read(String key) async {
    final f = _file(key);
    if (!f.existsSync()) return null;
    return f.readAsString();
  }

  @override
  Future<void> write(String key, String value) async {
    final target = _file(key);
    await target.parent.create(recursive: true);
    final tmp = File('${target.path}.tmp');
    await tmp.writeAsString(value, flush: true);
    await tmp.rename(target.path);
  }

  @override
  Future<void> delete(String key) async {
    final f = _file(key);
    if (f.existsSync()) await f.delete();
  }
}
