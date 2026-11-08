import 'dart:convert';
import 'dart:math' as math;

import 'package:bench_thermion/src/bench_stats.dart';
import 'package:bench_thermion/src/herd_layout.dart';
import 'package:bench_thermion/src/sky_light.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('herdLayout', () {
    for (final n in [34, 100, 200]) {
      test('$n camels on a jittered 4 m grid centred on the yard', () {
        final herd = herdLayout(n, clipDuration: 1.5);
        expect(herd, hasLength(n));

        final cols = math.sqrt(n).ceil();
        final rows = (n / cols).ceil();
        for (var i = 0; i < n; i++) {
          final p = herd[i];
          final slotX = (i % cols - (cols - 1) / 2) * kHerdSpacing;
          final slotZ = (i ~/ cols - (rows - 1) / 2) * kHerdSpacing;
          expect((p.x - slotX).abs(), lessThanOrEqualTo(kHerdJitter));
          expect((p.z - slotZ).abs(), lessThanOrEqualTo(kHerdJitter));
          expect(p.heading, inInclusiveRange(0, 2 * math.pi));
          expect(p.clipOffset, inInclusiveRange(0, 1.5));
        }

        final meanX = herd.map((p) => p.x).reduce((a, b) => a + b) / n;
        final meanZ = herd.map((p) => p.z).reduce((a, b) => a + b) / n;
        // Centred, up to jitter and the partly filled last row.
        expect(meanX.abs(), lessThan(kHerdSpacing));
        expect(meanZ.abs(), lessThan(kHerdSpacing));
      });
    }

    test('200 camels fit inside the ±72 m shadow area', () {
      for (final p in herdLayout(200, clipDuration: 1.5)) {
        expect(p.x.abs(), lessThan(72));
        expect(p.z.abs(), lessThan(72));
      }
    });

    test(
      'is deterministic and gives every camel its own heading and offset',
      () {
        final a = herdLayout(100, clipDuration: 1.5);
        final b = herdLayout(100, clipDuration: 1.5);
        for (var i = 0; i < 100; i++) {
          expect(a[i].x, b[i].x);
          expect(a[i].heading, b[i].heading);
          expect(a[i].clipOffset, b[i].clipOffset);
        }
        expect(a.map((p) => p.heading).toSet(), hasLength(100));
        expect(a.map((p) => p.clipOffset).toSet(), hasLength(100));
      },
    );

    test('empty herd', () {
      expect(herdLayout(0, clipDuration: 1.5), isEmpty);
    });
  });

  group('stats', () {
    test('nearest-rank percentiles', () {
      final samples = [for (var i = 1; i <= 100; i++) i.toDouble()]..shuffle();
      expect(percentile(samples, 50), 50);
      expect(percentile(samples, 90), 90);
      expect(percentile(samples, 99), 99);
      expect(percentile([7], 99), 7);
      expect(percentile([], 50), isNull);
    });

    test('window filter uses the start timestamp', () {
      const samples = [
        TimedSample(900, 5000),
        TimedSample(1000, 16000),
        TimedSample(1999, 17000),
        TimedSample(2000, 18000),
      ];
      expect(durationsInWindow(samples, 1000, 2000), [16.0, 17.0]);
    });

    test('measurement line has the README fields in order', () {
      final line = measurementLine(
        engine: 'thermion',
        n: 34,
        frameMs: List.filled(300, 10.0),
        engineMs: List.filled(290, 20.0),
        windowSeconds: 10,
        rssMb: 321.456,
      );
      expect(line, startsWith('BENCH {"engine":"thermion","n":34,'));
      final json = jsonDecode(line.substring('BENCH '.length)) as Map;
      expect(json.keys.take(8), [
        'engine',
        'n',
        'frames',
        'fps',
        'p50_ms',
        'p90_ms',
        'p99_ms',
        'rss_mb',
      ]);
      expect(json['frames'], 300);
      expect(json['fps'], 30.0);
      expect(json['p50_ms'], 10.0);
      expect(json['rss_mb'], 321.5);
      expect(json['engine_p50_ms'], 20.0);
      expect(json['engine_frames'], 290);
    });

    test('empty window still prints valid JSON', () {
      final line = measurementLine(
        engine: 'thermion',
        n: 200,
        frameMs: const [],
        windowSeconds: 10,
        rssMb: 1,
      );
      final json = jsonDecode(line.substring('BENCH '.length)) as Map;
      expect(json['frames'], 0);
      expect(json['p50_ms'], isNull);
    });
  });

  group('sky light', () {
    final sh = hemisphereHarmonics(kSkyRadiance, kGroundRadiance);

    test('27 floats, Filament 3-band layout', () {
      expect(sh, hasLength(27));
      expect(sh.skip(6).every((c) => c == 0), isTrue);
    });

    void expectRgb(Rgb actual, Rgb expected) {
      expect(actual.r, closeTo(expected.r, 1e-6));
      expect(actual.g, closeTo(expected.g, 1e-6));
      expect(actual.b, closeTo(expected.b, 1e-6));
    }

    test('up sees the sky, down the sand, a wall their mean', () {
      expectRgb(evaluateHarmonics(sh, 0, 1, 0), kSkyRadiance);
      expectRgb(evaluateHarmonics(sh, 0, -1, 0), kGroundRadiance);
      expectRgb(
        evaluateHarmonics(sh, 1, 0, 0),
        Rgb(
          (kSkyRadiance.r + kGroundRadiance.r) / 2,
          (kSkyRadiance.g + kGroundRadiance.g) / 2,
          (kSkyRadiance.b + kGroundRadiance.b) / 2,
        ),
      );
    });
  });
}
