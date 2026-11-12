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
/// Every request carries the launch's random [token] in `x-marah-save` (the
/// page has it in its address): nothing but the page reads or writes the save.
class SaveFiles {
  SaveFiles(this.dir, {String? token}) : token = token ?? _newToken();

  final Directory dir;
  final String token;
  int _n = 0;

  /// The most a save may hold (a 10,000-head farm's is about 10 MB).
  static const maxBytes = 256 << 20;

  static String _newToken() {
    final r = Random.secure();
    return [
      for (var i = 0; i < 16; i++)
        r.nextInt(256).toRadixString(16).padLeft(2, '0'),
    ].join();
  }

  /// A key may be a file name and nothing else.
  static bool validKey(String key) =>
      RegExp(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$').hasMatch(key) &&
      !key.contains('..');

  File _file(String key) => File('${dir.path}/$key');

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
          await dir.create(recursive: true);
          final tmp = File('${dir.path}/.$key.${_n++}.tmp');
          await tmp.writeAsBytes(bytes, flush: true);
          await tmp.rename(_file(key).path);
          res.statusCode = HttpStatus.noContent;
        } else if (req.method == 'DELETE') {
          final f = _file(key);
          if (await f.exists()) await f.delete();
          res.statusCode = HttpStatus.noContent;
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
