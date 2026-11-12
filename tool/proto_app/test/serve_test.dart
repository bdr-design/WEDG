import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:marah_proto/main.dart';

void main() {
  test('module scripts get a JavaScript type', () {
    expect(contentTypeFor('assets/web/play.js').mimeType, 'text/javascript');
    expect(contentTypeFor('assets/web/index.html').mimeType, ContentType.html.mimeType);
    expect(contentTypeFor('assets/web/lod0.json').mimeType, 'application/json');
  });
  test('only files inside the bundle are served', () {
    expect(assetFor('/'), 'assets/web/index.html');
    expect(assetFor('/three/build/three.module.js'), 'assets/web/three/build/three.module.js');
    expect(assetFor('/../pubspec.yaml'), isNull);
    expect(assetFor('/phone/../../x'), isNull);
  });
  saveTests();
}

/// A real server on the loopback address, its save in a fresh folder.
Future<(HttpServer, SaveFiles, Directory)> saveServer() async {
  final dir = await Directory.systemTemp.createTemp('marah_save_');
  final saves = SaveFiles(Directory('${dir.path}/Documents/marah'));
  return (await bindServer(saves), saves, dir);
}

Future<(int, String)> call(HttpServer s, String method, String path, {String? token, List<int>? body}) async {
  final client = HttpClient();
  try {
    final req = await client.open(method, '127.0.0.1', s.port, path);
    if (token != null) req.headers.set('x-marah-save', token);
    if (body != null) req.add(body);
    final res = await req.close();
    return (res.statusCode, await utf8.decoder.bind(res).join());
  } finally {
    client.close(force: true);
  }
}

void saveTests() {
  test('the save: written, read back whole, deleted', () async {
    final (s, saves, dir) = await saveServer();
    addTearDown(() async {
      await s.close(force: true);
      await dir.delete(recursive: true);
    });
    final t = saves.token;
    expect(t, hasLength(32));
    expect(await call(s, 'GET', '/save', token: t), (200, '{}'));
    final text = '{"مراح":"${'x' * 300000}"}';
    expect((await call(s, 'PUT', '/save/marah.save', token: t, body: utf8.encode(text))).$1, 204);
    expect((await call(s, 'PUT', '/save/marah.save.prev', token: t, body: utf8.encode('old'))).$1, 204);
    final (code, all) = await call(s, 'GET', '/save', token: t);
    expect(code, 200);
    expect(jsonDecode(all), {'marah.save': text, 'marah.save.prev': 'old'});
    expect((await call(s, 'DELETE', '/save/marah.save', token: t)).$1, 204);
    expect((await call(s, 'DELETE', '/save/marah.save', token: t)).$1, 204);
    expect(jsonDecode((await call(s, 'GET', '/save', token: t)).$2), {'marah.save.prev': 'old'});
    // nothing half-written left behind
    expect(Directory('${dir.path}/Documents/marah').listSync().map((f) => f.uri.pathSegments.last), ['marah.save.prev']);
  });

  test('the save: only with the token, only plain keys, only text', () async {
    final (s, saves, dir) = await saveServer();
    addTearDown(() async {
      await s.close(force: true);
      await dir.delete(recursive: true);
    });
    final t = saves.token;
    expect((await call(s, 'GET', '/save')).$1, 403);
    expect((await call(s, 'GET', '/save', token: 'nope')).$1, 403);
    expect((await call(s, 'PUT', '/save/marah.save', body: [65])).$1, 403);
    for (final bad in ['/save/..%2Fx', '/save/.hidden', '/save/a%2Fb', '/save/', '/save/%FF', '/save/index.html', '/save/x1']) {
      final (code, _) = await call(s, 'PUT', bad, token: t, body: [65]);
      expect(code, anyOf(400, 500), reason: bad);
    }
    expect((await call(s, 'PUT', '/save/marah.save', token: t, body: [0xFF, 0xFE])).$1, 500);
    expect((await call(s, 'POST', '/save/marah.save', token: t, body: [65])).$1, 405);
    expect(jsonDecode((await call(s, 'GET', '/save', token: t)).$2), isEmpty);
    expect(Directory('${dir.path}/Documents/marah').existsSync() ? Directory('${dir.path}/Documents/marah').listSync().where((f) => !f.uri.pathSegments.last.endsWith('.tmp')) : const [], isEmpty);
    expect(SaveFiles.validKey('marah.save.broken'), isTrue);
    expect(SaveFiles.validKey('../marah'), isFalse);
    expect(SaveFiles.validKey('a..b'), isFalse);
    expect(SaveFiles.validKey('index.html'), isFalse);
    // more than a save may hold is refused, and nothing is left behind
    // (answered 500 while the body is still coming, or the connection cut: either way not kept)
    try {
      expect((await call(s, 'PUT', '/save/marah.save', token: t, body: List.filled(SaveFiles.maxBytes + 1, 65))).$1, 500);
    } on HttpException {
      // the server stopped reading
    } on SocketException {
      // likewise
    }
    expect(jsonDecode((await call(s, 'GET', '/save', token: t)).$2), isEmpty);
  });

  test('the bundle is still served beside the save', () async {
    final (s, _, dir) = await saveServer();
    addTearDown(() async {
      await s.close(force: true);
      await dir.delete(recursive: true);
    });
    expect((await call(s, 'GET', '/../pubspec.yaml')).$1, anyOf(400, 404));
  });
}
