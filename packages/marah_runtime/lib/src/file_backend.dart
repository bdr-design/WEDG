import 'dart:io';

import 'package:marah_data/marah_data.dart';

/// Saves as files in an app-private directory, written atomically: the new
/// text goes to a uniquely named temp file, is flushed to disk, then renamed
/// over the old file, so a crash mid-write never leaves a half-written save.
/// One engine owns the folder (a single writer).
///
/// Runs inside the worker isolate with plain `dart:io`; the directory path
/// is resolved once on the UI isolate and passed in.
class FileBackend implements SaveBackend {
  FileBackend(this.directory);

  final String directory;
  int _tmpCounter = 0;

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
    final tmp = File('${target.path}.${_tmpCounter++}.tmp');
    await tmp.writeAsString(value, flush: true);
    await tmp.rename(target.path);
  }

  @override
  Future<void> delete(String key) async {
    final f = _file(key);
    if (f.existsSync()) await f.delete();
  }

  @override
  Future<void> copy(String from, String to) async {
    final src = _file(from);
    if (!src.existsSync()) return;
    final target = _file(to);
    final tmp = File('${target.path}.${_tmpCounter++}.tmp');
    await src.copy(tmp.path);
    await tmp.rename(target.path);
  }
}
