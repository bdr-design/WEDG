// The Saudi round system and cheating (GDD 7 and 7.1; the owner's decisions
// of 13 Nov 2026): each rule built has a test here that fails without it.
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/handlers/handlers.dart' as handlers;
import 'package:marah_domain/src/model/camel.dart';
import 'package:marah_domain/src/rules/eligibility.dart';
import 'package:marah_domain/src/rules/judging.dart';
import 'package:marah_domain/src/rules/valuation.dart';
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
Camel offspringOf(Game g, Camel bull, ContestRound r, {double mean = 70}) {
  final c = camelFor(g, r, ageOnDay: 4 * 365, sex: Sex.female, mean: mean);
  final json = c.toJson()..['sire'] = bull.asParent.toJson();
  final kid = Camel.fromJson(json);
  g.state.world.camels[kid.id] = kid;
  return kid;
}

Err refused(Game g, Command c) => g.dispatch(c) as Err;

Sim sim(Game g) => Sim(g.state);

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
      // a festival whose registration opens after the game starts
      final f = g.state.world.festivals.values.firstWhere(
        (f) => f.opensOn > g.today + 1 && f.tier != FestivalTier.local,
      );
      final r = roundOf(f, RoundKind.mafareed, sex: Sex.male);
      final a = camelFor(g, r), b = camelFor(g, r), c = camelFor(g, r);
      g.advanceTo(f.opensOn - 1);
      expect(
        refused(g, EnterRound(g.me.id, f.id, r.id, [a.id])).error.code,
        ErrorCode.registrationClosed,
      );
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
      // a bull and offspring well above the field, so the entry reaches the
      // final judging (the test fails if a stage removes it)
      final bull = camelFor(g, r, mean: 95, sex: Sex.male)..condition = 90;
      final kids = [
        for (var i = 0; i < 5; i++) offspringOf(g, bull, r, mean: 95).id,
      ];
      g.advanceTo(f.opensOn);
      expect(
        g.dispatch(EnterRound(g.me.id, f.id, r.id, [bull.id, ...kids])).ok,
        isTrue,
      );
      final day = g.advanceTo(r.day);
      expect(day.whereType<EntryRemoved>(), isEmpty);
      expect(r.judged, isTrue);
      RoundView rv() => GameView(
        g.state,
        g.me.id,
      ).festival(f.id)!.rounds.firstWhere((x) => x.id == r.id);
      expect(
        day.whereType<ResultsPending>().single.announceOn,
        r.day + Balance.dnaDays,
      );
      expect(day.whereType<Placed>(), isEmpty);
      expect(rv().announced, isFalse);
      expect(rv().results!.where((x) => x.rank != null), isEmpty);
      g.advanceTo(r.day + Balance.dnaDays - 1);
      expect(rv().announced, isFalse);
      final later = g.advanceDays(1);
      expect(later.whereType<Placed>().single.camel, bull.id);
      expect(rv().announced, isTrue);
      expect(bull.placings, hasLength(1));
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
      // the group rounds the rivals ran keep their top three
      final groups = f.rounds.where((x) => !x.kind.enterable).toList();
      expect(groups, hasLength(28));
      final seen = GameView(g.state, g.me.id).festival(f.id)!;
      for (final x in seen.rounds.where((x) => !x.enterable)) {
        expect(x.announced, isTrue);
        expect([for (final row in x.results!) row.rank], [1, 2, 3]);
        expect(x.results!.first.prize, x.prizes.first);
        expect(x.results!.first.head, x.size);
        expect(g.state.players.containsKey(x.results!.first.ownerId), isFalse);
      }
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

    test(
      'a treatment costs its price, lifts her fully in the judges\' eyes '
      'and by a small share in everyone else\'s, and is the owner\'s secret',
      () {
        final g = newGame();
        final f = grand(g);
        final r = roundOf(f, RoundKind.fardiDiq);
        final c = camelFor(g, r);
        // features low enough that the treatment's points are not cut at 100
        for (final t in TamperKind.botox.traits) {
          c.genes[t] = 40;
          c.env[t] = 0;
        }
        final cash = g.me.cash.value;
        final before = Judging.observedAll(c, g.today, judges: true);
        final shownBefore = Judging.observedAll(c, g.today);
        final value = Valuation.value(c, g.today).value;
        expect(
          g.dispatch(Tamper(g.me.id, c.id, TamperKind.botox, 2)).ok,
          isTrue,
        );
        expect(cash - g.me.cash.value, TamperKind.botox.price * 2);
        expect(g.me.ledger.last.category, LedgerCategory.tampering);
        // the judges see all of it; buyers, the broker and the cards a share
        final after = Judging.observedAll(c, g.today, judges: true);
        final shown = Judging.observedAll(c, g.today);
        final gain = Balance.tamperTraitGain(TamperKind.botox, 2);
        for (final t in Trait.values) {
          final up = TamperKind.botox.traits.contains(t) ? gain : 0;
          expect(after[t], closeTo((before[t]! + up).clamp(0, 100), 1e-9));
          expect(
            shown[t],
            closeTo(
              (shownBefore[t]! + up * Balance.tamperPriceShare).clamp(0, 100),
              1e-9,
            ),
          );
        }
        expect(Valuation.value(c, g.today).value, greaterThan(value));
        // the shown look moves by the share of the kind's lift
        final untreated = Camel.fromJson(c.toJson()..remove('treatments'));
        expect(
          Judging.quality(c, g.today) - Judging.quality(untreated, g.today),
          closeTo(
            Balance.tamperLift(TamperKind.botox, 2) * Balance.tamperPriceShare,
            1e-9,
          ),
        );
        // and the fast sum is the features' own sum
        var sum = 0.0;
        for (final t in Trait.values) {
          sum += shown[t]! * t.weight;
        }
        expect(Judging.quality(c, g.today), closeTo(sum, 1e-9));
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
        // no one else is told
        expect(c.treatments.single.knownBy, [g.me.id]);
        // it wears off
        g.advanceDays(TamperKind.botox.lastsDays);
        expect(GameView(g.state, g.me.id).tamperings, isEmpty);
        expect(c.treatments, isEmpty);
      },
    );

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
          expect(c.treatments, isEmpty);
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
      final t = Tampering(
        kind: TamperKind.dye,
        strength: 2,
        on: const GameDay(0),
        until: const GameDay(10),
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

  group('The review of e2775ff and the owner\'s answers (13 Nov)', () {
    test('one الفحل وإنتاجه entry an owner', () {
      final g = newGame();
      final f = grand(g);
      g.advanceTo(f.opensOn);
      final r = roundOf(f, RoundKind.fahal);
      List<CamelId> group() {
        final bull = camelFor(g, r, sex: Sex.male);
        return [
          bull.id,
          for (var i = 0; i < 5; i++) offspringOf(g, bull, r).id,
        ];
      }

      expect(g.dispatch(EnterRound(g.me.id, f.id, r.id, group())).ok, isTrue);
      expect(
        refused(g, EnterRound(g.me.id, f.id, r.id, group())).error.code,
        ErrorCode.roundOwnerLimit,
      );
    });

    test('an entry is withdrawn until the day before its round, not on it', () {
      final g = newGame();
      final f = grand(g);
      final r = roundOf(f, RoundKind.mafareed, sex: Sex.female);
      final c = camelFor(g, r);
      g.advanceTo(f.opensOn);
      g.dispatch(EnterRound(g.me.id, f.id, r.id, [c.id]));
      g.advanceTo(r.day - 1);
      // a day of the round itself, before it is run (the day's systems run
      // after the commands): refused
      g.state.world.day = r.day;
      expect(
        refused(g, WithdrawEntry(g.me.id, f.id, r.id, c.id)).error.code,
        ErrorCode.notFound,
      );
      g.state.world.day = r.day - 1;
      expect(g.dispatch(WithdrawEntry(g.me.id, f.id, r.id, c.id)).ok, isTrue);
    });

    test('stage 1 removes a group short of its camels', () {
      final g = newGame();
      final f = grand(g);
      g.advanceTo(f.opensOn);
      final r = roundOf(f, RoundKind.fahal);
      final bull = camelFor(g, r, sex: Sex.male, mean: 90);
      final kids = [for (var i = 0; i < 5; i++) offspringOf(g, bull, r)];
      g.dispatch(
        EnterRound(g.me.id, f.id, r.id, [bull.id, ...kids.map((k) => k.id)]),
      );
      // one of the offspring dies before the day
      final sim = Sim(g.state);
      kids.last
        ..status = CamelStatus.dead
        ..endedOn = g.today;
      releaseCamel(sim, kids.last);
      expect(r.entries.single.camels, hasLength(5));
      final out = g.advanceTo(r.day).whereType<EntryRemoved>().single;
      expect((out.stage, out.reason), (Stage.chipWitness, RemovalReason.short));
    });

    test('"5th of N" counts the round\'s entrants, not its finalists', () {
      final g = newGame();
      final f = grand(g);
      final r = roundOf(f, RoundKind.mafareed, sex: Sex.female);
      final c = camelFor(g, r, mean: 92)..condition = 90;
      g.advanceTo(f.opensOn);
      g.dispatch(EnterRound(g.me.id, f.id, r.id, [c.id]));
      final placed = g.advanceTo(r.day).whereType<Placed>().single;
      expect(r.entrants, r.rivals + 1);
      expect(placed.of, r.entrants);
      expect(c.placings.single.of, r.entrants);
      expect(r.field!.last, lessThan(r.entrants));
    });

    test('a treatment goes with the camel: the buyer, unknowing, answers for '
        'it if he enters her', () {
      for (var seed = 0; seed < 40; seed++) {
        final g = newGame(seed);
        final f = grand(g);
        final r = roundOf(f, RoundKind.fardiDiq, cat: ColorCategory.wodh);
        final c = camelFor(g, r, mean: 85);
        // treated by its former owner, someone outside the game's players
        c
          ..ownerId = g.state.world.owners.keys.first
          ..treatments.add(
            Tampering(
              kind: TamperKind.botox,
              strength: 3,
              on: g.today,
              until: g.today + 200,
            ),
          );
        expect(GameView(g.state, g.me.id).tamperings, isEmpty);
        // now the player's (bought in time to enter), still unknowing
        c
          ..ownerId = g.me.id
          ..acquiredOn = g.today - 200;
        expect(GameView(g.state, g.me.id).tamperings, isEmpty);
        g.advanceTo(f.opensOn);
        g.dispatch(EnterRound(g.me.id, f.id, r.id, [c.id]));
        final found = g
            .advanceTo(r.day)
            .whereType<TamperingFound>()
            .firstOrNull;
        if (found == null) continue;
        expect(found.camel, c.id);
        expect(found.fine, Balance.tamperFine(TamperKind.botox, 3));
        expect(g.state.world.bans[g.me.id], f.season + 5);
        return;
      }
      fail('never found');
    });

    test('sellers in الحراج cheat at the rivals\' rate; a vet\'s look before '
        'buying may find it, and only the buyer is told', () {
      var treated = 0, listings = 0, found = 0, checked = 0;
      for (var seed = 0; seed < 12; seed++) {
        final g = newGame(seed);
        g.advanceDays(120);
        for (final l in g.state.world.listings.values.toList()) {
          final c = g.state.world.camels[l.camelId]!;
          if (sim(g).isPlayer(l.sellerId)) continue;
          listings++;
          if (!c.treatments.any((t) => t.activeOn(g.today))) continue;
          treated++;
          final before = g.me.cash.value;
          final r = g.dispatch(CheckListing(g.me.id, l.id));
          expect(r.ok, isTrue);
          checked++;
          expect(before - g.me.cash.value, Balance.vetCheckFee);
          final told = r.events.whereType<ListingChecked>().single.found;
          final v = GameView(g.state, g.me.id);
          expect(v.listingOf(c.id)!.knownTreatments, told);
          expect(v.listingOf(c.id)!.timesChecked, 1);
          if (told.isNotEmpty) found++;
          // no one else is told
          final other = c.treatments.where(
            (t) => t.knownBy.any((o) => o != g.me.id),
          );
          expect(other, isEmpty);
        }
      }
      expect(treated / listings, closeTo(Balance.marketTamperChance, 0.03));
      expect(checked, greaterThan(0));
      expect(found / checked, closeTo(Balance.vetCheckChance, 0.35));
    });

    test('a fine larger than the money: the balance below zero, no camel '
        'bought and nothing built, feed and water still come', () {
      final g = newGame();
      // a fine of 5,000 more than the money
      grant(g, -g.me.cash.value - 5000);
      expect(g.me.cash.isNegative, isTrue);
      final l = g.state.world.listings.values.first;
      expect(
        refused(g, BuyListing(g.me.id, l.id)).error.code,
        ErrorCode.inDebt,
      );
      expect(
        refused(g, BuildFacility(g.me.id, Facility.pen)).error.code,
        ErrorCode.inDebt,
      );
      g.me.farm
        ..barleyKg = 0
        ..alfalfaKg = 0
        ..storeKg = 1000;
      expect(g.dispatch(OrderSupply(g.me.id, Supply.barley, 2)).ok, isTrue);
      expect(checkInvariants(g.state), isEmpty);
    });

    test('feed, water and the vet go on account up to its limit, never '
        'counting a fine; money in pays the merchant first', () {
      final g = newGame();
      g.me.farm
        ..barleyKg = 0
        ..alfalfaKg = 0
        ..storeKg = 1000000;
      final limit = handlers.accountLimit(Sim(g.state), g.me);
      expect(limit, greaterThanOrEqualTo(Balance.minCreditLimit));
      // short but above zero: the rest on account
      grant(g, -g.me.cash.value + 50);
      final bag = Provisions.unitPrice(Supply.barley, g.me.farm.region);
      expect(g.dispatch(OrderSupply(g.me.id, Supply.barley, 3)).ok, isTrue);
      expect(g.me.onAccount, (bag * 3).round() - 50);
      // a fine far past the limit does not count against the account
      grant(g, -1000000);
      expect(g.dispatch(OrderSupply(g.me.id, Supply.barley, 1)).ok, isTrue);
      // up to the limit, then the player must sell
      final most = ((limit - g.me.onAccount) / bag).floor();
      if (most > 0) {
        expect(
          g.dispatch(OrderSupply(g.me.id, Supply.barley, most)).ok,
          isTrue,
        );
      }
      final full = refused(g, OrderSupply(g.me.id, Supply.barley, 1));
      expect(full.error.code, ErrorCode.accountFull);
      // the vet's treatment of a sick camel too
      final c =
          g.state.world.camels.values.firstWhere(
              (c) => c.ownerId == g.me.id && c.isAlive,
            )
            ..health = HealthStatus.sick
            ..illness = Illness.lameness
            ..sickSince = g.today;
      expect(
        refused(g, Treat(g.me.id, c.id)).error.code,
        ErrorCode.accountFull,
      );
      // money in pays the merchant first, while the fine is still owed
      final owed = g.me.onAccount;
      grant(g, 2000);
      expect(g.me.onAccount, owed - 2000);
      expect(g.me.cash.isNegative, isTrue);
      expect(g.dispatch(Treat(g.me.id, c.id)).ok, isTrue);
      // and clear once the money is above zero
      grant(g, 2000000);
      expect(g.me.onAccount, 0);
      expect(checkInvariants(g.state), isEmpty);
      final v = GameView(g.state, g.me.id);
      expect(v.onAccount, 0);
      expect(v.accountLimit(), limit);
    });

    test('several kinds on one camel: each adds to her looks, has its own '
        'check and its own fine', () {
      final g = newGame();
      final f = grand(g);
      final r = roundOf(f, RoundKind.fardiDiq);
      final c = camelFor(g, r);
      for (final t in Trait.values) {
        c.genes[t] = 40;
        c.env[t] = 0;
      }
      double judged() {
        var sum = 0.0;
        for (final e in Judging.observedAll(c, g.today, judges: true).entries) {
          sum += e.value * e.key.weight;
        }
        return sum;
      }

      final q0 = judged();
      expect(g.dispatch(Tamper(g.me.id, c.id, TamperKind.dye, 1)).ok, isTrue);
      final q1 = judged();
      expect(g.dispatch(Tamper(g.me.id, c.id, TamperKind.botox, 1)).ok, isTrue);
      final q2 = judged();
      expect(q1 - q0, closeTo(Balance.tamperLift(TamperKind.dye, 1), 1e-9));
      expect(q2 - q1, closeTo(Balance.tamperLift(TamperKind.botox, 1), 1e-9));
      expect(GameView(g.state, g.me.id).tamperings, hasLength(2));
      // found at a festival: every kind found fined, each its own
      var both = 0;
      for (var seed = 0; seed < 60 && both == 0; seed++) {
        final h = newGame(seed);
        final hf = grand(h);
        final hr = roundOf(hf, RoundKind.fardiDiq);
        final x = camelFor(h, hr, mean: 85);
        h.advanceTo(hf.opensOn);
        h.dispatch(EnterRound(h.me.id, hf.id, hr.id, [x.id]));
        // close to the day: dye lasts a month
        h.advanceTo(hr.day - 5);
        h
          ..dispatch(Tamper(h.me.id, x.id, TamperKind.dye, 3))
          ..dispatch(Tamper(h.me.id, x.id, TamperKind.botox, 3));
        final found = h
            .advanceTo(hr.day)
            .whereType<TamperingFound>()
            .where((e) => e.festival != null)
            .toList();
        if (found.length < 2) continue;
        both++;
        expect(found.map((e) => e.kind).toSet(), {
          TamperKind.dye,
          TamperKind.botox,
        });
        expect(found.map((e) => e.fine).toSet(), {
          Balance.tamperFine(TamperKind.dye, 3),
          Balance.tamperFine(TamperKind.botox, 3),
        });
        expect(
          h.me.ledger.where(
            (l) => l.category == LedgerCategory.fine && l.ref == hf.id.value,
          ),
          hasLength(2),
        );
      }
      expect(both, 1);
      // the chance at least one is found adds up
      final one = ContestRules.festivalCatchChance(TamperKind.dye, 1);
      final two =
          1 -
          (1 - one) *
              (1 - ContestRules.festivalCatchChance(TamperKind.botox, 1));
      expect(two, greaterThan(one));
    });

    test('الصيت: strong sales raise it, and it moves what buyers pay', () {
      expect(Balance.reputationPriceFactor(Balance.startingReputation), 1);
      expect(Balance.reputationPriceFactor(100), closeTo(1.18, 1e-9));
      expect(Balance.reputationPriceFactor(0), closeTo(0.98, 1e-9));
      final g = newGame();
      final c = g.state.world.camels.values.firstWhere(
        (c) => c.ownerId == g.me.id && c.isAlive,
      );
      final low = GameView(g.state, g.me.id).quickSalePrice(c.id)!.value;
      g.me.reputation[c.category] = 100;
      final high = GameView(g.state, g.me.id).quickSalePrice(c.id)!.value;
      expect(high / low, closeTo(1.18, 0.05));
      // a strong sale: an offer well over her value, accepted
      g.me.reputation.remove(c.category);
      final value = Valuation.value(c, g.today).value;
      expect(g.dispatch(ListForSale(g.me.id, c.id, value * 2)).ok, isTrue);
      final listing = g.state.world.listings.values.firstWhere(
        (l) => l.camelId == c.id,
      );
      final buyer = g.state.world.owners.keys.first;
      final o = Offer(
        id: const OfferId('o-test'),
        listingId: listing.id,
        buyerId: buyer,
        amount: Riyal((value * 1.5).round()),
        madeOn: g.today,
        expiresOn: g.today + 3,
      );
      g.state.world.offers[o.id] = o;
      expect(g.dispatch(AcceptOffer(g.me.id, o.id)).ok, isTrue);
      expect(
        g.me.reputationIn(c.category),
        Balance.startingReputation + Balance.reputationForStrongSale,
      );
    });
  });

  group(
    'Round 4 (the owner\'s decisions 12 and 13; the review\'s round 2)',
    () {
      test(
        'a treatment moves no feature more than 7 a level, inside how far an '
        'untreated camel\'s neighbouring features differ',
        () {
          final g = newGame();
          final s0 = Sim(g.state);
          final pair = <double>[];
          for (var i = 0; i < 400; i++) {
            final c = WorldGen(s0).makeCamel(
              s0.rng(['spread', i]),
              owner: g.state.world.owners.keys.first,
              mean: 60,
            );
            final l = Judging.observedAll(c, g.today);
            for (var j = 0; j + 1 < Trait.values.length; j++) {
              pair.add((l[Trait.values[j]]! - l[Trait.values[j + 1]]!).abs());
            }
          }
          pair.sort();
          final p90 = pair[(pair.length * 0.9).floor()];
          for (final k in TamperKind.values) {
            for (var st = 1; st <= 3; st++) {
              final gain = Balance.tamperTraitGain(k, st);
              expect(
                gain,
                lessThanOrEqualTo(Balance.tamperFeatureCapPerLevel * st),
              );
              expect(gain, lessThanOrEqualTo(p90), reason: '${k.name} $st');
            }
          }
          // a stranger's view of a listed treated camel: each feature moved by
          // no more than the cap
          final r = roundOf(grand(g), RoundKind.fardiDiq);
          final c = camelFor(g, r, mean: 50);
          final before = GameView(
            g.state,
            const OwnerId('stranger'),
          ).camel(c.id)!.looks;
          g.dispatch(Tamper(g.me.id, c.id, TamperKind.lipStretch, 3));
          final after = GameView(
            g.state,
            const OwnerId('stranger'),
          ).camel(c.id)!.looks;
          for (final t in Trait.values) {
            expect(
              after[t]! - before[t]!,
              lessThanOrEqualTo(
                Balance.tamperFeatureCapPerLevel *
                        3 *
                        Balance.tamperPriceShare +
                    1e-9,
              ),
            );
          }
        },
      );

      test('a treated camel does not look cheap: her price and her shown '
          'quality agree as a clean camel\'s do', () {
        final g = newGame();
        final sim0 = Sim(g.state);
        // a camel's price over what the curve gives for the quality shown on
        // her card: the clean band
        double ratio(Camel c) {
          final q = GameView(
            g.state,
            const OwnerId('buyer'),
          ).camel(c.id)!.quality;
          return Valuation.value(c, g.today).value /
              (Valuation.basePrice(c.ageClass(g.today), c.sex) *
                  Valuation.qualityMultiplier(q) *
                  c.category.baseDemand *
                  Valuation.placingMultiplier(c));
        }

        final clean = <double>[];
        for (var i = 0; i < 300; i++) {
          final c = WorldGen(sim0).makeCamel(
            sim0.rng(['cheap', i]),
            owner: g.state.world.owners.keys.first,
            mean: 62,
            sex: Sex.female,
            ageDays: 5 * 365 + 40,
          )..condition = 72;
          clean.add(ratio(c));
        }
        clean.sort();
        final lo = clean[(clean.length * 0.05).floor()];
        final hi = clean[(clean.length * 0.95).floor()];
        for (final k in TamperKind.values) {
          for (var st = 1; st <= 3; st++) {
            final c = WorldGen(sim0).makeCamel(
              sim0.rng(['cheap-t', k.index, st]),
              owner: g.state.world.owners.keys.first,
              mean: 62,
              sex: Sex.female,
              ageDays: 5 * 365 + 40,
            )..condition = 72;
            c.treatments.add(
              Tampering(
                kind: k,
                strength: st,
                on: g.today,
                until: g.today + 20,
              ),
            );
            final r = ratio(c);
            expect(
              r,
              inInclusiveRange(lo - 0.02, hi + 0.02),
              reason: '${k.name} $st',
            );
          }
        }
      });

      test('every entry is examined: a weak treated camel is found as often as '
          'a strong one', () {
        var weak = 0, strong = 0;
        const n = 60;
        for (var seed = 0; seed < n; seed++) {
          for (final mean in [30.0, 92.0]) {
            final g = newGame(seed);
            final f = grand(g);
            final r = roundOf(f, RoundKind.diq, sex: Sex.female);
            final c = camelFor(g, r, mean: mean)..condition = 80;
            g.advanceTo(f.opensOn);
            g
              ..dispatch(EnterRound(g.me.id, f.id, r.id, [c.id]))
              ..dispatch(Tamper(g.me.id, c.id, TamperKind.botox, 3));
            final found = g
                .advanceTo(r.day)
                .whereType<TamperingFound>()
                .any((e) => e.camel == c.id && e.festival != null);
            if (found && mean < 50) weak++;
            if (found && mean > 50) strong++;
          }
        }
        final p = ContestRules.festivalCatchChance(TamperKind.botox, 3);
        // both found near the kind's chance, the weak one never spared by the
        // preliminary cut (it comes after the check)
        expect(weak / n, closeTo(p, 0.15));
        expect(strong / n, closeTo(p, 0.15));
      });

      test('selling a treated camel: the broker examines; found, the sale is '
          'off and the seller who treated her fined', () {
        var refusedSales = 0, sold = 0;
        for (var seed = 0; seed < 30; seed++) {
          final g = newGame(seed);
          final c = camelFor(g, roundOf(grand(g), RoundKind.fardiDiq));
          g.dispatch(Tamper(g.me.id, c.id, TamperKind.botox, 3));
          final cash = g.me.cash.value;
          final r = g.dispatch(QuickSale(g.me.id, c.id));
          if (r.ok) {
            sold++;
            continue;
          }
          refusedSales++;
          final err = r as Err;
          expect(err.error.code, ErrorCode.saleRefused);
          expect(err.error.params['fine'], Balance.outsideFine);
          final ev = r.events.whereType<SaleRefused>().single;
          expect(ev.fine, Balance.outsideFine);
          expect(ev.kinds, [TamperKind.botox]);
          expect(c.ownerId, g.me.id);
          expect(cash - g.me.cash.value, Balance.outsideFine);
        }
        final p = ContestRules.saleCheckChance(3);
        expect(refusedSales / 30, closeTo(p, 0.25));
        expect(sold, greaterThan(0));
      });

      test('an offer accepted on a treated camel: examined the same way, the '
          'buyer walks away', () {
        for (var seed = 0; seed < 30; seed++) {
          final g = newGame(seed);
          final c = camelFor(g, roundOf(grand(g), RoundKind.fardiDiq));
          g.dispatch(Tamper(g.me.id, c.id, TamperKind.hormones, 3));
          g.dispatch(ListForSale(g.me.id, c.id, 1000000));
          final l = g.state.world.listings.values.firstWhere(
            (l) => l.camelId == c.id,
          );
          final o = Offer(
            id: OfferId('o-$seed'),
            listingId: l.id,
            buyerId: g.state.world.owners.keys.first,
            amount: const Riyal(50000),
            madeOn: g.today,
            expiresOn: g.today + 3,
          );
          g.state.world.offers[o.id] = o;
          final r = g.dispatch(AcceptOffer(g.me.id, o.id));
          if (r.ok) continue;
          expect((r as Err).error.code, ErrorCode.saleRefused);
          expect(g.state.world.offers.containsKey(o.id), isFalse);
          expect(c.ownerId, g.me.id);
          return;
        }
        fail('never found in 30 sales of heavy hormones');
      });

      test('the money pump loses: the cheapest adult, all seven kinds at 3, '
          'sold to the broker', () {
        var net = 0;
        const n = 30;
        for (var seed = 0; seed < n; seed++) {
          final g = newGame(seed);
          final c = camelFor(
            g,
            roundOf(grand(g), RoundKind.fardiDiq),
            mean: 45,
          );
          final start = g.me.cash.value;
          for (final k in TamperKind.values) {
            expect(g.dispatch(Tamper(g.me.id, c.id, k, 3)).ok, isTrue);
          }
          final honest = Valuation.value(
            Camel.fromJson(c.toJson()..remove('treatments')),
            g.today,
          ).value;
          g.dispatch(QuickSale(g.me.id, c.id));
          // what it made over selling her untreated to the broker
          net +=
              g.me.cash.value -
              start -
              (honest * Balance.quickSaleFactor).round();
        }
        expect(net / n, lessThan(-50000));
      });

      test('outside a festival only an owner who treated her or knew is fined; '
          'one who did not is told; who treated her stays on it', () {
        final g = newGame();
        final c = camelFor(g, roundOf(grand(g), RoundKind.fardiDiq));
        final t = Tampering(
          kind: TamperKind.dye,
          strength: 3,
          on: g.today,
          until: g.today + 25,
          by: g.state.world.owners.keys.first,
        );
        c.treatments.add(t);
        final cash = g.me.cash.value;
        final s = Sim(g.state);
        expect(TamperingSystem.foundOutside(s, g.me, c, t), 0);
        expect(g.me.cash.value, cash);
        expect(t.knownBy, [g.me.id]);
        expect(c.treatments, contains(t));
        expect(
          GameView(g.state, g.me.id).tamperings.single.kind,
          TamperKind.dye,
        );
        // found again, now he knew: fined
        expect(
          TamperingSystem.foundOutside(s, g.me, c, t),
          Balance.outsideFine,
        );
        expect(cash - g.me.cash.value, Balance.outsideFine);
        expect(c.treatments, isEmpty);
        // his own treatment, sold on and bought back: still his
        final t2 = Tampering(
          kind: TamperKind.botox,
          strength: 1,
          on: g.today,
          until: g.today + 100,
          by: g.me.id,
        );
        c.treatments.add(t2);
        final json = Camel.fromJson(c.toJson());
        expect(json.treatments.single.by, g.me.id);
      });

      test('a stud\'s fee and a festival entry need the money; feed past the '
          'account is refused', () {
        final g = newGame();
        final f = grand(g);
        final r = roundOf(f, RoundKind.mafareed, sex: Sex.female);
        final c = camelFor(g, r);
        g.advanceTo(f.opensOn);
        grant(g, -g.me.cash.value + 10);
        final v = GameView(g.state, g.me.id);
        final why = v.canEnter(f.id, r.id, [c.id]);
        expect(why?.code, ErrorCode.insufficientFunds);
        expect(
          refused(g, EnterRound(g.me.id, f.id, r.id, [c.id])).error.code,
          why!.code,
        );
        grant(g, -50010);
        expect(
          GameView(g.state, g.me.id).canEnter(f.id, r.id, [c.id])?.code,
          ErrorCode.inDebt,
        );
        final dam =
            g.state.world.camels.values.firstWhere(
                (x) =>
                    x.ownerId == g.me.id &&
                    x.sex == Sex.female &&
                    x.ageYears(g.today) >= 6,
              )
              ..pregnancy = null
              ..lastCalvedOn = null;
        if (g.state.world.studs.isNotEmpty) {
          expect(
            refused(
              g,
              MateWithStud(
                g.me.id,
                dam.id,
                g.state.world.studs.values.first.id,
              ),
            ).error.code,
            anyOf(ErrorCode.inDebt, ErrorCode.notBreedingSeason),
          );
        }
        // 500 bags at -50,000: past the account's limit
        g.me.farm
          ..storeKg = 1 << 30
          ..barleyKg = 0
          ..alfalfaKg = 0;
        expect(
          refused(g, OrderSupply(g.me.id, Supply.barley, 500)).error.code,
          ErrorCode.accountFull,
        );
        // bargaining is buying: refused in debt
        final l = g.state.world.listings.values.first;
        expect(
          refused(g, Bargain(g.me.id, l.id, l.askPrice.value)).error.code,
          ErrorCode.inDebt,
        );
      });

      test(
        'الصيت moves what other buyers offer for the player\'s listed camels',
        () {
          double offered(double rep) {
            var sum = 0, count = 0;
            for (var seed = 0; seed < 8; seed++) {
              final g = newGame(seed);
              final c = g.state.world.camels.values.firstWhere(
                (x) =>
                    x.ownerId == g.me.id &&
                    x.isAlive &&
                    x.ageYears(g.today) > 2,
              );
              g.me.reputation[c.category] = rep;
              g.dispatch(
                ListForSale(g.me.id, c.id, Valuation.value(c, g.today).value),
              );
              for (final e in g.advanceDays(40).whereType<OfferReceived>()) {
                sum += e.amount;
                count++;
              }
            }
            return count == 0 ? 0 : sum / count;
          }

          expect(offered(100), greaterThan(offered(0) * 1.08));
        },
      );
    },
  );

  group('Round 5: the rules the mutations found untested', () {
    test('the preliminary cuts only among entries the check let through: a '
        'weak camel found treated is told as found, not as cut', () {
      var found = 0;
      for (var seed = 0; seed < 20; seed++) {
        final g = newGame(seed);
        final f = grand(g);
        final r = roundOf(f, RoundKind.diq, sex: Sex.female);
        g.advanceTo(f.opensOn);
        final c = camelFor(g, r, mean: 30)..acquiredOn = g.today - 200;
        expect(g.dispatch(EnterRound(g.me.id, f.id, r.id, [c.id])).ok, isTrue);
        g.dispatch(Tamper(g.me.id, c.id, TamperKind.botox, 3));
        final events = g.advanceTo(r.day);
        // (a weak camel can die before the day: her entry goes with her)
        if (!c.isAlive) continue;
        final out = events.whereType<EntryRemoved>().firstOrNull;
        if (events.whereType<TamperingFound>().any((e) => e.camel == c.id)) {
          found++;
          expect(out?.reason, RemovalReason.tampering);
        } else {
          // cut, or (a small field) placed
          expect(
            out?.reason == RemovalReason.cut ||
                events.whereType<Placed>().any((e) => e.camel == c.id),
            isTrue,
          );
        }
        // the found ones took none of the preliminary's places
        final field = r.field!;
        final checked = field[Stage.breedColourAge.index] - r.caught;
        final kept = (checked * Balance.preliminaryKeeps).ceil();
        final keep = kept < Balance.preliminaryKeepsAtLeast
            ? Balance.preliminaryKeepsAtLeast
            : kept;
        expect(
          field[Stage.preliminary.index],
          (keep < checked ? keep : checked) + r.caught,
        );
      }
      expect(found, greaterThan(5));
    });

    test(
      'the examination at a sale finds a stronger treatment more easily',
      () {
        final p = [
          for (var s = 1; s <= 3; s++) ContestRules.saleCheckChance(s),
        ];
        expect(p[0], closeTo(Balance.saleCheckPerLevel, 1e-9));
        expect(p[1], greaterThan(p[0]));
        expect(p[2], greaterThan(p[1]));
        expect(p[2], closeTo(1 - 0.65 * 0.65 * 0.65, 1e-9));
      },
    );

    test('the vet\'s treatment goes on the account; the account clears once '
        'the money is above zero', () {
      final g = newGame();
      final c =
          g.state.world.camels.values.firstWhere(
              (c) => c.ownerId == g.me.id && c.isAlive,
            )
            ..health = HealthStatus.sick
            ..illness = Illness.lameness
            ..sickSince = g.today;
      grant(g, -g.me.cash.value - 100);
      expect(g.dispatch(Treat(g.me.id, c.id)).ok, isTrue);
      final owed = g.me.onAccount;
      expect(owed, greaterThan(0));
      expect(g.me.onAccount, lessThanOrEqualTo(-g.me.cash.value));
      // income smaller than the account but enough to bring the money above
      // zero: the account is cleared, not just lowered
      grant(g, -g.me.cash.value - 100); // cash at -100
      g.me.onAccount = 100;
      grant(g, 150);
      expect(g.me.cash.isNegative, isFalse);
      expect(g.me.onAccount, 0);
      g.me.onAccount = 50;
      grant(g, -1000);
      g.me.onAccount = 50;
      grant(g, 1);
      expect(g.me.onAccount, 49);
    });

    test('a stud\'s fee needs the money: insufficientFunds when short, inDebt '
        'below zero', () {
      final g = newGame();
      // in the breeding season (November to April)
      g.advanceTo(GameDay.ofDate(DateTime.utc(2026, 12, 1)));
      final sim0 = Sim(g.state);
      final stud = WorldGen(sim0).addStud(sim0.rng(['test-stud']));
      final dam =
          g.state.world.camels.values.firstWhere(
              (x) =>
                  x.ownerId == g.me.id &&
                  x.sex == Sex.female &&
                  x.ageYears(g.today) >= 6,
            )
            ..pregnancy = null
            ..lastCalvedOn = null
            ..health = HealthStatus.healthy;
      expect(Eligibility.femaleCanBreed(dam, g.today), isNull);
      grant(g, -g.me.cash.value + 10);
      expect(
        refused(g, MateWithStud(g.me.id, dam.id, stud.id)).error.code,
        ErrorCode.insufficientFunds,
      );
      grant(g, -1000);
      expect(
        refused(g, MateWithStud(g.me.id, dam.id, stud.id)).error.code,
        ErrorCode.inDebt,
      );
    });
  });

  group('What a player sees', () {
    test('no row carries a score or a mark, the player\'s own included', () {
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
      expect(theirs.camelId, isNull);
      final mine = rows.firstWhere((x) => x.ownerId == g.me.id);
      expect(mine.camelId, c.id);
      for (final row in rows) {
        expect(
          row.toJson().keys,
          isNot(anyOf(contains('score'), contains('marks'))),
        );
      }
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
