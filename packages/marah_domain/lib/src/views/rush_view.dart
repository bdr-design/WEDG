// What the phone shows of the rush, the standing orders, the vet and the
// calendar's guard (task T15), as plain values the snapshot carries: the
// engine's own prices, so the phone never works one out itself (only the
// truck's falls with the hour, from the shares given here and the clock's
// hour the worker sends).
import '../away.dart';
import '../common/ids.dart';
import '../game.dart';
import '../handlers/handlers.dart' as handlers;
import '../handlers/rush.dart';
import '../model/camel.dart';
import '../model/game_state.dart';
import '../model/player.dart';
import '../rules/balance.dart';
import '../rules/eligibility.dart';
import '../rules/provisions.dart';
import '../sim.dart';

/// How many sick camels the snapshot lists by name.
const sickShown = 20;

Map<String, Object?> rushFacts(GameState state, OwnerId viewer) {
  final sim = Sim(state);
  final p = state.players[viewer]!;
  final f = p.farm;
  final today = sim.today;
  final r = f.today != null && f.today!.day == today ? f.today : null;
  int? deliveryFee(StandingOrder k) {
    final ds = coming(p, k);
    if (ds.isEmpty || !shortToday(sim, p, k)) return null;
    return rushDeliveryFee(p, k, ds);
  }

  final herd = sim.herdOf(viewer).toList();
  final dueSoon = [
    for (final c in herd)
      if (c.pregnancy case final preg? when preg.confirmed)
        if (preg.dueOn.daysSince(today) <= 30) c.id.value,
  ];
  final block = AwayRun.refusal(Game(state), today + 1);
  final sick = [
    for (final c in herd)
      if (c.health == HealthStatus.sick && c.illness != null) c,
  ]..sort((a, b) => a.sickSince!.value - b.sickSince!.value);
  return {
    'waterShort': r?.waterShort ?? false,
    'feedShort': r?.feedShort ?? false,
    'rushWater': deliveryFee(StandingOrder.water),
    'rushFeed': deliveryFee(StandingOrder.feed),
    // at ordering, on a short day: each tanker's rush; feed's share and cap
    'tankerNow': (r?.waterShort ?? false)
        ? {
            for (final t in Tanker.values)
              t.name: (Provisions.tankerPrice(t) * Balance.rushDeliveryShare)
                  .round(),
          }
        : null,
    'feedShare': Balance.rushDeliveryShare,
    'feedCap': Balance.rushFeedCap,
    'builds': [
      for (final fac in Facility.values)
        if (earliestBuilding(p, fac) case final b?)
          {
            'facility': fac.name,
            'doneOn': b.doneOn.value,
            'fee': rushBuildFee(sim, p, fac),
          },
    ],
    'buildNow': {
      for (final fac in Facility.values)
        fac.name: Balance.rushBuildFee(fac.price, Balance.buildDays),
    },
    'trucks': [
      for (final c in herd)
        if (Eligibility.onTheWay(c, today))
          {
            'camel': c.id.value,
            'name': c.name,
            'sex': c.sex.name,
            'trucking': truckingOf(p, c, sim),
          },
    ],
    'truckShare': Balance.rushTruckShare,
    'truckFloor': Balance.rushTruckFloor,
    'standing': [for (final o in f.standing) o.name],
    'vet': {
      'on': f.vet != null,
      'since': f.vet?.since.value,
      'endsOn': f.vet?.endsOn?.value,
      'monthly': Balance.vetContractFee(herd.length),
      'part': vetContractPart(sim, p),
    },
    // the first [sickShown] (the oldest illness first) and how many in all,
    // with the price of treating them all: at 10,000 head a thousand sick
    // made the snapshot four times its size (the review's B3)
    'sickCount': sick.length,
    'treatAll': sick.isEmpty ? 0 : treatAllQuote(sim, p),
    'sick': [
      for (final c in sick.take(sickShown))
        {
          'camel': c.id.value,
          'name': c.name,
          'sex': c.sex.name,
          'illness': c.illness!.name,
          'illnessName': c.illness!.label,
          'sickSince': c.sickSince?.value,
          'quote': handlers.vetQuote(sim, c).value,
          'recoverMin': c.illness!.recoverDays ~/ 2,
          'recoverMax': c.illness!.recoverDays,
          'graceDays': Balance.untreatedGraceDays,
        },
    ],
    'awayBlock': block?.params['reason'],
    'crowdedSoon': herd.length >= f.capacity && dueSoon.isNotEmpty
        ? dueSoon.length
        : 0,
    'lowStockDays': Balance.lowStockDays,
  };
}
