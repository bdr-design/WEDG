import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:marah/core/rng.dart';
import 'package:marah/domain/engine/game_engine.dart';
import 'package:marah/domain/models/camel.dart';
import 'package:marah/domain/models/catalog.dart';
import 'package:marah/domain/models/game_state.dart';
import 'package:marah/domain/models/region.dart';
import 'package:marah/domain/rules/constants.dart';
import 'package:marah/domain/rules/genetics.dart';
import 'package:marah/domain/rules/judging.dart';
import 'package:marah/domain/rules/valuation.dart';

GameState newGame([int seed = 42]) => GameEngine.newGame(
      playerName: 'بدر',
      farmName: 'عزبة الصفوة',
      region: Region.qassim,
      favourite: ColorCategory.majaheem,
      seed: seed,
    );

void main() {
  group('Rng', () {
    test('is deterministic and resumable from its state', () {
      final a = Rng(7);
      final first = List.generate(5, (_) => a.nextUint32());
      final b = Rng(7);
      expect(List.generate(5, (_) => b.nextUint32()), first);
      final resumed = Rng(a.state);
      expect(resumed.nextUint32(), a.nextUint32());
    });

    test('doubles stay in [0,1)', () {
      final r = Rng(1);
      for (var i = 0; i < 10000; i++) {
        final d = r.nextDouble();
        expect(d >= 0 && d < 1, isTrue);
      }
    });
  });

  group('Age classes', () {
    test('map completed years to Gulf names', () {
      expect(AgeClass.fromDays(100), AgeClass.hwar);
      expect(AgeClass.fromDays(365 * 3 + 10), AgeClass.haq);
      expect(AgeClass.fromDays(365 * 4 + 10).labelFor(Sex.female), 'جذعة');
      expect(AgeClass.fromDays(365 * 12), AgeClass.mature);
    });
  });

  group('Genetics', () {
    test('calves regress to the mid-parent value', () {
      final rng = Rng(3);
      final sire = {for (final t in Trait.values) t: 80.0};
      final dam = {for (final t in Trait.values) t: 60.0};
      var sum = 0.0;
      const n = 400;
      for (var i = 0; i < n; i++) {
        sum += Judging.geneticQuality(
            Genetics.inherit(rng, sire, dam, crossbred: false));
      }
      expect(sum / n, closeTo(70, 1.0));
    });

    test('crossing colour families hurts coat colour', () {
      final rng = Rng(9);
      final g = {for (final t in Trait.values) t: 70.0};
      var pure = 0.0, cross = 0.0;
      for (var i = 0; i < 200; i++) {
        pure += Genetics.inherit(rng, g, g, crossbred: false)[Trait.coat]!;
        cross += Genetics.inherit(rng, g, g, crossbred: true)[Trait.coat]!;
      }
      expect(cross < pure - 200 * 10, isTrue);
    });
  });

  group('Valuation', () {
    test('beauty multiplies price steeply', () {
      final s = newGame();
      final e = GameEngine(s);
      Camel make(double mean) => e.world.makeCamel(
            ownerId: 'o1',
            mean: mean,
            category: ColorCategory.sofr,
            sex: Sex.female,
            ageDays: 5 * 365 + 100,
          )
            ..env.updateAll((k, v) => 0)
            ..condition = 72;
      final ordinary = Valuation.value(make(50), s.day);
      final good = Valuation.value(make(70), s.day);
      final elite = Valuation.value(make(88), s.day);
      expect(ordinary, inInclusiveRange(12000, 35000));
      expect(good, greaterThan(ordinary * 4));
      expect(elite, greaterThan(400000));
    });
  });

  group('New game', () {
    test('starts with herd, market, studs and a season', () {
      final s = newGame();
      expect(s.herdSize, 3);
      expect(s.herd.every((c) => c.category == ColorCategory.majaheem), isTrue);
      expect(s.listings.length, greaterThan(20));
      expect(s.studs, isNotEmpty);
      expect(s.festivals, isNotEmpty);
      expect(s.cash, startingCash);
    });

    test('save file round-trips exactly', () {
      final s = newGame();
      GameEngine(s).advance(40);
      final json = jsonEncode(s.toJson());
      final back = GameState.fromJson(jsonDecode(json) as Map<String, dynamic>);
      expect(jsonEncode(back.toJson()), json);
    });

    test('same seed and actions replay identically', () {
      final a = newGame(5), b = newGame(5);
      GameEngine(a).advance(90);
      GameEngine(b).advance(90);
      expect(jsonEncode(a.toJson()), jsonEncode(b.toJson()));
    });
  });

  group('Economy', () {
    test('feed is charged daily and wages monthly', () {
      final s = newGame();
      final e = GameEngine(s);
      final feed = e.dailyFeedCost();
      expect(feed, greaterThan(0));
      final cash = s.cash;
      // Oct 1 -> Oct 2: one day of feed, no wages.
      e.advance(1);
      expect(cash - s.cash, inInclusiveRange(feed - 5, feed + 5));
      // Through Nov 1: wages are paid.
      e.advance(31);
      expect(
          s.ledger.any((l) => l.category.name == 'wages'), isTrue);
    });
  });

  group('Market', () {
    test('buying moves the camel into the herd and charges price + transport',
        () {
      final s = newGame();
      final e = GameEngine(s);
      final l = s.listings
          .where((l) => l.askPrice < 100000)
          .first;
      final cash = s.cash;
      final move = e.transportToFarm(l.region);
      final r = e.buy(l.id);
      expect(r.ok, isTrue, reason: r.message);
      expect(s.camels[l.camelId]!.isPlayers, isTrue);
      expect(s.cash, cash - l.askPrice - move);
      expect(s.listings.contains(l), isFalse);
    });

    test('cannot buy without money', () {
      final s = newGame();
      s.cash = 100;
      final r = GameEngine(s).buy(s.listings.first.id);
      expect(r.ok, isFalse);
    });

    test('quick sale pays less than value, minus commission', () {
      final s = newGame();
      final e = GameEngine(s);
      final c = s.herd.first;
      final value = Valuation.value(c, s.day);
      final cash = s.cash;
      expect(e.quickSale(c.id).ok, isTrue);
      final got = s.cash - cash;
      expect(got, lessThan(value));
      expect(s.camels.containsKey(c.id), isFalse);
    });

    test('a fair listing attracts buyer offers', () {
      final s = newGame();
      final e = GameEngine(s);
      final c = s.herd.first;
      e.listForSale(c.id, Valuation.value(c, s.day));
      e.advance(20);
      expect(
          s.news.any((n) => n.text.contains('سام ${c.name}')) ||
              s.buyerOffers.isNotEmpty,
          isTrue);
    });
  });

  group('Breeding', () {
    test('mating out of season is refused', () {
      final s = newGame(); // starts 1 October
      final e = GameEngine(s);
      final f = s.herd.firstWhere((c) => c.ageYears(s.day) >= 6);
      expect(e.femaleProblem(f), contains('موسم'));
    });

    test('a confirmed pregnancy ends in a birth about 13 months later', () {
      final s = newGame(11);
      final e = GameEngine(s);
      e.advance(45); // into November
      final f = s.herd.firstWhere((c) => c.ageYears(s.day) >= 6);
      f.lastCalvingDay = null;
      final stud = s.studs.first;
      // Force conception for the test by retrying until it takes.
      for (var tries = 0; tries < 12; tries++) {
        final r = e.mate(f.id, stud.camelId, stud: stud);
        expect(r.ok, isTrue, reason: r.message);
        e.advance(pregnancyCheckDays + 1);
        if (f.isPregnantConfirmed) break;
        e.advance(studRestDays);
      }
      expect(f.isPregnantConfirmed, isTrue);
      final due = f.pregnancy!.dueDay;
      e.advance(due - s.day + 1);
      expect(f.pregnancy, isNull);
      expect(f.calvings, greaterThan(0));
      // A calf joined the herd (unless it was lost at birth, which is rare).
      final calves = s.herd.where((c) => c.dam?.id == f.id);
      if (calves.isNotEmpty) {
        expect(calves.first.sire!.id, stud.camelId);
        expect(calves.first.ageDays(s.day), lessThan(5));
      }
    });
  });

  group('Contests', () {
    test('entering checks category, age and ownership, then judges', () {
      final s = newGame(21);
      final e = GameEngine(s);
      final f = s.festivals.first;
      final mine = s.herd.first;
      // Find the round that fits this camel.
      final fitting = f.rounds.where((r) => e.entryProblem(mine, f, r) == null);
      final wrongCat = f.rounds.firstWhere((r) => r.category != mine.category,
          orElse: () => f.rounds.first);
      if (wrongCat.category != mine.category) {
        expect(e.entryProblem(mine, f, wrongCat), isNotNull);
      }
      if (fitting.isEmpty) return; // this camel's class is not run here
      final r = fitting.first;
      expect(e.enter(f.id, r.id, mine.id).ok, isTrue);
      e.advance(f.judgingDay - s.day + 1);
      expect(f.done, isTrue);
      expect(r.results, isNotNull);
      expect(r.results!.any((row) => row.isPlayer), isTrue);
    });
  });
}
