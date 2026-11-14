// What the phone and the map read of the hunting season (task T18, part A),
// as plain values the snapshot carries (as rushFacts does): the catalog,
// his falcons, his permits and gear, the falcons' room's pin, today's lots.
// HIDDEN values never leave the engine: a falcon's skill and a bird's worth
// (the GDD 13.1: «مهارة الصقر ما تنعرض رقم أبد»; the design: «قيمته ما
// تنعرف إلا بالمزاد»). Every number is the engine's own: the phone works
// none out itself.
import '../catalog/falcon_lines.dart';
import '../catalog/falconry.dart';
import '../common/ids.dart';
import '../common/result.dart';
import '../common/time.dart';
import '../game.dart';
import '../handlers/falconry.dart';
import '../model/falconry.dart';
import '../model/game_state.dart';
import '../model/player.dart';
import '../rules/balance.dart';
import '../rules/falcon_market.dart';
import '../rules/hunt_balance.dart';
import '../sim.dart';
import '../trips.dart';

/// A length in quarter inches as the sale pages write it: 15, 15¼, 15½,
/// 15¾ [187][216].
String inches(int quarters) {
  final w = quarters ~/ 4;
  return '$w${const ['', '¼', '½', '¾'][quarters % 4]}';
}

/// What does not change from day to day (the phone asks once: the worker's
/// 'falconCatalog'): the routes' dates, the permits' fees, the gear's
/// prices, the grounds with their road from his farm, the sun table, the
/// refusals' and the release lines' words.
Map<String, Object?> falconCatalogOf(GameState state, OwnerId viewer) {
  final farm = state.players[viewer]!.farm;
  return {
    'routes': [
      for (final r in FalconRoute.values)
        {
          'route': r.name,
          'name': r.label,
          'from': [r.fromMonth, r.fromDay],
          'to': [r.toMonth, r.toDay],
        },
    ],
    'permits': [
      for (final k in PermitKind.values)
        {'kind': k.name, 'name': k.label, 'fee': k.fee},
    ],
    'gear': [
      for (final g in Gear.values)
        {'gear': g.name, 'name': g.label, 'price': g.price, 'most': g.most},
    ],
    'deliveryDays': Balance.deliveryDays,
    'grounds': [
      for (final g in Ground.values)
        {
          'ground': g.name,
          'name': g.label,
          'use': g.use.name,
          'km': g.kmFrom(farm.region),
          'hours': (g.hoursFrom(farm.region) * 10).round() / 10,
          'oneDay': g.oneDayFrom(farm.region),
          'quarry': [for (final q in g.quarry) q.label],
          if (g.coast) 'coast': true,
          if (g.north) 'north': true,
        },
    ],
    'quarry': [
      for (final q in Quarry.values)
        {
          'quarry': q.name,
          'name': q.label,
          'from': [q.fromMonth, q.fromDay],
          'to': [q.toMonth, q.toDay],
        },
    ],
    'room': {
      'price': Facility.falconRoom.price,
      'holds': HuntBalance.roomHolds,
    },
    'upkeepPerDay': HuntBalance.upkeepPerDay,
    'dauDaysNeeded': HuntBalance.dauDaysNeeded,
    'stepBackDays': HuntBalance.stepBackDays,
    'mostNights': HuntBalance.mostNights,
    'release': [
      HuntBalance.releaseFrom.$1,
      HuntBalance.releaseFrom.$2,
      HuntBalance.releaseTo.$1,
      HuntBalance.releaseTo.$2,
    ],
    'sun': {
      for (var m = 1; m <= 12; m++)
        '$m': {
          'dawn': HuntSun.dawn(GameDay.ofDate(DateTime.utc(2026, m, 15))),
          'sunrise': HuntSun.sunrise(GameDay.ofDate(DateTime.utc(2026, m, 15))),
          'sunset': HuntSun.sunset(GameDay.ofDate(DateTime.utc(2026, m, 15))),
        },
    },
    'lines': {
      'refusals': {
        for (final r in HuntRefusal.values)
          r.name: FalconLines.refusal(
            DomainError(ErrorCode.huntRefused, {
              'reason': r.name,
              'route': 'trapping',
              'kind': 'hunting',
              'lure': 'pigeon',
            }),
          ),
        'outOfSeason.trapping': FalconLines.refusal(
          const DomainError(ErrorCode.huntRefused, {
            'reason': 'outOfSeason',
            'kind': 'trapping',
          }),
        ),
        'noPermit.trapping': FalconLines.refusal(
          const DomainError(ErrorCode.huntRefused, {
            'reason': 'noPermit',
            'kind': 'trapping',
          }),
        ),
        'noLure.birdNet': FalconLines.refusal(
          const DomainError(ErrorCode.huntRefused, {
            'reason': 'noLure',
            'lure': 'birdNet',
          }),
        ),
        for (final r in FalconRoute.values)
          'routeClosed.${r.name}': FalconLines.closed(r),
      },
      'release': {
        for (final sp in FalconSpecies.values)
          for (final farkh in [true, false])
            if (FalconLines.release(sp, farkh) case final l?)
              '${sp.name}.${farkh ? 'farkh' : 'qarnas'}': l,
        'freedAtClose': FalconLines.freedAtClose,
      },
      'trap': FalconLines.trap,
      'summary': FalconLines.summary,
      'moneyKinds': FalconLines.moneyKinds,
    },
  };
}

/// What changes: his permits, gear, room, falcons, birds held for sale, the
/// trip he is on, today's lots and what is lawful today. Small and the
/// same size at any herd.
Map<String, Object?> falconFacts(GameState state, OwnerId viewer) {
  final sim = Sim(state);
  final p = state.players[viewer]!;
  final h = p.falconry;
  final today = sim.today;
  final farm = p.farm;
  final t = h?.trip;
  return {
    'open': [
      for (final r in FalconRoute.values)
        if (r.openOn(today)) r.name,
    ],
    'permits': [
      for (final k in PermitKind.values)
        {
          'kind': k.name,
          'season': k.seasonFor(today),
          'opens': k.opens(k.seasonFor(today)).value,
          'closes': k.closes(k.seasonFor(today)).value,
          'open': k.seasonOn(today) != null,
          'held': h?.permits[k],
          'valid': h?.holds(k, today) ?? false,
          'cannot': cannotBuyPermit(sim, p, k)?.params['reason'],
        },
    ],
    'gear': {
      for (final g in Gear.values)
        g.name: [h?.has(g) ?? 0, h?.onTheWay(g) ?? 0, gearRoom(p, g)],
    },
    'room': {
      'built': farm.has(Facility.falconRoom) > 0,
      'building': [
        for (final b in farm.building)
          if (b.facility == Facility.falconRoom) b.doneOn.value,
      ],
      'held': h?.falcons.length ?? 0,
      'moult': HuntBalance.moultMonths.contains(today.month),
      'wantCare': [
        for (final f in h?.falcons ?? const <Falcon>[])
          if (f.where == FalconWhere.home && f.caredOn != today) f.id.value,
      ],
      'cannot': noRoomFor(p)?.params['reason'],
    },
    'falcons': [
      for (final f in h?.falcons ?? const <Falcon>[])
        _falcon(
          f,
          today,
          tracked: (h!.falcons.indexOf(f)) < h.has(Gear.tracker),
        ),
    ],
    'held': [
      for (final f in h?.held ?? const <Falcon>[])
        {..._falcon(f, today), 'entered': h!.entered.contains(f.id)},
    ],
    'trip': t == null
        ? null
        : {
            'kind': t.kind.name,
            'ground': t.ground.name,
            'groundName': t.ground.label,
            'startedOn': t.startedOn.value,
            'endOn': t.endOn.value,
            'oneDay': t.oneDay,
            'supplyDays': h!.has(Gear.supplies),
            'arriveOn': t.arriveOn.value,
            'arriveMinute': t.arriveMinute,
            'homeOn': t.homeOn?.value,
            'homeMinute': t.homeMinute,
            'sighted':
                h.work?.day == today &&
                h.work!.ground == t.ground &&
                h.work!.sighted &&
                !h.work!.resolved,
            'done': h.work?.day == today && h.work!.resolved,
            'workedToday': h.work?.day == today ? h.work!.ground.name : null,
            'lines': tripLines(t, today),
            'leg': Trips.leg(Game(state))?.landing,
            'stop': Trips.campStop(Game(state)),
          },
    'today': {
      'huntFrom': HuntSun.sunrise(today) + 60,
      'huntTo': HuntSun.sunset(today) - 60,
      'trapFrom': HuntSun.dawn(today),
      'trapTo': HuntSun.sunset(today),
      'quarry': {
        for (final g in Ground.values)
          if (g.hunting) g.name: quarryAt(g, today)?.label,
      },
    },
    'lots': [
      for (final r in FalconRoute.values)
        for (final l in FalconMarket.lots(state.world.seed, r, today))
          {
            'lot': l.key,
            'route': r.name,
            'species': l.species.label,
            'female': l.female,
            'age': FalconAge.on(today, l.hatched).label,
            'size': '${inches(l.lengthQ)} × ${inches(l.widthQ)}',
            'weight': l.weightG,
            'opening': l.opening,
            if (l.ground != null) 'ground': l.ground!.label,
            'trappedDaysAgo': ?l.trappedDaysAgo,
            'gone': h?.lotsGone.contains(l.key) ?? false,
          },
    ],
  };
}

Map<String, Object?> _falcon(Falcon f, GameDay today, {bool tracked = false}) =>
    {
      'id': f.id.value,
      'name': f.name,
      'species': f.species.name,
      'speciesName': f.species.label,
      'female': f.female,
      'age': f.ageOn(today).label,
      'how': f.how.name,
      'on': f.on.value,
      if (f.route != null) 'route': f.route!.label,
      'price': ?f.price,
      if (f.ground != null) 'ground': f.ground!.label,
      'size': '${inches(f.lengthQ)} × ${inches(f.widthQ)}',
      'weight': f.weightG,
      'passport': ?f.passport,
      if (f.ring) 'ring': true,
      'trapDoc': ?f.trapDoc,
      'dauDays': f.dauDays,
      'dauNeeded': HuntBalance.dauDaysNeeded,
      'caredOn': f.caredOn?.value,
      'flights': f.flights,
      'taken': {for (final e in f.taken.entries) e.key.label: e.value},
      'where': f.where.name,
      if (f.keep) 'keep': true,
      'ready': ready(f),
      if (tracked) 'tracker': true,
      // the day it steps back without الدعو (none in the moult's months)
      if (f.caredOn != null && f.dauDays > 0)
        'stepsBackOn': (f.caredOn! + HuntBalance.stepBackDays).value,
    };
