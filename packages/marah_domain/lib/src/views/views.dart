import '../catalog/catalog.dart';
import '../catalog/region.dart';
import '../common/ids.dart';
import '../common/money.dart';
import '../common/result.dart';
import '../common/rng.dart';
import '../common/time.dart';
import '../handlers/handlers.dart' as handlers;
import '../model/camel.dart';
import '../model/contest.dart';
import '../model/game_state.dart';
import '../model/market.dart';
import '../model/player.dart';
import '../model/tampering.dart';
import '../rules/account.dart';
import '../rules/balance.dart';
import '../rules/contest_rules.dart';
import '../rules/eligibility.dart';
import '../rules/judging.dart';
import '../rules/milk.dart';
import '../rules/pasture.dart';
import '../rules/provisions.dart';
import '../rules/valuation.dart';
import '../sim.dart';
import '../systems/systems.dart';
import 'money.dart';

/// One nursing camel's milk today, as the player sees it.
class MilkView {
  const MilkView({
    required this.camel,
    required this.days,
    required this.calf,
    required this.litres,
    required this.sold,
  });
  final CamelView camel;

  /// Days since she calved.
  final int days;
  final CamelView? calf;
  final double litres;
  final double sold;
}

/// What one player is allowed to see of a camel: what the eye sees and
/// what is on record. Breeding values, hidden deviations, the exact market
/// value and an unchecked pregnancy's outcome are never exposed.
class CamelView {
  CamelView._(this._c, this._today, this._viewer, this._seed);

  final Camel _c;
  final GameDay _today;
  final OwnerId _viewer;
  final int _seed;

  CamelId get id => _c.id;
  String get name => _c.name;
  Sex get sex => _c.sex;
  ColorCategory get category => _c.category;
  GameDay get born => _c.born;

  /// The day it came to its owner's farm (its birth for one born there).
  GameDay get acquiredOn => _c.acquiredOn;

  /// Bought today and on the truck: the farm has it tomorrow.
  bool get onTheWay => isMine && Eligibility.onTheWay(_c, _today);
  int get ageDays => _c.ageDays(_today);
  AgeClass get ageClass => _c.ageClass(_today);
  String get chip => _c.chip;
  OwnerId get ownerId => _c.ownerId;
  bool get isMine => _c.ownerId == _viewer && _c.isAlive;
  bool get isAlive => _c.isAlive;
  CamelStatus get status => _c.status;
  double get condition => _c.condition;
  HealthStatus get health => _c.health;
  Illness? get illness => _c.illness;
  GameDay? get sickSince => _c.sickSince;
  bool get crossbred => _c.crossbred;
  ParentRef? get sire => _c.sire;
  ParentRef? get dam => _c.dam;
  int get calvings => _c.calvings;
  GameDay? get lastCalvedOn => _c.lastCalvedOn;
  List<Placing> get placings => List.unmodifiable(_c.placings);
  int get purchasePrice => isMine ? _c.purchasePrice : 0;

  /// Mated and waiting for the check (outcome unknown). Only the owner
  /// knows a mating happened.
  bool get awaitingCheck =>
      isMine && _c.pregnancy != null && !_c.pregnancy!.confirmed;
  bool get pregnant => _c.pregnancyConfirmed;
  String? get pregnantBy => pregnant ? _c.pregnancy!.sire.name : null;
  GameDay? get dueOn => pregnant ? _c.pregnancy!.dueOn : null;

  /// Observed features 0–100 (what judges and buyers see).
  Map<Trait, double> get looks => Judging.observedAll(_c, _today);
  double get quality => Judging.quality(_c, _today);

  /// What the market would pay, as this viewer hears it: an appraisal that
  /// differs from the true value by a few percent (different for each
  /// viewer and each week), shown as a range around it. The exact value and
  /// the hidden sire genes behind it cannot be read back from the range.
  (Riyal, Riyal) get estimate {
    final a = appraise(_c, _today, _viewer, _seed);
    return (marketRound(a * 0.9), marketRound(a * 1.1));
  }

  /// The appraisal behind [estimate]: [c]'s value as [viewer] hears it this
  /// week, a few percent off the true value.
  static double appraise(Camel c, GameDay today, OwnerId viewer, int seed) =>
      _appraised(c, today, appraisalKey(seed, viewer));

  /// The fixed part of [viewer]'s appraisals' key, hashed once for a herd.
  static int appraisalKey(int seed, OwnerId viewer) =>
      Rng.hashMore(Rng.hashStart(seed), ['appraise', viewer.value]);

  static double _appraised(Camel c, GameDay today, int key) {
    final value = Valuation.value(c, today).value.toDouble();
    final rng = Rng(Rng.hashMore(key, [c.id.value, today.value ~/ 7]));
    return value * (1 + clampDouble(rng.normal(sd: 0.06), -0.15, 0.15));
  }

  /// [herd]'s worth as [viewer] hears it: the sum of the appraisals behind
  /// each camel's range.
  static double appraiseAll(
    Iterable<Camel> herd,
    GameDay today,
    OwnerId viewer,
    int seed,
  ) {
    final key = appraisalKey(seed, viewer);
    var sum = 0.0;
    for (final c in herd) {
      sum += _appraised(c, today, key);
    }
    return sum;
  }
}

/// A market listing as buyers see it: never the seller's floor price.
class ListingView {
  ListingView._(
    Listing listing,
    this.camel,
    this.sellerName,
    this.transport,
    this.knownTreatments,
  ) : id = listing.id,
      declared = listing.declared,
      timesChecked = listing.checks[camel._viewer.value] ?? 0,
      askPrice = listing.askPrice,
      region = listing.region,
      expiresOn = listing.expiresOn,
      listedOn = listing.listedOn,
      sellerId = listing.sellerId;

  final ListingId id;
  final Riyal askPrice;
  final Region region;
  final GameDay expiresOn;
  final GameDay listedOn;
  final OwnerId sellerId;
  final CamelView camel;
  final String sellerName;

  /// Trucking it to the viewer's farm.
  final Riyal transport;

  /// Treatments in her the viewer's vet found (CheckListing); never one he
  /// was not told of.
  final List<TamperKind> knownTreatments;

  /// How many times the viewer's vet has looked at her (so the phone can
  /// say "checked N times, nothing found").
  final int timesChecked;

  /// Offered as treated: [knownTreatments] then shows every buyer what is
  /// in her (the owner's decision 15).
  final bool declared;
}

class StudView {
  StudView._(this.stud, this.bull, this.ownerName, this.transport);
  final StudOffer stud;
  final CamelView bull;
  final String ownerName;
  final Riyal transport;
}

/// Read-only projection of the game for one player. Screens use this and
/// commands; they never touch the state directly.
class GameView {
  GameView(this._state, this.viewer);

  final GameState _state;
  final OwnerId viewer;

  WorldState get _w => _state.world;
  GameDay get today => _w.day;
  PlayerState get me => _state.players[viewer]!;
  Sim get _sim => Sim(_state);

  CamelView _view(Camel c) => CamelView._(c, today, viewer, _w.seed);

  CamelView? camel(CamelId id) {
    final c = _w.camels[id];
    return c == null ? null : _view(c);
  }

  List<CamelView> get herd => [
    for (final c in _w.aliveOwnedBy(viewer)) _view(c),
  ];

  String ownerName(OwnerId id) =>
      _state.players[id]?.name ?? _w.owners[id]?.name ?? '';

  List<ListingView> get market => [
    for (final l in _w.listings.values)
      if (l.sellerId != viewer) _listing(l),
  ];

  List<ListingView> get myListings => [
    for (final l in _w.listings.values)
      if (l.sellerId == viewer) _listing(l),
  ];

  ListingView? listingOf(CamelId camel) {
    final l = _w.listings.values.where((x) => x.camelId == camel).firstOrNull;
    return l == null ? null : _listing(l);
  }

  ListingView _listing(Listing l) {
    final c = _w.camels[l.camelId]!;
    return ListingView._(
      l,
      _view(c),
      ownerName(l.sellerId),
      Riyal(handlers.transportToFarm(me, l)),
      [
        for (final t in c.treatments)
          if (t.activeOn(today) &&
              (l.declared || t.knownBy.contains(viewer) || t.by == viewer))
            t.kind,
      ],
    );
  }

  /// Bargaining attempts the viewer has left on a listing.
  int bargainsLeft(ListingId id) =>
      Balance.maxBargainsPerBuyer -
      (_w.listings[id]?.bargains[viewer.value] ?? 0);

  /// Buyers' offers, only on the viewer's own listings.
  List<Offer> offersOn(ListingId id) {
    if (_w.listings[id]?.sellerId != viewer) return const [];
    return [
      for (final o in _w.offers.values)
        if (o.listingId == id) o,
    ];
  }

  int get openOffers => _w.offers.values
      .where((o) => _w.listings[o.listingId]?.sellerId == viewer)
      .length;

  List<StudView> get studs => [
    for (final s in _w.studs.values)
      if (_w.camels[s.camelId]?.isAlive ?? false)
        StudView._(
          s,
          _view(_w.camels[s.camelId]!),
          ownerName(s.ownerId),
          Riyal(Balance.transportCost(s.region.roadKmTo(me.farm.region), 1)),
        ),
  ];

  /// The festivals as this player may see them (FestivalView): never
  /// another owner's entries, their marks, or places not yet announced.
  List<FestivalView> get festivals => [
    for (final f
        in _w.festivals.values.toList()
          ..sort((a, b) => a.startsOn.value - b.startsOn.value))
      FestivalView._(f, this),
  ];

  FestivalView? festival(FestivalId id) {
    final f = _w.festivals[id];
    return f == null ? null : FestivalView._(f, this);
  }

  /// The last season the player is barred from festivals through (GDD 7.1),
  /// or null.
  int? get bannedThrough => _w.bans[viewer];

  /// الصيت in each family (GDD 8) as the player hears it: a band, never
  /// the number (Balance.reputationBand).
  Map<ColorCategory, ReputationBand> get reputation => {
    for (final c in ColorCategory.values)
      c: Balance.reputationBand(me.reputationIn(c)),
  };

  /// The secret treatment man's messages (the oldest first) and how many
  /// are unread.
  List<DealerMessage> get dealerMessages => List.unmodifiable(me.dealer);
  int get unreadMessages => me.dealer.where((m) => !m.read).length;

  /// Treatments found outside a festival and a sale, not yet told.
  List<Finding> get untoldFindings => List.unmodifiable(me.untold);

  /// الفحل وإنتاجه at festival [f] for [bull]: the round, the group the
  /// player would show (the bull, then his best offspring by look in the
  /// herd, as many as the round takes: (balance) the engine picks them, the
  /// phone does not choose), and why it cannot be entered now, or null.
  /// Too few offspring: wrongGroupSize with the round's size and the head he
  /// has ('have'). Null round: no الفحل وإنتاجه here, or not a grown bull.
  (RoundId?, List<CamelId>, DomainError?) fahalGroup(
    FestivalId f,
    CamelId bull,
  ) {
    final fest = _w.festivals[f];
    final c = _w.camels[bull];
    final r = fest?.rounds.where((x) => x.kind == RoundKind.fahal).firstOrNull;
    if (fest == null ||
        c == null ||
        r == null ||
        c.sex != Sex.male ||
        c.ageYears(r.day) < Balance.maleMinBreedingYears) {
      return (null, const [], null);
    }
    final kids =
        [
          for (final k in _w.aliveOwnedBy(viewer))
            if (k.sire?.id == bull) (k, Judging.quality(k, today)),
        ]..sort((a, b) {
          final d = b.$2.compareTo(a.$2);
          return d != 0 ? d : a.$1.id.value.compareTo(b.$1.id.value);
        });
    final group = [bull, for (final (k, _) in kids.take(r.size - 1)) k.id];
    if (group.length < r.size) {
      return (
        r.id,
        group,
        DomainError(ErrorCode.wrongGroupSize, {
          'size': r.size,
          'have': group.length,
        }),
      );
    }
    final e = handlers.cannotEnter(_sim, me, fest, r, [
      for (final id in group) _w.camels[id],
    ]);
    return (r.id, group, e);
  }

  /// [c]'s own round at festival [f] (its colour, its sex, its age's kind on
  /// the round's day; الفحل وإنتاجه, a group, is not one) and why it cannot
  /// enter it now, or null: the round it may enter, else the one whose
  /// refusal says most (the money or the rules before its age's or calvings'
  /// kind, which before none). No round of its colour and sex there: null and
  /// wrongCategory.
  (RoundId?, DomainError?) ownRound(FestivalId f, CamelId c) {
    final fest = _w.festivals[f];
    final camel = _w.camels[c];
    if (fest == null || camel == null) {
      return (null, const DomainError(ErrorCode.notFound));
    }
    RoundId? best;
    DomainError? why;
    var rank = 99;
    int rankOf(DomainError? e) => switch (e?.code) {
      null => 0,
      ErrorCode.tooFewCalvings => 2,
      ErrorCode.wrongAgeClass => 3,
      _ => 1,
    };
    for (final r in fest.rounds) {
      if (!r.kind.single ||
          (r.category != null && r.category != camel.category) ||
          (r.sex != null && r.sex != camel.sex)) {
        continue;
      }
      final e = handlers.cannotEnter(_sim, me, fest, r, [camel]);
      final k = rankOf(e);
      if (k < rank) {
        rank = k;
        best = r.id;
        why = e;
        if (k == 0) break;
      }
    }
    if (best == null) {
      return (
        null,
        DomainError(ErrorCode.wrongCategory, {'category': camel.category.name}),
      );
    }
    return (best, why);
  }

  /// The secret treatments in the player's camels that he knows of (his
  /// own, or found by his vet), showing now, with their risk.
  List<TamperingView> get tamperings => [
    for (final c in _w.aliveOwnedBy(viewer))
      for (final t in c.treatments)
        if (t.activeOn(today) && t.knownBy.contains(viewer))
          TamperingView._(t, _view(c)),
  ];

  DomainError? canTamper(CamelId camel, TamperKind kind, int strength) =>
      handlers.cannotTamper(_sim, me, _w.camels[camel], kind, strength);

  // ------------------------------------------------------------- checks

  bool get breedingSeason => Eligibility.isBreedingSeason(today);

  DomainError? canBreed(CamelId female) {
    final c = _w.camels[female];
    return Eligibility.owned(c, viewer) ??
        Eligibility.femaleCanBreed(c!, today);
  }

  DomainError? canServe(CamelId bull) {
    final c = _w.camels[bull];
    if (c == null) return const DomainError(ErrorCode.notFound);
    return Eligibility.bullCanServe(c, today);
  }

  /// The camel is a calf still suckling its mother (Milk.suckling).
  bool suckling(CamelId id) {
    final c = _w.camels[id];
    return c != null && Milk.suckling(c, _w, today);
  }

  DomainError? canSell(CamelId id) =>
      Eligibility.canSell(_w, _w.camels[id], viewer);

  DomainError? canEnter(FestivalId f, RoundId r, List<CamelId> camels) {
    final fest = _w.festivals[f];
    final round = fest?.round(r);
    if (fest == null || round == null) {
      return const DomainError(ErrorCode.notFound);
    }
    return handlers.cannotEnter(_sim, me, fest, round, [
      for (final c in camels) _w.camels[c],
    ]);
  }

  /// Why the player may not enter [r] today whatever camels he brings (the
  /// owner's own checks of [canEnter]), or null.
  DomainError? mayEnter(FestivalId f, RoundId r) {
    final fest = _w.festivals[f];
    final round = fest?.round(r);
    if (fest == null || round == null) {
      return const DomainError(ErrorCode.notFound);
    }
    return Eligibility.ownerMayEnter(_w, fest, round, viewer, today);
  }

  /// What entering [head] camels today costs in fees (a late entry's).
  int entryFee(FestivalId f, int head) {
    final fest = _w.festivals[f];
    return fest != null && Eligibility.isLate(fest, today)
        ? Balance.lateEntryFee * head
        : 0;
  }

  // ------------------------------------------------------------- money

  Riyal get dailyFeed => UpkeepSystem.dailyFeed(_sim, me);

  // ------------------------------------------------------------ provisions

  /// The herd's needs a day under the current ration.
  ({double barley, double alfalfa, double water}) get dailyNeeds =>
      Provisions.needs(_w.aliveOwnedBy(viewer), me.farm.feedPlan, today);

  /// Feed, water and vet treatments on account and not yet paid, and the
  /// account's limit (Account; [needs] saves walking the herd again).
  int get onAccount => me.onAccount;
  int accountLimit([({double barley, double alfalfa, double water})? needs]) =>
      Account.limitFor(needs ?? dailyNeeds, me);

  /// Why a necessity costing [cost] cannot be bought now, from the money
  /// and then on account up to [limit] (accountFull), or null; and what of
  /// it would go on the account.
  DomainError? cannotPayNecessity(int cost, int limit) =>
      Account.canPay(me, cost, limit);
  int onAccountFor(int cost) => Account.shortfall(me, cost);

  /// What is in store now (kg or L), not counting orders on the way.
  double inStore(Supply s) => Provisions.stocked(me.farm, s, withOrders: false);

  /// Whole days a store lasts at today's needs (null when nothing is needed).
  /// [needs] saves walking the herd again when the caller has them already.
  int? daysLeft(
    Supply s, [
    ({double barley, double alfalfa, double water})? needs,
  ]) {
    final n = needs ?? dailyNeeds;
    return Provisions.daysLeft(inStore(s), switch (s) {
      Supply.barley => n.barley,
      Supply.alfalfa => n.alfalfa,
      Supply.water => n.water,
    });
  }

  /// Units of [s] that fit in the store or tank, orders on the way counted
  /// (water by the [tanker]'s load).
  int roomFor(Supply s, {Tanker tanker = Tanker.large}) {
    final size = s == Supply.water
        ? Provisions.tankerSize(tanker)
        : Provisions.unitSize(s);
    return Provisions.fits(me.farm, s, size);
  }

  /// What the herd's feed would cost a day under [plan].
  Riyal dailyFeedFor(FeedPlan plan) => Riyal(
    Provisions.feedCost(
      Provisions.needs(_w.aliveOwnedBy(viewer), plan, today),
      me.farm.region,
    ).round(),
  );

  /// The money in and out today (the ledger's entries of the day, the
  /// opening balance not among them, and today's milk, which the ledger
  /// keeps as one row a month).
  Riyal get todayNet => Riyal(
    me.ledger
            .where(
              (e) =>
                  e.day == today &&
                  e.category != LedgerCategory.opening &&
                  e.category != LedgerCategory.milk,
            )
            .fold(0, (n, e) => n + e.amount.value) +
        milkIncomeToday,
  );

  /// The bank (Money): every month's money in and out by kind, the newest
  /// first; today's money in and out; the opening balance.
  List<MonthMoney> get moneyMonths => Money.months(_state, viewer);

  MonthMoney? moneyMonth(String month) => Money.month(_state, viewer, month);

  ({int income, int spent}) get moneyToday =>
      Money.today(me, today, milkIncomeToday);

  Riyal get openingBalance => Riyal(Money.opening(me));

  /// The day the game began.
  GameDay get startedOn => _state.startedOn;

  /// Today's milk: each nursing camel's litres, what her calf keeps and
  /// what was sold.
  List<MilkView> get milk => [
    for (final m in Milk.today(_w, viewer, me.farm, today))
      MilkView(
        camel: _view(m.camel),
        days: m.days,
        calf: m.calf == null ? null : _view(m.calf!),
        litres: m.litres,
        sold: m.sold,
      ),
  ];

  /// What today's milk brought (none before the day's milking: a new
  /// game's first day).
  int get milkIncomeToday => me.farm.milkOn == today ? me.farm.milkIncome : 0;

  /// What the milk has brought this month.
  Riyal get milkThisMonth {
    final d = today.date;
    final month = '${d.year}-${d.month.toString().padLeft(2, '0')}';
    return me.ledger
            .where((e) => e.month == month && e.category == LedgerCategory.milk)
            .firstOrNull
            ?.amount ??
        Riyal.zero;
  }

  /// Why [f] cannot be built now (all built or building, or the money),
  /// or null.
  DomainError? cannotBuild(Facility f) => handlers.cannotBuild(me, f);

  /// What a [tanker] of water costs.
  Riyal tankerPrice(Tanker tanker) =>
      Riyal(Provisions.tankerPrice(tanker).round());

  /// Whether the farm's grazing is green, and so the days the herd can go
  /// without water now.
  bool get pastureGreen => Pasture.green(_w.seed, me.farm.region, today);
  int get thirstDays => Balance.thirstDays(today.month, green: pastureGreen);

  Riyal unitPrice(Supply s) =>
      Riyal(Provisions.unitPrice(s, me.farm.region).round());
  List<Delivery> get onTheWay => List.unmodifiable(me.farm.deliveries);
  int get dryDays => me.farm.dryDays;
  Riyal get monthlyWages =>
      Riyal(me.farm.shepherds * Balance.shepherdMonthlyWage);
  int get shepherdsNeeded => CareSystem.shepherdsNeeded(herd.length);

  /// What the broker pays now, only for the viewer's own camels.
  Riyal? quickSalePrice(CamelId id, {bool declared = false}) {
    final c = _w.camels[id];
    if (c == null || !c.isAlive || c.ownerId != viewer) return null;
    return handlers.quickSalePrice(c, _sim, declared: declared);
  }

  /// Why the viewer cannot sell [id] declared as treated (no treatment he
  /// knows of in her), or null (the owner's decision 15).
  DomainError? cannotDeclare(CamelId id) {
    final c = _w.camels[id];
    final own = Eligibility.owned(c, viewer);
    return own ?? handlers.cannotDeclare(_sim, me, c!);
  }

  /// The herd's worth as the viewer hears it: the sum of the appraisals
  /// behind each camel's range, so it sits within their ranges' sum (the
  /// re-review: one draw for the whole herd put it outside them one week in
  /// nine), and never the exact values' sum (with it, buying or selling one
  /// camel moved it by that camel's exact value). The key's fixed part is
  /// hashed once for the herd.
  Riyal get herdValue => marketRound(
    CamelView.appraiseAll(_w.aliveOwnedBy(viewer), today, viewer, _w.seed),
  );
}

/// A festival as one player sees it.
class FestivalView {
  FestivalView._(this._f, GameView v)
    : rounds = [for (final r in _f.rounds) RoundView._(r, _f, v)],
      late = Eligibility.isLate(_f, v.today),
      bannedThrough = Eligibility.ownerBan(v._w, v.viewer, _f),
      distanceKm = v.me.farm.region.roadKmTo(_f.region);

  final Festival _f;
  FestivalId get id => _f.id;
  String get name => _f.name;
  Region get region => _f.region;
  FestivalTier get tier => _f.tier;
  int get season => _f.season;
  GameDay get opensOn => _f.opensOn;
  GameDay get closesOn => _f.closesOn;
  GameDay get startsOn => _f.startsOn;
  GameDay get endsOn => _f.endsOn;
  bool get done => _f.done;
  bool registrationOpen(GameDay today) => _f.registrationOpen(today);
  final List<RoundView> rounds;

  /// Past the closing: an entry now is late, with its fee.
  final bool late;

  /// The player is barred from this festival, through this season.
  final int? bannedThrough;
  final int distanceKm;
}

/// A round as one player sees it: his own entries, the field's story by
/// stage, and the places once announced (other owners' rows without their
/// per-trait marks).
class RoundView {
  RoundView._(ContestRound r, Festival f, GameView v)
    : id = r.id,
      kind = r.kind,
      category = r.category,
      sex = r.sex,
      size = r.size,
      day = r.day,
      legacyAge = r.legacyAge,
      lastEntryDay = Eligibility.lastEntryDay(r),
      rivals = r.rivals,
      prizes = ContestRules.prizes(f.tier, r.kind, r.size),
      myEntries = [
        for (final e in r.entries)
          if (e.ownerId == v.viewer) e,
      ],
      judged = r.judged,
      told = r.judged ? r.told : 0,
      entrants = r.judged ? r.entrants : 0,
      announced = r.over && r.paid,
      announceOn = r.announceOn,
      // only what the stages told so far decided (the owner, 13 Nov 2026:
      // the day told stage by stage; no later stage's outcome before its
      // hour)
      field = r.field?.sublist(0, r.told.clamp(0, r.field!.length)),
      caught = r.told > Stage.medical.index ? r.caught : 0,
      results = !(r.over && r.paid)
          ? (r.judged
                // its day being told, or the places to come: only the
                // owner's entries the stages told so far removed
                ? [
                    for (final row in r.results!)
                      if (row.ownerId == v.viewer &&
                          row.rank == null &&
                          row.removedAt != null &&
                          row.removedAt!.index < r.told)
                        ResultView._(row, v, r.told),
                  ]
                : null)
          : [for (final row in r.results!) ResultView._(row, v, r.told)];

  final RoundId id;
  final RoundKind kind;
  final ColorCategory? category;
  final Sex? sex;
  final int size;
  final GameDay day;
  final AgeClass? legacyAge;
  final GameDay lastEntryDay;
  final int rivals;
  final List<int> prizes;
  final List<Entry> myEntries;
  final bool judged;

  /// How many of the day's six stages have been told (Stage order).
  final int told;

  /// The entries on its day, before the first stage (once judged).
  final int entrants;

  /// The places announced (الفحل وإنتاجه's after the DNA tests).
  final bool announced;
  final GameDay? announceOn;
  final List<int>? field;
  final int caught;

  /// The rows the player may see: all places once announced, and his own
  /// entries' removals; never a score or a mark (the judges' marks are not
  /// announced, the design: «والدرجات ما تنعلن»).
  final List<ResultView>? results;

  /// A player may enter it now (the group rounds come later).
  bool get enterable => kind.enterable;
}

/// One row of a round's results as a player sees it: the place, the prize
/// and the stage an entry left at; never its score or marks, the player's
/// own included (hidden values: the judges' marks are not announced).
class ResultView {
  ResultView._(ResultRow r, GameView v, int told)
    : foundAt = r.ownerId == v.viewer && (r.foundAt?.index ?? 99) < told
          ? r.foundAt
          : null,
      foundKind = r.ownerId == v.viewer && (r.foundAt?.index ?? 99) < told
          ? r.foundKind
          : null,
      fine = r.ownerId == v.viewer && (r.foundAt?.index ?? 99) < told
          ? r.fine
          : 0,
      rank = r.rank,
      camelName = r.camelName,
      ownerId = r.ownerId,
      ownerName = v.ownerName(r.ownerId),
      prize = r.prize,
      head = r.head,
      removedAt = r.removedAt,
      reason = r.reason,
      camelId = r.ownerId == v.viewer ? r.camelId : null,
      reputation = r.ownerId != v.viewer
          ? null
          : r.reason == RemovalReason.tampering ||
                (r.foundAt?.index ?? 99) < told
          ? ReputationMove.fell
          : (r.rank ?? 99) <= 10
          ? ReputationMove.rose
          : ReputationMove.same;

  final int? rank;
  final String camelName;
  final OwnerId ownerId;

  /// The owner's name (the places name the owners).
  final String ownerName;
  final int prize;
  final int head;
  final Stage? removedAt;
  final RemovalReason? reason;

  /// Only on the viewer's own rows.
  final CamelId? camelId;

  /// Only on the viewer's own rows, once its stage is told: the treatment
  /// the check found (told at the tampering experts' or the medical
  /// committee's stage, the entry cut at the preliminary or not), and the
  /// fines.
  final Stage? foundAt;
  final TamperKind? foundKind;
  final int fine;

  /// Only on the viewer's own rows: what the entry did to his name in its
  /// family (GDD 8: the top ten raise it, a treatment found lowers it).
  final ReputationMove? reputation;

  Map<String, Object?> toJson() => {
    'rank': rank,
    'name': camelName,
    'owner': ownerId.value,
    'ownerName': ownerName,
    'prize': prize,
    'head': head,
    if (camelId != null) 'camel': camelId!.value,
    if (removedAt != null) 'removedAt': removedAt!.name,
    if (reason != null) 'reason': reason!.name,
    if (reputation != null) 'reputation': reputation!.name,
    if (foundAt != null) 'foundAt': foundAt!.name,
    if (foundKind != null) 'foundKind': foundKind!.name,
    if (fine > 0) 'fine': fine,
  };
}

/// Which way an entry moved its owner's name (الصيت).
enum ReputationMove { rose, fell, same }

/// One of the player's own secret treatments and its risk, in words: at a
/// festival, outside one in a month, and who finds it most (never the odds).
class TamperingView {
  TamperingView._(this._t, this.camel);
  final Tampering _t;
  final CamelView camel;
  TamperKind get kind => _t.kind;
  int get strength => _t.strength;
  GameDay get until => _t.until;
  RiskBand get festivalRisk => ContestRules.festivalRisk(_t.kind, _t.strength);
  RiskBand get outsideRisk => ContestRules.outsideRisk(_t.strength);
  Stage get foundMostlyBy => ContestRules.foundMostlyBy(_t.kind);
  int get fineIfFound => Balance.tamperFine(_t.kind, _t.strength);

  /// The player had it done (not one his vet found in a camel he bought).
  bool get bought => _t.by == camel.ownerId;
  GameDay get on => _t.on;
}
