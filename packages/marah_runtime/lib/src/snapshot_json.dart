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
    'herdValue': s.herdValue,
    'farm': farm(s.farm),
    'herd': herd(s.herd),
    'herdTop': [for (final c in s.herdTop) camel(c)],
    'herdSignature': s.herdSignature,
    'sections': {
      'farm': s.sections.farm,
      'herd': s.sections.herd,
      'market': s.sections.market,
      'studs': s.sections.studs,
      'festivals': s.sections.festivals,
      'news': s.sections.news,
    },
    'market': [for (final l in s.market) listing(l)],
    'myListings': [for (final l in s.myListings) listing(l)],
    'studs': [for (final x in s.studs) stud(x)],
    'festivals': [for (final f in s.festivals) festival(f)],
    'openOffers': s.openOffers,
    'breedingSeason': s.breedingSeason,
    'recentEvents': [for (final e in s.recentEvents) e.toJson()],
  };

  static Map<String, Object?> farm(FarmSummary f) => {
    'name': f.name,
    'region': f.region.name,
    'capacity': f.capacity,
    'shepherds': f.shepherds,
    'shepherdsNeeded': f.shepherdsNeeded,
    'feedPlan': f.feedPlan.name,
    'dailyFeed': f.dailyFeed,
    'monthlyWages': f.monthlyWages,
    'expansionCost': f.expansionCost,
    'storeKg': f.storeKg,
    'tankL': f.tankL,
    'dryDays': f.dryDays,
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
    'opensOn': f.opensOn.value,
    'closesOn': f.closesOn.value,
    'judgedOn': f.judgedOn.value,
    'done': f.done,
    'rounds': f.rounds,
    'myEntries': f.myEntries,
    'topPrize': f.topPrize,
    'myBestRank': f.myBestRank,
    'myPrizes': f.myPrizes,
  };

  static String _date(GameDay d) {
    final t = d.date;
    String two(int n) => n < 10 ? '0$n' : '$n';
    return '${t.year}-${two(t.month)}-${two(t.day)}';
  }
}
