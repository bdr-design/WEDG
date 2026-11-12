// The game's save kept as files for the 3D prototype's rules engine (see
// main.dart). Plain dart:io, no Flutter, so a test server can use it too.
import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'dart:typed_data';

/// The game's save as files, one per key ('marah.save', its '.prev' and
/// '.broken' copies), for the rules engine in the page's worker
/// (docs/plan-gameplay.md, G2):
/// * `GET /save`: every key and its text, as one JSON object.
/// * `PUT /save/KEY`: the body becomes the key's text (written whole, then
///   renamed over the old file, so a crash leaves one or the other).
/// * `DELETE /save/KEY`.
/// * A write numbered `x-marah-write: LOAD:SEQ` that is older than one already
///   applied is refused (409): see [_inOrder].
/// Every request carries the launch's random [token] in `x-marah-save` (the
/// page has it in its address): nothing but the page reads or writes the save.
class SaveFiles {
  SaveFiles(this.dir, {String? token}) : token = token ?? _newToken();

  final Directory dir;
  final String token;
  int _n = 0;

  /// The most a save may hold (a 10,000-head farm's is 6.7 MB).
  static const maxBytes = 64 << 20;

  /// The only keys there are: the save, the last one proven readable, and a
  /// copy of one that could not be read (marah_data's SaveStore).
  static const keys = {'marah.save', 'marah.save.prev', 'marah.save.broken'};

  static String _newToken() {
    final r = Random.secure();
    return [
      for (var i = 0; i < 16; i++)
        r.nextInt(256).toRadixString(16).padLeft(2, '0'),
    ].join();
  }

  /// A key may be a file name and nothing else.
  static bool validKey(String key) => keys.contains(key);

  File _file(String key) => File('${dir.path}/$key');

  // The writes' order. Each comes numbered from the engine that sent it
  // (`x-marah-write: LOAD:SEQ`, LOAD new each time an engine opens the save):
  // a write the engine gave up on (cut off after 15 s) can still reach here,
  // or be delayed here, after a newer one; it must not land over it. So the
  // writes are applied one at a time, a write older than the last applied to
  // its key from the same engine is refused, and once an engine's writes come
  // the previous engine's are refused for good.
  Future<void> _writes = Future.value();
  String? _load;
  final Set<String> _retired = {};
  final Map<String, int> _applied = {};

  /// Whether a write numbered [stamp] may land on [key] now (and if so, it is
  /// counted as applied). An unnumbered write always may.
  bool _inOrder(String key, String? stamp) {
    if (stamp == null) return true;
    final i = stamp.lastIndexOf(':');
    final load = i > 0 ? stamp.substring(0, i) : '';
    final seq = int.tryParse(stamp.substring(i + 1));
    if (load.isEmpty || seq == null || _retired.contains(load)) return false;
    if (load != _load) {
      if (_load != null) _retired.add(_load!);
      _load = load;
      _applied.clear();
    }
    if (seq <= (_applied[key] ?? -1)) return false;
    _applied[key] = seq;
    return true;
  }

  /// Runs [write] after every write before it.
  Future<T> _inTurn<T>(Future<T> Function() write) {
    final done = _writes.then((_) => write());
    _writes = done.then((_) {}, onError: (Object _) {});
    return done;
  }

  Future<void> handle(HttpRequest req) async {
    final res = req.response;
    res.headers.set('Cache-Control', 'no-store');
    try {
      if (req.headers.value('x-marah-save') != token) {
        res.statusCode = HttpStatus.forbidden;
      } else if (req.uri.path == '/save' && req.method == 'GET') {
        final all = <String, String>{};
        if (await dir.exists()) {
          await for (final f in dir.list()) {
            final name = f.uri.pathSegments.last;
            if (f is File && validKey(name)) all[name] = await f.readAsString();
          }
        }
        res.headers.contentType = ContentType.json;
        res.write(jsonEncode(all));
      } else {
        final key = Uri.decodeComponent(
          req.uri.path.substring('/save/'.length),
        );
        if (!validKey(key)) {
          res.statusCode = HttpStatus.badRequest;
        } else if (req.method == 'PUT') {
          final body = BytesBuilder(copy: false);
          await for (final chunk in req) {
            body.add(chunk);
            if (body.length > maxBytes) throw const HttpException('too large');
          }
          final bytes = body.takeBytes();
          utf8.decode(bytes); // text only: GET reads it back as text
          final stamp = req.headers.value('x-marah-write');
          res.statusCode = await _inTurn(() async {
            if (!_inOrder(key, stamp)) return HttpStatus.conflict;
            await dir.create(recursive: true);
            final tmp = File('${dir.path}/.$key.${_n++}.tmp');
            try {
              await tmp.writeAsBytes(bytes, flush: true);
              await tmp.rename(_file(key).path);
            } catch (_) {
              // a full disk: the old file stays whole, and no half-written copy is left
              if (await tmp.exists()) await tmp.delete();
              rethrow;
            }
            return HttpStatus.noContent;
          });
        } else if (req.method == 'DELETE') {
          final stamp = req.headers.value('x-marah-write');
          res.statusCode = await _inTurn(() async {
            if (!_inOrder(key, stamp)) return HttpStatus.conflict;
            final f = _file(key);
            if (await f.exists()) await f.delete();
            return HttpStatus.noContent;
          });
        } else {
          res.statusCode = HttpStatus.methodNotAllowed;
        }
      }
    } catch (_) {
      // a malformed escape, a body that is not UTF-8 or too large, a full disk:
      // the page hears it failed (the engine reports it and tries again)
      res.statusCode = HttpStatus.internalServerError;
    }
    await res.close();
  }
}
