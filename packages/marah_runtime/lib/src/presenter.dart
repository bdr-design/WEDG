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
    final sell = c.isMine ? v.canSell(c.id) : null;
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
      entered: c.isMine && sell?.code == ErrorCode.enteredInContest,
      bestRank: placings.isEmpty
          ? null
          : placings.map((p) => p.rank).reduce((a, b) => a < b ? a : b),
      crossbred: c.crossbred,
      onTheWay: c.onTheWay,
      suckling: v.suckling(c.id),
      declaredSale: c.isMine && sell == null && v.cannotDeclare(c.id) == null
          ? v.quickSalePrice(c.id, declared: true)?.value
          : null,
      quickSale: c.isMine && sell == null
          ? v.quickSalePrice(c.id)?.value
          : null,
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
    knownTreatments: l.knownTreatments,
    timesChecked: l.timesChecked,
    declared: l.declared,
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

  FestivalCard festival(FestivalView f) {
    var mine = 0;
    int? best;
    var prizes = 0;
    var top = 0;
    var topIn = 0;
    RoundKind? topKind;
    final entries = <MyEntryCard>[];
    for (final r in f.rounds) {
      mine += r.myEntries.length;
      final p = r.prizes.first;
      if (p > top) top = p;
      if (r.enterable && p > topIn) {
        topIn = p;
        topKind = r.kind;
      }
      for (final e in r.myEntries) {
        final row = r.results?.where((x) => x.camelId == e.camelId).firstOrNull;
        final c = state.world.camels[e.camelId];
        entries.add(
          MyEntryCard(
            camel: e.camelId,
            name: c?.name ?? row?.camelName ?? '',
            sex: c?.sex ?? r.sex ?? Sex.female,
            round: r.id,
            kind: r.kind,
            category: r.category,
            day: r.day,
            lastEntryDay: r.lastEntryDay,
            told: r.told,
            rank: row?.rank,
            prize: row?.prize ?? 0,
            removedAt: row?.removedAt,
            reason: row?.reason,
            reputation: row?.reputation,
          ),
        );
      }
      for (final row in r.results ?? const <ResultView>[]) {
        if (row.ownerId != viewer) continue;
        prizes += row.prize;
        final rank = row.rank;
        if (rank != null && (best == null || rank < best)) best = rank;
      }
    }
    return FestivalCard(
      id: f.id,
      name: f.name,
      region: f.region,
      tier: f.tier,
      season: f.season,
      opensOn: f.opensOn,
      closesOn: f.closesOn,
      startsOn: f.startsOn,
      endsOn: f.endsOn,
      done: f.done,
      rounds: f.rounds.length,
      myEntries: mine,
      topPrize: top,
      myBestRank: best,
      myPrizes: prizes,
      late: f.late,
      bannedThrough: f.bannedThrough,
      topEnterable: topIn,
      topEnterableKind: topKind,
      entries: entries,
    );
  }

  List<TamperingCard> tamperings(GameView v) => [
    for (final t in v.tamperings)
      TamperingCard(
        camel: t.camel.id,
        camelName: t.camel.name,
        kind: t.kind,
        strength: t.strength,
        until: t.until,
        festivalRisk: t.festivalRisk,
        outsideRisk: t.outsideRisk,
        foundMostlyBy: t.foundMostlyBy,
        fineIfFound: t.fineIfFound,
      ),
  ];

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
    final limit = v.accountLimit(needs);
    final milk = v.milk;
    final farm = FarmSummary(
      name: me.farm.name,
      region: me.farm.region,
      capacity: me.farm.capacity,
      shepherds: me.farm.shepherds,
      shepherdsNeeded: v.shepherdsNeeded,
      feedPlan: me.farm.feedPlan,
      dailyFeed: v.dailyFeed.value,
      monthlyWages: v.monthlyWages.value,
      onAccount: v.onAccount,
      accountLimit: limit,
      accountSpend:
          (me.cash.value > 0 ? me.cash.value : 0) +
          (limit > v.onAccount ? limit - v.onAccount : 0),
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
            goes: v.cannotPayNecessity(v.tankerPrice(t).value, limit) == null,
            onAccount: v.onAccountFor(v.tankerPrice(t).value),
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
      facilities: [
        for (final f in Facility.values)
          FacilitySummary(
            facility: f,
            price: f.price,
            has: me.farm.has(f),
            most: f.most,
            building: me.farm.building.where((b) => b.facility == f).length,
            doneOn: me.farm.building
                .where((b) => b.facility == f)
                .map((b) => b.doneOn)
                .firstOrNull,
            cannot: v.cannotBuild(f)?.code,
            doneOns: [
              for (final b in me.farm.building)
                if (b.facility == f) b.doneOn,
            ],
          ),
      ],
      milk: MilkSummary(
        camels: [
          for (final m in milk.take(milkCount))
            MilkCamel(
              id: m.camel.id,
              name: m.camel.name,
              days: m.days,
              calfId: m.calf?.id,
              calfName: m.calf?.name,
              calfSex: m.calf?.sex,
              litres: m.litres,
              sold: m.sold,
            ),
        ],
        nursing: milk.length,
        litres: milk.fold(0.0, (n, m) => n + m.litres),
        sold: milk.fold(0.0, (n, m) => n + m.sold),
        calfShare: me.farm.calfShare,
        price: Balance.milkPrice,
        incomeToday: v.milkIncomeToday,
        thisMonth: v.milkThisMonth.value,
      ),
    );
    final summary = _summary(herdViews, v);
    final top = _sorted(
      herdViews,
      HerdSort.quality,
    ).take(topCount).map((c) => card(c, v)).toList(growable: false);
    // the first to come to the farm (by the day they came, then id), picked
    // as the herd is walked: a newcomer only ever joins at the end, and the
    // whole herd is not sorted (3-5 ms at 10,000 head, the review)
    int came(CamelView a, CamelView b) {
      final c = a.acquiredOn.value.compareTo(b.acquiredOn.value);
      return c != 0 ? c : a.id.value.compareTo(b.id.value);
    }

    final first = <CamelView>[];
    for (final c in herdViews) {
      if (c.onTheWay) continue; // (on the truck: on the farm tomorrow)
      if (first.length == yardCount && came(c, first.last) >= 0) continue;
      var i = first.length;
      while (i > 0 && came(c, first[i - 1]) < 0) {
        i--;
      }
      first.insert(i, c);
      if (first.length > yardCount) first.removeLast();
    }
    final yard = [for (final c in first) card(c, v)];
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
    final dealer = [
      for (final m in v.dealerMessages)
        () {
          final f = state.world.festivals[m.festival];
          final r = f?.round(m.round);
          return DealerMessageCard(
            camel: m.camel,
            name: m.name,
            sex: state.world.camels[m.camel]?.sex,
            festival: m.festival,
            festivalName: f?.name ?? '',
            round: m.round,
            kind: r?.kind,
            category: r?.category,
            roundDay: r?.day,
            day: m.day,
            read: m.read,
          );
        }(),
    ];
    final findings = v.untoldFindings;
    final money = v.moneyToday;
    final bank = BankSummary(
      opening: v.openingBalance.value,
      startedOn: v.startedOn,
      todayIn: money.income,
      todayOut: money.spent,
      months: [
        for (final m in v.moneyMonths)
          BankMonthRow(month: m.month, net: m.net, top: m.top),
      ],
    );
    final reputation = v.reputation;
    final tampers = tamperings(v);

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
            _same(p.herdTop, top) &&
            _same(p.yard, yard),
      ),
      market: bump(
        p?.sections.market,
        p != null && _same(p.market, market) && _same(p.myListings, myListings),
      ),
      studs: bump(p?.sections.studs, p != null && _same(p.studs, studs)),
      festivals: bump(
        p?.sections.festivals,
        p != null &&
            _same(p.festivals, festivals) &&
            _same(p.tamperings, tampers) &&
            p.bannedThrough == v.bannedThrough &&
            ColorCategory.values.every((c) => p.reputation[c] == reputation[c]),
      ),
      news: bump(
        p?.sections.news,
        p != null && _sameEvents(p.recentEvents, events),
      ),
      bank: bump(p?.sections.bank, p != null && p.bank == bank),
      notices: bump(
        p?.sections.notices,
        p != null &&
            _same(p.dealer, dealer) &&
            p.findings.length == findings.length &&
            (findings.isEmpty || identical(p.findings.last, findings.last)),
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
      yard: yard,
      herdSignature: signature,
      sections: sections,
      market: market,
      myListings: myListings,
      studs: studs,
      festivals: festivals,
      reputation: reputation,
      bannedThrough: v.bannedThrough,
      tamperings: tampers,
      openOffers: v.openOffers,
      breedingSeason: v.breedingSeason,
      recentEvents: List.unmodifiable(events),
      bank: bank,
      dealer: dealer,
      findings: findings,
    );
  }

  /// How many of the best camels the snapshot carries.
  static const topCount = 12;

  /// How many camels the 3D farm shows at most (its yard held 34 drawn
  /// camels within the frame budget, ADR 0005).
  static const yardCount = 40;

  /// How many nursing camels the snapshot lists by name (the totals count
  /// them all).
  static const milkCount = 40;

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
            if (!r.over)
              for (final e in r.entries)
                if (e.ownerId == viewer) ...e.camels,
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
  /// One month of البنك, its kinds, when it is opened (null: no money moved
  /// in it).
  MonthMoney? bankMonth(String month) => view.moneyMonth(month);

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
      declaredSalePrice: v.canSell(id) == null && v.cannotDeclare(id) == null
          ? v.quickSalePrice(id, declared: true)?.value
          : null,
      quickSalePrice: v.canSell(id) == null
          ? v.quickSalePrice(id)?.value
          : null,
    );
  }

  FestivalDetail? festivalDetail(FestivalId id) {
    final v = view;
    final f = v.festival(id);
    if (f == null) return null;
    final herd = v.herd;
    final byId = {for (final c in herd) c.id: c};
    // each camel's look worked out once, and only for one a round could
    // take (the review: the whole herd's, sorted, was most of the time)
    final looks = <CamelId, double>{};
    double look(CamelView c) => looks[c.id] ??= c.quality;

    // registering: while it takes entries and the player is not barred,
    // the best of his camels by look (those on the truck among them), each
    // with its own round and the engine's answer (the design probed with
    // real entries; this never enters one)
    final register = <RegisterRow>[];
    if (f.bannedThrough == null &&
        !f.done &&
        v.today >= f.opensOn &&
        f.rounds.any((r) => r.enterable && v.today <= r.lastEntryDay)) {
      final keyed = [for (final c in herd) (c, look(c))]
        ..sort((a, b) {
          final k = b.$2.compareTo(a.$2);
          return k != 0 ? k : a.$1.id.value.compareTo(b.$1.id.value);
        });
      for (final (c, _) in keyed.take(registerShown)) {
        final (round, error) = v.ownRound(f.id, c.id);
        register.add(
          RegisterRow(camel: card(c, v), round: round, error: error),
        );
      }
    }
    return FestivalDetail(
      register: register,
      registerTotal: herd.length,
      card: festival(f),
      distanceKm: f.distanceKm,
      transportPerHead: Balance.transportCost(f.distanceKm, 1) * 2,
      rounds: [
        for (final r in f.rounds)
          RoundCard(
            id: r.id,
            kind: r.kind,
            category: r.category,
            sex: r.sex,
            size: r.size,
            day: r.day,
            lastEntryDay: r.lastEntryDay,
            legacyAge: r.legacyAge,
            enterable: r.enterable,
            prizes: r.prizes,
            rivals: r.rivals,
            myEntries: [
              for (final e in r.myEntries)
                [
                  for (final c in e.camels)
                    if (byId[c] case final cv?) card(cv, v),
                ],
            ],
            eligible: _eligible(v, f, r, herd, look),
            entryFee: v.entryFee(f.id, 1),
            judged: r.judged,
            told: r.told,
            entrants: r.entrants,
            announced: r.announced,
            announceOn: r.announceOn,
            field: r.field,
            caught: r.caught,
            results: r.results,
          ),
      ],
    );
  }

  /// How many camels a round lists that may enter it (the best by look).
  static const eligibleShown = 20;

  /// How many of the player's camels the registering list shows (the best
  /// by look), as many as the 3D farm shows.
  static const registerShown = yardCount;

  /// The best of the player's camels ([herd], best first) that may enter [r]
  /// now, [eligibleShown] at most (none once it no longer takes entries):
  /// each alone for a single round; for الفحل وإنتاجه each bull that may,
  /// shown with his first offspring in the herd.
  List<CamelCard> _eligible(
    GameView v,
    FestivalView f,
    RoundView r,
    List<CamelView> herd,
    double Function(CamelView) look,
  ) {
    if (v.mayEnter(f.id, r.id) != null) return const [];
    List<CamelView> best(Iterable<CamelView> cs) {
      final keyed = [for (final c in cs) (c, look(c))]
        ..sort((a, b) {
          final k = b.$2.compareTo(a.$2);
          return k != 0 ? k : a.$1.id.value.compareTo(b.$1.id.value);
        });
      return [for (final (c, _) in keyed) c];
    }

    final out = <CamelCard>[];
    if (r.kind == RoundKind.fahal) {
      final kids = <CamelId, List<CamelId>>{};
      for (final c in herd) {
        final sire = c.sire?.id;
        if (sire != null) (kids[sire] ??= []).add(c.id);
      }
      bool sires(CamelView c) =>
          c.sex == Sex.male && (kids[c.id]?.length ?? 0) >= r.size - 1;
      for (final c in best(herd.where(sires))) {
        if (out.length >= eligibleShown) break;
        final group = [c.id, ...kids[c.id]!.take(r.size - 1)];
        if (v.canEnter(f.id, r.id, group) == null) out.add(card(c, v));
      }
      return out;
    }
    // the cheap checks first: a herd of thousands, rounds by the dozen
    final age = r.legacyAge;
    bool may(CamelView c) {
      final days = r.day.daysSince(c.born);
      return (r.category == null || c.category == r.category) &&
          (r.sex == null || c.sex == r.sex) &&
          (age != null ||
              ContestRules.ageFits(r.kind, AgeClass.fromDays(days), days));
    }

    for (final c in best(herd.where(may))) {
      if (out.length >= eligibleShown) break;
      if (v.canEnter(f.id, r.id, [c.id]) == null) out.add(card(c, v));
    }
    return out;
  }
}
