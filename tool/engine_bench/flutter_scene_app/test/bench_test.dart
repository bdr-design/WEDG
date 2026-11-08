import 'dart:convert';
import 'dart:math' as math;

import 'package:bench_flutter_scene/src/bench.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('herdLayout', () {
    for (final n in kHerdSizes) {
      test('$n camels on a centred 4 m grid', () {
        final slots = herdLayout(n, random: math.Random(1), clipLength: 1.5);
        expect(slots, hasLength(n));
        final cols = math.sqrt(n).ceil();
        final rows = (n / cols).ceil();
        for (var i = 0; i < n; i++) {
          final gx = (i % cols - (cols - 1) / 2) * kHerdSpacing;
          final gz = (i ~/ cols - (rows - 1) / 2) * kHerdSpacing;
          expect((slots[i].x - gx).abs(), lessThanOrEqualTo(kHerdJitter));
          expect((slots[i].z - gz).abs(), lessThanOrEqualTo(kHerdJitter));
          expect(slots[i].heading, inInclusiveRange(0, 2 * math.pi));
          expect(slots[i].clipOffset, inInclusiveRange(0, 1.5));
        }
        // Centred on the origin: the grid's bounding box is symmetric.
        final halfX = (cols - 1) / 2 * kHerdSpacing;
        final halfZ = (rows - 1) / 2 * kHerdSpacing;
        for (final s in slots) {
          expect(s.x.abs(), lessThanOrEqualTo(halfX + kHerdJitter));
          expect(s.z.abs(), lessThanOrEqualTo(halfZ + kHerdJitter));
        }
      });
    }

    test('headings and clip offsets differ between camels', () {
      final slots = herdLayout(34, random: math.Random(2), clipLength: 1.5);
      expect(slots.map((s) => s.heading).toSet(), hasLength(34));
      expect(slots.map((s) => s.clipOffset).toSet(), hasLength(34));
    });

    test('is deterministic for a seed', () {
      final a = herdLayout(100, random: math.Random(7), clipLength: 1.5);
      final b = herdLayout(100, random: math.Random(7), clipLength: 1.5);
      expect([for (final s in a) s.x], [for (final s in b) s.x]);
    });

    test('no camels for n <= 0', () {
      expect(herdLayout(0, random: math.Random(), clipLength: 1), isEmpty);
    });
  });

  group('percentiles', () {
    test('nearest rank', () {
      final values = [for (var i = 1; i <= 100; i++) i.toDouble()]..shuffle();
      final p = percentiles(values);
      expect(p.p50, 50);
      expect(p.p90, 90);
      expect(p.p99, 99);
    });

    test('a single value is every percentile', () {
      final p = percentiles([16.7]);
      expect([p.p50, p.p90, p.p99], [16.7, 16.7, 16.7]);
    });

    test('empty gives NaN', () {
      expect(percentiles(const <double>[]).p50, isNaN);
    });
  });

  test('framesInWindow keeps frames whose build starts inside it', () {
    FrameSample at(int start) => FrameSample(
      buildStart: start,
      rasterFinish: start + 10,
      totalSpan: 10,
      build: 4,
      raster: 5,
    );
    final picked = framesInWindow([at(5), at(10), at(15), at(20)], 10, 20);
    expect(picked.map((f) => f.buildStart), [10, 15]);
  });

  test('benchLine is the README format and valid JSON', () {
    final line = benchLine({
      'engine': kEngine,
      'n': 34,
      'fps': roundTo(59.987, 1),
      'p50_ms': double.nan,
    });
    expect(line, startsWith('BENCH {"engine":"flutter_scene","n":34'));
    final json = jsonDecode(line.substring('BENCH '.length)) as Map;
    expect(json['fps'], 60.0);
    expect(json['p50_ms'], isNull);
    expect(benchLine({'a': 1}, tag: 'BENCH_INFO'), 'BENCH_INFO {"a":1}');
  });
}
