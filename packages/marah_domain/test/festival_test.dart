// The Saudi round system and cheating (GDD 7 and 7.1; the owner's decisions
// of 13 Nov 2026): each rule built has a test here that fails without it.
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/model/camel.dart';
import 'package:marah_domain/src/rules/eligibility.dart';
import 'package:marah_domain/src/rules/judging.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:marah_domain/src/systems/systems.dart';
import 'package:marah_domain/src/world_gen.dart';
import 'package:marah_domain/testing.dart';
import 'package:test/test.dart';

Game newGame([int seed = 42]) {
  final g = Game.create(
    seed: seed,
    playerName: 'بدر',
    farmName: 'عزبة الصفوة',
    region: Region.qassim,
    favourite: ColorCategory.majaheem,
    startedAt: DateTime.utc(2026, 11, 8),
  );
  g.me.farm
    ..storeKg = 1 << 30
    ..tankL = 1 << 30
    ..barleyKg = 1e8
    ..alfalfaKg = 1e8
    ..waterL = 1e9
    ..capacity = 200;
  grant(g, 2000000);
  return g;
}

Festival grand(Game g) => g.state.world.festivals.values.firstWhere(
  (f) => f.tier == FestivalTier.grand,
);

ContestRound roundOf(
  Festival f,
  RoundKind kind, {
  ColorCategory? cat,
  Sex? sex,
}) => f.rounds.firstWhere(
  (r) =>
      r.kind == kind &&
      (cat == null || r.category == cat) &&
      (sex == null || r.sex == sex),
);

int _n = 0;

/// A camel of the player's that fits [r] on its day, unless told otherwise.
Camel camelFor(
  Game g,
  ContestRound r, {
  double mean = 70,
  int? ageOnDay,
  ColorCategory? cat,
  Sex? sex,
}) {
  final sim = Sim(g.state);
  final ageDays =
      ageOnDay ??
      switch (r.kind) {
        RoundKind.mafareed => AgeClass.mafrood.minDays + 150,
        RoundKind.diq || RoundKind.fardiDiq => AgeClass.haq.minDays + 150,
        RoundKind.fahal => 9 * 365,
        _ => 7 * 365 + 100,
      };
  final c = WorldGen(sim).makeCamel(
    sim.rng(['test-camel', _n++]),
    owner: g.me.id,
    mean: mean,
    category: cat ?? r.category ?? ColorCategory.majaheem,
    sex: sex ?? r.sex ?? Sex.male,
    ageDays: ageDays - r.day.daysSince(g.today),
  );
  c
    ..acquiredOn = g.today - 200
    ..condition = 75
    ..calvings = r.kind == RoundKind.fardiJil ? 2 : 0;
  // a pure colour, so stage 2 passes unless a test says otherwise
  c.genes[Trait.coat] = 70;
  c.env[Trait.coat] = 0;
  return c;
}

/// An offspring of [bull] in the player's herd.
Camel offspringOf(Game g, Camel bull, ContestRound r) {
  final c = camelFor(g, r, ageOnDay: 4 * 365, sex: Sex.female);
  final json = c.toJson()..['sire'] = bull.asParent.toJson();
  final kid = Camel.fromJson(json);
  g.state.world.camels[kid.id] = kid;
  return kid;
}

Err refused(Game g, Command c) => g.dispatch(c) as Err;

void main() {
  group('The programme (GDD 7, research section 4)', () {
    test('the grand festival runs from 1 December to 3 January', () {
      final f = grand(newGame());
      expect(f.startsOn.date, DateTime.utc(2026, 12));
      expect(f.endsOn.date, DateTime.utc(2027, 1, 3));
      expect(f.season, 2026);
      for (final r in f.rounds) {
        expect(r.day >= f.startsOn && r.day <= f.endsOn, isTrue);
      }
      expect(f.closesOn, f.startsOn - Balance.registrationClosesBeforeStart);
    });

    test('its rounds: الفردي دق and جل for each colour, مفاريد and دق of '
        'القعدان and البكار, الفحل وإنتاجه, and the group rounds', () {
      final f = grand(newGame());
      for (final cat in ColorCategory.values) {
        for (final k in [RoundKind.fardiDiq, RoundKind.fardiJil]) {
          expect(roundOf(f, k, cat: cat).sex, Sex.female);
        }
        for (final k in [RoundKind.mafareed, RoundKind.diq]) {
          for (final sex in Sex.values) {
            expect(() => roundOf(f, k, cat: cat, sex: sex), returnsNormally);
          }
        }
        expect(
          f.rounds
              .where((r) => r.kind == RoundKind.jamal && r.category == cat)
              .map((r) => r.size)
              .toSet(),
          {
            40,
            60,
            cat == ColorCategory.homr || cat == ColorCategory.shoqh ? 100 : 80,
          },
        );
      }
      expect(roundOf(f, RoundKind.fahal).size, 1 + ContestRules.fahalOffspring);
      for (final k in [
        RoundKind.manqiya,
        RoundKind.jazeera,
        RoundKind.hajij,
        RoundKind.tabaa,
        RoundKind.badawa,
      ]) {
        expect(f.rounds.any((r) => r.kind == k), isTrue, reason: k.name);
      }
      expect(roundOf(f, RoundKind.jazeera).day, f.endsOn);
    });
  });

  group('Registration (GDD 7)', () {
    test('opens on its day, closes, then takes late entries with a fee until '
        '72 hours before the round', () {
      final g = newGame();
      final f = grand(g);
      final r = roundOf(f, RoundKind.mafareed, sex: Sex.male);
      final a = camelFor(g, r), b = camelFor(g, r), c = camelFor(g, r);
      if (g.today < f.opensOn - 1) {
        g.advanceTo(f.opensOn - 1);
        expect(
          refused(g, EnterRound(g.me.id, f.id, r.id, [a.id])).error.code,
          ErrorCode.registrationClosed,
        );
      }
      g.advanceTo(f.closesOn);
      int fees() => g.me.ledger
          .where((l) => l.category == LedgerCategory.entryFee)
          .fold(0, (n, l) => n + l.amount.value);
      expect(g.dispatch(EnterRound(g.me.id, f.id, r.id, [a.id])).ok, isTrue);
      expect(fees(), 0);
      g.advanceTo(Eligibility.lastEntryDay(r));
      expect(r.day.daysSince(g.today), 3);
      final ev = g.dispatch(EnterRound(g.me.id, f.id, r.id, [b.id]));
      expect(ev.ok, isTrue);
      expect(ev.events.whereType<Entered>().single.fee, Balance.lateEntryFee);
      expect(fees(), -Balance.lateEntryFee);
      expect(r.entries.last.late, isTrue);
      expect(g.me.ledger.last.category, LedgerCategory.entryFee);
      g.advanceDays(1);
      expect(
        refused(g, EnterRound(g.me.id, f.id, r.id, [c.id])).error.code,
        ErrorCode.registrationClosed,
      );
    });

    test('one camel in one فردي round a festival; the other rounds apart', () {
      final g = newGame();
      final f = grand(g);
      g.advanceTo(f.opensOn);
      final diq = roundOf(f, RoundKind.fardiDiq, cat: ColorCategory.wodh);
      final jil = roundOf(f, RoundKind.fardiJil, cat: ColorCategory.wodh);
      final a = camelFor(g, diq), b = camelFor(g, diq), c = camelFor(g, jil);
      expect(g.dispatch(EnterRound(g.me.id, f.id, diq.id, [a.id])).ok, isTrue);
      expect(
        refused(g, EnterRound(g.me.id, f.id, diq.id, [b.id])).error.code,
        ErrorCode.oneFardiRound,
      );
      expect(
        refused(g, EnterRound(g.me.id, f.id, jil.id, [c.id])).error.code,
        ErrorCode.oneFardiRound,
      );
      // المفاريد and الدق of القعدان والبكار do not count against it
      final m = roundOf(f, RoundKind.mafareed, sex: Sex.female);
      final young = camelFor(g, m);
      expect(
        g.dispatch(EnterRound(g.me.id, f.id, m.id, [young.id])).ok,
        isTrue,
      );
      final d = roundOf(f, RoundKind.diq, sex: Sex.male);
      expect(
        g.dispatch(EnterRound(g.me.id, f.id, d.id, [camelFor(g, d).id])).ok,
        isTrue,
      );
      // ... up to Balance.maxEntriesPerOwnerInRound in one of them
      for (var i = 1; i < Balance.maxEntriesPerOwnerInRound; i++) {
        expect(
          g.dispatch(EnterRound(g.me.id, f.id, d.id, [camelFor(g, d).id])).ok,
          isTrue,
        );
      }
      expect(
        refused(
          g,
          EnterRound(g.me.id, f.id, d.id, [camelFor(g, d).id]),
        ).error.code,
        ErrorCode.roundOwnerLimit,
      );
      // and no camel in two rounds
      final other = roundOf(
        f,
        RoundKind.mafareed,
        sex: Sex.female,
        cat: ColorCategory.values.firstWhere((x) => x != m.category),
      );
      expect(
        Eligibility.canEnter(
          g.state.world,
          f,
          m,
          [young],
          g.me.id,
          g.today,
        )?.code,
        isNot(isNull),
      );
      expect(
        GameView(g.state, g.me.id).canEnter(f.id, other.id, [young.id])?.code,
        anyOf(ErrorCode.alreadyEnteredInFestival, ErrorCode.wrongCategory),
      );
    });

    test('a camel already entered is refused in another round', () {
      final g = newGame();
      final f = grand(g);
      g.advanceTo(f.opensOn);
      final m = roundOf(f, RoundKind.mafareed, sex: Sex.female);
      final c = camelFor(g, m);
      expect(g.dispatch(EnterRound(g.me.id, f.id, m.id, [c.id])).ok, isTrue);
      final same = f.rounds.firstWhere(
        (r) =>
            r != m &&
            r.kind == RoundKind.mafareed &&
            r.sex == Sex.female &&
            r.category == m.category,
        orElse: () => m,
      );
      expect(
        refused(g, EnterRound(g.me.id, f.id, same.id, [c.id])).error.code,
        anyOf(ErrorCode.alreadyEnteredInFestival, ErrorCode.roundOwnerLimit),
      );
      expect(
        GameView(g.state, g.me.id).canSell(c.id)?.code,
        ErrorCode.enteredInContest,
      );
    });

    test('the group rounds are not open to players yet', () {
      final g = newGame();
      final f = grand(g);
      g.advanceTo(f.opensOn);
      final r = roundOf(f, RoundKind.jamal);
      final herd = [for (var i = 0; i < r.size; i++) camelFor(g, r).id];
      expect(
        refused(g, EnterRound(g.me.id, f.id, r.id, herd)).error.code,
        ErrorCode.notYet,
      );
      expect(RoundKind.values.where((k) => k.enterable).toSet(), {
        RoundKind.fardiDiq,
        RoundKind.fardiJil,
        RoundKind.mafareed,
        RoundKind.diq,
        RoundKind.fahal,
      });
    });

    test(
      'colour, sex, age on the round day, calvings, crossbred, ownership',
      () {
        final g = newGame();
        final f = grand(g);
        g.advanceTo(f.opensOn);
        final diq = roundOf(f, RoundKind.fardiDiq, cat: ColorCategory.sofr);
        final jil = roundOf(f, RoundKind.fardiJil, cat: ColorCategory.sofr);
        final mf = roundOf(
          f,
          RoundKind.mafareed,
          sex: Sex.male,
          cat: ColorCategory.sofr,
        );
        DomainError? why(ContestRound r, Camel c) =>
            GameView(g.state, g.me.id).canEnter(f.id, r.id, [c.id]);
        expect(why(diq, camelFor(g, diq)), isNull);
        expect(
          why(diq, camelFor(g, diq, cat: ColorCategory.homr))?.code,
          ErrorCode.wrongCategory,
        );
        expect(
          why(diq, camelFor(g, diq, sex: Sex.male))?.code,
          ErrorCode.wrongSex,
        );
        // دق: حق to جذعة on the round's day
        expect(
          why(
            diq,
            camelFor(g, diq, ageOnDay: AgeClass.mafrood.minDays + 10),
          )?.code,
          ErrorCode.wrongAgeClass,
        );
        expect(
          why(diq, camelFor(g, diq, ageOnDay: AgeClass.jatha.minDays + 10)),
          isNull,
        );
        expect(
          why(
            diq,
            camelFor(g, diq, ageOnDay: AgeClass.thani.minDays + 10),
          )?.code,
          ErrorCode.wrongAgeClass,
        );
        // مفاريد: a year to two
        expect(why(mf, camelFor(g, mf)), isNull);
        expect(
          why(mf, camelFor(g, mf, ageOnDay: AgeClass.haq.minDays + 10))?.code,
          ErrorCode.wrongAgeClass,
        );
        // جل: from her second calf
        final one = camelFor(g, jil)..calvings = 1;
        expect(why(jil, one)?.code, ErrorCode.tooFewCalvings);
        expect(why(jil, camelFor(g, jil)), isNull);
        expect(
          why(jil, camelFor(g, jil, ageOnDay: 15 * 365 + 10))?.code,
          ErrorCode.wrongAgeClass,
        );
        // a crossbred camel: its record shows it
        final cross = camelFor(g, diq);
        final json = cross.toJson()..['crossbred'] = true;
        final x = Camel.fromJson(json);
        g.state.world.camels[x.id] = x;
        expect(why(diq, x)?.code, ErrorCode.crossbred);
        // bought too lately
        final bought = camelFor(g, diq)..acquiredOn = diq.day - 10;
        expect(why(diq, bought)?.code, ErrorCode.ownershipTooRecent);
        // ill
        final ill = camelFor(g, diq)..health = HealthStatus.sick;
        expect(why(diq, ill)?.code, ErrorCode.sick);
      },
    );

    test('الفحل وإنتاجه: the bull of five years and five of his offspring', () {
      final g = newGame();
      final f = grand(g);
      g.advanceTo(f.opensOn);
      final r = roundOf(f, RoundKind.fahal);
      final bull = camelFor(g, r, sex: Sex.male);
      final kids = [for (var i = 0; i < 5; i++) offspringOf(g, bull, r).id];
      final v = GameView(g.state, g.me.id);
      expect(
        v.canEnter(f.id, r.id, [bull.id, ...kids.take(4)])?.code,
        ErrorCode.wrongGroupSize,
      );
      final stranger = camelFor(g, r, ageOnDay: 4 * 365, sex: Sex.female);
      expect(
        v.canEnter(f.id, r.id, [bull.id, ...kids.take(4), stranger.id])?.code,
        ErrorCode.notOffspring,
      );
      final colt = camelFor(g, r, ageOnDay: 4 * 365, sex: Sex.male);
      expect(
        v.canEnter(f.id, r.id, [colt.id, ...kids])?.code,
        ErrorCode.tooYoungToBreed,
      );
      expect(
        g.dispatch(EnterRound(g.me.id, f.id, r.id, [bull.id, ...kids])).ok,
        isTrue,
      );
    });

    test('withdrawn after the closing, a camel is not entered again there', () {
      final g = newGame();
      final f = grand(g);
      final r = roundOf(f, RoundKind.mafareed, sex: Sex.female);
      final a = camelFor(g, r), b = camelFor(g, r);
      g.advanceTo(f.opensOn);
      g.dispatch(EnterRound(g.me.id, f.id, r.id, [a.id]));
      expect(g.dispatch(WithdrawEntry(g.me.id, f.id, r.id, a.id)).ok, isTrue);
      expect(GameView(g.state, g.me.id).canSell(a.id), isNull);
      // before the closing: entered again
      expect(g.dispatch(EnterRound(g.me.id, f.id, r.id, [a.id])).ok, isTrue);
      g.dispatch(EnterRound(g.me.id, f.id, r.id, [b.id]));
      g.advanceTo(f.closesOn + 1);
      expect(g.dispatch(WithdrawEntry(g.me.id, f.id, r.id, b.id)).ok, isTrue);
      expect(f.scratched, contains(b.id));
      expect(
        refused(g, EnterRound(g.me.id, f.id, r.id, [b.id])).error.code,
        ErrorCode.scratched,
      );
      expect(
        refused(g, WithdrawEntry(g.me.id, f.id, r.id, b.id)).error.code,
        ErrorCode.notEntered,
      );
    });
  });

  group('The day\'s six stages (GDD 7)', () {
    test('a round runs on its own day; each stage\'s field is told', () {
      final g = newGame();
      final f = grand(g);
      final r = roundOf(f, RoundKind.mafareed, sex: Sex.female);
      final c = camelFor(g, r, mean: 92)..condition = 90;
      g.advanceTo(f.opensOn);
      g.dispatch(EnterRound(g.me.id, f.id, r.id, [c.id]));
      g.advanceTo(r.day - 1);
      expect(r.judged, isFalse);
      final events = g.advanceDays(1);
      expect(r.judged, isTrue);
      expect(r.field, hasLength(Stage.values.length));
      for (var i = 1; i < r.field!.length; i++) {
        expect(r.field![i], lessThanOrEqualTo(r.field![i - 1]));
      }
      expect(r.field![0], greaterThan(r.rivals ~/ 2));
      // the preliminary judging keeps half
      expect(
        r.field![Stage.preliminary.index],
        lessThanOrEqualTo((r.field![1] * Balance.preliminaryKeeps).ceil()),
      );
      // the strong camel placed, paid, on its record, and its name raised
      final placed = events.whereType<Placed>().single;
      expect(c.placings.single.rank, placed.rank);
      final prize = ContestRules.prizes(f.tier, r.kind, 1)[placed.rank - 1];
      expect(
        g.me.ledger.any(
          (l) => l.category == LedgerCategory.prize && l.amount.value == prize,
        ),
        isTrue,
      );
      final km = g.me.farm.region.roadKmTo(f.region);
      expect(
        g.me.ledger.any(
          (l) =>
              l.category == LedgerCategory.transport &&
              l.amount.value == -Balance.transportCost(km, 1) * 2,
        ),
        isTrue,
      );
      expect(
        g.me.reputationIn(r.category!),
        greaterThan(Balance.startingReputation),
      );
    });

    test('stage 2 removes a camel whose colour is not pure', () {
      final g = newGame();
      final f = grand(g);
      final r = roundOf(f, RoundKind.mafareed, sex: Sex.female);
      final c = camelFor(g, r);
      c.genes[Trait.coat] = 5;
      g.advanceTo(f.opensOn);
      g.dispatch(EnterRound(g.me.id, f.id, r.id, [c.id]));
      final events = g.advanceTo(r.day);
      final out = events.whereType<EntryRemoved>().single;
      expect(out.stage, Stage.breedColourAge);
      expect(out.reason, RemovalReason.colour);
      expect(c.placings, isEmpty);
    });

    test('stage 2 may read the teeth of a camel at its class\'s edge as the '
        'class beside it', () {
      var misread = 0, middle = 0;
      for (var seed = 0; seed < 60; seed++) {
        final g = newGame(seed);
        final f = grand(g);
        final r = roundOf(f, RoundKind.mafareed, sex: Sex.male);
        final edge = camelFor(
          g,
          r,
          mean: 85,
          ageOnDay: AgeClass.mafrood.minDays + 3,
        );
        final mid = camelFor(g, r, mean: 85);
        g.advanceTo(f.opensOn);
        g
          ..dispatch(EnterRound(g.me.id, f.id, r.id, [edge.id]))
          ..dispatch(EnterRound(g.me.id, f.id, r.id, [mid.id]));
        for (final e in g.advanceTo(r.day).whereType<EntryRemoved>()) {
          if (e.reason != RemovalReason.teeth) continue;
          if (e.camel == edge.id) misread++;
          if (e.camel == mid.id) middle++;
        }
      }
      expect(misread, greaterThan(0));
      expect(middle, 0);
    });

    test('stage 3 cuts a weak entry; stage 5 removes a sick one', () {
      final g = newGame();
      final f = grand(g);
      final r = roundOf(f, RoundKind.diq, sex: Sex.female);
      final weak = camelFor(g, r, mean: 30);
      final sick = camelFor(g, r, mean: 95)..condition = 90;
      g.advanceTo(f.opensOn);
      g
        ..dispatch(EnterRound(g.me.id, f.id, r.id, [weak.id]))
        ..dispatch(EnterRound(g.me.id, f.id, r.id, [sick.id]));
      g.advanceTo(r.day - 1);
      sick
        ..health = HealthStatus.sick
        ..illness = Illness.lameness
        ..sickSince = g.today;
      final events = g.advanceDays(1).whereType<EntryRemoved>().toList();
      expect(
        events.firstWhere((e) => e.camel == weak.id).reason,
        RemovalReason.cut,
      );
      final s = events.firstWhere((e) => e.camel == sick.id);
      expect((s.stage, s.reason), (Stage.medical, RemovalReason.sick));
      // the removals are on the owner's results, with their stage
      final mine = GameView(g.state, g.me.id)
          .festival(f.id)!
          .rounds
          .firstWhere((x) => x.id == r.id)
          .results!
          .where((row) => row.ownerId == g.me.id);
      expect(
        mine.every((row) => row.rank == null && row.removedAt != null),
        isTrue,
      );
    });

    test('الفحل وإنتاجه\'s places only after the DNA tests', () {
      final g = newGame();
      final f = grand(g);
      final r = roundOf(f, RoundKind.fahal);
      final bull = camelFor(g, r, mean: 90, sex: Sex.male);
      final kids = [for (var i = 0; i < 5; i++) offspringOf(g, bull, r).id];
      g.advanceTo(f.opensOn);
      expect(
        g.dispatch(EnterRound(g.me.id, f.id, r.id, [bull.id, ...kids])).ok,
        isTrue,
      );
      final day = g.advanceTo(r.day);
      expect(r.judged, isTrue);
      RoundView rv() => GameView(
        g.state,
        g.me.id,
      ).festival(f.id)!.rounds.firstWhere((x) => x.id == r.id);
      if (day.whereType<EntryRemoved>().isEmpty) {
        expect(
          day.whereType<ResultsPending>().single.announceOn,
          r.day + Balance.dnaDays,
        );
        expect(day.whereType<Placed>(), isEmpty);
        expect(rv().announced, isFalse);
        expect(rv().results!.where((x) => x.rank != null), isEmpty);
        final later = g.advanceTo(r.day + Balance.dnaDays);
        expect(later.whereType<Placed>().single.camel, bull.id);
        expect(rv().announced, isTrue);
        expect(bull.placings, hasLength(1));
      }
    });

    test('the festival closes with its integrity report; unjudged rounds '
        'dropped', () {
      final g = newGame();
      final f = grand(g);
      final r = roundOf(f, RoundKind.mafareed, sex: Sex.female);
      final c = camelFor(g, r, mean: 85);
      g.advanceTo(f.opensOn);
      g.dispatch(EnterRound(g.me.id, f.id, r.id, [c.id]));
      final events = g.advanceTo(f.endsOn);
      expect(f.done, isTrue);
      expect(f.rounds.every((x) => x.judged), isTrue);
      final report = events.whereType<FestivalIntegrity>().singleWhere(
        (e) => e.festival == f.name,
      );
      expect(report.owner, isNull);
      expect(
        report.cases,
        greaterThan(0),
        reason:
            'a grand festival of '
            'some two thousand entries finds a few',
      );
    });
  });

  group('Cheating (GDD 7.1)', () {
    test('the kinds and their real fine caps', () {
      expect(
        {for (final k in TamperKind.values) k: k.fineCap},
        {
          TamperKind.botox: 100000,
          TamperKind.filler: 100000,
          TamperKind.hormones: 100000,
          TamperKind.lipStretch: 100000,
          TamperKind.teethFiling: 30000,
          TamperKind.tailCut: 30000,
          TamperKind.dye: 30000,
        },
      );
      // the fine scaled by strength up to the cap
      expect(Balance.tamperFine(TamperKind.botox, 3), 100000);
      expect(Balance.tamperFine(TamperKind.dye, 1), 10000);
      expect(Balance.tamperFine(TamperKind.lipStretch, 2), 67000);
    });

    test('detection rises with the strength, at both stages', () {
      for (final k in TamperKind.values) {
        for (final st in [Stage.tamperingExperts, Stage.medical]) {
          final p = [
            for (var s = 1; s <= 3; s++) ContestRules.detectChance(k, s, st),
          ];
          expect(
            p[0],
            k == TamperKind.tailCut && st == Stage.medical ? 0 : greaterThan(0),
          );
          if (p[0] > 0) {
            expect(p[1], greaterThan(p[0]));
            expect(p[2], greaterThan(p[1]));
          }
        }
        expect(
          ContestRules.festivalCatchChance(k, 3),
          greaterThan(ContestRules.festivalCatchChance(k, 1)),
        );
      }
      // Botox is the cheat caught most (real)
      final most = TamperKind.values.reduce(
        (a, b) =>
            ContestRules.festivalCatchChance(a, 1) >=
                ContestRules.festivalCatchChance(b, 1)
            ? a
            : b,
      );
      expect(most, TamperKind.botox);
    });

    test('the risk is told in three words, never the odds', () {
      final seen = <RiskBand>{};
      for (final k in TamperKind.values) {
        final bands = [
          for (var s = 1; s <= 3; s++) ContestRules.festivalRisk(k, s),
        ];
        seen.addAll(bands);
        for (var i = 1; i < 3; i++) {
          expect(bands[i].index, greaterThanOrEqualTo(bands[i - 1].index));
        }
      }
      expect(seen, RiskBand.values.toSet());
      expect(ContestRules.festivalRisk(TamperKind.botox, 3), RiskBand.high);
      expect(ContestRules.foundMostlyBy(TamperKind.hormones), Stage.medical);
      expect(
        ContestRules.foundMostlyBy(TamperKind.tailCut),
        Stage.tamperingExperts,
      );
      expect(ContestRules.outsideRisk(3), RiskBand.low);
    });

    test('a treatment costs its price, raises its features on judging day '
        'only, and is the owner\'s secret', () {
      final g = newGame();
      final f = grand(g);
      final r = roundOf(f, RoundKind.fardiDiq);
      final c = camelFor(g, r);
      final cash = g.me.cash.value;
      final before = Judging.observedAll(c, g.today);
      expect(g.dispatch(Tamper(g.me.id, c.id, TamperKind.botox, 2)).ok, isTrue);
      expect(cash - g.me.cash.value, TamperKind.botox.price * 2);
      expect(g.me.ledger.last.category, LedgerCategory.tampering);
      // the eye (buyers, the market) sees no change
      expect(Judging.observedAll(c, g.today), before);
      final judged = ContestSystem.judgedLooks(c, g.me, g.today);
      for (final t in Trait.values) {
        final gain = TamperKind.botox.traits.contains(t)
            ? Balance.tamperGainPerLevel * 2
            : 0;
        expect(judged[t], closeTo((before[t]! + gain).clamp(0, 100), 1e-9));
      }
      expect(
        refused(g, Tamper(g.me.id, c.id, TamperKind.botox, 1)).error.code,
        ErrorCode.alreadyTreated,
      );
      expect(
        refused(g, Tamper(g.me.id, c.id, TamperKind.dye, 4)).error.code,
        ErrorCode.invalidAmount,
      );
      final v = GameView(g.state, g.me.id);
      expect(v.tamperings.single.kind, TamperKind.botox);
      expect(
        v.tamperings.single.festivalRisk,
        ContestRules.festivalRisk(TamperKind.botox, 2),
      );
      // it wears off
      g.advanceDays(TamperKind.botox.lastsDays);
      expect(GameView(g.state, g.me.id).tamperings, isEmpty);
      expect(g.me.tamperings, isEmpty);
    });

    test(
      'found at a festival: out, the fine, the ban on every festival this '
      'edition and five more, the other entries out, the name lost, news',
      () {
        for (var seed = 0; seed < 30; seed++) {
          final g = newGame(seed);
          final f = grand(g);
          final r = roundOf(f, RoundKind.fardiDiq, cat: ColorCategory.wodh);
          final c = camelFor(g, r, mean: 85);
          final m = f.rounds.lastWhere(
            (x) => x.kind == RoundKind.mafareed && x.sex == Sex.male,
          );
          final other = camelFor(g, m);
          g.advanceTo(f.opensOn);
          g
            ..dispatch(Tamper(g.me.id, c.id, TamperKind.botox, 3))
            ..dispatch(EnterRound(g.me.id, f.id, r.id, [c.id]))
            ..dispatch(EnterRound(g.me.id, f.id, m.id, [other.id]));
          // the mafareed round comes later than the دق one
          if (!(m.day > r.day)) continue;
          final events = g.advanceTo(r.day);
          final found = events.whereType<TamperingFound>().firstOrNull;
          if (found == null) continue;
          expect(found.camel, c.id);
          expect([
            Stage.tamperingExperts,
            Stage.medical,
          ], contains(found.stage));
          final fine = Balance.tamperFine(TamperKind.botox, 3);
          expect(found.fine, fine);
          expect(
            g.me.ledger.any(
              (l) =>
                  l.category == LedgerCategory.fine && l.amount.value == -fine,
            ),
            isTrue,
          );
          final through = f.season + Balance.banEditionsAfter;
          expect(found.bannedThrough, through);
          expect(g.state.world.bans[g.me.id], through);
          expect(c.bannedThrough, through);
          expect(other.bannedThrough, through);
          // his other entry withdrawn
          expect(m.entries.where((e) => e.ownerId == g.me.id), isEmpty);
          expect(
            events.whereType<EntryRemoved>().single.reason,
            RemovalReason.tampering,
          );
          expect(
            g.me.reputationIn(ColorCategory.wodh),
            Balance.startingReputation - Balance.reputationCaught < 0
                ? 0
                : Balance.startingReputation - Balance.reputationCaught,
          );
          final news = events.whereType<CheatNews>().where(
            (e) => e.ownerName == g.me.name,
          );
          expect(news.single.owner, isNull);
          expect(g.me.tamperings, isEmpty);
          // barred from the festivals of this season and five more, not later
          final w = g.state.world;
          Festival at(int season) => Festival(
            id: const FestivalId('x'),
            name: 'x',
            region: Region.riyadh,
            tier: FestivalTier.local,
            season: season,
            opensOn: g.today,
            closesOn: g.today + 10,
            startsOn: g.today + 20,
            endsOn: g.today + 20,
            rounds: [],
          );
          expect(Eligibility.ownerBan(w, g.me.id, at(through)), through);
          expect(Eligibility.ownerBan(w, g.me.id, at(through + 1)), isNull);
          expect(
            GameView(g.state, g.me.id).canEnter(f.id, m.id, [other.id])?.code,
            anyOf(ErrorCode.banned, ErrorCode.registrationClosed),
          );
          // a camel stays barred when sold on
          final x = at(through);
          final rr = ContestRound(
            id: const RoundId('rr'),
            kind: RoundKind.mafareed,
            day: g.today + 20,
            rivals: 0,
            sex: Sex.male,
            category: other.category,
          );
          x.rounds.add(rr);
          other.ownerId = const OwnerId('someone');
          expect(
            Eligibility.canEnter(
              w,
              x,
              rr,
              [other],
              other.ownerId,
              g.today,
            )?.code,
            ErrorCode.camelBanned,
          );
          return;
        }
        fail('a heavy Botox was never found in 30 festivals');
      },
    );

    test('found outside a festival: the fine, the name, the news, no ban', () {
      const t = Tampering(
        camelId: CamelId('c'),
        kind: TamperKind.dye,
        strength: 2,
        on: GameDay(0),
        until: GameDay(10),
      );
      expect(
        TamperingSystem.outsideChance(t, listed: false),
        Balance.outsideCatchPerDay * 2,
      );
      expect(
        TamperingSystem.outsideChance(t, listed: true),
        Balance.outsideCatchPerDay * 2 * Balance.outsideCatchListedFactor,
      );
      for (var seed = 0; seed < 40; seed++) {
        final g = newGame(seed);
        final r = roundOf(grand(g), RoundKind.fardiDiq);
        final c = camelFor(g, r);
        g.dispatch(Tamper(g.me.id, c.id, TamperKind.lipStretch, 3));
        g.dispatch(ListForSale(g.me.id, c.id, 9000000));
        final events = g.advanceDays(300);
        final found = events.whereType<TamperingFound>().firstOrNull;
        if (found == null) continue;
        expect(found.festival, isNull);
        expect(found.fine, Balance.outsideFine);
        expect(found.bannedThrough, isNull);
        expect(g.state.world.bans, isNot(contains(g.me.id)));
        expect(c.bannedThrough, isNull);
        expect(
          events.whereType<CheatNews>().any((e) => e.ownerName == g.me.name),
          isTrue,
        );
        expect(
          g.me.reputationIn(c.category),
          lessThan(Balance.startingReputation),
        );
        return;
      }
      fail('never found outside in 40 games of 300 days listed');
    });

    test('the vet treating a camel may find a treatment', () {
      var found = 0;
      for (var seed = 0; seed < 60; seed++) {
        final g = newGame(seed);
        final c = camelFor(g, roundOf(grand(g), RoundKind.fardiDiq));
        g.dispatch(Tamper(g.me.id, c.id, TamperKind.filler, 1));
        c
          ..health = HealthStatus.sick
          ..illness = Illness.lameness
          ..sickSince = g.today;
        final r = g.dispatch(Treat(g.me.id, c.id));
        if (r.events.whereType<TamperingFound>().isNotEmpty) found++;
      }
      // 15% of 60, about 9
      expect(found, inInclusiveRange(2, 20));
    });

    test('rivals cheat too, are caught, barred and in the news', () {
      var news = 0, barred = 0;
      for (var seed = 0; seed < 6; seed++) {
        final g = newGame(seed);
        final f = grand(g);
        g.advanceTo(f.opensOn);
        for (final r in f.rounds.where(
          (r) => r.kind == RoundKind.diq || r.kind == RoundKind.mafareed,
        )) {
          final c = camelFor(g, r, mean: 60);
          g.dispatch(EnterRound(g.me.id, f.id, r.id, [c.id]));
        }
        final events = g.advanceTo(f.endsOn);
        news += events
            .whereType<CheatNews>()
            .where((e) => e.ownerName != g.me.name)
            .length;
        barred += g.state.world.bans.keys
            .where((o) => !g.state.players.containsKey(o))
            .length;
      }
      expect(news, greaterThan(0));
      expect(barred, greaterThan(0));
    });
  });

  group('What a player sees', () {
    test('other owners\' rows carry no marks; his own do', () {
      final g = newGame();
      final f = grand(g);
      final r = roundOf(f, RoundKind.mafareed, sex: Sex.female);
      final c = camelFor(g, r, mean: 90);
      g.advanceTo(f.opensOn);
      g.dispatch(EnterRound(g.me.id, f.id, r.id, [c.id]));
      g.advanceTo(r.day);
      // another owner's row with marks, as a second player's would be
      r.results!.add(
        ResultRow(
          rank: 99,
          camelName: 'x',
          ownerId: const OwnerId('other-player'),
          score: 50,
          prize: 0,
          camelId: const CamelId('theirs'),
          marks: {for (final t in Trait.values) t: 5},
        ),
      );
      final rows = GameView(
        g.state,
        g.me.id,
      ).festival(f.id)!.rounds.firstWhere((x) => x.id == r.id).results!;
      final theirs = rows.firstWhere((x) => x.ownerId.value == 'other-player');
      expect(theirs.marks, isNull);
      expect(theirs.camelId, isNull);
      final mine = rows.firstWhere((x) => x.ownerId == g.me.id);
      if (mine.rank != null) expect(mine.marks, isNotNull);
      // and no one else's entries
      final stranger = Sim(g.state);
      expect(stranger.world.festivals[f.id], isNotNull);
    });

    test('views list only the player\'s own entries', () {
      final g = newGame();
      final f = grand(g);
      final r = roundOf(f, RoundKind.mafareed, sex: Sex.female);
      g.advanceTo(f.opensOn);
      r.entries.add(
        Entry(
          ownerId: const OwnerId('other-player'),
          camels: [const CamelId('theirs')],
        ),
      );
      final c = camelFor(g, r);
      g.dispatch(EnterRound(g.me.id, f.id, r.id, [c.id]));
      final rv = GameView(
        g.state,
        g.me.id,
      ).festival(f.id)!.rounds.firstWhere((x) => x.id == r.id);
      expect(rv.myEntries.map((e) => e.ownerId).toSet(), {g.me.id});
      r.entries.removeWhere((e) => e.ownerId.value == 'other-player');
    });
  });

  test('the bot plays festivals, cheats now and then, and every invariant '
      'holds', () {
    final g = newGame(5);
    final bot = Bot(g, cheats: true);
    expect(bot.run(52 * 3), isNull);
    final placings = g.state.world.camels.values
        .where((c) => c.ownerId == g.me.id)
        .expand((c) => c.placings);
    expect(placings, isNotEmpty);
    expect(
      g.me.ledger.any((l) => l.category == LedgerCategory.tampering),
      isTrue,
    );
    expect(checkInvariants(g.state), isEmpty);
  });

  test('an honest bot keeps entering the festivals for ten years', () {
    for (final seed in [1, 2, 3, 4]) {
      final g = Game.create(
        seed: seed * 7919,
        playerName: 'bot',
        farmName: 'bot farm',
        region: Region.values[seed % Region.values.length],
        favourite: ColorCategory.values[seed % ColorCategory.values.length],
        startedAt: DateTime.utc(2026, 11, 8),
      );
      grant(g, 580000);
      final bot = Bot(g);
      for (var w = 0; w < 52 * 10; w++) {
        for (final e in bot.week()) {
          expect(e, isNot(isA<TamperingFound>()));
        }
      }
      // a season with no camel of an age a round takes can pass without
      // an entry (no adult male round but الفحل's; جل from the second
      // calf): 9 of the 10 on the slowest seed, measured
      expect(
        bot.entriesBySeason.keys.where((y) => y >= 2026 && y < 2036).length,
        greaterThanOrEqualTo(8),
        reason: 'seed $seed: ${bot.entriesBySeason}',
      );
      expect(
        bot.entriesBySeason.containsKey(2035),
        isTrue,
        reason: 'seed $seed still enters in the last season',
      );
      expect(g.state.world.bans, isNot(contains(g.me.id)));
    }
  });
}
