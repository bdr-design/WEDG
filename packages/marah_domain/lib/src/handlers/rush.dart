// The rush (task T15, docs/proposals/rush_and_calendar.md section 2; the
// proxy's batches 4 and 4b, provisional): what money can hurry in the real
// world finishes now, for more, from cash only (never on the merchant's
// account; refused below zero). The standing order and the vet's contract,
// the player's switches for being away, are here too.
import '../commands.dart';
import '../common/ids.dart';
import '../common/money.dart';
import '../common/result.dart';
import '../common/rng.dart';
import '../common/time.dart';
import '../events.dart';
import '../model/camel.dart';
import '../model/player.dart';
import '../rules/balance.dart';
import '../rules/eligibility.dart';
import '../rules/provisions.dart';
import '../sim.dart';
import '../systems/systems.dart';
import 'handlers.dart';
import 'handlers.dart' as handlers;

Err _no(Sim sim, ErrorCode code, [Map<String, Object> params = const {}]) =>
    Err(DomainError(code, params), sim.drain());

// ------------------------------------------------------------ facilities

/// What finishing the earliest [f] being built costs today, or null.
int? rushBuildFee(Sim sim, PlayerState p, Facility f) {
  final b = earliestBuilding(p, f);
  if (b == null) return null;
  return Balance.rushBuildFee(f.price, b.doneOn.daysSince(sim.today));
}

Construction? earliestBuilding(PlayerState p, Facility f) {
  Construction? best;
  for (final b in p.farm.building) {
    if (b.facility == f && (best == null || b.doneOn < best.doneOn)) best = b;
  }
  return best;
}

Result rushBuild(Sim sim, PlayerState p, RushBuild cmd) {
  final b = earliestBuilding(p, cmd.facility);
  if (b == null) return _no(sim, ErrorCode.nothingToRush);
  final fee = rushBuildFee(sim, p, cmd.facility)!;
  final money = cashFor(p, fee);
  if (money != null) return Err(money, sim.drain());
  sim.pay(p, Riyal(-fee), LedgerCategory.rush, ref: cmd.facility.name);
  sim.emit(
    Rushed(
      sim.today,
      owner: p.id,
      what: 'facility',
      ref: cmd.facility.name,
      fee: fee,
    ),
  );
  p.farm.building.remove(b);
  UpkeepSystem.stand(sim, p, b.facility);
  return Ok(sim.drain());
}

// ------------------------------------------------------------ deliveries

bool _ofKind(Supply s, StandingOrder k) =>
    k == StandingOrder.water ? s == Supply.water : s != Supply.water;

/// The deliveries of [kind] still on their way.
List<Delivery> coming(PlayerState p, StandingOrder kind) => [
  for (final d in p.farm.deliveries)
    if (_ofKind(d.supply, kind)) d,
];

/// The herd went short of [kind] today (the day's record, UpkeepSystem).
bool shortToday(Sim sim, PlayerState p, StandingOrder kind) {
  final r = p.farm.today;
  if (r == null || r.day != sim.today) return false;
  return kind == StandingOrder.water ? r.waterShort : r.feedShort;
}

/// What bringing [ds] now costs: a tanker half its price again; feed half
/// the order again, at most Balance.rushFeedCap.
int rushDeliveryFee(PlayerState p, StandingOrder kind, List<Delivery> ds) {
  var price = 0.0;
  for (final d in ds) {
    price += d.supply == Supply.water
        ? Provisions.tankerPrice(
                d.size == Balance.smallWaterLoadL ? Tanker.small : Tanker.large,
              ) *
              d.units
        : Provisions.unitPrice(d.supply, p.farm.region) * d.units;
  }
  final fee = (price * Balance.rushDeliveryShare).round();
  return kind == StandingOrder.feed && fee > Balance.rushFeedCap
      ? Balance.rushFeedCap
      : fee;
}

Result rushDelivery(Sim sim, PlayerState p, RushDelivery cmd) {
  if (!shortToday(sim, p, cmd.kind)) {
    return _no(sim, ErrorCode.notShortToday, {'supply': cmd.kind.name});
  }
  final ds = coming(p, cmd.kind);
  if (ds.isEmpty) return _no(sim, ErrorCode.nothingToRush);
  final fee = rushDeliveryFee(p, cmd.kind, ds);
  final money = cashFor(p, fee);
  if (money != null) return Err(money, sim.drain());
  sim.pay(p, Riyal(-fee), LedgerCategory.rush, ref: cmd.kind.name);
  sim.emit(
    Rushed(
      sim.today,
      owner: p.id,
      what: cmd.kind.name,
      ref: cmd.kind.name,
      fee: fee,
    ),
  );
  for (final d in ds) {
    p.farm.deliveries.remove(d);
    UpkeepSystem.deliverOne(sim, p, d);
  }
  makeGood(sim, p, cmd.kind);
  return Ok(sim.drain());
}

/// Makes up what today lacked of [kind] from what is now in the store or
/// the tank (the note's 2.2): the herd drinks or eats what the day's need
/// still lacks; a day made full no longer counts dry or hungry; today's
/// condition is corrected once by what Care would have made of the
/// corrected day (exact up to Care's rounding to 0.01 and its clamp). The
/// dawn's milk stands (the record keeps it); a death at dawn stands.
void makeGood(Sim sim, PlayerState p, StandingOrder kind) {
  final f = p.farm, r = f.today;
  if (r == null || r.day != sim.today) return;
  // the herd as it was at dawn: a camel bought or born today (after the
  // day's step) never went short (the review's L1)
  final herd = [
    for (final c in sim.herdOf(p.id))
      if (c.acquiredOn < sim.today) c,
  ];
  var pull = 0.0;
  if (kind == StandingOrder.water && r.waterShort) {
    final wasDry = f.dryDays > 0;
    final lack = r.waterNeed - r.waterDrunk;
    final x = lack < f.waterL ? lack : f.waterL;
    f.waterL = q2(f.waterL - x);
    r.waterDrunk += x;
    if (r.waterDrunk >= r.waterNeed - 1e-9) {
      f
        ..dryDays = 0
        ..short.remove(Supply.water);
    } else if (r.waterDrunk >= r.waterNeed / 2) {
      f.dryDays = r.dryBefore;
    }
    if (wasDry && f.dryDays == 0) pull += Balance.thirstPenalty;
  }
  if (kind == StandingOrder.feed && r.feedShort) {
    final before = f.fedShare;
    double eat(double need, double eaten, double have) {
      final lack = need - eaten;
      return lack < have ? lack : have;
    }

    final b = eat(r.barleyNeed, r.barleyEaten, f.barleyKg);
    final a = eat(r.alfalfaNeed, r.alfalfaEaten, f.alfalfaKg);
    f
      ..barleyKg = q2(f.barleyKg - b)
      ..alfalfaKg = q2(f.alfalfaKg - a);
    r
      ..barleyEaten += b
      ..alfalfaEaten += a;
    final need = r.barleyNeed + r.alfalfaNeed;
    f.fedShare = need <= 0 ? 1 : q2((r.barleyEaten + r.alfalfaEaten) / need);
    if (r.barleyEaten >= r.barleyNeed - 1e-9) f.short.remove(Supply.barley);
    if (r.alfalfaEaten >= r.alfalfaNeed - 1e-9) f.short.remove(Supply.alfalfa);
    pull += (f.feedPlan.conditionTarget - 35) * (f.fedShare - before);
  }
  if (pull == 0) return;
  for (final c in herd) {
    c.condition = q2(
      clampDouble(c.condition + pull * Balance.conditionPull, 5, 98),
    );
  }
}

// ------------------------------------------------------------ the truck

/// What the trucking of [c], bought today, cost (the ledger's row), or 0.
int truckingOf(PlayerState p, Camel c, Sim sim) {
  for (var i = p.ledger.length - 1; i >= 0; i--) {
    final e = p.ledger[i];
    if (e.day != sim.today) break;
    if (e.category == LedgerCategory.transport && e.ref == c.id.value) {
      return -e.amount.value;
    }
  }
  return 0;
}

Result rushTruck(Sim sim, PlayerState p, RushTruck cmd) {
  final c = sim.world.camels[cmd.camel];
  final own = Eligibility.owned(c, p.id);
  if (own != null) return Err(own, sim.drain());
  if (!Eligibility.onTheWay(c!, sim.today)) {
    return _no(sim, ErrorCode.nothingToRush);
  }
  final hour = cmd.hour ?? 0;
  if (hour < 0 || hour > 23) return _no(sim, ErrorCode.invalidAmount);
  final fee = Balance.rushTruckFee(truckingOf(p, c, sim), hour);
  final money = cashFor(p, fee);
  if (money != null) return Err(money, sim.drain());
  sim.pay(p, Riyal(-fee), LedgerCategory.rush, ref: c.id.value);
  c.arrivedOn = sim.today;
  sim.emit(
    Rushed(
      sim.today,
      owner: p.id,
      camel: c.id,
      what: 'camel',
      ref: c.id.value,
      fee: fee,
    ),
  );
  return Ok(sim.drain());
}

// ------------------------------------------------------------ switches

Result setStanding(Sim sim, PlayerState p, SetStandingOrder cmd) {
  if (cmd.on) {
    p.farm.standing.add(cmd.kind);
  } else {
    p.farm.standing.remove(cmd.kind);
  }
  sim.emit(
    StandingOrderChanged(sim.today, owner: p.id, kind: cmd.kind, on: cmd.on),
  );
  return Ok(sim.drain());
}

/// This month's part of the contract's fee, from today to the month's end.
int vetContractPart(Sim sim, PlayerState p) {
  final d = sim.today.date;
  final days = DateTime.utc(d.year, d.month + 1, 0).day;
  final left = days - d.day + 1;
  return (Balance.vetContractFee(sim.herdOf(p.id).length) * left / days)
      .round();
}

Result signVet(Sim sim, PlayerState p, SignVetContract cmd) {
  final v = p.farm.vet;
  if (v != null && v.endsOn == null) return _no(sim, ErrorCode.contractState);
  if (v != null) {
    // cancelled and running to the month's end: signed again, paid already
    v.endsOn = null;
    sim.emit(VetContractChanged(sim.today, owner: p.id, on: true));
    return Ok(sim.drain());
  }
  final fee = vetContractPart(sim, p);
  // a retainer is no treatment: cash only (the proxy's batch 4c)
  final money = cashFor(p, fee);
  if (money != null) return Err(money, sim.drain());
  sim.pay(p, Riyal(-fee), LedgerCategory.vetContract);
  p.farm.vet = VetContract(since: sim.today);
  sim.emit(VetContractChanged(sim.today, owner: p.id, on: true, fee: fee));
  // every camel sick now treated, each at its price, on account as the vet is
  for (final c in sim.herdOf(p.id).toList()) {
    if (c.health == HealthStatus.sick) {
      final r = treatCamel(sim, p, c);
      r.events.forEach(sim.emit); // (drained by the handler: put back)
      if (r is Err) {
        sim.emit(VetRefused(sim.today, owner: p.id, camel: c.id, name: c.name));
      }
    }
  }
  return Ok(sim.drain());
}

Result cancelVet(Sim sim, PlayerState p, CancelVetContract cmd) {
  final v = p.farm.vet;
  if (v == null || v.endsOn != null) return _no(sim, ErrorCode.contractState);
  final d = sim.today.date;
  v.endsOn = GameDay.ofDate(DateTime.utc(d.year, d.month + 1, 0));
  sim.emit(
    VetContractChanged(sim.today, owner: p.id, on: false, endsOn: v.endsOn),
  );
  return Ok(sim.drain());
}

/// Every sick camel treated, the oldest illness first, till the account's
/// limit stops it (what was treated stands; the rest are said by the refusal
/// when none could be).
Result treatAll(Sim sim, PlayerState p) {
  final sick = [
    for (final c in sim.herdOf(p.id))
      if (c.health == HealthStatus.sick && c.illness != null) c,
  ]..sort((a, b) => a.sickSince!.value - b.sickSince!.value);
  if (sick.isEmpty) return _no(sim, ErrorCode.notSick);
  final out = <DomainEvent>[];
  Err? refused;
  for (final c in sick) {
    final r = treatCamel(sim, p, c);
    out.addAll(r.events);
    if (r is Err) {
      refused = r;
      break;
    }
  }
  if (refused != null && !out.any((e) => e is Treated)) {
    return Err(refused.error, out);
  }
  return Ok(out);
}

/// What treating every sick camel would cost today (the vet's quotes).
int treatAllQuote(Sim sim, PlayerState p) => [
  for (final c in sim.herdOf(p.id))
    if (c.health == HealthStatus.sick && c.illness != null)
      handlers.vetQuote(sim, c).value,
].fold(0, (a, b) => a + b);

/// Whether [p] has a vet's contract in force today.
bool hasVet(PlayerState p) => p.farm.vet != null;

/// The ids [owner]'s camels sick and untreated.
Iterable<CamelId> sickUntreated(Sim sim, OwnerId owner) => [
  for (final c in sim.herdOf(owner))
    if (c.health == HealthStatus.sick) c.id,
];
