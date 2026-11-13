import 'catalog/catalog.dart';
import 'catalog/region.dart';
import 'common/ids.dart';
import 'common/money.dart';
import 'common/rng.dart';
import 'common/time.dart';
import 'events.dart';
import 'model/camel.dart';
import 'model/contest.dart';
import 'model/market.dart';
import 'rules/balance.dart';
import 'rules/contest_rules.dart';
import 'rules/genetics.dart';
import 'rules/judging.dart';
import 'rules/names.dart';
import 'rules/valuation.dart';
import 'sim.dart';

/// Creates what the world needs around the players: other owners, market
/// camels, studs and the contest calendar.
class WorldGen {
  WorldGen(this.sim);
  final Sim sim;

  /// (balance) How common each colour family is on the market. وضح takes
  /// the old pure-white مغاتير family's share too (1.0 + 0.9), so the market's
  /// mix of colours is as it was.
  static const categoryWeights = {
    ColorCategory.majaheem: 1.3,
    ColorCategory.wodh: 1.9,
    ColorCategory.sofr: 1.0,
    ColorCategory.homr: 0.9,
    ColorCategory.shoal: 0.9,
    ColorCategory.shoqh: 0.8,
  };

  static Map<OwnerId, Owner> makeOwners(IdGenerator ids) {
    final owners = <OwnerId, Owner>{};
    for (var i = 0; i < ownerNames.length; i++) {
      final o = Owner(
        id: ids.owner(),
        name: ownerNames[i],
        region: Region.values[i % Region.values.length],
      );
      owners[o.id] = o;
    }
    return owners;
  }

  Owner randomOwner(Rng rng, {Region? region}) {
    final all = sim.world.owners.values
        .where((o) => !sim.isPlayer(o.id))
        .toList();
    final local = region == null
        ? all
        : all.where((o) => o.region == region).toList();
    return rng.pick(local.isEmpty ? all : local);
  }

  /// A camel from outside any player's herd, breeding values centred on
  /// [mean] (≈50 ordinary, 65 good, 80 elite).
  Camel makeCamel(
    Rng rng, {
    required OwnerId owner,
    required double mean,
    ColorCategory? category,
    Sex? sex,
    int? ageDays,
  }) {
    final w = sim.world;
    final cat =
        category ??
        rng.weighted<ColorCategory>(
          categoryWeights.keys.toList(),
          categoryWeights.values.toList(),
        );
    final sx = sex ?? (rng.chance(0.62) ? Sex.female : Sex.male);
    final age = ageDays ?? _randomAgeDays(rng);
    final born = sim.today - age;
    final c = Camel(
      id: w.ids.camel(),
      name: randomCamelName(rng, female: sx == Sex.female),
      sex: sx,
      category: cat,
      born: born,
      ownerId: owner,
      chip: randomChipNumber(rng),
      genes: Genetics.randomGenes(rng, mean: mean),
      env: Genetics.randomEnv(rng),
      condition: q2(clampDouble(rng.normal(mean: 72, sd: 8), 45, 92)),
      acquiredOn: born,
      sire: ParentRef(
        id: w.ids.camel(),
        name: randomCamelName(rng, female: false),
        category: cat,
      ),
      dam: ParentRef(
        id: w.ids.camel(),
        name: randomCamelName(rng, female: true),
        category: cat,
      ),
    );
    final years = c.ageYears(sim.today);
    if (sx == Sex.female && years >= 6) {
      c.calvings = rng.range(0, (years - 4) ~/ 2);
      if (c.calvings > 0) c.lastCalvedOn = sim.today - rng.range(200, 700);
    }
    w.camels[c.id] = c;
    return c;
  }

  int _randomAgeDays(Rng rng) {
    final years = rng.weighted(
      [0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12],
      [0.6, 1.4, 1.5, 1.4, 1.3, 1.1, 0.9, 0.7, 0.8, 0.5, 0.3],
    );
    return years * 365 + rng.range(30, 330);
  }

  /// Mostly ordinary camels, some good, a few elite.
  static double marketMean(Rng rng) {
    final band = rng.weighted([0, 1, 2, 3], [0.62, 0.26, 0.10, 0.02]);
    return switch (band) {
      0 => rng.rangeDouble(42, 56),
      1 => rng.rangeDouble(56, 66),
      2 => rng.rangeDouble(66, 76),
      _ => rng.rangeDouble(76, 86),
    };
  }

  Listing addMarketListing(Rng rng) {
    final owner = randomOwner(rng);
    final camel = makeCamel(rng, owner: owner.id, mean: marketMean(rng));
    final value = Valuation.value(camel, sim.today).value.toDouble();
    final l = Listing(
      id: sim.world.ids.listing(),
      camelId: camel.id,
      sellerId: owner.id,
      region: owner.region,
      askPrice: marketRound(value * rng.rangeDouble(1.05, 1.32)),
      reservePrice: marketRound(value * rng.rangeDouble(0.88, 1.0)),
      listedOn: sim.today,
      expiresOn: sim.today + rng.range(8, 35),
    );
    sim.world.listings[l.id] = l;
    return l;
  }

  StudOffer addStud(Rng rng) {
    final owner = randomOwner(rng);
    final mean = rng.weighted(
      [
        rng.rangeDouble(55, 65),
        rng.rangeDouble(65, 75),
        rng.rangeDouble(75, 88),
      ],
      [0.45, 0.4, 0.15],
    );
    final camel = makeCamel(
      rng,
      owner: owner.id,
      mean: mean,
      sex: Sex.male,
      ageDays: rng.range(7, 16) * 365 + rng.range(0, 300),
    );
    final q = Judging.quality(camel, sim.today);
    final fee = marketRound(
      clampDouble(800 * Valuation.qualityMultiplier(q) / 2, 1500, 80000),
    );
    final s = StudOffer(
      id: sim.world.ids.stud(),
      camelId: camel.id,
      ownerId: owner.id,
      region: owner.region,
      fee: fee,
      until: sim.today + rng.range(30, 90),
    );
    sim.world.studs[s.id] = s;
    return s;
  }

  // ------------------------------------------------------------ festivals

  /// (balance) The season's festivals and the day each begins (month
  /// numbers past 12 fall in the next year); most run in the cool months,
  /// Tabuk's in June, as the real one (GDD 4.4). (field) The grand festival
  /// begins on 1 December (research section 4).
  static List<(String, Region, FestivalTier, int, int)> seasonPlan(int year) =>
      [
        ('مزاين حائل', Region.hail, FestivalTier.regional, 10, 18),
        ('مزاين القصيم', Region.qassim, FestivalTier.local, 11, 8),
        ('مزاين الجوف', Region.jouf, FestivalTier.regional, 11, 29),
        ('مهرجان المزاين الكبير', Region.riyadh, FestivalTier.grand, 12, 1),
        ('مزاين الأحساء', Region.sharqiya, FestivalTier.regional, 14, 7),
        ('مزاين الشمال', Region.northern, FestivalTier.local, 14, 28),
        ('مزاين تبوك', Region.tabuk, FestivalTier.local, 18, 14),
        ('مزاين نجران', Region.najran, FestivalTier.regional, 15, 28),
      ];

  /// The festival's last day: (field) the grand one's on 3 January (the 9th
  /// and 10th editions, research section 4), (balance) the others' by
  /// [Balance.regionalFestivalDays] and [Balance.localFestivalDays].
  static GameDay lastDay(FestivalTier tier, GameDay starts) => switch (tier) {
    FestivalTier.grand => GameDay.ofDate(DateTime.utc(starts.year + 1, 1, 3)),
    FestivalTier.regional => starts + (Balance.regionalFestivalDays - 1),
    FestivalTier.local => starts + (Balance.localFestivalDays - 1),
  };

  /// Schedules the season starting in autumn of [year].
  void planSeason(int year) {
    final w = sim.world;
    final rng = sim.rng(['season', year]);
    for (final (name, region, tier, month, day) in seasonPlan(year)) {
      final starts = GameDay.ofDate(
        DateTime.utc(year + (month - 1) ~/ 12, (month - 1) % 12 + 1, day),
      );
      if (starts <= sim.today + 8) continue;
      final ends = lastDay(tier, starts);
      final opens =
          starts -
          (tier == FestivalTier.grand
              ? Balance.grandRegistrationOpensBefore
              : Balance.registrationOpensBefore);
      final f = Festival(
        id: w.ids.festival(),
        name: name,
        region: region,
        tier: tier,
        season: year,
        opensOn: opens < sim.today ? sim.today : opens,
        closesOn: starts - Balance.registrationClosesBeforeStart,
        startsOn: starts,
        endsOn: ends,
        rounds: _rounds(rng, tier, starts, ends),
      );
      w.festivals[f.id] = f;
    }
    w.plannedUntil = GameDay.ofDate(DateTime.utc(year + 1, 8, 31));
    sim.emit(SeasonPlanned(sim.today, year: year));
  }

  /// (balance) A festival's programme. The grand one: for each colour, الفردي
  /// دق and جل, مفاريد and دق of القعدان and البكار; for each colour a جمل of
  /// 40, 60 and 80 head (100 for الحمر and الشقح: research section 2, the
  /// 2020 sizes) and a منقية of 15, 20 or 30; then منقية الجزيرة (30),
  /// الهجيج and الطبع (15), البداوة (40) and الفحل وإنتاجه (the bull and his
  /// offspring). A regional one: five colours' individual rounds, a جمل of 20
  /// for each and الفحل وإنتاجه. A local one: three colours' الفردي and
  /// مفاريد. The individual rounds come first, the groups after, منقية
  /// الجزيرة on the last day; each on its own day, spread over the festival.
  List<ContestRound> _rounds(
    Rng rng,
    FestivalTier tier,
    GameDay starts,
    GameDay ends,
  ) {
    final categories = switch (tier) {
      FestivalTier.grand => ColorCategory.values,
      FestivalTier.regional =>
        rng.shuffled(ColorCategory.values).take(5).toList(),
      FestivalTier.local => rng.shuffled(ColorCategory.values).take(3).toList(),
    };
    // (kind, colour, sex, size)
    final plan = <(RoundKind, ColorCategory?, Sex?, int)>[];
    for (final cat in categories) {
      plan
        ..add((RoundKind.fardiDiq, cat, Sex.female, 1))
        ..add((RoundKind.fardiJil, cat, Sex.female, 1))
        ..add((RoundKind.mafareed, cat, Sex.female, 1))
        ..add((RoundKind.mafareed, cat, Sex.male, 1));
      if (tier != FestivalTier.local) {
        plan
          ..add((RoundKind.diq, cat, Sex.female, 1))
          ..add((RoundKind.diq, cat, Sex.male, 1));
      }
    }
    if (tier == FestivalTier.grand) {
      for (final cat in categories) {
        final big = cat == ColorCategory.homr || cat == ColorCategory.shoqh
            ? 100
            : 80;
        for (final n in [40, 60, big]) {
          plan.add((RoundKind.jamal, cat, Sex.female, n));
        }
        plan.add((RoundKind.manqiya, cat, Sex.female, rng.pick([15, 20, 30])));
      }
      plan
        ..add((RoundKind.badawa, null, Sex.female, 40))
        ..add((RoundKind.hajij, null, Sex.female, 15))
        ..add((RoundKind.tabaa, null, null, 15));
    } else if (tier == FestivalTier.regional) {
      for (final cat in categories) {
        plan.add((RoundKind.jamal, cat, Sex.female, 20));
      }
    }
    if (tier != FestivalTier.local) {
      plan.add((RoundKind.fahal, null, null, 1 + ContestRules.fahalOffspring));
    }
    if (tier == FestivalTier.grand) {
      plan.add((RoundKind.jazeera, null, Sex.female, 30));
    }
    final days = ends.daysSince(starts) + 1;
    final rounds = <ContestRound>[];
    for (var i = 0; i < plan.length; i++) {
      final (kind, cat, sex, size) = plan[i];
      final fardi = kind.single || kind == RoundKind.fahal;
      rounds.add(
        ContestRound(
          id: sim.world.ids.round(),
          kind: kind,
          category: cat,
          sex: sex,
          size: size,
          day: i == plan.length - 1 ? ends : starts + i * days ~/ plan.length,
          rivals: fardi ? _fieldSize(rng, tier) : _groupField(rng, tier),
        ),
      );
    }
    return rounds;
  }

  static int _fieldSize(Rng rng, FestivalTier tier) => switch (tier) {
    FestivalTier.grand => rng.range(28, 44),
    FestivalTier.regional => rng.range(16, 28),
    FestivalTier.local => rng.range(9, 16),
  };

  static int _groupField(Rng rng, FestivalTier tier) => switch (tier) {
    FestivalTier.grand => rng.range(8, 16),
    _ => rng.range(4, 10),
  };
}
