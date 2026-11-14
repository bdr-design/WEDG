import 'package:marah_domain/marah_domain.dart';

import 'view_models.dart';

/// The view models as plain JSON, for a screen outside Dart: the 3D design
/// prototype reads them from its Web Worker (docs/plan-gameplay.md, G2).
/// Enums by name, days as numbers, hidden values never (the view models carry
/// none). One way only: screens never send these back.
class SnapshotJson {
  const SnapshotJson._();

  static Map<String, Object?> snapshot(PlayerSnapshot s) => {
    'revision': s.revision,
    'today': s.today.value,
    'date': _date(s.today),
    'playerId': s.playerId.value,
    'playerName': s.playerName,
    'cash': s.cash,
    'testMoney': s.testMoney,
    'testedFrom': s.testedFrom == null ? null : _date(s.testedFrom!),
    'herdValue': s.herdValue,
    'todayNet': s.todayNet,
    'farm': farm(s.farm),
    'herd': herd(s.herd),
    'herdTop': [for (final c in s.herdTop) camel(c)],
    'yard': [for (final c in s.yard) camel(c)],
    'herdSignature': s.herdSignature,
    'sections': {
      'farm': s.sections.farm,
      'herd': s.sections.herd,
      'market': s.sections.market,
      'studs': s.sections.studs,
      'festivals': s.sections.festivals,
      'news': s.sections.news,
      'bank': s.sections.bank,
      'notices': s.sections.notices,
    },
    'market': [for (final l in s.market) listing(l)],
    'myListings': [for (final l in s.myListings) listing(l)],
    'studs': [for (final x in s.studs) stud(x)],
    'festivals': [for (final f in s.festivals) festival(f)],
    // a band, never the number (Balance.reputationBand)
    'reputation': {
      for (final e in s.reputation.entries) e.key.name: e.value.name,
    },
    'bannedThrough': s.bannedThrough,
    'tamperings': [for (final t in s.tamperings) tampering(t)],
    'festivalRules': festivalRules(),
    'openOffers': s.openOffers,
    // الحراج's rules the screens say (Balance): the broker's commission on a
    // sale he brokers, how long a listing stays, how long an offer holds
    'haraj': {
      'commission': Balance.brokerCommission,
      'listingDays': Balance.playerListingDays,
      'offerDays': Balance.offerValidDays,
      'minAsk': Balance.minAskPrice,
    },
    'breedingSeason': s.breedingSeason,
    // a place's score is the judges' mark, never announced (hidden)
    'recentEvents': [
      for (final e in s.recentEvents) e.toJson()..remove('score'),
    ],
    'bank': bank(s.bank),
    // the secret treatment man's messages (after each registration), and the
    // treatments found outside a festival and a sale not yet told
    'dealer': {
      'name': s.dealerName,
      'unread': s.dealer.where((m) => !m.read).length,
      'messages': [
        for (final m in s.dealer)
          {
            'camel': m.camel.value,
            'name': m.name,
            'sex': m.sex?.name,
            'festival': m.festival.value,
            'festivalName': m.festivalName,
            'round': m.round.value,
            'kind': m.kind?.name,
            'cat': m.category?.name,
            'roundDay': m.roundDay?.value,
            'day': m.day.value,
            'read': m.read,
          },
      ],
    },
    'findings': [
      for (final f in s.findings)
        {
          'camel': f.camel.value,
          'name': f.name,
          'kind': f.kind.name,
          'fine': f.fine,
          'knew': f.knew,
          'day': f.day.value,
        },
    ],
  };

  /// البنك's main screen: the opening balance, today's money in and out, and
  /// every month's net with its biggest kind (newest first).
  static Map<String, Object?> bank(BankSummary b) => {
    'opening': b.opening,
    'startedOn': _date(b.startedOn),
    'todayIn': b.todayIn,
    'todayOut': b.todayOut,
    'months': [
      for (final m in b.months)
        {'month': m.month, 'net': m.net, 'top': moneyLine(m.top)},
    ],
  };

  /// One month opened: what came in, what went out, each kind.
  static Map<String, Object?> moneyMonth(MonthMoney m) => {
    'month': m.month,
    'in': m.income,
    'out': m.spent,
    'lines': [for (final l in m.lines) moneyLine(l)],
  };

  /// A kind of money: its sum and count, and what its line says (the fields
  /// a kind does not have are left out).
  static Map<String, Object?> moneyLine(MoneyLine l) => {
    'kind': l.kind.name,
    'amount': l.amount,
    'count': l.count,
    if (l.name != null) 'name': l.name,
    if (l.day != null) 'day': _date(l.day!),
    if (l.price != null) 'price': l.price,
    if (l.fee != null) 'fee': l.fee,
    if (l.trip != null) 'trip': l.trip!.name,
    if (l.fineFor != null) 'fineFor': l.fineFor!.name,
    if (l.facilities.isNotEmpty)
      'facilities': [for (final f in l.facilities) f.name],
  };

  static Map<String, Object?> farm(FarmSummary f) => {
    'name': f.name,
    'region': f.region.name,
    'capacity': f.capacity,
    'shepherds': f.shepherds,
    'shepherdsNeeded': f.shepherdsNeeded,
    'ownerTendsUpTo': Balance.ownerTendsUpTo,
    'feedPlan': f.feedPlan.name,
    'dailyFeed': f.dailyFeed,
    'monthlyWages': f.monthlyWages,
    'storeKg': f.storeKg,
    'tankL': f.tankL,
    'dryDays': f.dryDays,
    'tankers': [
      for (final t in f.tankers)
        {
          'tanker': t.tanker.name,
          'litres': t.litres,
          'price': t.price,
          'room': t.room,
          'goes': t.goes,
          'onAccount': t.onAccount,
        },
    ],
    'pastureGreen': f.pastureGreen,
    'thirstDays': f.thirstDays,
    'rations': [
      for (final r in f.rations)
        {
          'plan': r.plan.name,
          'dryMatterKg': r.dryMatterKg,
          'asFedKg': r.asFedKg,
          'barleyShare': r.barleyShare,
          'costPerDay': r.costPerDay,
          'conditionTarget': r.conditionTarget,
        },
    ],
    'facilities': [
      for (final x in f.facilities)
        {
          'facility': x.facility.name,
          'price': x.price,
          'has': x.has,
          'most': x.most,
          'building': x.building,
          'doneOn': x.doneOn == null ? null : _date(x.doneOn!),
          'doneOns': [for (final d in x.doneOns) _date(d)],
          'cannot': x.cannot?.name,
        },
    ],
    // the merchant's account: what is owed for feed, water and the vet,
    // and its limit (the debt itself is the cash below zero)
    'account': {
      'owed': f.onAccount,
      'limit': f.accountLimit,
      // the most an order of necessities may cost now (the money above zero
      // and the room left on the account); what the money does not cover of
      // it goes on the account
      'spend': f.accountSpend,
    },
    'milk': {
      'camels': [
        for (final m in f.milk.camels)
          {
            'id': m.id.value,
            'name': m.name,
            'days': m.days,
            'calfId': m.calfId?.value,
            'calfName': m.calfName,
            'calfSex': m.calfSex?.name,
            'litres': _tenth(m.litres),
            'sold': _tenth(m.sold),
          },
      ],
      'nursing': f.milk.nursing,
      'litres': _tenth(f.milk.litres),
      'sold': _tenth(f.milk.sold),
      'calfShare': f.milk.calfShare.name,
      'price': f.milk.price,
      'incomeToday': f.milk.incomeToday,
      'thisMonth': f.milk.thisMonth,
    },
    'supplies': [
      for (final x in f.supplies)
        {
          'supply': x.supply.name,
          'amount': x.amount,
          'daysLeft': x.daysLeft,
          'room': x.room,
          'unitPrice': x.unitPrice,
          'unitSize': x.unitSize,
          'onTheWay': x.onTheWay,
          'onTheWayAmount': x.onTheWayAmount,
          'need': x.need,
          'short': x.short,
        },
    ],
  };

  static Map<String, Object?> herd(HerdSummary h) => {
    'total': h.total,
    'females': h.females,
    'males': h.males,
    'young': h.young,
    'pregnant': h.pregnant,
    'awaitingCheck': h.awaitingCheck,
    'sick': h.sick,
    'listed': h.listed,
    'entered': h.entered,
    'byCategory': {for (final e in h.byCategory.entries) e.key.name: e.value},
    'byAge': {for (final e in h.byAge.entries) e.key.name: e.value},
  };

  static Map<String, Object?> camel(CamelCard c) => {
    'id': c.id.value,
    'name': c.name,
    'sex': c.sex.name,
    'category': c.category.name,
    'ageClass': c.ageClass.name,
    // a calf still suckling is a حوار whatever its age (the owner, 13 Nov)
    'ageName': (c.suckling ? AgeClass.hwar : c.ageClass).labelFor(c.sex),
    'ageDays': c.ageDays,
    'quality': c.quality,
    'estimateLow': c.estimateLow,
    'estimateHigh': c.estimateHigh,
    'condition': c.condition,
    'health': c.health.name,
    'illness': c.illness?.name,
    'pregnant': c.pregnant,
    'dueOn': c.dueOn?.value,
    'awaitingCheck': c.awaitingCheck,
    'listed': c.listed,
    'entered': c.entered,
    'bestRank': c.bestRank,
    'crossbred': c.crossbred,
    'onTheWay': c.onTheWay,
    'quickSale': c.quickSale,
    if (c.declaredSale != null) 'declaredSale': c.declaredSale,
  };

  static Map<String, Object?> listing(ListingCard l) => {
    'id': l.id.value,
    'camel': camel(l.camel),
    'askPrice': l.askPrice,
    'region': l.region.name,
    'sellerName': l.sellerName,
    'transport': l.transport,
    'listedOn': l.listedOn.value,
    'expiresOn': l.expiresOn.value,
    'bargainsLeft': l.bargainsLeft,
    'isMine': l.isMine,
    if (l.knownTreatments.isNotEmpty)
      'treatments': [for (final k in l.knownTreatments) k.name],
    if (l.timesChecked > 0) 'checked': l.timesChecked,
    if (l.declared) 'declared': true,
    'offers': [
      for (final o in l.offers)
        {
          'id': o.id.value,
          'buyerName': o.buyerName,
          'amount': o.amount,
          'expiresOn': o.expiresOn.value,
        },
    ],
  };

  static Map<String, Object?> stud(StudCard s) => {
    'id': s.id.value,
    'bull': camel(s.bull),
    'ownerName': s.ownerName,
    'region': s.region.name,
    'fee': s.fee,
    'transport': s.transport,
    'until': s.until.value,
  };

  static Map<String, Object?> festival(FestivalCard f) => {
    'id': f.id.value,
    'name': f.name,
    'region': f.region.name,
    'tier': f.tier.name,
    'season': f.season,
    'opensOn': f.opensOn.value,
    'closesOn': f.closesOn.value,
    'startsOn': f.startsOn.value,
    'endsOn': f.endsOn.value,
    'done': f.done,
    'rounds': f.rounds,
    'myEntries': f.myEntries,
    'topPrize': f.topPrize,
    'myBestRank': f.myBestRank,
    'myPrizes': f.myPrizes,
    'late': f.late,
    'bannedThrough': f.bannedThrough,
    'topEnterable': f.topEnterable,
    'topEnterableKind': f.topEnterableKind?.name,
    'entries': [
      for (final e in f.entries)
        {
          'camel': e.camel.value,
          'name': e.name,
          'sex': e.sex.name,
          'round': e.round.value,
          'kind': e.kind.name,
          'cat': e.category?.name,
          'day': e.day.value,
          'lastEntryDay': e.lastEntryDay.value,
          'told': e.told,
          if (e.rank != null) 'rank': e.rank,
          if (e.prize > 0) 'prize': e.prize,
          if (e.removedAt != null) 'removedAt': e.removedAt!.name,
          if (e.reason != null) 'reason': e.reason!.name,
          if (e.reputation != null) 'reputation': e.reputation!.name,
          if (e.foundAt != null) 'foundAt': e.foundAt!.name,
          if (e.foundKind != null) 'foundKind': e.foundKind!.name,
          if (e.fine > 0) 'fine': e.fine,
          if (e.head > 1) 'head': e.head,
          if (e.announceOn != null) 'announceOn': e.announceOn!.value,
        },
    ],
  };

  /// A festival's page (the phone's المزاين app asks for it when opened):
  /// its rounds, the player's entries and the camels that may enter, the
  /// day's stages and the places once announced.
  static Map<String, Object?> festivalDetail(FestivalDetail d) => {
    'festival': festival(d.card),
    'distanceKm': d.distanceKm,
    'transportPerHead': d.transportPerHead,
    'registerTotal': d.registerTotal,
    'tripPaid': d.tripPaid,
    'register': [
      for (final x in d.register)
        {
          'camel': camel(x.camel),
          'round': x.round?.value,
          'error': x.error == null
              ? null
              : {'code': x.error!.code.name, 'params': x.error!.params},
          if (x.group.isNotEmpty) 'group': [for (final c in x.group) camel(c)],
          'trip': x.trip,
          'fee': x.fee,
          'lateFee': x.lateFee,
        },
    ],
    'rounds': [
      for (final r in d.rounds)
        {
          'id': r.id.value,
          'kind': r.kind.name,
          'cat': r.category?.name,
          'sex': r.sex?.name,
          'size': r.size,
          'day': r.day.value,
          'lastEntryDay': r.lastEntryDay.value,
          'legacyAge': r.legacyAge?.name,
          'enterable': r.enterable,
          'prizes': r.prizes,
          'rivals': r.rivals,
          'myEntries': [
            for (final e in r.myEntries) [for (final c in e) camel(c)],
          ],
          'eligible': [for (final c in r.eligible) camel(c)],
          'entryFee': r.entryFee,
          'judged': r.judged,
          'told': r.told,
          'entrants': r.entrants,
          'announced': r.announced,
          'announceOn': r.announceOn?.value,
          'field': r.field,
          'caught': r.caught,
          'results': r.results == null
              ? null
              : [for (final row in r.results!) row.toJson()],
        },
    ],
  };

  static Map<String, Object?> tampering(TamperingCard t) => {
    'camel': t.camel.value,
    'camelName': t.camelName,
    'kind': t.kind.name,
    'strength': t.strength,
    'until': t.until.value,
    'festivalRisk': t.festivalRisk.name,
    'outsideRisk': t.outsideRisk.name,
    'foundMostlyBy': t.foundMostlyBy.name,
    'fineIfFound': t.fineIfFound,
    // the player had it done (the chat shows only those he bought)
    if (t.bought) 'bought': true,
    if (t.on != null) 'on': t.on!.value,
  };

  /// The festival rules the screens say (Balance, TamperKind): the late
  /// fee, the hours before a round it closes, the ban's length, and each
  /// treatment's price, fine cap, features, its risk at a festival at each
  /// strength in words and who finds it most.
  static Map<String, Object?> festivalRules() => {
    'lateEntryFee': Balance.lateEntryFee,
    'lateEntryHoursBefore': Balance.lateEntryHoursBefore,
    'banEditionsAfter': Balance.banEditionsAfter,
    'dnaDays': Balance.dnaDays,
    // the minute of the round's day each stage is told (a game choice)
    'stageMinutes': Balance.stageMinutes,
    'tamperKinds': [
      for (final k in TamperKind.values)
        {
          'kind': k.name,
          'fineCap': k.fineCap,
          'traits': [for (final t in k.traits) t.name],
          'lastsDays': k.lastsDays,
          'price': [
            for (var s = 1; s <= 3; s++) ContestRules.tamperPrice(k, s),
          ],
          'fine': [for (var s = 1; s <= 3; s++) Balance.tamperFine(k, s)],
          'festivalRisk': [
            for (var s = 1; s <= 3; s++) ContestRules.festivalRisk(k, s).name,
          ],
          'foundMostlyBy': ContestRules.foundMostlyBy(k).name,
        },
    ],
  };

  /// To a tenth: a litre to a tenth is what the screens show, and the full
  /// doubles were most of the milk's bytes.
  static double _tenth(double v) => (v * 10).roundToDouble() / 10;

  static String _date(GameDay d) {
    final t = d.date;
    String two(int n) => n < 10 ? '0$n' : '$n';
    return '${t.year}-${two(t.month)}-${two(t.day)}';
  }
}
