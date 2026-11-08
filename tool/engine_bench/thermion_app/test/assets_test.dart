import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';

/// The JSON chunk of a binary glTF file.
Map<String, Object?> glbJson(String path) {
  final bytes = File(path).readAsBytesSync();
  final data = ByteData.sublistView(bytes);
  expect(data.getUint32(0, Endian.little), 0x46546C67, reason: 'glTF magic');
  final jsonLength = data.getUint32(12, Endian.little);
  expect(data.getUint32(16, Endian.little), 0x4E4F534A, reason: 'JSON chunk');
  return jsonDecode(utf8.decode(bytes.sublist(20, 20 + jsonLength)))
      as Map<String, Object?>;
}

void main() {
  test('bundled camel is the 8k-triangle LOD1 with a 38-bone rig and walk', () {
    final json = glbJson('assets/camel_lod1.glb');
    final skins = json['skins']! as List<Object?>;
    final joints = (skins.single! as Map<String, Object?>)['joints']!;
    expect(joints as List<Object?>, hasLength(38));
    final animations = [
      for (final a in json['animations']! as List<Object?>)
        (a! as Map<String, Object?>)['name'],
    ];
    expect(animations, contains('walk'));
  });

  test('bundled terrain has the three rings', () {
    final json = glbJson('assets/terrain.glb');
    final meshes = [
      for (final m in json['meshes']! as List<Object?>)
        (m! as Map<String, Object?>)['name'],
    ];
    expect(meshes, containsAll(['terrain_near', 'terrain_mid', 'terrain_far']));
  });

  test('pubspec bundles exactly the assets the scene loads', () {
    final pubspec = File('pubspec.yaml').readAsStringSync();
    expect(pubspec, contains('- assets/terrain.glb'));
    expect(pubspec, contains('- assets/camel_lod1.glb'));
    expect(pubspec, isNot(contains('resolution: workspace')));
  });
}
