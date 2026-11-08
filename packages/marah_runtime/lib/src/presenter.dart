import 'package:marah_domain/marah_domain.dart';

import 'view_models.dart';

/// Builds view models from the game for one player. Runs where the engine
/// runs (the worker isolate), never on the UI thread.
class Presenter {
  Presenter(this.state, this.viewer);

  final GameState state;
  final OwnerId viewer;

  /// How many of the player's latest events a snapshot carries.
  static const recentEventCount = 40;

  GameView get view => GameView(state, viewer);

  CamelCard card(CamelView c, GameView v) {
    final (lo, hi) = c.estimate;
    final placings = c.placings;
    return CamelCard(
      id: c.id,
      name: c.name,
      sex: c.sex,
      category: c.category,
      ageClass: c.ageClass,
      ageDays: c.ageDays,
      quality: c.quality,
      estimateLow: lo.value,
      estimateHigh: hi.value,
      condition: c.condition,
      health: c.health,
      illness: c.illness,
      pregnant: c.pregnant,
      dueOn: c.dueOn,
      awaitingCheck: c.isMine && c.awaitingCheck,
      listed: v.listingOf(c.id) != null,
      entered: c.isMine && v.canSell(c.id)?.code == ErrorCode.enteredInContest,
      bestRank: placings.isEmpty
          ? null
          : placings.map((p) => p.rank).reduce((a, b) => a < b ? a : b),
      crossbred: c.crossbred,
    );
  }

  ListingCard listing(ListingView l, GameView v) => ListingCard(
    id: l.id,
    camel: card(l.camel, v),
    askPrice: l.askPrice.value,
    region: l.region,
    sellerName: l.sellerName,
    transport: l.transport.value,
    listedOn: l.listedOn,
    expiresOn: l.expiresOn,
    bargainsLeft: v.bargainsLeft(l.id),
    isMine: l.sellerId == viewer,
    offers: l.sellerId == viewer
        ? [
            for (final o in v.offersOn(l.id))
              OfferCard(
                id: o.id,
                buyerName: v.ownerName(o.buyerId),
                amount: o.amount.value,
                expiresOn: o.expiresOn,
              ),
          ]
        : const [],
  );

  FestivalCard festival(Festival f) {
    var mine = 0;
    int? best;
    var prizes = 0;
    var top = 0;
    for (final r in f.rounds) {
      mine += r.entries.where((e) => e.ownerId == viewer).length;
      final p = ContestRules.prizes(f.tier, r.age).first;
      if (p > top) top = p;
      for (final row in r.results ?? const <ResultRow>[]) {
        if (row.ownerId != viewer) continue;
        prizes += row.prize;
        if (best == null || row.rank < best) best = row.rank;
      }
    }
    return FestivalCard(
      id: f.id,
      name: f.name,
      region: f.region,
      tier: f.tier,
      opensOn: f.opensOn,
      closesOn: f.closesOn,
      judgedOn: f.judgedOn,
      done: f.done,
      rounds: f.rounds.length,
      myEntries: mine,
      topPrize: top,
      myBestRank: best,
      myPrizes: prizes,
    );
  }

  PlayerSnapshot snapshot(int revision) {
    final v = view;
    final me = v.me;
    final mine = state.inboxOf(viewer);
    final public = state.publicNews;
    final events = [
      ...mine.skip(
        mine.length > recentEventCount ? mine.length - recentEventCount : 0,
      ),
      ...public.skip(public.length > 10 ? public.length - 10 : 0),
    ]..sort((a, b) => a.day.value - b.day.value);
    return PlayerSnapshot(
      revision: revision,
      today: v.today,
      playerId: me.id,
      playerName: me.name,
      cash: me.cash.value,
      herdValue: v.herdValue.value,
      farm: FarmSummary(
        name: me.farm.name,
        region: me.farm.region,
        capacity: me.farm.capacity,
        shepherds: me.farm.shepherds,
        shepherdsNeeded: v.shepherdsNeeded,
        feedPlan: me.farm.feedPlan,
        dailyFeed: v.dailyFeed.value,
        monthlyWages: v.monthlyWages.value,
        expansionCost: v.expansionCost.value,
      ),
      herd: [for (final c in v.herd) card(c, v)],
      market: [for (final l in v.market) listing(l, v)],
      myListings: [for (final l in v.myListings) listing(l, v)],
      studs: [
        for (final s in v.studs)
          StudCard(
            id: s.stud.id,
            bull: card(s.bull, v),
            ownerName: s.ownerName,
            region: s.stud.region,
            fee: s.stud.fee.value,
            transport: s.transport.value,
            until: s.stud.until,
          ),
      ],
      festivals: [for (final f in v.festivals) festival(f)],
      openOffers: v.openOffers,
      breedingSeason: v.breedingSeason,
      recentEvents: List.unmodifiable(events),
    );
  }

  CamelDetail? camelDetail(CamelId id) {
    final v = view;
    final c = v.camel(id);
    if (c == null) return null;
    final l = v.listingOf(id);
    return CamelDetail(
      card: card(c, v),
      isMine: c.isMine,
      looks: c.looks,
      chip: c.chip,
      sire: c.sire,
      dam: c.dam,
      calvings: c.calvings,
      lastCalvedOn: c.lastCalvedOn,
      pregnantBy: c.pregnantBy,
      placings: c.placings,
      purchasePrice: c.purchasePrice,
      listing: l == null ? null : listing(l, v),
      canSell: c.isMine ? v.canSell(id) : null,
      canBreed: c.isMine && c.sex == Sex.female ? v.canBreed(id) : null,
      quickSalePrice: c.isMine && v.canSell(id) == null
          ? v.quickSalePrice(id).value
          : null,
    );
  }

  FestivalDetail? festivalDetail(FestivalId id) {
    final v = view;
    final f = state.world.festivals[id];
    if (f == null) return null;
    final km = v.me.farm.region.roadKmTo(f.region);
    final herd = v.herd;
    return FestivalDetail(
      card: festival(f),
      distanceKm: km,
      transportPerHead: Balance.transportCost(km, 1) * 2,
      rounds: [
        for (final r in f.rounds)
          RoundCard(
            id: r.id,
            category: r.category,
            sex: r.sex,
            age: r.age,
            prizes: ContestRules.prizes(f.tier, r.age),
            rivals: r.rivals,
            myEntries: [
              for (final e in r.entries)
                if (e.ownerId == viewer && v.camel(e.camelId) != null)
                  card(v.camel(e.camelId)!, v),
            ],
            eligible: [
              for (final c in herd)
                if (v.canEnter(f.id, r.id, c.id) == null) card(c, v),
            ],
            results: r.results,
          ),
      ],
    );
  }
}
