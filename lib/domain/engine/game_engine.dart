import 'dart:math' as math;

import '../../core/format.dart';
import '../../core/rng.dart';
import '../models/camel.dart';
import '../models/catalog.dart';
import '../models/contest.dart';
import '../models/farm.dart';
import '../models/game_state.dart';
import '../models/ledger.dart';
import '../models/market.dart';
import '../models/region.dart';
import '../rules/constants.dart';
import '../rules/genetics.dart';
import '../rules/judging.dart';
import '../rules/names.dart';
import '../rules/valuation.dart';
import 'world_gen.dart';

/// Outcome of a player action, with a message for the UI.
class ActionResult {
  const ActionResult.ok(this.message) : ok = true;
  const ActionResult.fail(this.message) : ok = false;
  final bool ok;
  final String message;
}

/// All game rules that change state. The UI calls these; nothing else
/// mutates [GameState]. Every random draw goes through [rng], whose state is
/// written back to the save so a game replays identically.
class GameEngine {
  GameEngine(this.s) : rng = Rng(s.rngState);

  final GameState s;
  final Rng rng;
  late final WorldGen world = WorldGen(s, rng);

  void _sync() => s.rngState = rng.state;

  // ================================================================ new game

  static GameState newGame({
    required String playerName,
    required String farmName,
    required Region region,
    required ColorCategory favourite,
    required int seed,
  }) {
    final rng = Rng(seed);
    final start = dayOfDate(DateTime.utc(2026, 10, 1));
    final s = GameState(
      rngState: rng.state,
      day: start,
      startDay: start,
      playerName: playerName,
      cash: startingCash,
      farm: Farm(
        name: farmName,
        region: region,
        capacity: startingCapacity,
        shepherds: 1,
        feedPlan: FeedPlan.standard,
      ),
      camels: {},
      owners: WorldGen.makeOwners(rng),
      listings: [],
      buyerOffers: [],
      studs: [],
      festivals: [],
      ledger: [],
      news: [],
      nextId: 1,
    );
    final e = GameEngine(s);
    final w = e.world;

    // Starter herd: camels a new owner typically begins with, of the
    // colour family they chose.
    final starters = [
      (Sex.female, 6 * 365 + 120, 54.0),
      (Sex.female, 4 * 365 + 200, 52.0),
      (Sex.female, 2 * 365 + 90, 50.0),
    ];
    for (final (sex, age, mean) in starters) {
      final c = w.makeCamel(
        ownerId: playerOwnerId,
        mean: mean,
        category: favourite,
        sex: sex,
        ageDays: age,
      );
      c.acquiredDay = start - 200;
      c.purchasePrice = Valuation.value(c, start);
      s.camels[c.id] = c;
    }

    for (var i = 0; i < 34; i++) {
      w.addMarketListing();
    }
    for (var i = 0; i < 8; i++) {
      w.addStud();
    }
    w.planSeason(2026);

    e._news(NewsKind.info,
        'أهلًا $playerName. عزبة "${s.farm.name}" في ${region.label} جاهزة، وفيها ${s.herdSize} من الحلال.');
    e._news(NewsKind.contest,
        'موسم المزاين بدأ. أول مهرجان: ${s.festivals.first.name}، والتسجيل مفتوح في صفحة المشاركات.');
    e._sync();
    return s;
  }

  // ================================================================ helpers

  void _news(NewsKind kind, String text, {String? camelId}) {
    s.news.add(NewsItem(day: s.day, kind: kind, text: text, camelId: camelId));
    if (s.news.length > 300) s.news.removeRange(0, s.news.length - 300);
  }

  void _money(int amount, LedgerCategory cat, String note) {
    s.cash += amount;
    s.ledger.add(LedgerEntry(day: s.day, amount: amount, category: cat, note: note));
    if (s.ledger.length > 800) s.ledger.removeRange(0, s.ledger.length - 800);
  }

  Camel? camel(String id) => s.camels[id];

  int shepherdsNeeded([int? head]) =>
      ((head ?? s.herdSize) / camelsPerShepherd).ceil().clamp(1, 999);

  /// Feed bill for the whole herd per day at the current plan.
  int dailyFeedCost() {
    var total = 0.0;
    for (final c in s.herd) {
      total += feedPerAdultPerDay * feedAgeFactor(c.ageDays(s.day));
    }
    return (total * s.farm.feedPlan.costFactor * s.farm.region.feed).round();
  }

  int monthlyWages() => s.farm.shepherds * shepherdMonthlyWage;

  int expansionCost() =>
      (expansionCostPer10 * s.farm.region.land / 500).round() * 500;

  int herdValue() =>
      s.herd.fold(0, (sum, c) => sum + Valuation.value(c, s.day));

  // ============================================================== the clock

  /// Advances the game by [days]. Returns the news generated meanwhile.
  List<NewsItem> advance(int days) {
    final before = s.news.length;
    for (var i = 0; i < days; i++) {
      _tick();
    }
    _sync();
    final added = s.news.length - before;
    return added > 0 ? s.news.sublist(s.news.length - added) : const [];
  }

  void _tick() {
    s.day++;
    final date = s.date;

    // Feed is bought daily.
    final feed = dailyFeedCost();
    if (feed > 0) {
      _money(-feed, LedgerCategory.feed,
          'علف ${s.herdSize} راس (${s.farm.feedPlan.label})');
    }

    // Wages on the first of each month.
    if (date.day == 1 && s.farm.shepherds > 0) {
      _money(-monthlyWages(), LedgerCategory.wages,
          'رواتب ${s.farm.shepherds} راعي لشهر ${monthName(date.month)}');
    }

    _careAndHealth();
    _pregnancies();
    _market();
    _contests();

    // Schedule next season in early summer; drop festivals over a year old.
    if (s.day >= s.festivalsPlannedUntil - 60) {
      world.planSeason(dateOfDay(s.festivalsPlannedUntil).year);
      s.festivals.removeWhere((f) => f.done && s.day - f.judgingDay > 400);
    }

    if (s.cash < 0 && date.day == 1) {
      _news(NewsKind.bad,
          'الحساب بالسالب (${riyal(s.cash)}). بِع من الحلال أو خفّف المصاريف قبل ما تتراكم الديون.');
    }
  }

  // ------------------------------------------------------- care and health

  static const _illnesses = [
    'جرب',
    'التهاب رئوي',
    'عرج في القوائم',
    'نزلة معوية',
    'حمى',
    'تسمم غذائي',
  ];

  void _careAndHealth() {
    final head = s.herdSize;
    final needed = shepherdsNeeded(head);
    final understaffed = s.farm.shepherds < needed;
    final crowded = head > s.farm.capacity;
    final dead = <Camel>[];

    for (final c in s.herd) {
      var target = s.farm.feedPlan.conditionTarget.toDouble();
      if (understaffed) {
        target -= 14 * (needed - s.farm.shepherds) / needed;
      }
      if (crowded) target -= 8;
      if (c.health == HealthStatus.sick) target -= 22;
      if (c.health == HealthStatus.treated) target -= 8;
      if (c.isPregnantConfirmed && c.pregnancy!.dueDay - s.day < 90) {
        target -= 4;
      }
      c.condition += (target - c.condition) * 0.035;
      c.condition = clampDouble(c.condition, 5, 98);

      switch (c.health) {
        case HealthStatus.healthy:
          var p = dailySickChance;
          if (c.condition < 50) p *= 2;
          if (crowded) p *= 1.8;
          if (c.ageDays(s.day) < 120) p *= 1.6;
          if (rng.chance(p)) {
            c.health = HealthStatus.sick;
            c.sickDays = 0;
            c.illness = rng.pick(_illnesses);
            _news(NewsKind.warning,
                '${c.name} عليها أعراض ${c.illness}. تحتاج بيطري.',
                camelId: c.id);
          }
        case HealthStatus.sick:
          c.sickDays++;
          if (c.sickDays > 10 && rng.chance(0.006 + (c.sickDays - 10) * 0.0008)) {
            dead.add(c);
          } else if (c.sickDays > 25 && rng.chance(0.03)) {
            // Some recover on their own.
            c.health = HealthStatus.healthy;
            c.illness = null;
            _news(NewsKind.good, '${c.name} تعافت بدون علاج.', camelId: c.id);
          }
        case HealthStatus.treated:
          c.sickDays++;
          if (c.sickDays >= 0) {
            c.health = HealthStatus.healthy;
            c.illness = null;
            _news(NewsKind.good, '${c.name} تعافت وردّت لحالتها.',
                camelId: c.id);
          }
      }

      final years = c.ageYears(s.day);
      if (years >= 22 && rng.chance(0.0004 * (years - 21))) dead.add(c);
      if (years >= maxAgeYears) dead.add(c);
    }

    for (final c in dead.toSet()) {
      _removeFromHerd(c);
      _news(NewsKind.bad,
          'نفقت ${c.name} (${c.ageLabel(s.day)}). الله يعوضك.',
          camelId: c.id);
    }
  }

  void _removeFromHerd(Camel c) {
    s.camels.remove(c.id);
    final mine = s.listings.where((l) => l.camelId == c.id).toList();
    for (final l in mine) {
      s.listings.remove(l);
      s.buyerOffers.removeWhere((o) => o.listingId == l.id);
    }
    for (final f in s.festivals) {
      for (final r in f.rounds) {
        r.entries.remove(c.id);
      }
    }
  }

  ActionResult treat(String camelId) {
    final c = camel(camelId);
    if (c == null || !c.isPlayers) return const ActionResult.fail('الناقة مو لك');
    if (c.health != HealthStatus.sick) {
      return const ActionResult.fail('ما تحتاج علاج');
    }
    final cost = Valuation.roundPrice(
        rng.range(vetTreatmentMin, vetTreatmentMax).toDouble());
    _money(-cost, LedgerCategory.vet, 'علاج ${c.name} من ${c.illness}');
    c.health = HealthStatus.treated;
    // Recovers after 4–9 days; sickDays counts up to 0.
    c.sickDays = -rng.range(4, 9);
    _sync();
    return ActionResult.ok('البيطري عالج ${c.name}. التكلفة ${riyal(cost)}');
  }

  // ------------------------------------------------------------- breeding

  bool isBreedingSeason([int? day]) =>
      breedingMonths.contains(dateOfDay(day ?? s.day).month);

  /// Why [female] cannot be mated today, or null if she can.
  String? femaleProblem(Camel f) {
    if (f.sex != Sex.female) return 'لازم تكون ناقة';
    if (f.ageYears(s.day) < femaleMinBreedingYears) {
      return 'صغيرة على التلقيح (أقل من $femaleMinBreedingYears سنين)';
    }
    if (f.pregnancy != null) {
      return f.pregnancy!.confirmed ? 'عشراء (حامل)' : 'تنتظر فحص الحمل';
    }
    if (f.lastCalvingDay != null &&
        s.day - f.lastCalvingDay! < postCalvingRestDays) {
      final left = postCalvingRestDays - (s.day - f.lastCalvingDay!);
      return 'قريبة ولادة، تحتاج راحة ${formatDays(left)}';
    }
    if (f.health != HealthStatus.healthy) return 'مريضة';
    if (!isBreedingSeason()) {
      return 'مو موسم التلقيح (من نوفمبر إلى أبريل)';
    }
    return null;
  }

  String? bullProblem(Camel m) {
    if (m.sex != Sex.male) return 'لازم يكون جمل';
    if (m.ageYears(s.day) < maleMinBreedingYears) {
      return 'صغير على الضراب (أقل من $maleMinBreedingYears سنين)';
    }
    if (m.health != HealthStatus.healthy) return 'مريض';
    if (m.lastServiceDay != null && s.day - m.lastServiceDay! < studRestDays) {
      return 'ضرب قريب، يحتاج راحة';
    }
    return null;
  }

  ActionResult mate(String femaleId, String bullId, {StudOffer? stud}) {
    final f = camel(femaleId);
    final m = camel(bullId);
    if (f == null || !f.isPlayers) return const ActionResult.fail('الناقة مو لك');
    if (m == null) return const ActionResult.fail('الفحل مو موجود');
    if (stud == null && !m.isPlayers) {
      return const ActionResult.fail('الفحل مو لك');
    }
    final fp = femaleProblem(f);
    if (fp != null) return ActionResult.fail(fp);
    final mp = bullProblem(m);
    if (mp != null) return ActionResult.fail(mp);

    if (stud != null) {
      final km = s.farm.region.roadKmTo(stud.region);
      final move = transportCost(km, 1);
      if (s.cash < stud.fee + move) {
        return const ActionResult.fail('الرصيد ما يكفي لأجرة الفحل والنقل');
      }
      _money(-stud.fee, LedgerCategory.studFee,
          'أجرة الفحل ${m.name} (${stud.ownerName}) لـ ${f.name}');
      if (move > 0) {
        _money(-move, LedgerCategory.transport,
            'نقل ${f.name} إلى ${stud.region.label} ($km كم)');
      }
    }

    var p = baseConceptionRate;
    if (f.condition < 55) p -= 0.15;
    if (f.condition > 80) p += 0.05;
    if (f.ageYears(s.day) > 16) p -= 0.15;
    final conceived = rng.chance(p);
    final due = s.day + gestationDays + rng.range(-gestationSpread, gestationSpread);
    f.pregnancy = Pregnancy(
      sire: m.ref,
      sireGenes: Map.of(m.genes),
      matedDay: s.day,
      checkDay: s.day + pregnancyCheckDays,
      dueDay: due,
      conceived: conceived,
    );
    m.lastServiceDay = s.day;
    _news(NewsKind.info,
        'انضربت ${f.name} من ${m.name}. فحص الحمل بعد ${formatDays(pregnancyCheckDays)}.',
        camelId: f.id);
    _sync();
    return ActionResult.ok(
        'تم التلقيح. نعرف النتيجة بعد ${formatDays(pregnancyCheckDays)}');
  }

  void _pregnancies() {
    final births = <Camel>[];
    for (final f in s.herd) {
      final p = f.pregnancy;
      if (p == null) continue;
      if (!p.confirmed && s.day >= p.checkDay) {
        if (p.conceived) {
          p.confirmed = true;
          _news(NewsKind.good,
              '${f.name} عشراء من ${p.sire.name}. الولادة المتوقعة ${formatDate(dateOfDay(p.dueDay))}.',
              camelId: f.id);
        } else {
          f.pregnancy = null;
          _news(NewsKind.warning,
              '${f.name} ما لقحت من ${p.sire.name}. تقدر تعيد التلقيح.',
              camelId: f.id);
        }
      } else if (p.confirmed && s.day >= p.dueDay) {
        births.add(f);
      }
    }
    for (final dam in births) {
      _birth(dam);
    }
  }

  void _birth(Camel dam) {
    final p = dam.pregnancy!;
    dam.pregnancy = null;
    dam.lastCalvingDay = s.day;
    dam.calvings++;

    final crossbred = p.sire.category != dam.category || dam.crossbred;
    final sex = rng.chance(0.5) ? Sex.female : Sex.male;
    final calf = Camel(
      id: s.newId('c'),
      name: randomCamelName(rng, female: sex == Sex.female),
      sex: sex,
      category: Genetics.calfCategory(rng, p.sire.category, dam.category),
      birthDay: s.day,
      ownerId: playerOwnerId,
      chip: randomChipNumber(rng),
      genes: Genetics.inherit(rng, p.sireGenes, dam.genes, crossbred: crossbred),
      env: Genetics.randomEnv(rng),
      condition: clampDouble(dam.condition - 5, 40, 90),
      sire: p.sire,
      dam: dam.ref,
      acquiredDay: s.day,
      crossbred: crossbred,
    );

    // Newborn losses happen even with good care.
    final lossChance = 0.03 + (dam.condition < 50 ? 0.05 : 0);
    if (rng.chance(lossChance)) {
      _news(NewsKind.bad,
          'ولدت ${dam.name} لكن الحوار ما عاش. الله يعوضك.',
          camelId: dam.id);
      return;
    }
    s.camels[calf.id] = calf;
    final kind = sex == Sex.female ? 'حوارة (أنثى)' : 'حوار (ذكر)';
    _news(NewsKind.birth,
        'ولدت ${dam.name} $kind من ${p.sire.name}، وسمّيناه "${calf.name}". تقدر تغير الاسم.',
        camelId: calf.id);
  }

  ActionResult rename(String camelId, String name) {
    final c = camel(camelId);
    final n = name.trim();
    if (c == null || !c.isPlayers) return const ActionResult.fail('مو من حلالك');
    if (n.isEmpty || n.length > 24) {
      return const ActionResult.fail('الاسم لازم يكون من 1 إلى 24 حرف');
    }
    c.name = n;
    return const ActionResult.ok('تم تغيير الاسم');
  }

  // ---------------------------------------------------------------- farm

  ActionResult expand() {
    final cost = expansionCost();
    if (s.cash < cost) return const ActionResult.fail('الرصيد ما يكفي للتوسعة');
    _money(-cost, LedgerCategory.construction,
        'توسعة العزبة +$expansionStep (شبوك ومظلات ومشارب)');
    s.farm.capacity += expansionStep;
    return ActionResult.ok('صارت العزبة تتسع ${s.farm.capacity} راس');
  }

  ActionResult setShepherds(int n) {
    if (n < 1 || n > 40) return const ActionResult.fail('عدد غير منطقي');
    s.farm.shepherds = n;
    return ActionResult.ok('عدد الرعاة صار $n');
  }

  void setFeedPlan(FeedPlan plan) => s.farm.feedPlan = plan;

  // -------------------------------------------------------------- market

  Camel? listingCamel(Listing l) => s.camels[l.camelId];

  int transportToFarm(Region from, [int head = 1]) =>
      transportCost(from.roadKmTo(s.farm.region), head);

  ActionResult buy(String listingId, {int? price}) {
    final l = _listing(listingId);
    if (l == null) return const ActionResult.fail('العرض انتهى');
    if (l.sellerId == playerOwnerId) {
      return const ActionResult.fail('هذا عرضك');
    }
    final c = s.camels[l.camelId]!;
    final pay = price ?? l.askPrice;
    final move = transportToFarm(l.region);
    if (s.cash < pay + move) {
      return ActionResult.fail(
          'الرصيد ما يكفي. تحتاج ${riyal(pay + move)} مع النقل');
    }
    if (s.herdSize >= s.farm.capacity) {
      return const ActionResult.fail('العزبة ممتلية. وسّعها أو بِع من الحلال');
    }
    _money(-pay, LedgerCategory.purchase,
        'شراء ${c.name} (${c.category.label}) من ${l.sellerName}');
    if (move > 0) {
      _money(-move, LedgerCategory.transport,
          'نقل ${c.name} من ${l.region.label} إلى العزبة');
    }
    c.ownerId = playerOwnerId;
    c.acquiredDay = s.day;
    c.purchasePrice = pay;
    s.listings.remove(l);
    _news(NewsKind.market,
        'اشتريت ${c.name} بـ ${riyal(pay)} من ${l.sellerName} (${l.region.marketName}).',
        camelId: c.id);
    _sync();
    return ActionResult.ok('مبروك! ${c.name} صارت من حلالك');
  }

  /// The player bargains (يسوم) on a market camel.
  ActionResult bargain(String listingId, int offer) {
    final l = _listing(listingId);
    if (l == null) return const ActionResult.fail('العرض انتهى');
    if (l.bargains >= 3) {
      return ActionResult.fail('${l.sellerName} ما عاد يقبل سوم على هذي');
    }
    if (offer >= l.askPrice) return buy(listingId);
    l.bargains++;
    if (offer >= l.reservePrice) {
      return buy(listingId, price: offer);
    }
    if (offer >= l.reservePrice * 0.85) {
      // Counter-offer: meet half-way, never under his floor.
      final counter = Valuation.roundPrice((offer + l.askPrice) / 2);
      l.askPrice = math.min(l.askPrice, math.max(l.reservePrice, counter));
      _sync();
      return ActionResult.fail(
          '${l.sellerName}: "ما تمشي، بس عشانك ${riyal(l.askPrice)} وتوكل على الله"');
    }
    _sync();
    return ActionResult.fail('${l.sellerName}: "السوم بعيد، الله يرزقك"');
  }

  String? sellProblem(Camel c) {
    if (!c.isPlayers) return 'مو من حلالك';
    if (s.listings.any((l) => l.camelId == c.id)) return 'معروضة في السوق';
    if (_enteredAnywhere(c.id)) return 'مسجلة في مهرجان';
    return null;
  }

  ActionResult listForSale(String camelId, int askPrice) {
    final c = camel(camelId);
    if (c == null) return const ActionResult.fail('مو موجودة');
    final problem = sellProblem(c);
    if (problem != null) return ActionResult.fail(problem);
    if (askPrice < 1000) return const ActionResult.fail('السعر قليل');
    s.listings.add(Listing(
      id: s.newId('l'),
      camelId: c.id,
      sellerId: playerOwnerId,
      sellerName: s.playerName,
      region: s.farm.region,
      askPrice: askPrice,
      reservePrice: askPrice,
      listedDay: s.day,
      expiresDay: s.day + 45,
    ));
    _news(NewsKind.market,
        'عرضت ${c.name} في ${s.farm.region.marketName} بـ ${riyal(askPrice)}.',
        camelId: c.id);
    return const ActionResult.ok('انعرضت في السوق. السوّام بيجونك');
  }

  ActionResult cancelListing(String listingId) {
    final l = _listing(listingId);
    if (l == null || l.sellerId != playerOwnerId) {
      return const ActionResult.fail('العرض مو موجود');
    }
    s.listings.remove(l);
    s.buyerOffers.removeWhere((o) => o.listingId == l.id);
    return const ActionResult.ok('سحبت العرض من السوق');
  }

  ActionResult acceptOffer(String offerId) {
    final o = s.buyerOffers.where((x) => x.id == offerId).firstOrNull;
    if (o == null) return const ActionResult.fail('السوم انتهى');
    final l = _listing(o.listingId);
    if (l == null) return const ActionResult.fail('العرض انتهى');
    return _sell(s.camels[l.camelId]!, o.amount, o.buyerName, l);
  }

  void declineOffer(String offerId) =>
      s.buyerOffers.removeWhere((o) => o.id == offerId);

  /// Selling straight to the broker for a quick, lower price.
  int quickSalePrice(Camel c) =>
      Valuation.roundPrice(Valuation.value(c, s.day) * quickSaleFactor);

  ActionResult quickSale(String camelId) {
    final c = camel(camelId);
    if (c == null) return const ActionResult.fail('مو موجودة');
    final problem = sellProblem(c);
    if (problem != null) return ActionResult.fail(problem);
    return _sell(c, quickSalePrice(c), 'الدلال', null);
  }

  ActionResult _sell(Camel c, int price, String buyer, Listing? l) {
    final commission = (price * brokerCommission).round();
    _money(price, LedgerCategory.sale, 'بيع ${c.name} على $buyer');
    _money(-commission, LedgerCategory.commission, 'سعي بيع ${c.name}');
    if (l != null) {
      s.listings.remove(l);
      s.buyerOffers.removeWhere((x) => x.listingId == l.id);
    }
    final profit = price - commission - c.purchasePrice;
    _removeFromHerd(c);
    _news(NewsKind.market,
        'بعت ${c.name} على $buyer بـ ${riyal(price)}${c.purchasePrice > 0 ? (profit >= 0 ? '، بربح ${riyal(profit)}' : '، بخسارة ${riyal(-profit)}') : ''}.');
    _sync();
    return ActionResult.ok('انباعت ${c.name} بـ ${riyal(price)}');
  }

  Listing? _listing(String id) =>
      s.listings.where((l) => l.id == id).firstOrNull;

  void _market() {
    // Expired market camels leave with their owners.
    final expired = s.listings.where((l) => l.expiresDay < s.day).toList();
    for (final l in expired) {
      s.listings.remove(l);
      if (l.sellerId == playerOwnerId) {
        s.buyerOffers.removeWhere((o) => o.listingId == l.id);
        final c = s.camels[l.camelId];
        if (c != null) {
          _news(NewsKind.market,
              'انتهت مدة عرض ${c.name} بدون بيع. جرّب سعر أقرب للسوق.',
              camelId: c.id);
        }
      } else {
        s.camels.remove(l.camelId);
      }
    }
    s.buyerOffers.removeWhere((o) => o.expiresDay < s.day);

    // New camels come to market every day.
    final npcListings =
        s.listings.where((l) => l.sellerId != playerOwnerId).length;
    final arrivals = npcListings < 26 ? rng.range(1, 3) : rng.range(0, 1);
    for (var i = 0; i < arrivals; i++) {
      world.addMarketListing();
    }

    // Buyers bargain on the player's listings.
    for (final l in s.listings.where((l) => l.sellerId == playerOwnerId)) {
      final c = s.camels[l.camelId];
      if (c == null) continue;
      final value = Valuation.value(c, s.day);
      final ratio = l.askPrice / math.max(1, value);
      final p = clampDouble(0.32 * math.pow(1 / ratio, 3).toDouble(), 0.01, 0.6);
      final open = s.buyerOffers.where((o) => o.listingId == l.id).length;
      if (open < 3 && rng.chance(p)) {
        final buyer = world.randomOwner();
        var amount = Valuation.roundPrice(value * rng.rangeDouble(0.8, 1.04));
        if (amount >= l.askPrice) amount = l.askPrice;
        s.buyerOffers.add(BuyerOffer(
          id: s.newId('b'),
          listingId: l.id,
          buyerName: buyer.name,
          buyerRegion: buyer.region,
          amount: amount,
          day: s.day,
          expiresDay: s.day + 3,
        ));
        _news(NewsKind.market,
            '${buyer.name} من ${buyer.region.label} سام ${c.name} بـ ${riyal(amount)}.',
            camelId: c.id);
      }
    }

    // Studs at service.
    s.studs.removeWhere((st) {
      final gone = st.untilDay < s.day;
      if (gone) s.camels.remove(st.camelId);
      return gone;
    });
    final wantStuds = isBreedingSeason() ? 9 : 4;
    if (s.studs.length < wantStuds && rng.chance(0.3)) world.addStud();
  }

  // ------------------------------------------------------------- contests

  bool _enteredAnywhere(String camelId) => s.festivals.any(
      (f) => !f.done && f.rounds.any((r) => r.entries.contains(camelId)));

  /// Minimum days a camel must be registered in the owner's name before the
  /// judging day (ownership transfer rule; game rule).
  static const ownershipDaysBeforeJudging = 30;

  String? entryProblem(Camel c, Festival f, ContestRound r) {
    if (!c.isPlayers) return 'مو من حلالك';
    if (!f.isRegistrationOpen(s.day)) return 'التسجيل مقفل';
    if (c.category != r.category) return 'الفئة ${r.category.label} بس';
    if (c.sex != r.sex) return r.sex == Sex.female ? 'للنوق' : 'للقعدان';
    final ageThen = AgeClass.fromDays(f.judgingDay - c.birthDay);
    if (ageThen != r.age) {
      return 'عمرها يوم التحكيم ${ageThen.labelFor(c.sex)}';
    }
    final homeBred = c.acquiredDay == c.birthDay;
    if (!homeBred &&
        f.judgingDay - c.acquiredDay < ownershipDaysBeforeJudging) {
      return 'الملكية لازم تكون باسمك قبل التحكيم بـ$ownershipDaysBeforeJudging يوم';
    }
    if (f.rounds.any((x) => x.entries.contains(c.id))) {
      return 'مسجلة في شوط ثاني بنفس المهرجان';
    }
    if (s.listings.any((l) => l.camelId == c.id)) return 'معروضة للبيع';
    if (c.health == HealthStatus.sick) return 'مريضة';
    if (r.entries.length >= 3) return 'الحد 3 من كل مالك في الشوط';
    return null;
  }

  ActionResult enter(String festivalId, String roundId, String camelId) {
    final f = s.festivals.where((x) => x.id == festivalId).firstOrNull;
    final r = f?.rounds.where((x) => x.id == roundId).firstOrNull;
    final c = camel(camelId);
    if (f == null || r == null || c == null) {
      return const ActionResult.fail('غير موجود');
    }
    final problem = entryProblem(c, f, r);
    if (problem != null) return ActionResult.fail(problem);
    r.entries.add(c.id);
    _news(NewsKind.contest, 'سجّلت ${c.name} في ${r.title} - ${f.name}.',
        camelId: c.id);
    return ActionResult.ok('تم تسجيل ${c.name} في ${r.title}');
  }

  ActionResult withdraw(String festivalId, String roundId, String camelId) {
    final f = s.festivals.where((x) => x.id == festivalId).firstOrNull;
    final r = f?.rounds.where((x) => x.id == roundId).firstOrNull;
    if (r == null || f!.done) return const ActionResult.fail('غير موجود');
    r.entries.remove(camelId);
    return const ActionResult.ok('انسحبت من الشوط');
  }

  void _contests() {
    for (final f in s.festivals) {
      if (f.done) continue;
      if (f.registrationOpens == s.day) {
        _news(NewsKind.contest,
            'فتح التسجيل في ${f.name} (${f.tier.label}). التحكيم ${formatDate(dateOfDay(f.judgingDay))}.');
      }
      if (f.registrationCloses - s.day == 3) {
        _news(NewsKind.contest, 'باقي 3 أيام ويقفل التسجيل في ${f.name}.');
      }
      if (s.day >= f.judgingDay) _runFestival(f);
    }
  }

  void _runFestival(Festival f) {
    f.done = true;
    final entered = <Camel>[];
    for (final r in f.rounds) {
      for (final id in r.entries) {
        final c = s.camels[id];
        if (c != null) entered.add(c);
      }
    }
    if (entered.isEmpty) return;

    // Trucking to the festival and back.
    final km = s.farm.region.roadKmTo(f.region);
    final move = transportCost(km, entered.length) * 2;
    _money(-move, LedgerCategory.transport,
        'نقل ${entered.length} راس إلى ${f.name} والرجعة ($km كم)');

    var prizes = 0;
    for (final r in f.rounds) {
      if (r.entries.isEmpty) continue;
      final rows = <_Scored>[];

      for (final id in r.entries) {
        final c = s.camels[id];
        if (c == null) continue;
        if (c.health == HealthStatus.sick) {
          _news(NewsKind.warning,
              'الفحص البيطري استبعد ${c.name} من ${r.title} لأنها مريضة.',
              camelId: c.id);
          continue;
        }
        final js = Judging.judge(rng, Judging.phenotypes(c, s.day));
        rows.add(_Scored(js.total, c.name, s.playerName, c.id, js.marks));
      }
      final (mean, sd) = WorldGen.rivalQuality(f.tier);
      for (var i = 0; i < r.fieldSize; i++) {
        final q = rng.gaussian(mean: mean, sd: sd);
        final phen = {
          for (final t in Trait.values)
            t: clampDouble(q + rng.gaussian(sd: 6), 0, 100),
        };
        final js = Judging.judge(rng, phen);
        final owner = world.randomOwner();
        rows.add(_Scored(js.total,
            randomCamelName(rng, female: r.sex == Sex.female), owner.name,
            null, null));
      }
      rows.sort((a, b) => b.score.compareTo(a.score));

      final results = <ResultRow>[];
      for (var i = 0; i < rows.length; i++) {
        final row = rows[i];
        final rank = i + 1;
        final prize = rank <= r.prizes.length ? r.prizes[rank - 1] : 0;
        final mine = row.camelId != null;
        if (mine || rank <= 10) {
          results.add(ResultRow(
            rank: rank,
            camelName: row.name,
            ownerName: row.owner,
            score: row.score,
            prize: prize,
            camelId: row.camelId,
            isPlayer: mine,
            breakdown: row.marks,
          ));
        }
        if (mine) {
          final c = s.camels[row.camelId]!;
          if (prize > 0) {
            prizes += prize;
            _money(prize, LedgerCategory.prize,
                'جائزة المركز $rank - ${r.title} - ${f.name}');
            c.titles.add(ContestTitle(
              festival: f.name,
              round: r.title,
              rank: rank,
              day: s.day,
              tier: f.tier.level,
              prize: prize,
            ));
            _news(rank <= 3 ? NewsKind.good : NewsKind.contest,
                '${c.name} أخذت المركز $rank في ${r.title} - ${f.name} وجائزتها ${riyal(prize)}.',
                camelId: c.id);
          } else {
            _news(NewsKind.contest,
                '${c.name} جات $rank من ${rows.length} في ${r.title} (${row.score.toStringAsFixed(1)} من 100).',
                camelId: c.id);
          }
        }
      }
      r.results = results;
    }
    if (prizes > 0) {
      _news(NewsKind.good,
          'مجموع جوائزك في ${f.name}: ${riyal(prizes)}.');
    }
  }
}

class _Scored {
  _Scored(this.score, this.name, this.owner, this.camelId, this.marks);
  final double score;
  final String name;
  final String owner;
  final String? camelId;
  final Map<Trait, double>? marks;
}
