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
import '../rules/balance.dart';
import '../rules/eligibility.dart';
import '../rules/judging.dart';
import '../rules/milk.dart';
import '../rules/pasture.dart';
import '../rules/provisions.dart';
import '../rules/valuation.dart';
import '../sim.dart';
import '../systems/systems.dart';

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
    final value = Valuation.value(_c, _today).value.toDouble();
    final rng = Rng.keyed(_seed, [
      'appraise',
      _viewer.value,
      _c.id.value,
      _today.value ~/ 7,
    ]);
    final appraisal =
        value * (1 + clampDouble(rng.normal(sd: 0.06), -0.15, 0.15));
    return (marketRound(appraisal * 0.9), marketRound(appraisal * 1.1));
  }
}

/// A market listing as buyers see it: never the seller's floor price.
class ListingView {
  ListingView._(Listing listing, this.camel, this.sellerName, this.transport)
    : id = listing.id,
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

  ListingView _listing(Listing l) => ListingView._(
    l,
    _view(_w.camels[l.camelId]!),
    ownerName(l.sellerId),
    Riyal(handlers.transportToFarm(me, l)),
  );

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

  List<Festival> get festivals =>
      _w.festivals.values.toList()
        ..sort((a, b) => a.judgedOn.value - b.judgedOn.value);

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

  DomainError? canSell(CamelId id) =>
      Eligibility.canSell(_w, _w.camels[id], viewer);

  DomainError? canEnter(FestivalId f, RoundId r, CamelId c) {
    final fest = _w.festivals[f];
    final round = fest?.rounds.where((x) => x.id == r).firstOrNull;
    if (fest == null || round == null) {
      return const DomainError(ErrorCode.notFound);
    }
    return Eligibility.canEnter(_w, fest, round, _w.camels[c], viewer, today);
  }

  // ------------------------------------------------------------- money

  Riyal get dailyFeed => UpkeepSystem.dailyFeed(_sim, me);

  // ------------------------------------------------------------ provisions

  /// The herd's needs a day under the current ration.
  ({double barley, double alfalfa, double water}) get dailyNeeds =>
      Provisions.needs(_w.aliveOwnedBy(viewer), me.farm.feedPlan, today);

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
  Riyal? quickSalePrice(CamelId id) {
    final c = _w.camels[id];
    if (c == null || !c.isAlive || c.ownerId != viewer) return null;
    return handlers.quickSalePrice(c, _sim);
  }

  Riyal get herdValue => Riyal(
    _w
        .aliveOwnedBy(viewer)
        .fold<int>(0, (a, c) => a + Valuation.value(c, today).value),
  );
}
