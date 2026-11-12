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

  /// Builds the snapshot. Each section's revision moves only when its
  /// content differs from [previous], so screens rebuild only what changed.
  PlayerSnapshot snapshot(int revision, {PlayerSnapshot? previous}) {
    final v = view;
    final me = v.me;
    final mine = state.inboxOf(viewer);
    final public = state.publicNews;
    final events = _mergeByDay(
      mine.sublist(
        mine.length > recentEventCount ? mine.length - recentEventCount : 0,
      ),
      public.sublist(public.length > 10 ? public.length - 10 : 0),
    );

    final herdViews = v.herd;
    var signature = herdViews.length;
    for (final c in state.world.aliveOwnedBy(viewer)) {
      signature =
          (signature * 31 + Object.hashAll(c.mutableFields())) & 0x3FFFFFFF;
    }
    final needs = v.dailyNeeds; // once: each walks the whole herd
    final farm = FarmSummary(
      name: me.farm.name,
      region: me.farm.region,
      capacity: me.farm.capacity,
      shepherds: me.farm.shepherds,
      shepherdsNeeded: v.shepherdsNeeded,
      feedPlan: me.farm.feedPlan,
      dailyFeed: v.dailyFeed.value,
      monthlyWages: v.monthlyWages.value,
      expansionCost: v.expansionCost.value,
      supplies: [
        for (final s in Supply.values)
          SupplySummary(
            supply: s,
            amount: v.inStore(s).floor(),
            daysLeft: v.daysLeft(s, needs),
            room: v.roomFor(s),
            unitPrice: v.unitPrice(s).value,
            unitSize: Provisions.unitSize(s),
            onTheWay: v.onTheWay
                .where((d) => d.supply == s)
                .fold(0, (n, d) => n + d.units),
            onTheWayAmount: v.onTheWay
                .where((d) => d.supply == s)
                .fold(0, (n, d) => n + d.units * d.size),
            need: switch (s) {
              Supply.barley => needs.barley,
              Supply.alfalfa => needs.alfalfa,
              Supply.water => needs.water,
            },
            short: me.farm.short.contains(s),
          ),
      ],
      storeKg: me.farm.storeKg,
      tankL: me.farm.tankL,
      dryDays: me.farm.dryDays,
      tankers: [
        for (final t in Tanker.values)
          TankerSummary(
            tanker: t,
            litres: Provisions.tankerSize(t),
            price: v.tankerPrice(t).value,
            room: v.roomFor(Supply.water, tanker: t),
          ),
      ],
      pastureGreen: v.pastureGreen,
      thirstDays: v.thirstDays,
      rations: [
        for (final r in FeedPlan.values)
          RationSummary(
            plan: r,
            dryMatterKg: r.dryMatterKg,
            asFedKg: Provisions.asFedKg(r),
            barleyShare: r.barleyShare,
            costPerDay: v.dailyFeedFor(r).value,
            conditionTarget: r.conditionTarget,
          ),
      ],
    );
    final summary = _summary(herdViews, v);
    final top = _sorted(
      herdViews,
      HerdSort.quality,
    ).take(topCount).map((c) => card(c, v)).toList(growable: false);
    final market = [for (final l in v.market) listing(l, v)];
    final myListings = [for (final l in v.myListings) listing(l, v)];
    final studs = [
      for (final st in v.studs)
        StudCard(
          id: st.stud.id,
          bull: card(st.bull, v),
          ownerName: st.ownerName,
          region: st.stud.region,
          fee: st.stud.fee.value,
          transport: st.transport.value,
          until: st.stud.until,
        ),
    ];
    final festivals = [for (final f in v.festivals) festival(f)];

    final p = previous;
    int bump(int? old, bool same) => old == null ? 1 : (same ? old : old + 1);
    final sections = SectionRevisions(
      farm: bump(
        p?.sections.farm,
        p != null &&
            p.farm == farm &&
            p.cash == me.cash.value &&
            p.today == v.today,
      ),
      herd: bump(
        p?.sections.herd,
        p != null &&
            p.herd == summary &&
            p.herdSignature == signature &&
            _same(p.herdTop, top),
      ),
      market: bump(
        p?.sections.market,
        p != null && _same(p.market, market) && _same(p.myListings, myListings),
      ),
      studs: bump(p?.sections.studs, p != null && _same(p.studs, studs)),
      festivals: bump(
        p?.sections.festivals,
        p != null && _same(p.festivals, festivals),
      ),
      news: bump(
        p?.sections.news,
        p != null && _sameEvents(p.recentEvents, events),
      ),
    );

    return PlayerSnapshot(
      revision: revision,
      today: v.today,
      playerId: me.id,
      playerName: me.name,
      cash: me.cash.value,
      herdValue: v.herdValue.value,
      todayNet: v.todayNet.value,
      farm: farm,
      herd: summary,
      herdTop: top,
      herdSignature: signature,
      sections: sections,
      market: market,
      myListings: myListings,
      studs: studs,
      festivals: festivals,
      openOffers: v.openOffers,
      breedingSeason: v.breedingSeason,
      recentEvents: List.unmodifiable(events),
    );
  }

  /// How many of the best camels the snapshot carries.
  static const topCount = 12;

  /// Merges two day-ordered lists, keeping each list's own order (stable).
  static List<DomainEvent> _mergeByDay(
    List<DomainEvent> a,
    List<DomainEvent> b,
  ) {
    final out = <DomainEvent>[];
    var i = 0, j = 0;
    while (i < a.length || j < b.length) {
      if (j >= b.length || (i < a.length && a[i].day <= b[j].day)) {
        out.add(a[i++]);
      } else {
        out.add(b[j++]);
      }
    }
    return out;
  }

  static bool _sameEvents(List<DomainEvent> a, List<DomainEvent> b) {
    if (a.length != b.length) return false;
    for (var i = 0; i < a.length; i++) {
      if (!identical(a[i], b[i])) return false;
    }
    return true;
  }

  static bool _same<T>(List<T> a, List<T> b) {
    if (a.length != b.length) return false;
    for (var i = 0; i < a.length; i++) {
      if (a[i] != b[i]) return false;
    }
    return true;
  }

  HerdSummary _summary(List<CamelView> herd, GameView v) {
    var females = 0, males = 0, young = 0, pregnant = 0, waiting = 0;
    var sick = 0, listed = 0, entered = 0;
    final byCategory = <ColorCategory, int>{};
    final byAge = <AgeClass, int>{};
    final listedIds = {for (final l in v.myListings) l.camel.id};
    final enteredIds = {
      for (final f in state.world.festivals.values)
        if (!f.done)
          for (final r in f.rounds)
            for (final e in r.entries)
              if (e.ownerId == viewer) e.camelId,
    };
    for (final c in herd) {
      if (c.sex == Sex.female) {
        females++;
      } else {
        males++;
      }
      if (c.ageDays < 730) young++;
      if (c.pregnant) pregnant++;
      if (c.awaitingCheck) waiting++;
      if (c.health == HealthStatus.sick) sick++;
      if (listedIds.contains(c.id)) listed++;
      if (enteredIds.contains(c.id)) entered++;
      byCategory[c.category] = (byCategory[c.category] ?? 0) + 1;
      byAge[c.ageClass] = (byAge[c.ageClass] ?? 0) + 1;
    }
    return HerdSummary(
      total: herd.length,
      females: females,
      males: males,
      young: young,
      pregnant: pregnant,
      awaitingCheck: waiting,
      sick: sick,
      listed: listed,
      entered: entered,
      byCategory: byCategory,
      byAge: byAge,
    );
  }

  static List<CamelView> _sorted(List<CamelView> herd, HerdSort sort) {
    final keyed =
        switch (sort) {
          HerdSort.quality => [for (final c in herd) (c, -c.quality)],
          HerdSort.value => [
            for (final c in herd) (c, -c.estimate.$2.value.toDouble()),
          ],
          HerdSort.oldest => [for (final c in herd) (c, -c.ageDays.toDouble())],
          HerdSort.youngest => [
            for (final c in herd) (c, c.ageDays.toDouble()),
          ],
        }..sort((a, b) {
          final k = a.$2.compareTo(b.$2);
          return k != 0 ? k : a.$1.id.value.compareTo(b.$1.id.value);
        });
    return [for (final (c, _) in keyed) c];
  }

  /// One page of the herd, filtered and sorted.
  HerdPage herdPage(HerdQuery q) {
    final v = view;
    final listedIds = {for (final l in v.myListings) l.camel.id};
    final matches = [
      for (final c in v.herd)
        if ((q.category == null || c.category == q.category) &&
            switch (q.filter) {
              HerdFilter.all => true,
              HerdFilter.females => c.sex == Sex.female && c.ageDays >= 730,
              HerdFilter.males => c.sex == Sex.male && c.ageDays >= 730,
              HerdFilter.young => c.ageDays < 730,
              HerdFilter.pregnant => c.pregnant,
              HerdFilter.sick => c.health != HealthStatus.healthy,
              HerdFilter.listed => listedIds.contains(c.id),
            })
          c,
    ];
    final sorted = _sorted(matches, q.sort);
    final start = q.offset.clamp(0, sorted.length);
    final end = (start + q.limit).clamp(start, sorted.length);
    return HerdPage(
      cards: [for (final c in sorted.sublist(start, end)) card(c, v)],
      total: sorted.length,
      offset: start,
    );
  }

  /// Details of a camel the player may look at: their own, one for sale, or
  /// a stud bull on offer. Anything else is not theirs to inspect.
  CamelDetail? camelDetail(CamelId id) {
    final v = view;
    final c = v.camel(id);
    if (c == null) return null;
    final l = v.listingOf(id);
    final isStud = v.studs.any((s) => s.bull.id == id);
    if (!c.isMine && l == null && !isStud) return null;
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
      quickSalePrice: v.canSell(id) == null
          ? v.quickSalePrice(id)?.value
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
            results: r.results == null ? null : List.unmodifiable(r.results!),
          ),
      ],
    );
  }
}
