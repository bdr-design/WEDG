import '../../core/rng.dart';
import '../models/camel.dart';
import '../models/catalog.dart';
import '../models/contest.dart';
import '../models/game_state.dart';
import '../models/market.dart';
import '../models/region.dart';
import '../rules/genetics.dart';
import '../rules/judging.dart';
import '../rules/names.dart';
import '../rules/valuation.dart';

/// Builds the world around the player: other owners, market camels, studs and
/// the contest season.
class WorldGen {
  WorldGen(this.s, this.rng);

  final GameState s;
  final Rng rng;

  // --------------------------------------------------------------- owners

  static List<Owner> makeOwners(Rng rng) {
    final names = [...ownerNames];
    final owners = <Owner>[];
    for (var i = 0; i < names.length; i++) {
      owners.add(Owner(
        id: 'o$i',
        name: names[i],
        region: Region.values[i % Region.values.length],
      ));
    }
    return owners;
  }

  Owner randomOwner({Region? region}) {
    final pool = region == null
        ? s.owners
        : s.owners.where((o) => o.region == region).toList();
    return rng.pick(pool.isEmpty ? s.owners : pool);
  }

  // --------------------------------------------------------------- camels

  /// How common each colour family is on the market (game balance).
  static const _categoryWeights = {
    ColorCategory.majaheem: 1.3,
    ColorCategory.maghateer: 0.9,
    ColorCategory.wodh: 1.0,
    ColorCategory.sofr: 1.0,
    ColorCategory.homr: 0.9,
    ColorCategory.shoal: 0.9,
    ColorCategory.shoqh: 0.8,
  };

  ColorCategory randomCategory() => rng.weighted(
        _categoryWeights.keys.toList(),
        _categoryWeights.values.toList(),
      );

  /// A new camel from outside the player's herd, with breeding values
  /// centred on [mean] (≈50 ordinary, 65 good, 80 elite).
  Camel makeCamel({
    required String ownerId,
    required double mean,
    ColorCategory? category,
    Sex? sex,
    int? ageDays,
  }) {
    final cat = category ?? randomCategory();
    final sx = sex ?? (rng.chance(0.62) ? Sex.female : Sex.male);
    final age = ageDays ?? _randomAgeDays(sx);
    final female = sx == Sex.female;
    final c = Camel(
      id: s.newId('c'),
      name: randomCamelName(rng, female: female),
      sex: sx,
      category: cat,
      birthDay: s.day - age,
      ownerId: ownerId,
      chip: randomChipNumber(rng),
      genes: Genetics.randomGenes(rng, mean: mean),
      env: Genetics.randomEnv(rng),
      condition: clampDouble(rng.gaussian(mean: 72, sd: 8), 45, 92),
      sire: PedigreeRef(
        id: 'ext${rng.nextUint32()}',
        name: randomCamelName(rng, female: false),
        category: cat,
      ),
      dam: PedigreeRef(
        id: 'ext${rng.nextUint32()}',
        name: randomCamelName(rng, female: true),
        category: cat,
      ),
    );
    if (female && c.ageYears(s.day) >= 6) {
      c.calvings = rng.range(0, (c.ageYears(s.day) - 4) ~/ 2);
      if (c.calvings > 0) {
        c.lastCalvingDay = s.day - rng.range(200, 700);
      }
    }
    return c;
  }

  int _randomAgeDays(Sex sex) {
    // Markets see many young stock and fewer old camels.
    final years = rng.weighted(
      [0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12],
      [0.6, 1.4, 1.5, 1.4, 1.3, 1.1, 0.9, 0.7, 0.8, 0.5, 0.3],
    );
    return years * 365 + rng.range(30, 330);
  }

  /// Breeding-value mean for a market camel: mostly ordinary, some good,
  /// a few elite.
  double randomMarketMean() {
    final band = rng.weighted([0, 1, 2, 3], [0.62, 0.26, 0.10, 0.02]);
    return switch (band) {
      0 => rng.rangeDouble(42, 56),
      1 => rng.rangeDouble(56, 66),
      2 => rng.rangeDouble(66, 76),
      _ => rng.rangeDouble(76, 86),
    };
  }

  // --------------------------------------------------------------- market

  Listing addMarketListing({Region? region}) {
    final owner = randomOwner(region: region);
    final camel = makeCamel(ownerId: owner.id, mean: randomMarketMean());
    s.camels[camel.id] = camel;
    final value = Valuation.value(camel, s.day);
    final listing = Listing(
      id: s.newId('l'),
      camelId: camel.id,
      sellerId: owner.id,
      sellerName: owner.name,
      region: owner.region,
      askPrice: Valuation.roundPrice(value * rng.rangeDouble(1.05, 1.32)),
      reservePrice: Valuation.roundPrice(value * rng.rangeDouble(0.88, 1.0)),
      listedDay: s.day,
      expiresDay: s.day + rng.range(8, 35),
    );
    s.listings.add(listing);
    return listing;
  }

  StudOffer addStud() {
    final owner = randomOwner();
    final camel = makeCamel(
      ownerId: owner.id,
      mean: rng.weighted(
        [rng.rangeDouble(55, 65), rng.rangeDouble(65, 75), rng.rangeDouble(75, 88)],
        [0.45, 0.4, 0.15],
      ),
      sex: Sex.male,
      ageDays: rng.range(7, 16) * 365 + rng.range(0, 300),
    );
    s.camels[camel.id] = camel;
    final q = Judging.quality(camel, s.day);
    final fee = Valuation.roundPrice(
      clampDouble(800 * Valuation.qualityMultiplier(q) / 2, 1500, 80000),
    );
    final stud = StudOffer(
      id: s.newId('st'),
      camelId: camel.id,
      ownerName: owner.name,
      region: owner.region,
      fee: fee,
      untilDay: s.day + rng.range(30, 90),
    );
    s.studs.add(stud);
    return stud;
  }

  // ------------------------------------------------------------ festivals

  /// Schedules the contest season that starts in autumn of [year]. Contests
  /// run in the cool months (Oct–Mar); summer has none.
  void planSeason(int year) {
    final plan = <(String, Region, FestivalTier, DateTime)>[
      ('مزاين حائل', Region.hail, FestivalTier.regional,
          DateTime.utc(year, 10, 18)),
      ('مزاين القصيم', Region.qassim, FestivalTier.local,
          DateTime.utc(year, 11, 8)),
      ('مزاين الجوف', Region.jouf, FestivalTier.regional,
          DateTime.utc(year, 11, 29)),
      ('مهرجان المزاين الكبير', Region.riyadh, FestivalTier.grand,
          DateTime.utc(year + 1, 1, 10)),
      ('مزاين الأحساء', Region.sharqiya, FestivalTier.regional,
          DateTime.utc(year + 1, 2, 7)),
      ('مزاين الشمال', Region.northern, FestivalTier.local,
          DateTime.utc(year + 1, 2, 28)),
      ('مزاين تبوك', Region.tabuk, FestivalTier.local,
          DateTime.utc(year + 1, 3, 14)),
      ('مزاين نجران', Region.najran, FestivalTier.regional,
          DateTime.utc(year + 1, 3, 28)),
    ];
    for (final (name, region, tier, date) in plan) {
      final judging = dayOfDate(date);
      if (judging <= s.day + 8) continue; // too late to take part
      final opens = judging - (tier == FestivalTier.grand ? 45 : 30);
      s.festivals.add(Festival(
        id: s.newId('f'),
        name: '$name $year',
        region: region,
        tier: tier,
        registrationOpens: opens < s.day ? s.day : opens,
        registrationCloses: judging - 7,
        judgingDay: judging,
        rounds: _roundsFor(tier),
      ));
    }
    s.festivalsPlannedUntil = dayOfDate(DateTime.utc(year + 1, 8, 31));
  }

  List<ContestRound> _roundsFor(FestivalTier tier) {
    final categories = switch (tier) {
      FestivalTier.grand => ColorCategory.values,
      FestivalTier.regional => _shuffled(ColorCategory.values).take(5).toList(),
      FestivalTier.local => _shuffled(ColorCategory.values).take(3).toList(),
    };
    final femaleAges = switch (tier) {
      FestivalTier.grand => [
          AgeClass.mafrood,
          AgeClass.laqi,
          AgeClass.haq,
          AgeClass.jatha,
          AgeClass.thani,
          AgeClass.mature,
        ],
      FestivalTier.regional => [
          AgeClass.laqi,
          AgeClass.haq,
          AgeClass.jatha,
          AgeClass.thani,
          AgeClass.mature,
        ],
      FestivalTier.local => [AgeClass.haq, AgeClass.jatha, AgeClass.mature],
    };
    final rounds = <ContestRound>[];
    for (final cat in categories) {
      for (final age in femaleAges) {
        rounds.add(ContestRound(
          id: s.newId('r'),
          category: cat,
          sex: Sex.female,
          age: age,
          prizes: prizeTable(tier, age),
          fieldSize: _fieldSize(tier),
        ));
      }
      if (tier != FestivalTier.local) {
        rounds.add(ContestRound(
          id: s.newId('r'),
          category: cat,
          sex: Sex.male,
          age: AgeClass.mature,
          prizes: prizeTable(tier, AgeClass.mature),
          fieldSize: _fieldSize(tier) ~/ 2,
        ));
      }
    }
    return rounds;
  }

  int _fieldSize(FestivalTier tier) => switch (tier) {
        FestivalTier.grand => rng.range(28, 44),
        FestivalTier.regional => rng.range(16, 28),
        FestivalTier.local => rng.range(9, 16),
      };

  List<T> _shuffled<T>(List<T> items) {
    final list = [...items];
    for (var i = list.length - 1; i > 0; i--) {
      final j = rng.nextInt(i + 1);
      final t = list[i];
      list[i] = list[j];
      list[j] = t;
    }
    return list;
  }

  /// Prize money for places 1–10 (game balance, scaled from real festivals
  /// where top rounds pay in the millions).
  static List<int> prizeTable(FestivalTier tier, AgeClass age) {
    final top = switch (tier) {
      FestivalTier.grand => 800000,
      FestivalTier.regional => 150000,
      FestivalTier.local => 40000,
    };
    final ageFactor = switch (age) {
      AgeClass.mafrood || AgeClass.laqi => 0.6,
      AgeClass.haq || AgeClass.jatha => 0.8,
      _ => 1.0,
    };
    const shares = [1.0, 0.6, 0.42, 0.3, 0.22, 0.16, 0.12, 0.09, 0.07, 0.05];
    return [
      for (final sh in shares) Valuation.roundPrice(top * ageFactor * sh),
    ];
  }

  /// Typical quality of the rivals a tier attracts.
  static (double, double) rivalQuality(FestivalTier tier) => switch (tier) {
        FestivalTier.grand => (76, 7),
        FestivalTier.regional => (68, 7),
        FestivalTier.local => (61, 7),
      };
}
