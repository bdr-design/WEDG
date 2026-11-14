// The hunting season's commands (task T18, part A). Every refusal is a
// DomainError(huntRefused, {'reason'}) with its words in FalconLines, and
// changes nothing (the owner's decision 4).
import '../catalog/falcon_lines.dart';
import '../catalog/falconry.dart';
import '../commands.dart';
import '../common/ids.dart';
import '../common/money.dart';
import '../common/result.dart';
import '../common/rng.dart';
import '../common/time.dart';
import '../events.dart';
import '../model/falconry.dart';
import '../model/player.dart';
import '../rules/balance.dart';
import '../rules/falcon_market.dart';
import '../rules/hunt_balance.dart';
import '../rules/trap_odds.dart';
import '../sim.dart';
import 'handlers.dart' show cashFor;

Err refuse(Sim sim, HuntRefusal why, [Map<String, Object> more = const {}]) =>
    Err(
      DomainError(ErrorCode.huntRefused, {'reason': why.name, ...more}),
      sim.drain(),
    );

// ---------------------------------------------------------------- permits

/// Why [kind] cannot be bought today, or null.
DomainError? cannotBuyPermit(Sim sim, PlayerState p, PermitKind kind) {
  final h = p.falconry;
  final season = kind.seasonFor(sim.today);
  if (h != null && h.permits[kind] == season) {
    return DomainError(ErrorCode.huntRefused, {
      'reason': HuntRefusal.permitHeld.name,
      'kind': kind.name,
    });
  }
  // the hunting permit: for a falconer whose falcon has its passport
  // [128][131]
  if (kind == PermitKind.hunting &&
      !(h?.falcons.any((f) => f.passport != null) ?? false)) {
    return DomainError(ErrorCode.huntRefused, {
      'reason': HuntRefusal.needsFalcon.name,
    });
  }
  return cashFor(p, kind.fee);
}

Result buyPermit(Sim sim, PlayerState p, BuyPermit cmd) {
  final no = cannotBuyPermit(sim, p, cmd.kind);
  if (no != null) return Err(no, sim.drain());
  final season = cmd.kind.seasonFor(sim.today);
  p.hunt.permits[cmd.kind] = season;
  sim.pay(
    p,
    Riyal(-cmd.kind.fee),
    LedgerCategory.huntPermit,
    ref: cmd.kind.name,
  );
  sim.emit(
    PermitBought(
      sim.today,
      owner: p.id,
      kind: cmd.kind,
      season: season,
      fee: cmd.kind.fee,
    ),
  );
  return Ok(sim.drain());
}

// ------------------------------------------------------------------- gear

/// How many more of [g] he may order now (held and on the way count).
int gearRoom(PlayerState p, Gear g) {
  final h = p.falconry;
  final held = h == null ? 0 : h.has(g) + h.onTheWay(g);
  return g.most - held < 0 ? 0 : g.most - held;
}

Result orderGear(Sim sim, PlayerState p, OrderGear cmd) {
  if (cmd.units < 1) {
    return Err(const DomainError(ErrorCode.invalidAmount), sim.drain());
  }
  final room = gearRoom(p, cmd.gear);
  if (cmd.units > room) {
    return refuse(sim, HuntRefusal.gearFull, {'room': room});
  }
  final cost = cmd.gear.price * cmd.units;
  final money = cashFor(p, cost);
  if (money != null) return Err(money, sim.drain());
  final arrives = sim.today + Balance.deliveryDays;
  p.hunt.coming.add(GearDelivery(cmd.gear, cmd.units, arrives));
  // (the tracker is the falcon's, not the trapping's: booked with the
  // falcons)
  sim.pay(
    p,
    Riyal(-cost),
    cmd.gear == Gear.tracker
        ? LedgerCategory.falconPurchase
        : LedgerCategory.falconGear,
    ref: cmd.gear.name,
  );
  sim.emit(
    GearOrdered(
      sim.today,
      owner: p.id,
      gear: cmd.gear,
      units: cmd.units,
      cost: cost,
      arrivesOn: arrives,
    ),
  );
  return Ok(sim.drain());
}

// ---------------------------------------------------------------- falcons

/// Why a falcon cannot come to the farm now: no room, or a full one.
DomainError? noRoomFor(PlayerState p) {
  if (p.farm.has(Facility.falconRoom) == 0) {
    return DomainError(ErrorCode.huntRefused, {
      'reason': HuntRefusal.noRoom.name,
    });
  }
  if ((p.falconry?.falcons.length ?? 0) >= HuntBalance.roomHolds) {
    return DomainError(ErrorCode.huntRefused, {
      'reason': HuntRefusal.roomFull.name,
    });
  }
  return null;
}

/// Today's lot [key], or null (not today's, or not offered).
FalconLot? lotOf(Sim sim, String key) {
  final parts = key.split(':');
  if (parts.length != 3) return null;
  final route = FalconRoute.values.where((r) => r.name == parts[0]).firstOrNull;
  final day = int.tryParse(parts[1]);
  final i = int.tryParse(parts[2]);
  if (route == null || day != sim.today.value || i == null) return null;
  final lots = FalconMarket.lots(sim.world.seed, route, sim.today);
  return i >= 0 && i < lots.length ? lots[i] : null;
}

/// The next name of the game's list for a new falcon.
String nextName(PlayerState p) {
  final h = p.hunt;
  final n = HuntBalance.names[h.named % HuntBalance.names.length];
  final round = h.named ~/ HuntBalance.names.length;
  h.named++;
  return round == 0 ? n : '$n ${round + 1}';
}

Result buyFalcon(Sim sim, PlayerState p, BuyFalcon cmd) {
  final route = FalconRoute.values
      .where((r) => cmd.lot.startsWith('${r.name}:'))
      .firstOrNull;
  if (route != null && !route.openOn(sim.today)) {
    return refuse(sim, HuntRefusal.routeClosed, {'route': route.name});
  }
  final lot = lotOf(sim, cmd.lot);
  if (lot == null) return refuse(sim, HuntRefusal.notALot);
  if (p.falconry?.lotsGone.contains(lot.key) ?? false) {
    return refuse(sim, HuntRefusal.lotGone);
  }
  final room = noRoomFor(p);
  if (room != null) return Err(room, sim.drain());
  if (cmd.upTo < 1) {
    return Err(const DomainError(ErrorCode.invalidAmount), sim.drain());
  }
  final money = cashFor(p, cmd.upTo);
  if (money != null) return Err(money, sim.drain());
  final h = p.hunt;
  h.lotsGone
    ..removeWhere((k) => !k.contains(':${sim.today.value}:'))
    ..add(lot.key);
  // the hammer falls at the bird's worth tonight: his ceiling reaches it and
  // he pays it; else it goes to another, its price told, gone for good
  final paid = lot.value;
  if (cmd.upTo < paid) {
    sim.emit(
      FalconLotLost(
        sim.today,
        owner: p.id,
        lot: lot.key,
        route: route!,
        price: paid,
      ),
    );
    return Ok(sim.drain());
  }
  final rng = sim.rng(['falconPassport', lot.key]);
  final f = Falcon(
    id: sim.world.ids.falcon(),
    name: nextName(p),
    species: lot.species,
    female: lot.female,
    hatched: lot.hatched,
    how: FalconHow.bought,
    on: sim.today,
    route: lot.route,
    price: paid,
    lengthQ: lot.lengthQ,
    widthQ: lot.widthQ,
    weightG: lot.weightG,
    passport: FalconMarket.passportNumber(rng),
    // the trapping auction rings its birds after the sale [191]
    ring: lot.route == FalconRoute.trapping,
    skill: lot.skill,
  );
  h.falcons.add(f);
  sim.pay(p, Riyal(-paid), LedgerCategory.falconPurchase, ref: f.id.value);
  sim.emit(
    FalconBought(
      sim.today,
      owner: p.id,
      falcon: f.id.value,
      name: f.name,
      species: f.species,
      route: lot.route,
      price: paid,
    ),
  );
  return Ok(sim.drain());
}

// ------------------------------------------------------------------ trips

DomainError _no(HuntRefusal why, [Map<String, Object> more = const {}]) =>
    DomainError(ErrorCode.huntRefused, {'reason': why.name, ...more});

/// A falcon of his in the room, home and with its الدعو done.
bool ready(Falcon f) =>
    f.where == FalconWhere.home && f.dauDays >= HuntBalance.dauDaysNeeded;

/// Why [kind] cannot go to [ground] for [nights] now, or null.
DomainError? cannotStart(
  Sim sim,
  PlayerState p,
  TripKind kind,
  Ground ground,
  int nights,
) {
  final h = p.falconry;
  if (h?.trip != null) return _no(HuntRefusal.onTrip);
  if (nights < 0 || nights > HuntBalance.mostNights) {
    return const DomainError(ErrorCode.invalidAmount);
  }
  final today = sim.today;
  if (kind == TripKind.trapping) {
    if (!ground.trapping) return _no(HuntRefusal.offGround);
    if (PermitKind.trapping.seasonOn(today) == null) {
      return _no(HuntRefusal.outOfSeason, {'kind': 'trapping'});
    }
    if (!(h?.holds(PermitKind.trapping, today) ?? false)) {
      return _no(HuntRefusal.noPermit, {'kind': 'trapping'});
    }
  } else {
    if (!ground.hunting) return _no(HuntRefusal.notHuntingGround);
    if (PermitKind.hunting.seasonOn(today) == null) {
      return _no(HuntRefusal.outOfSeason, {'kind': 'hunting'});
    }
    if (!(h?.holds(PermitKind.hunting, today) ?? false)) {
      return _no(HuntRefusal.noPermit, {'kind': 'hunting'});
    }
    if (!(h?.falcons.any(ready) ?? false)) return _no(HuntRefusal.notReady);
  }
  if (nights == 0 && !ground.oneDayFrom(p.farm.region)) {
    return _no(HuntRefusal.tooFar);
  }
  if (nights > 0 && (h?.has(Gear.supplies) ?? 0) == 0) {
    return _no(HuntRefusal.noSupplies);
  }
  return null;
}

Result startTrip(Sim sim, PlayerState p, StartTrip cmd) {
  final no = cannotStart(sim, p, cmd.kind, cmd.ground, cmd.nights);
  if (no != null) return Err(no, sim.drain());
  p.hunt.trip = Trip(
    kind: cmd.kind,
    ground: cmd.ground,
    startedOn: sim.today,
    endOn: sim.today + cmd.nights,
    oneDay: cmd.nights == 0,
  );
  sim.emit(
    TripChanged(
      sim.today,
      owner: p.id,
      what: TripChange.started,
      kind: cmd.kind,
      ground: cmd.ground,
    ),
  );
  return Ok(sim.drain());
}

/// The trip's own lines for the summary (TripChanged.lines and the away
/// call's extra lines).
Map<String, int> tripLines(Trip t, GameDay today) => {
  'nights': t.oneDay ? 0 : today.daysSince(t.startedOn),
  'caught': t.caught,
  'released': t.released,
  'stooped': t.stooped,
  'flights': t.flights,
  'taken': t.taken,
  'suppliesUsed': t.suppliesUsed,
};

/// Ends [p]'s trip today (his tap, or a day's outing at the day's end).
void endTripNow(Sim sim, PlayerState p) {
  final h = p.falconry;
  final t = h?.trip;
  if (t == null) return;
  h!.trip = null;
  sim.emit(
    TripChanged(
      sim.today,
      owner: p.id,
      what: TripChange.ended,
      kind: t.kind,
      ground: t.ground,
      lines: tripLines(t, sim.today),
    ),
  );
}

Result endTrip(Sim sim, PlayerState p, EndTrip cmd) {
  if (p.falconry?.trip == null) return refuse(sim, HuntRefusal.notOnTrip);
  endTripNow(sim, p);
  return Ok(sim.drain());
}

Result moveCamp(Sim sim, PlayerState p, MoveCamp cmd) {
  final t = p.falconry?.trip;
  if (t == null || t.kind != TripKind.trapping || t.oneDay) {
    return refuse(sim, HuntRefusal.notOnTrip);
  }
  if (p.hunt.has(Gear.mobileTent) == 0) return refuse(sim, HuntRefusal.noTent);
  if (!cmd.ground.trapping) return refuse(sim, HuntRefusal.offGround);
  t
    ..ground = cmd.ground
    // the day's falcon was the old ground's
    ..workDay = null;
  t.today(sim.today);
  t.resolved = true;
  sim.emit(
    TripChanged(
      sim.today,
      owner: p.id,
      what: TripChange.moved,
      kind: t.kind,
      ground: cmd.ground,
    ),
  );
  return Ok(sim.drain());
}

// --------------------------------------------------------------- trapping

/// Why the net cannot be used where [at] is at [minute], or null: off a
/// trapping ground, out of the season, without the permit, at night, not
/// camped there. The order is the warning's (the place first).
DomainError? cannotTrap(Sim sim, PlayerState p, HuntAt at, int minute) {
  final g = at.ground;
  if (g == null || !g.trapping) return _no(HuntRefusal.offGround);
  final today = sim.today;
  if (PermitKind.trapping.seasonOn(today) == null) {
    return _no(HuntRefusal.outOfSeason, {'kind': 'trapping'});
  }
  final h = p.falconry;
  if (!(h?.holds(PermitKind.trapping, today) ?? false)) {
    return _no(HuntRefusal.noPermit, {'kind': 'trapping'});
  }
  if (!HuntSun.trappingHours(today, minute)) return _no(HuntRefusal.night);
  final t = h!.trip;
  if (t == null || t.kind != TripKind.trapping || t.ground != g) {
    return _no(HuntRefusal.notOnTrip);
  }
  return null;
}

Result spotFalcon(Sim sim, PlayerState p, SpotFalcon cmd) {
  final minute = cmd.minute ?? 0;
  final no = cannotTrap(sim, p, cmd.at, minute);
  if (no != null) return Err(no, sim.drain());
  final t = p.hunt.trip!..today(sim.today);
  final w = HuntSun.window(sim.today, minute)!;
  final passer = TrapOdds.passer(sim.world.seed, t.ground, sim.today);
  // one look a window counts: the same falcon is seen or missed however
  // often he looks (no help from tapping)
  final first = t.looked.add(w);
  var seen = t.sighted && !t.resolved && passer?.window == w;
  if (!seen && first && passer != null && !t.resolved && passer.window == w) {
    final eye = p.hunt.has(Gear.binoculars) > 0
        ? TrapOdds.spotBinoculars
        : TrapOdds.spotEyes;
    seen = sim.rng(['trapSpot', t.ground.name, w.name]).chance(eye);
    t.sighted = seen;
  }
  sim.emit(
    TrapResult(
      sim.today,
      owner: p.id,
      outcome: seen ? TrapOutcome.inSight : TrapOutcome.nothingInSight,
      window: seen ? w : null,
    ),
  );
  return Ok(sim.drain());
}

Result releaseLure(Sim sim, PlayerState p, ReleaseLure cmd) {
  final minute = cmd.minute ?? 0;
  final no = cannotTrap(sim, p, cmd.at, minute);
  if (no != null) return Err(no, sim.drain());
  final h = p.hunt;
  final has = cmd.lure == Lure.pigeon
      ? h.has(Gear.pigeon) > 0 && h.has(Gear.pigeonNet) > 0
      : h.has(Gear.birdNet) > 0;
  if (!has) return refuse(sim, HuntRefusal.noLure, {'lure': cmd.lure.name});
  final t = h.trip!..today(sim.today);
  final w = HuntSun.window(sim.today, minute)!;
  final passer = TrapOdds.passer(sim.world.seed, t.ground, sim.today);
  void out(TrapOutcome o, {FalconSpecies? s, bool? farkh, String? falcon}) =>
      sim.emit(
        TrapResult(
          sim.today,
          owner: p.id,
          outcome: o,
          species: s,
          farkh: farkh,
          falcon: falcon,
        ),
      );
  // nothing seen: nothing comes, and the pigeon flies back
  if (!t.sighted || t.resolved || passer == null || passer.window != w) {
    out(TrapOutcome.nothingCame);
    return Ok(sim.drain());
  }
  if (cmd.lure == Lure.pigeon) h.gear[Gear.pigeon] = h.has(Gear.pigeon) - 1;
  // the same lure after a refusal is half as likely to be taken
  final same = t.tries; // tries so far at this falcon
  final base = cmd.lure == Lure.pigeon
      ? TrapOdds.takePigeon
      : TrapOdds.takeBirdNet;
  final halves = _sameBefore(t, cmd.lure);
  var take = base;
  for (var i = 0; i < halves; i++) {
    take /= 2;
  }
  final rng = sim.rng(['trapTake', t.ground.name, same]);
  _noteLure(t, cmd.lure);
  t.tries++;
  if (!rng.chance(take)) {
    if (t.tries >= TrapOdds.triesMost) {
      t.resolved = true;
      out(TrapOutcome.refusedAndWent);
    } else {
      out(TrapOutcome.refused);
    }
    return Ok(sim.drain());
  }
  t.resolved = true;
  if (!rng.chance(TrapOdds.hold)) {
    t.stooped++;
    out(TrapOutcome.stooped);
    return Ok(sim.drain());
  }
  if (!passer.sellable) {
    t.released++;
    out(TrapOutcome.released, s: passer.species, farkh: passer.farkh);
    return Ok(sim.drain());
  }
  final bird = _netted(sim, p, t.ground, rng);
  h.held.add(bird);
  t.caught++;
  out(TrapOutcome.netted, s: bird.species, farkh: true, falcon: bird.id.value);
  return Ok(sim.drain());
}

/// The lures tried at the day's falcon, by kind: kept in [Trip.casts] under
/// a key of their own (the day's map is cleared with the day).
int _sameBefore(Trip t, Lure l) => t.casts['lure:${l.name}'] ?? 0;
void _noteLure(Trip t, Lure l) =>
    t.casts['lure:${l.name}'] = _sameBefore(t, l) + 1;

/// A passage peregrine of the year in the net: its size and weight, its
/// worth at the trapping auction (HIDDEN, drawn from the real spread), its
/// skill (HIDDEN).
Falcon _netted(Sim sim, PlayerState p, Ground g, Rng rng) {
  const female = true; // females only for now (the answers, phase 2)
  final (len, wid, wt) = HuntBalance.sizeOf(
    FalconSpecies.passagePeregrine,
    female,
    rng,
  );
  final value = HuntBalance.worthAt(FalconRoute.trapping, rng.nextDouble());
  return Falcon(
    id: sim.world.ids.falcon(),
    name: nextName(p),
    species: FalconSpecies.passagePeregrine,
    female: female,
    hatched: sim.today.date.year,
    how: FalconHow.trapped,
    on: sim.today,
    ground: g,
    lengthQ: len,
    widthQ: wid,
    weightG: wt,
    skill: FalconMarket.q(0.3 + 0.5 * rng.nextDouble()),
    value: value,
    caredOn: sim.today,
  );
}

// ----------------------------------------------------- a trapped bird's fate

Falcon? _held(PlayerState p, FalconId id) =>
    p.falconry?.held.where((f) => f.id == id).firstOrNull;

/// The club's check: the trapping documented, its registration's number
/// (وثيقة تسجيل طرح [190][191][192]).
void clubCheck(Sim sim, Falcon f) {
  f.trapDoc ??= FalconMarket.passportNumber(sim.rng(['trapDoc', f.id.value]));
}

Result enterTrapAuction(Sim sim, PlayerState p, EnterTrapAuction cmd) {
  final f = _held(p, cmd.falcon);
  if (f == null) return refuse(sim, HuntRefusal.notHeld);
  if (!FalconRoute.trapping.openOn(sim.today)) {
    return refuse(sim, HuntRefusal.auctionClosed);
  }
  clubCheck(sim, f);
  p.hunt.entered.add(f.id);
  sim.emit(
    FalconFate(
      sim.today,
      owner: p.id,
      falcon: f.id.value,
      name: f.name,
      fate: Fate.entered,
    ),
  );
  return Ok(sim.drain());
}

Result keepBird(Sim sim, PlayerState p, KeepBird cmd) {
  final f = _held(p, cmd.falcon);
  if (f == null) return refuse(sim, HuntRefusal.notHeld);
  final room = noRoomFor(p);
  if (room != null) return Err(room, sim.drain());
  final h = p.hunt;
  // kept through the club too: the same check, the registration, then the
  // passport (the answers' Q-7)
  clubCheck(sim, f);
  f
    ..passport = FalconMarket.passportNumber(
      sim.rng(['falconPassport', f.id.value]),
    )
    ..keep = true
    ..caredOn = sim.today;
  h.held.remove(f);
  h.entered.remove(f.id);
  h.falcons.add(f);
  sim.emit(
    FalconFate(
      sim.today,
      owner: p.id,
      falcon: f.id.value,
      name: f.name,
      fate: Fate.kept,
    ),
  );
  return Ok(sim.drain());
}

Result releaseFalcon(Sim sim, PlayerState p, ReleaseFalcon cmd) {
  final f = p.falconry?.falcon(cmd.falcon);
  if (f == null || !f.keep) return refuse(sim, HuntRefusal.notKept);
  final (fm, fd) = HuntBalance.releaseFrom;
  final (tm, td) = HuntBalance.releaseTo;
  if (!inSpan(sim.today, fm, fd, tm, td)) {
    return refuse(sim, HuntRefusal.releaseMonths);
  }
  p.hunt.falcons.remove(f);
  sim.emit(
    FalconFate(
      sim.today,
      owner: p.id,
      falcon: f.id.value,
      name: f.name,
      fate: Fate.freed,
    ),
  );
  return Ok(sim.drain());
}

// --------------------------------------------------------------- falconry

/// Why [f] cannot be cast where [at] is now, or null.
DomainError? cannotCast(
  Sim sim,
  PlayerState p,
  Falcon? f,
  HuntAt at, {
  required bool moving,
  required int minute,
}) {
  final today = sim.today;
  switch (at.off) {
    case HuntOff.farm:
      return _no(HuntRefusal.nearFarm);
    case HuntOff.coast:
      return _no(HuntRefusal.coast);
    case HuntOff.reserve:
      return _no(HuntRefusal.reserve);
    case HuntOff.open || null:
      break;
  }
  final g = at.ground;
  if (g != null && !g.hunting) return _no(HuntRefusal.notHuntingGround);
  if (PermitKind.hunting.seasonOn(today) == null) {
    return _no(HuntRefusal.outOfSeason, {'kind': 'hunting'});
  }
  final h = p.falconry;
  if (!(h?.holds(PermitKind.hunting, today) ?? false)) {
    return _no(HuntRefusal.noPermit, {'kind': 'hunting'});
  }
  if (!HuntSun.huntingHours(today, minute)) return _no(HuntRefusal.notByDay);
  if (moving) return _no(HuntRefusal.movingCar);
  if (quarryAt(g, today) == null) return _no(HuntRefusal.noQuarry);
  if (f == null || f.where != FalconWhere.home) {
    return _no(HuntRefusal.falconAway);
  }
  if (f.dauDays < HuntBalance.dauDaysNeeded) return _no(HuntRefusal.notReady);
  final t = h!.trip;
  if (t != null &&
      t.workDay == today &&
      (t.casts[f.id.value] ?? 0) >= TrapOdds.flightsADay) {
    return _no(HuntRefusal.flownOut);
  }
  return null;
}

/// The quarry lawful at [g] (null: open land) today, the houbara first in
/// the estate; or null.
Quarry? quarryAt(Ground? g, GameDay day) {
  final kinds = g == null ? const [Quarry.stoneCurlew] : g.quarry;
  for (final q in kinds) {
    if (q.openOn(day)) return q;
  }
  return null;
}

Result castFalcon(Sim sim, PlayerState p, CastFalcon cmd) {
  final f = p.falconry?.falcon(cmd.falcon);
  final minute = cmd.minute ?? 0;
  final no = cannotCast(
    sim,
    p,
    f,
    cmd.at,
    moving: cmd.inCar && cmd.moving,
    minute: minute,
  );
  if (no != null) return Err(no, sim.drain());
  final h = p.hunt;
  // a cast on no trip is a day's flight from where he stands: it is counted
  // on a trip if there is one
  final t = h.trip?..today(sim.today);
  final n = t?.casts[f!.id.value] ?? 0;
  t?.casts[f!.id.value] = n + 1;
  final q = quarryAt(cmd.at.ground, sim.today)!;
  final rng = sim.rng(['cast', f!.id.value, n, minute ~/ 60]);
  f
    ..flights += 1
    ..caredOn = sim.today; // a day it flew counts as cared for (Q-24)
  t?.flights++;
  if (rng.chance(TrapOdds.lost)) {
    f.where = FalconWhere.lost;
    sim.emit(
      CastResult(
        sim.today,
        owner: p.id,
        falcon: f.id.value,
        name: f.name,
        outcome: CastOutcome.lost,
      ),
    );
    return Ok(sim.drain());
  }
  final caught = rng.chance(TrapOdds.castChance(f.skill, cmd.at.ground, q));
  if (caught) {
    f.taken[q] = (f.taken[q] ?? 0) + 1;
    t?.taken++;
  }
  sim.emit(
    CastResult(
      sim.today,
      owner: p.id,
      falcon: f.id.value,
      name: f.name,
      outcome: caught ? CastOutcome.caught : CastOutcome.missed,
      quarry: q,
    ),
  );
  return Ok(sim.drain());
}

Result searchFalcon(Sim sim, PlayerState p, SearchFalcon cmd) {
  final h = p.falconry;
  final f = h?.falcon(cmd.falcon);
  if (f == null || f.where != FalconWhere.lost) {
    return refuse(sim, HuntRefusal.notLost);
  }
  // each falcon wears its own tracker (the answers' Q-27): one held for
  // each falcon up to the count
  final i = h!.falcons.indexOf(f);
  final tracked = i < h.has(Gear.tracker);
  final found = sim
      .rng(['falconSearch', f.id.value])
      .chance(tracked ? TrapOdds.foundWithTracker : TrapOdds.foundWithout);
  if (found) {
    f.where = FalconWhere.home;
  } else {
    h.falcons.remove(f);
  }
  sim.emit(
    FalconFate(
      sim.today,
      owner: p.id,
      falcon: f.id.value,
      name: f.name,
      fate: found ? Fate.found : Fate.gone,
    ),
  );
  return Ok(sim.drain());
}

Result careFalcons(Sim sim, PlayerState p, CareFalcons cmd) {
  final h = p.falconry;
  if (h == null || h.falcons.isEmpty)
    return refuse(sim, HuntRefusal.falconAway);
  if (HuntBalance.moultMonths.contains(sim.today.month)) {
    return refuse(sim, HuntRefusal.moult);
  }
  for (final f in h.falcons.where((f) => f.where == FalconWhere.home)) {
    final gap = f.caredOn == null ? 1 : sim.today.daysSince(f.caredOn!);
    if (gap <= 0) continue;
    // the days since the last care count (the design's view 8: «وتنحسب لك
    // الأيام اللي فاتت»), unless two weeks went by: then it stepped back
    // (FalconrySystem) and today counts alone
    final add = gap < HuntBalance.stepBackDays ? gap : 1;
    f
      ..dauDays = (f.dauDays + add).clamp(0, HuntBalance.dauDaysNeeded)
      ..caredOn = sim.today;
    sim.emit(
      FalconFate(
        sim.today,
        owner: p.id,
        falcon: f.id.value,
        name: f.name,
        fate: Fate.cared,
      ),
    );
  }
  return Ok(sim.drain());
}
