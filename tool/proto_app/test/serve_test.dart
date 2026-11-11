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
}
