import '../catalog/catalog.dart';
import '../common/ids.dart';
import '../common/money.dart';
import '../common/rng.dart';
import '../events.dart';
import '../model/camel.dart';
import '../model/contest.dart';
import '../model/game_state.dart';
import '../model/market.dart';
import '../model/player.dart';
import '../model/tampering.dart';
import '../rules/balance.dart';
import '../rules/contest_rules.dart';
import '../rules/genetics.dart';
import '../rules/judging.dart';
import '../rules/milk.dart';
import '../rules/names.dart';
import '../rules/pasture.dart';
import '../rules/provisions.dart';
import '../rules/valuation.dart';
import '../sim.dart';
import '../world_gen.dart';

/// One part of the daily simulation. Systems run in a fixed order each day
/// (see [dailyPipeline]); each draws randomness from its own keyed stream.
abstract interface class DailySystem {
  void run(Sim sim);
}

/// The order matters: the calendar first, money and care before health,
/// births before the market, contests last.
const List<DailySystem> dailyPipeline = [
  CalendarSystem(),
  UpkeepSystem(),
  CareSystem(),
  MilkSystem(),
  HealthSystem(),
  BreedingSystem(),
  MarketSystem(),
  TamperingSystem(),
  ContestSystem(),
];

// ------------------------------------------------------------- calendar

class CalendarSystem implements DailySystem {
  const CalendarSystem();

  @override
  void run(Sim sim) {
    final w = sim.world;
    if (sim.today >= w.plannedUntil - 60) {
      WorldGen(sim).planSeason(w.plannedUntil.year);
      w.festivals.removeWhere(
        (_, f) => f.done && sim.today.daysSince(f.endsOn) > 400,
      );
    }
  }
}

// ------------------------------------------------------------- upkeep

/// Feed is bought daily; shepherds are paid on the first of the month.
class UpkeepSystem implements DailySystem {
  const UpkeepSystem();

  /// What a day of the ration costs at today's prices (for the player's
  /// reckoning: feed is paid for when ordered).
  static Riyal dailyFeed(Sim sim, PlayerState p) {
    final n = Provisions.needs(sim.herdOf(p.id), p.farm.feedPlan, sim.today);
    return Riyal(Provisions.feedCost(n, p.farm.region).round());
  }

  @override
  void run(Sim sim) {
    for (final p in sim.state.players.values) {
      _finish(sim, p);
      _deliver(sim, p);
      _consume(sim, p);
      if (sim.today.date.day == 1 && p.farm.shepherds > 0) {
        final wages = Riyal(p.farm.shepherds * Balance.shepherdMonthlyWage);
        sim.bill(p, -wages, LedgerCategory.wages);
        sim.emit(
          WagesPaid(
            sim.today,
            owner: p.id,
            amount: wages.value,
            shepherds: p.farm.shepherds,
          ),
        );
        if (p.cash.isNegative) {
          sim.emit(CashNegative(sim.today, owner: p.id, cash: p.cash.value));
        }
      }
    }
  }

  /// The facilities done today stand on the farm from today.
  static void _finish(Sim sim, PlayerState p) {
    final f = p.farm;
    for (final b in f.building.where((b) => b.doneOn <= sim.today)) {
      f.built[b.facility] = f.has(b.facility) + 1;
      f
        ..capacity += b.facility.head
        ..tankL += b.facility.litres
        ..storeKg += b.facility.kg;
      sim.emit(FacilityBuilt(sim.today, owner: p.id, facility: b.facility));
    }
    f.building.removeWhere((b) => b.doneOn <= sim.today);
  }

  static void _deliver(Sim sim, PlayerState p) {
    final f = p.farm;
    for (final d in f.deliveries.where((d) => d.arrivesOn <= sim.today)) {
      final amount = (d.units * d.size).toDouble();
      var returned = 0;
      switch (d.supply) {
        case Supply.barley:
          f.barleyKg += amount;
        case Supply.alfalfa:
          f.alfalfaKg += amount;
        case Supply.water:
          // filled to the top; the rest goes back with the tanker
          final room = f.tankL - f.waterL;
          final kept = amount < room ? amount : (room > 0 ? room : 0.0);
          f.waterL += kept;
          returned = (amount - kept).round();
      }
      sim.emit(
        SupplyDelivered(
          sim.today,
          owner: p.id,
          supply: d.supply,
          units: d.units,
          size: d.size,
          returned: returned,
        ),
      );
    }
    f.deliveries.removeWhere((d) => d.arrivesOn <= sim.today);
  }

  /// The day's ration and water from the stores, as far as they go; a
  /// warning when a store is down to a few days, or out.
  static void _consume(Sim sim, PlayerState p) {
    final f = p.farm;
    final n = Provisions.needs(sim.herdOf(p.id), f.feedPlan, sim.today);
    // a warning when a store comes down to a few days
    void warn(Supply s, double before, double after, double need) {
      final b = Provisions.daysLeft(before, need),
          a = Provisions.daysLeft(after, need);
      if (b == null || a == null) return;
      if (a <= Balance.lowStockDays && a > 0 && b > Balance.lowStockDays) {
        sim.emit(SupplyLow(sim.today, owner: p.id, supply: s, days: a));
      }
    }

    // and when it goes short of the day's need, once until it covers it again
    // (a warning by the days left skipped it when the need jumped past a low
    // stock overnight: camels bought, a calving, the season's water)
    void cover(Supply s, bool enough) {
      if (enough) {
        f.short.remove(s);
      } else if (f.short.add(s)) {
        sim.emit(SupplyLow(sim.today, owner: p.id, supply: s, days: 0));
      }
    }

    final barley = n.barley < f.barleyKg ? n.barley : f.barleyKg;
    final alfalfa = n.alfalfa < f.alfalfaKg ? n.alfalfa : f.alfalfaKg;
    warn(Supply.barley, f.barleyKg, f.barleyKg - barley, n.barley);
    warn(Supply.alfalfa, f.alfalfaKg, f.alfalfaKg - alfalfa, n.alfalfa);
    cover(Supply.barley, barley >= n.barley);
    cover(Supply.alfalfa, alfalfa >= n.alfalfa);
    f
      ..barleyKg = q2(f.barleyKg - barley)
      ..alfalfaKg = q2(f.alfalfaKg - alfalfa);
    final need = n.barley + n.alfalfa;
    f.fedShare = need <= 0 ? 1 : q2((barley + alfalfa) / need);
    cover(Supply.water, f.waterL >= n.water);
    if (f.waterL >= n.water) {
      warn(Supply.water, f.waterL, f.waterL - n.water, n.water);
      f
        ..waterL = q2(f.waterL - n.water)
        ..dryDays = 0;
    } else {
      // what is left is drunk; under half the herd's water is a dry day, half
      // or more holds the count where it is (only a full day ends it: a 60%
      // day had set it back to nothing, the review)
      final half = f.waterL >= n.water / 2;
      f
        ..waterL = 0
        ..dryDays = half ? f.dryDays : f.dryDays + 1;
    }
  }
}

// ------------------------------------------------------------- care

/// Body condition drifts toward what the feed plan and care allow.
class CareSystem implements DailySystem {
  const CareSystem();

  /// The player tends a small herd himself (Balance.ownerTendsUpTo); past
  /// it, a shepherd for each 25 head.
  static int shepherdsNeeded(int head) => head <= Balance.ownerTendsUpTo
      ? 0
      : (head / Balance.camelsPerShepherd).ceil();

  @override
  void run(Sim sim) {
    for (final p in sim.state.players.values) {
      final herd = sim.herdOf(p.id).toList();
      final needed = shepherdsNeeded(herd.length);
      final short = p.farm.shepherds < needed;
      final crowded = herd.length > p.farm.capacity;
      final byId = {for (final c in herd) c.id: c};
      for (final c in herd) {
        // the ration's condition for the share of it the herd got (unfed, a
        // camel drifts to 35: balance), and lower again without water
        final fed = p.farm.fedShare;
        var target = 35 + (p.farm.feedPlan.conditionTarget - 35) * fed;
        if (p.farm.dryDays > 0) target -= Balance.thirstPenalty;
        if (short) {
          target -=
              Balance.understaffedPenalty *
              (needed - p.farm.shepherds) /
              needed;
        }
        if (crowded) target -= Balance.crowdedPenalty;
        if (c.health == HealthStatus.sick) target -= Balance.sickPenalty;
        if (c.health == HealthStatus.treated) target -= Balance.treatedPenalty;
        // a suckling calf by the milk its dam's milking leaves it, and one
        // without its dam (sold or dead) by none (the review: an orphan did
        // as well as a calf on half its dam's milk)
        final age = c.ageDays(sim.today);
        if (age < Balance.lactationDays) {
          final dam = c.dam == null ? null : byId[c.dam!.id];
          final suckles = dam != null && dam.lastCalvedOn == c.born;
          target += suckles
              ? Balance.calfMilkTarget(p.farm.calfShare, age)
              : Balance.orphanMilkTarget(age);
        }
        final preg = c.pregnancy;
        if (preg != null &&
            preg.confirmed &&
            preg.dueOn.daysSince(sim.today) < Balance.latePregnancyDays) {
          target -= Balance.latePregnancyPenalty;
        }
        c.condition = q2(
          clampDouble(
            c.condition + (target - c.condition) * Balance.conditionPull,
            5,
            98,
          ),
        );
      }
    }
    // Camels owned by the world's other owners keep a steady condition.
  }
}

// ------------------------------------------------------------- milk

/// The nursing camels are milked and what their calves do not keep is sold
/// to the buyer who comes each day (GDD 12.1; the owner, 13 Nov 2026).
class MilkSystem implements DailySystem {
  const MilkSystem();

  @override
  void run(Sim sim) {
    for (final p in sim.state.players.values) {
      var sold = 0.0;
      for (final m in Milk.today(sim.world, p.id, p.farm, sim.today)) {
        sold += m.sold;
      }
      final income = (sold * Balance.milkPrice).round();
      if (income > 0) sim.bill(p, Riyal(income), LedgerCategory.milk);
      p.farm
        ..milkIncome = income
        ..milkOn = sim.today;
    }
  }
}

// ------------------------------------------------------------- health

class HealthSystem implements DailySystem {
  const HealthSystem();

  /// Each illness's weight in [month]: three in its peak months (balance).
  static List<double> seasonWeights(List<Illness> options, int month) => [
    for (final i in options) i.peakMonths.contains(month) ? 3.0 : 1.0,
  ];

  /// How much likelier a camel that can have [options] falls ill in [month]
  /// than on average over the year: the illnesses' mean weight that month over
  /// its mean across the twelve, so the year's rate stays the balance's (about
  /// 0.5 illnesses a camel) and only moves into the winter and the summer
  /// (GDD 5.5).
  static double seasonFactor(List<Illness> options, int month) {
    double mean(int m) =>
        seasonWeights(options, m).fold(0.0, (a, b) => a + b) / options.length;
    var year = 0.0;
    for (var m = 1; m <= 12; m++) {
      year += mean(m);
    }
    return mean(month) / (year / 12);
  }

  static List<Illness> possibleIllnesses(Camel c, Sim sim) => _options(
    c.ageDays(sim.today) < 365,
    c.sex == Sex.female && c.calvings > 0,
  );

  static List<Illness> _options(bool young, bool mother) => [
    for (final i in Illness.values)
      if ((!i.youngOnly || young) && (!i.femaleOnly || mother)) i,
  ];

  @override
  void run(Sim sim) {
    for (final p in sim.state.players.values) {
      final herd = sim.herdOf(p.id).toList();
      final crowded = herd.length > p.farm.capacity;
      // the contagious illnesses going round the herd
      final going = {
        for (final c in herd)
          if (c.health == HealthStatus.sick && (c.illness?.contagious ?? false))
            c.illness!,
      }.toList()..sort((a, b) => a.index - b.index);
      final contagious = going.isNotEmpty;
      // the illnesses, their weights and the season's factor for each kind of
      // camel, worked out once a day (a camel's own lists cost 40% more a day
      // at 10,000 head, the review)
      final month = sim.today.month;
      final kinds = [
        for (var k = 0; k < 4; k++)
          () {
            final o = _options(k & 1 == 1, k & 2 == 2);
            return (o, seasonWeights(o, month), seasonFactor(o, month));
          }(),
      ];
      // the days the herd can go without water: looked up once, and only for
      // a farm that has gone without (worked out for every camel every day,
      // the pasture's random draw made a winter day at 10,000 head twice as
      // long, the review)
      int? limit;
      int thirstLimit() => Balance.thirstDays(
        month,
        green: Pasture.green(sim.world.seed, p.farm.region, sim.today),
      );
      for (final c in herd) {
        final rng = sim.rng(['health', c.id.value]);
        switch (c.health) {
          case HealthStatus.healthy:
            var chance = Balance.dailySickChance;
            if (c.condition < 50) chance *= Balance.sickChanceThinFactor;
            if (crowded) chance *= Balance.sickChanceCrowdedFactor;
            if (c.ageDays(sim.today) < 120) {
              chance *= Balance.sickChanceCalfFactor;
            }
            if (contagious) chance *= 2;
            // more often in the illnesses' peak months, as often over a year
            final (options, weights, season) =
                kinds[(c.ageDays(sim.today) < 365 ? 1 : 0) |
                    (c.sex == Sex.female && c.calvings > 0 ? 2 : 0)];
            chance *= season;
            if (rng.chance(chance)) {
              // one going round, that this camel can catch, half the time
              final catching = [
                for (final i in going)
                  if (options.contains(i)) i,
              ];
              final illness = (catching.isNotEmpty && rng.chance(0.5))
                  ? rng.pick(catching)
                  : rng.weighted(options, weights);
              c
                ..health = HealthStatus.sick
                ..illness = illness
                ..sickSince = sim.today;
              sim.emit(
                FellSick(
                  sim.today,
                  owner: p.id,
                  camel: c.id,
                  name: c.name,
                  illness: illness,
                ),
              );
            }
          case HealthStatus.sick:
            final days = sim.today.daysSince(c.sickSince!);
            if (days > Balance.untreatedGraceDays &&
                rng.chance(
                  Balance.untreatedDeathBase +
                      (days - Balance.untreatedGraceDays) *
                          Balance.untreatedDeathPerDay,
                )) {
              _die(sim, c, DeathCause.illness);
            } else if (days > Balance.selfRecoveryAfterDays &&
                rng.chance(Balance.selfRecoveryChance)) {
              _recover(sim, c);
            }
          case HealthStatus.treated:
            if (sim.today >= c.recoversOn!) _recover(sim, c);
        }
        if (!c.isAlive) continue;
        final pastThirst = p.farm.dryDays > 0
            ? p.farm.dryDays - (limit ??= thirstLimit())
            : 0;
        if (pastThirst > 0 &&
            rng.chance(Balance.thirstDeathPerDay * pastThirst)) {
          _die(sim, c, DeathCause.thirst);
          continue;
        }
        if (c.ageDays(sim.today) < 365 &&
            rng.chance(Balance.calfDailyDeath * (c.condition < 50 ? 2 : 1))) {
          _die(sim, c, DeathCause.young);
          continue;
        }
        final years = c.ageYears(sim.today);
        if (years >= Balance.maxAgeYears ||
            (years >= Balance.oldAgeFromYears &&
                rng.chance(
                  Balance.oldAgeDeathPerYear *
                      (years - Balance.oldAgeFromYears + 1),
                ))) {
          _die(sim, c, DeathCause.age);
        }
      }
    }
  }

  static void _recover(Sim sim, Camel c) {
    c
      ..health = HealthStatus.healthy
      ..illness = null
      ..sickSince = null
      ..recoversOn = null;
    sim.emit(Recovered(sim.today, owner: c.ownerId, camel: c.id, name: c.name));
  }

  static void _die(Sim sim, Camel c, DeathCause cause) {
    c
      ..status = CamelStatus.dead
      ..endedOn = sim.today
      ..pregnancy = null;
    releaseCamel(sim, c);
    sim.emit(
      Died(
        sim.today,
        owner: c.ownerId,
        camel: c.id,
        name: c.name,
        cause: cause,
        age: c.ageClass(sim.today),
      ),
    );
  }
}

/// Removes a camel that left its owner (died or was sold) from listings,
/// offers and contest entries.
void releaseCamel(Sim sim, Camel c) {
  final w = sim.world;
  final listings = w.listings.values
      .where((l) => l.camelId == c.id)
      .map((l) => l.id)
      .toSet();
  w.listings.removeWhere((id, _) => listings.contains(id));
  w.offers.removeWhere((_, o) => listings.contains(o.listingId));
  for (final f in w.festivals.values) {
    if (f.done) continue;
    for (final r in f.rounds) {
      if (r.judged) continue;
      for (final e in r.entries) {
        e.camels.remove(c.id);
      }
      r.entries.removeWhere((e) => e.camels.isEmpty);
    }
  }
}

// ------------------------------------------------------------- breeding

class BreedingSystem implements DailySystem {
  const BreedingSystem();

  @override
  void run(Sim sim) {
    for (final p in sim.state.players.values) {
      final births = <Camel>[];
      for (final f in sim.herdOf(p.id)) {
        final preg = f.pregnancy;
        if (preg == null) continue;
        if (!preg.confirmed && sim.today >= preg.checkOn) {
          if (preg.conceived) {
            preg.confirmed = true;
            sim.emit(
              PregnancyConfirmed(
                sim.today,
                owner: p.id,
                camel: f.id,
                name: f.name,
                sire: preg.sire.name,
                due: preg.dueOn,
              ),
            );
          } else {
            f.pregnancy = null;
            sim.emit(
              PregnancyFailed(
                sim.today,
                owner: p.id,
                camel: f.id,
                name: f.name,
                sire: preg.sire.name,
              ),
            );
          }
        } else if (preg.confirmed && sim.today >= preg.dueOn) {
          births.add(f);
        }
      }
      for (final dam in births) {
        _birth(sim, dam);
      }
    }
  }

  static void _birth(Sim sim, Camel dam) {
    final preg = dam.pregnancy!;
    final rng = sim.rng(['birth', dam.id.value]);
    dam
      ..pregnancy = null
      ..lastCalvedOn = sim.today
      ..calvings += 1;
    final lossChance =
        Balance.calfLossBase +
        (dam.condition < 50 ? Balance.calfLossThinDam : 0);
    if (rng.chance(lossChance)) {
      sim.emit(
        CalfLost(sim.today, owner: dam.ownerId, camel: dam.id, name: dam.name),
      );
      return;
    }
    final crossbred = preg.sire.category != dam.category || dam.crossbred;
    final sex = rng.chance(0.5) ? Sex.female : Sex.male;
    final calf = Camel(
      id: sim.world.ids.camel(),
      name: randomCamelName(rng, female: sex == Sex.female),
      sex: sex,
      category: Genetics.calfCategory(rng, preg.sire.category, dam.category),
      born: sim.today,
      ownerId: dam.ownerId,
      chip: randomChipNumber(rng),
      genes: Genetics.inherit(
        rng,
        preg.sireGenes,
        dam.genes,
        crossbred: crossbred,
      ),
      env: Genetics.randomEnv(rng),
      condition: q2(clampDouble(dam.condition - 5, 40, 90)),
      acquiredOn: sim.today,
      lastPlayerOwner: sim.isPlayer(dam.ownerId) ? dam.ownerId : null,
      sire: preg.sire,
      dam: dam.asParent,
      crossbred: crossbred,
    );
    sim.world.camels[calf.id] = calf;
    sim.emit(
      CalfBorn(
        sim.today,
        owner: dam.ownerId,
        camel: calf.id,
        dam: dam.name,
        sire: preg.sire.name,
        name: calf.name,
        sex: sex,
      ),
    );
  }
}

// ------------------------------------------------------------- market

class MarketSystem implements DailySystem {
  const MarketSystem();

  @override
  void run(Sim sim) {
    final w = sim.world;
    final gen = WorldGen(sim);

    // Expired listings: other owners take their camels home (out of the
    // world registry as "gone"); players are told.
    for (final l in w.listings.values.toList()) {
      if (l.expiresOn >= sim.today) continue;
      w.listings.remove(l.id);
      w.offers.removeWhere((_, o) => o.listingId == l.id);
      final c = w.camels[l.camelId];
      if (sim.isPlayer(l.sellerId)) {
        sim.emit(
          ListingExpired(
            sim.today,
            owner: l.sellerId,
            camel: l.camelId,
            name: c?.name ?? '',
          ),
        );
      } else if (c != null) {
        c
          ..status = CamelStatus.gone
          ..endedOn = sim.today;
      }
    }
    w.offers.removeWhere((_, o) => o.expiresOn < sim.today);

    // New camels come to market.
    final rng = sim.rng(['market']);
    final npc = w.listings.values
        .where((l) => !sim.isPlayer(l.sellerId))
        .length;
    final arrivals = npc < Balance.npcListingsTarget
        ? rng.range(1, 3)
        : rng.range(0, 1);
    for (var i = 0; i < arrivals; i++) {
      gen.addMarketListing(rng);
    }

    // Buyers bargain on players' listings.
    for (final l in w.listings.values.toList()) {
      if (!sim.isPlayer(l.sellerId)) continue;
      final c = w.camels[l.camelId];
      if (c == null || !c.isAlive) continue;
      final r = sim.rng(['buyers', l.id.value]);
      final value = offerValue(sim, l, c);
      final ratio = l.askPrice.value / (value <= 0 ? 1 : value);
      final p = clampDouble(
        Balance.buyerInterest / (ratio * ratio * ratio),
        0.01,
        0.6,
      );
      final open = w.offers.values.where((o) => o.listingId == l.id).length;
      if (open < Balance.maxOffersPerListing && r.chance(p)) {
        final buyer = gen.randomOwner(r);
        var amount = marketRound(value * r.rangeDouble(0.8, 1.04));
        if (amount > l.askPrice) amount = l.askPrice;
        final o = Offer(
          id: w.ids.offer(),
          listingId: l.id,
          buyerId: buyer.id,
          amount: amount,
          madeOn: sim.today,
          expiresOn: sim.today + Balance.offerValidDays,
        );
        w.offers[o.id] = o;
        sim.emit(
          OfferReceived(
            sim.today,
            owner: l.sellerId,
            camel: c.id,
            name: c.name,
            buyer: buyer.name,
            region: buyer.region,
            amount: amount.value,
            offer: o.id,
          ),
        );
      }
    }

    // Studs at service: fewer outside the breeding season.
    for (final s in w.studs.values.toList()) {
      if (s.until < sim.today) {
        w.studs.remove(s.id);
        w.camels[s.camelId]
          ?..status = CamelStatus.gone
          ..endedOn = sim.today;
      }
    }
    final want = Balance.breedingMonths.contains(sim.today.month)
        ? Balance.studsInSeason
        : Balance.studsOffSeason;
    final sr = sim.rng(['studs']);
    if (w.studs.length < want && sr.chance(0.3)) gen.addStud(sr);

    // Forget other owners' camels once they have left the world, unless a
    // player's camel descends from them. Players' own camels are kept.
    {
      final keep = <CamelId>{
        for (final x in w.camels.values)
          if (x.lastPlayerOwner != null) ...[
            ?x.sire?.id,
            ?x.dam?.id,
            ?x.pregnancy?.sire.id,
          ],
      };
      w.camels.removeWhere(
        (_, c) =>
            c.status != CamelStatus.alive &&
            c.lastPlayerOwner == null &&
            !sim.isPlayer(c.ownerId) &&
            !keep.contains(c.id),
      );
    }
  }
}

/// What buyers reckon a player's listed camel worth when they make their
/// offers: her value, moved by the seller's name in her family (GDD 8); a
/// declared treated camel at her natural look (the owner's decision 15).
int offerValue(Sim sim, Listing l, Camel c) =>
    (Valuation.value(c, sim.today, natural: l.declared).value *
            Balance.reputationPriceFactor(
              sim.player(l.sellerId)!.reputationIn(c.category),
            ))
        .round();

// ------------------------------------------------------------- cheating

/// A treatment can be found outside the festivals too, in the market or by
/// the vet (GDD 7.1): each day, for each treatment showing on a player's
/// camel (his own doing or not: it goes with the camel), a small chance
/// (Balance), more while the camel is listed for sale. Spent treatments
/// leave the camel.
class TamperingSystem implements DailySystem {
  const TamperingSystem();

  @override
  void run(Sim sim) {
    final w = sim.world;
    Set<CamelId>? listed;
    for (final c in w.camels.values) {
      if (c.treatments.isEmpty) continue;
      c.treatments.removeWhere((t) => sim.today > t.until);
      final p = sim.player(c.ownerId);
      if (p == null || !c.isAlive) continue;
      listed ??= {for (final l in w.listings.values) l.camelId};
      for (final t in [...c.treatments]) {
        if (sim
            .rng(['tamper-out', c.id.value, t.kind.name])
            .chance(outsideChance(t, listed: listed.contains(c.id)))) {
          foundOutside(sim, p, c, t);
        }
      }
    }
  }

  /// The day's chance [t] is found outside the festivals: more while the
  /// camel is listed for sale (buyers and their vets look closely).
  static double outsideChance(Tampering t, {required bool listed}) =>
      Balance.outsideCatchPerDay *
      t.strength *
      (listed ? Balance.outsideCatchListedFactor : 1);

  /// A treatment found outside a festival (the market, the vet): MEWA's
  /// fine on the camel's owner [p] (whoever had it done), the name lost in
  /// the family, the news; no festival ban (the festivals' committees did
  /// not find it).
  static int foundOutside(
    Sim sim,
    PlayerState p,
    Camel c,
    Tampering t, {
    bool atSale = false,
  }) {
    // the director's reading of the owner's decisions 7 and 12, awaiting
    // his confirmation: outside a festival the fine falls only on an owner
    // who had her treated or knew of it; one who did not is told (it joins
    // what he knows) and is not fined this time. Who treated her stays on
    // the treatment, so passing her on clears no one.
    final knew = t.by == p.id || t.knownBy.contains(p.id);
    // told on the sale's refusal at a sale; else it waits in the player's
    // untold findings till the phone tells it
    void untold(int fine) {
      if (!atSale) {
        p.untold.add(
          Finding(
            camel: c.id,
            name: c.name,
            kind: t.kind,
            fine: fine,
            knew: knew,
            day: sim.today,
          ),
        );
      }
    }

    if (!knew) {
      t.knownBy.add(p.id);
      untold(0);
      sim.emit(
        TamperingFound(
          sim.today,
          owner: p.id,
          camel: c.id,
          name: c.name,
          kind: t.kind,
          festival: null,
          stage: null,
          fine: 0,
          bannedThrough: null,
        ),
      );
      return 0;
    }
    c.treatments.remove(t);
    untold(Balance.outsideFine);
    sim.pay(
      p,
      const Riyal(-Balance.outsideFine),
      atSale ? LedgerCategory.fineAtSale : LedgerCategory.fine,
      ref: c.id.value,
    );
    lowerReputation(p, c.category, Balance.reputationCaughtOutside);
    sim
      ..emit(
        TamperingFound(
          sim.today,
          owner: p.id,
          camel: c.id,
          name: c.name,
          kind: t.kind,
          festival: null,
          stage: null,
          fine: Balance.outsideFine,
          bannedThrough: null,
        ),
      )
      ..emit(
        CheatNews(
          sim.today,
          ownerName: p.name,
          name: c.name,
          kind: t.kind,
          festival: null,
          fine: Balance.outsideFine,
        ),
      );
    return Balance.outsideFine;
  }
}

/// الصيت (GDD 8) moved by [by] in [family], kept within 0 to 100.
void raiseReputation(PlayerState p, ColorCategory family, double by) =>
    p.reputation[family] = clampDouble(p.reputationIn(family) + by, 0, 100);

void lowerReputation(PlayerState p, ColorCategory family, double by) =>
    raiseReputation(p, family, -by);

// ------------------------------------------------------------- contests

/// One entry on the festival day: a player's (its camels) or a rival's
/// (generated for the day).
class _Competitor {
  _Competitor({
    required this.owner,
    required this.name,
    this.entry,
    this.camels = const [],
    required this.head,
  });
  final OwnerId owner;
  final String name;
  final Entry? entry;
  final List<Camel> camels;
  final int head;
  double score = 0;
  Map<Trait, double>? marks;
  Stage? removedAt;
  RemovalReason? reason;

  /// The stage the clinical check's finding is told at (it looks at every
  /// entry before the preliminary judging).
  Stage? caughtAt;

  /// A rival's treatment, if it has one.
  TamperKind? kind;
  int strength = 0;

  bool get rival => entry == null;
  bool get inField => removedAt == null;
}

/// Festivals: registration news, each round on its day through the six
/// stages (GDD 7), the places announced (الفحل وإنتاجه's after the DNA
/// tests) and the festival closed with its integrity report.
class ContestSystem implements DailySystem {
  const ContestSystem();

  @override
  void run(Sim sim) {
    for (final f in sim.world.festivals.values) {
      if (f.done) continue;
      if (f.opensOn == sim.today) {
        sim.emit(
          RegistrationOpened(
            sim.today,
            festival: f.id,
            name: f.name,
            tier: f.tier,
            judgedOn: f.startsOn,
          ),
        );
      }
      if (f.closesOn.daysSince(sim.today) == 3) {
        sim.emit(
          RegistrationClosingSoon(sim.today, festival: f.id, name: f.name),
        );
      }
      for (final r in f.rounds) {
        if (!r.judged && r.day <= sim.today && r.entries.isNotEmpty) {
          _judge(sim, f, r);
        }
        // الفحل وإنتاجه's places, once its day is told and the DNA is back
        if (r.over &&
            !r.paid &&
            r.announceOn != null &&
            sim.today >= r.announceOn!) {
          _announce(sim, f, r);
        }
      }
      if (sim.today >= f.endsOn &&
          f.rounds.every((r) => r.judged ? r.paid : r.entries.isEmpty)) {
        _close(sim, f);
      }
    }
  }

  /// The camels [o] has entered at [f], judged rounds counted.
  static int entered(Festival f, OwnerId o) => {
    for (final r in f.rounds)
      for (final e in r.entries)
        if (e.ownerId == o) ...e.camels,
  }.length;

  /// What [p] pays to truck his camels entered at [f] there and back that
  /// are not there yet (Balance.transportCost, both ways); [more] counts
  /// camels about to be entered.
  static int festivalTrip(Festival f, PlayerState p, {int more = 0}) {
    final km = p.farm.region.roadKmTo(f.region);
    final there = f.trucked[p.id.value] ?? 0;
    final going = entered(f, p.id) + more - there;
    if (going <= 0) return 0;
    return Balance.transportCost(km, going) * 2;
  }

  static OwnerId _rivalOwner(WorldGen gen, Rng rng, Festival f) {
    final w = gen.sim.world;
    var o = gen.randomOwner(rng).id;
    for (var i = 0; i < 4 && (w.bans[o] ?? -1) >= f.season; i++) {
      o = gen.randomOwner(rng).id;
    }
    return o;
  }

  static void _judge(Sim sim, Festival f, ContestRound r) {
    final w = sim.world;
    final rng = sim.rng(['judge', f.id.value, r.id.value]);
    final comps = <_Competitor>[];
    for (final e in r.entries) {
      final camels = [
        for (final id in e.camels)
          if (w.camels[id] case final c?
              when c.isAlive && c.ownerId == e.ownerId)
            c,
      ];
      if (camels.isEmpty) continue;
      comps.add(
        _Competitor(
          owner: e.ownerId,
          name: camels.first.name,
          entry: e,
          camels: camels,
          head: camels.length,
        ),
      );
    }
    // each player's camels go to the festival together, on the day of
    // his first round there, stay for its days and come back (one trip,
    // paid whatever the result); one entered later goes on a trip of its own
    for (final o in {for (final c in comps) c.owner}) {
      final p = sim.player(o);
      if (p == null) continue;
      final extra = festivalTrip(f, p);
      f.trucked[o.value] = entered(f, o);
      sim.pay(p, Riyal(-extra), LedgerCategory.transport, ref: f.id.value);
    }
    final gen = WorldGen(sim);
    for (var i = 0; i < r.rivals; i++) {
      final c = _Competitor(
        owner: _rivalOwner(gen, rng, f),
        name: randomCamelName(rng, female: r.sex != Sex.male),
        head: r.size,
      );
      if (rng.chance(Balance.rivalTamperChance)) {
        c
          ..kind = rng.pick(TamperKind.values)
          ..strength = rng.range(1, 3);
      }
      comps.add(c);
    }

    final field = <int>[];
    void remove(_Competitor c, Stage s, RemovalReason why) {
      c
        ..removedAt = s
        ..reason = why;
    }

    Iterable<_Competitor> active() => comps.where((c) => c.inField);

    // 1. the chip and the witness
    for (final c in comps) {
      if (!c.rival && c.camels.length < r.size) {
        remove(c, Stage.chipWitness, RemovalReason.short);
      } else if (rng.chance(Balance.chipMismatchChance)) {
        remove(c, Stage.chipWitness, RemovalReason.chip);
      }
    }
    field.add(active().length);

    // 2. the colour's purity and the age by the teeth
    for (final c in active().toList()) {
      if (c.rival) {
        if (rng.chance(Balance.rivalBreedCheckChance)) {
          remove(
            c,
            Stage.breedColourAge,
            rng.chance(0.5) ? RemovalReason.colour : RemovalReason.teeth,
          );
        }
        continue;
      }
      for (final camel in c.camels) {
        if (Judging.observed(camel, Trait.coat, r.day, judges: true) <
            Balance.colourPurityMin) {
          remove(c, Stage.breedColourAge, RemovalReason.colour);
          break;
        }
        if (_teethMisread(rng, r, camel)) {
          remove(c, Stage.breedColourAge, RemovalReason.teeth);
          break;
        }
      }
    }
    field.add(active().length);

    // the clinical check of every camel that entered (the owner, 13 Nov
    // 2026; research section 3, [33]: every camel is examined), before the
    // preliminary judging decides who goes on; what it finds is announced
    // at the tampering experts' stage or the medical committee's, in the
    // day's order (GDD 7)
    for (final stage in [Stage.tamperingExperts, Stage.medical]) {
      for (final c in active().toList()) {
        if (!c.inField || c.caughtAt != null) continue;
        if (c.rival) {
          final kind = c.kind;
          if (kind != null &&
              rng.chance(ContestRules.detectChance(kind, c.strength, stage))) {
            c.caughtAt = stage;
            _rivalCaught(sim, f, r, c, kind, stage);
          }
          continue;
        }
        // the one who entered her answers for it (the owner, 13 Nov 2026:
        // the treatment goes with the camel, the buyer carries its risk)
        final p = sim.player(c.owner);
        if (p == null) continue;
        final found =
            [
                  for (final camel in c.camels)
                    for (final t in camel.treatments)
                      if (t.activeOn(r.day)) (camel, t),
                ]
                .where(
                  (x) => rng.chance(
                    ContestRules.detectChance(x.$2.kind, x.$2.strength, stage),
                  ),
                )
                .toList();
        // several kinds in her: each has its own check and its own fine
        // (the owner, 13 Nov 2026: the risk adds up); one found by the
        // tampering experts, the medical committee still looks for the rest
        if (found.isEmpty) continue;
        c.caughtAt = stage;
        final later = stage == Stage.tamperingExperts
            ? [
                for (final camel in c.camels)
                  for (final t in camel.treatments)
                    if (t.activeOn(r.day) && !found.any((x) => x.$2 == t))
                      if (rng.chance(
                        ContestRules.detectChance(
                          t.kind,
                          t.strength,
                          Stage.medical,
                        ),
                      ))
                        (camel, t),
              ]
            : const <(Camel, Tampering)>[];
        for (final (camel, t) in found) {
          _caught(f, r, p, camel, t, stage);
        }
        for (final (camel, t) in later) {
          _caught(f, r, p, camel, t, Stage.medical);
        }
      }
    }

    // 3. the preliminary judging keeps the best part of the field, on their
    // looks, every entry in it judged alike, those the check found among
    // them: the day's announcements keep the six stages' order (the owner, 13
    // Nov 2026), and the preliminary's list must not tell who was found (one
    // left off it for a finding would be told at the preliminary's hour). A
    // found entry on the list leaves at its finding's stage; one cut here is
    // cut, its finding still told at its stage with the fine and the ban
    final (mean, sd) = ContestRules.rivalQuality(f.tier);
    final judgedField = active().toList();
    for (final c in judgedField) {
      _score(sim, rng, r, c, mean, sd);
    }
    judgedField.sort((a, b) => b.score.compareTo(a.score));
    final keep = (judgedField.length * Balance.preliminaryKeeps).ceil();
    for (final c in judgedField.skip(
      keep < Balance.preliminaryKeepsAtLeast
          ? Balance.preliminaryKeepsAtLeast
          : keep,
    )) {
      remove(c, Stage.preliminary, RemovalReason.cut);
    }
    field.add(active().length);

    // 4 and 5. the tampering experts' and the medical committee's findings,
    // and the medical committee's look at each camel's health
    for (final stage in [Stage.tamperingExperts, Stage.medical]) {
      // an owner found at this stage (in the field or cut) is barred from
      // here: his other entries still in the round leave with it
      final barred = {
        for (final c in comps)
          if (!c.rival && c.caughtAt == stage) c.owner,
      };
      for (final c in active().toList()) {
        if (c.caughtAt == stage) {
          remove(c, stage, RemovalReason.tampering);
        } else if (!c.rival && barred.contains(c.owner)) {
          remove(c, stage, RemovalReason.banned);
        } else if (stage == Stage.medical &&
            c.caughtAt == null &&
            !c.rival &&
            c.camels.any((x) => x.health == HealthStatus.sick)) {
          remove(c, stage, RemovalReason.sick);
        }
      }
      field.add(active().length);
    }

    // 6. the final judging: the panel looks again
    final finalists = active().toList();
    for (final c in finalists) {
      c.score = clampDouble(
        c.score + rng.normal(sd: Balance.finalLookSd),
        0,
        100,
      );
    }
    finalists.sort((a, b) => b.score.compareTo(a.score));
    field.add(finalists.length);

    final prizes = ContestRules.prizes(f.tier, r.kind, r.size);
    final rows = <ResultRow>[];
    for (var i = 0; i < finalists.length; i++) {
      final c = finalists[i];
      if (c.rival && i >= 10) continue;
      rows.add(
        ResultRow(
          rank: i + 1,
          camelName: c.name,
          ownerId: c.owner,
          score: c.score,
          prize: i < prizes.length ? prizes[i] : 0,
          camelId: c.rival ? null : c.camels.first.id,
          marks: c.marks,
          head: c.head,
        ),
      );
    }
    for (final c in comps) {
      if (c.rival || c.inField) continue;
      final ids = {for (final x in c.camels) x.id};
      final found = [
        for (final x in r.found)
          if (x.camel != null && ids.contains(x.camel)) x,
      ];
      rows.add(
        ResultRow(
          rank: null,
          camelName: c.name,
          ownerId: c.owner,
          score: c.score,
          prize: 0,
          camelId: c.camels.first.id,
          marks: c.marks,
          removedAt: c.removedAt,
          reason: c.reason,
          head: c.head,
          foundAt: found.isEmpty ? null : found.first.stage,
          foundKind: found.isEmpty ? null : found.first.kind,
          fine: found.fold(0, (n, x) => n + x.fine),
        ),
      );
    }
    r
      ..results = rows
      ..field = field
      ..entrants = comps.length
      ..told = 0;
    if (r.kind == RoundKind.fahal) r.announceOn = r.day + Balance.dnaDays;
  }

  /// Tells the stages of today's rounds whose hour has come by [minute] of
  /// the day (Balance.stageMinutes; 1440 or more tells them all), and every
  /// stage left of a round of an earlier day.
  static void tellDay(Sim sim, int minute) {
    var due = 0;
    while (due < Balance.stageMinutes.length &&
        Balance.stageMinutes[due] <= minute) {
      due++;
    }
    for (final f in sim.world.festivals.values) {
      if (f.done) continue;
      for (final r in f.rounds) {
        if (!r.judged || r.over) continue;
        _tell(sim, f, r, r.day < sim.today ? Stage.values.length : due);
      }
    }
  }

  /// The minute of the day the next stage of a round judged today is told,
  /// or null when none is left today.
  static int? nextTelling(WorldState w) {
    int? next;
    for (final f in w.festivals.values) {
      if (f.done) continue;
      for (final r in f.rounds) {
        if (!r.judged || r.over || r.day != w.day) continue;
        final at = Balance.stageMinutes[r.told];
        if (next == null || at < next) next = at;
      }
    }
    return next;
  }

  /// Tells [r]'s stages up to [upTo] (Stage.index, exclusive), each with
  /// what it decided: the entries it removed, the treatments found (for a
  /// player the fine, the ban and the name lost; for a rival the news), and
  /// at the final judging the places (الفحل وإنتاجه's wait for the DNA).
  static void _tell(Sim sim, Festival f, ContestRound r, int upTo) {
    while (r.told < upTo && r.told < Stage.values.length) {
      final stage = Stage.values[r.told];
      for (final c in [...r.found]) {
        if (c.stage != stage) continue;
        r.found.remove(c);
        final p = sim.player(c.owner);
        if (p != null) {
          _caughtTold(sim, f, r, p, c);
        } else {
          sim.emit(
            CheatNews(
              sim.today,
              ownerName: sim.world.owners[c.owner]?.name ?? '',
              name: c.name,
              kind: c.kind,
              festival: f.name,
              fine: c.fine,
            ),
          );
        }
      }
      for (final row in r.results!) {
        if (row.removedAt != stage || !sim.isPlayer(row.ownerId)) continue;
        sim.emit(
          EntryRemoved(
            sim.today,
            owner: row.ownerId,
            camel: row.camelId,
            name: row.camelName,
            festival: f.name,
            round: r.id,
            stage: stage,
            reason: row.reason!,
          ),
        );
      }
      r.told++;
      if (stage != Stage.finalJudging) continue;
      if (r.announceOn == null) {
        _announce(sim, f, r);
        continue;
      }
      for (final o in {
        for (final row in r.results!)
          if (row.rank != null && sim.isPlayer(row.ownerId)) row.ownerId,
      }) {
        sim.emit(
          ResultsPending(
            sim.today,
            owner: o,
            festival: f.name,
            round: r.id,
            announceOn: r.announceOn!,
          ),
        );
      }
    }
  }

  /// The age by the teeth (stage 2): a camel within
  /// [Balance.teethMarginDays] of its class's edge may be read as the class
  /// beside it; removed if that class does not fit the round.
  static bool _teethMisread(Rng rng, ContestRound r, Camel camel) {
    final banded =
        r.legacyAge != null ||
        r.kind == RoundKind.mafareed ||
        r.kind == RoundKind.diq ||
        r.kind == RoundKind.fardiDiq;
    if (!banded) return false;
    final days = r.day.daysSince(camel.born);
    final age = AgeClass.fromDays(days);
    final i = age.index;
    AgeClass? read;
    if (i > 0 && days - age.minDays < Balance.teethMarginDays) {
      read = AgeClass.values[i - 1];
    } else if (i + 1 < AgeClass.values.length &&
        AgeClass.values[i + 1].minDays - days <= Balance.teethMarginDays) {
      read = AgeClass.values[i + 1];
    }
    if (read == null || !rng.chance(Balance.teethMisreadChance)) return false;
    final legacy = r.legacyAge;
    final fits = legacy != null
        ? read == legacy ||
              (legacy == AgeClass.fater && read.index > legacy.index)
        : ContestRules.ageFits(r.kind, read, read.minDays);
    return !fits;
  }

  /// The panel's mark (0 to 100) for [c].
  static void _score(
    Sim sim,
    Rng rng,
    ContestRound r,
    _Competitor c,
    double mean,
    double sd,
  ) {
    if (c.rival) {
      if (!r.kind.beauty) {
        c.score = clampDouble(rng.normal(mean: 55, sd: 8), 0, 100);
        return;
      }
      if (r.size == 1) {
        final q = rng.normal(mean: mean, sd: sd);
        final observed = {
          for (final t in Trait.values)
            t: clampDouble(q + rng.normal(sd: 6), 0, 100),
        };
        c.score = Judging.judge(
          rng,
          observed,
          judges: Balance.judgesPerPanel,
        ).total;
      } else {
        c.score = clampDouble(rng.normal(mean: mean, sd: sd * 0.5), 0, 100);
      }
      final kind = c.kind;
      if (kind != null) {
        c.score = clampDouble(
          c.score + Balance.tamperLift(kind, c.strength),
          0,
          100,
        );
      }
      return;
    }
    final judged = [
      for (final camel in c.camels)
        Judging.judge(
          rng,
          Judging.observedAll(camel, r.day, judges: true),
          judges: Balance.judgesPerPanel,
        ),
    ];
    if (r.kind == RoundKind.fahal && judged.length > 1) {
      final kids =
          judged.skip(1).fold(0.0, (s, j) => s + j.total) / (judged.length - 1);
      c.score =
          ContestRules.fahalBullShare * judged.first.total +
          (1 - ContestRules.fahalBullShare) * kids;
    } else {
      c.score = judged.fold(0.0, (s, j) => s + j.total) / judged.length;
    }
    if (judged.length == 1) c.marks = judged.first.marks;
  }

  /// A player's treatment found at a festival (GDD 7.1), on the day:
  /// counted in the round's cases and kept to be told at [stage]; the entry
  /// leaves at that stage if the preliminary kept it, and what follows (the
  /// fine, the ban, the news) waits for the stage to be told ([_caughtTold]).
  static void _caught(
    Festival f,
    ContestRound r,
    PlayerState p,
    Camel camel,
    Tampering t,
    Stage stage,
  ) {
    final fine = Balance.tamperFine(t.kind, t.strength);
    r
      ..caught += 1
      ..fines += fine
      ..found.add(
        Caught(
          stage: stage,
          owner: p.id,
          name: camel.name,
          kind: t.kind,
          strength: t.strength,
          fine: fine,
          camel: camel.id,
        ),
      );
  }

  /// A player's treatment found at a festival, told at its stage: the fine
  /// (the cap, scaled by the treatment's strength), the owner and his camels
  /// barred from this edition and five more, every festival (the owner, 13
  /// Nov 2026), his entries elsewhere withdrawn (a round of the same day
  /// already judged loses his places from the stage it has come to), the
  /// name lost in the family, and the news. The treatment leaves her.
  static void _caughtTold(
    Sim sim,
    Festival f,
    ContestRound r,
    PlayerState p,
    Caught found,
  ) {
    final w = sim.world;
    final camel = found.camel == null ? null : w.camels[found.camel!];
    if (camel != null) {
      final t = camel.treatments
          .where((x) => x.kind == found.kind && x.strength == found.strength)
          .firstOrNull;
      if (t != null) camel.treatments.remove(t);
    }
    final through = f.season + Balance.banEditionsAfter;
    sim.pay(p, Riyal(-found.fine), LedgerCategory.fine, ref: f.id.value);
    if ((w.bans[p.id] ?? -1) < through) w.bans[p.id] = through;
    for (final c in w.aliveOwnedBy(p.id)) {
      if ((c.bannedThrough ?? -1) < through) c.bannedThrough = through;
    }
    for (final x in w.festivals.values) {
      if (x.done || x.season > through) continue;
      for (final y in x.rounds) {
        if (y == r) continue;
        if (!y.judged) {
          y.entries.removeWhere((e) => e.ownerId == p.id);
        } else if (!y.over) {
          _barFrom(x, y, p.id);
        }
      }
    }
    lowerReputation(
      p,
      camel?.category ?? r.category ?? ColorCategory.majaheem,
      Balance.reputationCaught,
    );
    sim
      ..emit(
        TamperingFound(
          sim.today,
          owner: p.id,
          camel: found.camel,
          name: found.name,
          kind: found.kind,
          festival: f.name,
          stage: found.stage,
          fine: found.fine,
          bannedThrough: through,
        ),
      )
      ..emit(
        CheatNews(
          sim.today,
          ownerName: p.name,
          name: found.name,
          kind: found.kind,
          festival: f.name,
          fine: found.fine,
        ),
      );
  }

  /// [owner] barred while [r] (judged, its day being told) is under way: his
  /// entries still in its field leave at the stage it has come to, the
  /// places after them move up and the field counts from that stage on
  /// drop by as many.
  static void _barFrom(Festival f, ContestRound r, OwnerId owner) {
    final stage = Stage.values[r.told];
    final rows = r.results!;
    var out = 0;
    for (var i = 0; i < rows.length; i++) {
      final row = rows[i];
      if (row.ownerId != owner || row.removedAt != null) continue;
      out++;
      rows[i] = ResultRow(
        rank: null,
        camelName: row.camelName,
        ownerId: row.ownerId,
        score: row.score,
        prize: 0,
        camelId: row.camelId,
        marks: row.marks,
        removedAt: stage,
        reason: RemovalReason.banned,
        head: row.head,
      );
    }
    if (out == 0) return;
    final prizes = ContestRules.prizes(f.tier, r.kind, r.size);
    final placed = [
      for (var i = 0; i < rows.length; i++)
        if (rows[i].rank != null) i,
    ]..sort((a, b) => rows[a].rank!.compareTo(rows[b].rank!));
    for (var k = 0; k < placed.length; k++) {
      final row = rows[placed[k]];
      rows[placed[k]] = ResultRow(
        rank: k + 1,
        camelName: row.camelName,
        ownerId: row.ownerId,
        score: row.score,
        prize: k < prizes.length ? prizes[k] : 0,
        camelId: row.camelId,
        marks: row.marks,
        head: row.head,
      );
    }
    final field = r.field!;
    for (var i = r.told; i < field.length; i++) {
      field[i] = field[i] > out ? field[i] - out : 0;
    }
  }

  /// A rival caught in a round the player is in, on the day: barred, and in
  /// the news when the stage is told.
  static void _rivalCaught(
    Sim sim,
    Festival f,
    ContestRound r,
    _Competitor c,
    TamperKind kind,
    Stage stage,
  ) {
    final w = sim.world;
    final fine = Balance.tamperFine(kind, c.strength);
    final through = f.season + Balance.banEditionsAfter;
    r
      ..caught += 1
      ..fines += fine
      ..found.add(
        Caught(
          stage: stage,
          owner: c.owner,
          name: c.name,
          kind: kind,
          strength: c.strength,
          fine: fine,
        ),
      );
    if ((w.bans[c.owner] ?? -1) < through) w.bans[c.owner] = through;
  }

  /// The places announced and paid; each placing on the camel's record and
  /// the owner's name (الصيت) in its family raised.
  static void _announce(Sim sim, Festival f, ContestRound r) {
    r.paid = true;
    final w = sim.world;
    final of = r.entrants;
    for (final row in r.results!) {
      final rank = row.rank;
      final id = row.camelId;
      if (rank == null || id == null) continue;
      final c = w.camels[id];
      final p = sim.player(row.ownerId);
      c?.placings.add(
        Placing(
          festivalId: f.id,
          festivalName: f.name,
          roundId: r.id,
          rank: rank,
          of: of,
          day: sim.today,
          tier: f.tier.level,
          prize: row.prize,
        ),
      );
      if (p == null) continue;
      if (row.prize > 0) {
        sim.pay(p, Riyal(row.prize), LedgerCategory.prize, ref: f.id.value);
      }
      if (rank <= 10) {
        final by = rank == 1
            ? Balance.reputationForFirst
            : rank <= 3
            ? Balance.reputationForPodium
            : Balance.reputationForTopTen;
        raiseReputation(
          p,
          r.category ?? c?.category ?? ColorCategory.majaheem,
          by * f.tier.level,
        );
      }
      sim.emit(
        Placed(
          sim.today,
          owner: row.ownerId,
          camel: id,
          name: row.camelName,
          festival: f.name,
          round: r.id,
          rank: rank,
          of: of,
          score: row.score,
          prize: row.prize,
        ),
      );
    }
  }

  /// The festival over: the rounds no player entered are run as rivals'
  /// rounds for their committees' count of treatments found; the group
  /// rounds keep their top three (rivals run them, the owner's decision of 13
  /// Nov 2026), the single ones are dropped; the integrity report and each
  /// player's prizes in the news.
  static void _close(Sim sim, Festival f) {
    f.done = true;
    final w = sim.world;
    final rng = sim.rng(['integrity', f.id.value]);
    var cases = 0, fines = 0;
    for (final r in f.rounds) {
      if (r.judged) {
        cases += r.caught;
        fines += r.fines;
        continue;
      }
      for (var i = 0; i < r.rivals; i++) {
        if (!rng.chance(Balance.rivalTamperChance)) continue;
        final kind = rng.pick(TamperKind.values);
        final strength = rng.range(1, 3);
        if (rng.chance(ContestRules.festivalCatchChance(kind, strength))) {
          cases++;
          fines += Balance.tamperFine(kind, strength);
        }
      }
    }
    // the group rounds, run by the rivals only (the owner, 13 Nov 2026):
    // their top three kept for the festival's page
    final gen = WorldGen(sim);
    final (mean, sd) = ContestRules.rivalQuality(f.tier);
    for (final r in f.rounds) {
      if (r.judged || r.kind.enterable) continue;
      final prizes = ContestRules.prizes(f.tier, r.kind, r.size);
      final scores = [
        for (var i = 0; i < 3; i++)
          q2(clampDouble(rng.normal(mean: mean, sd: sd * 0.5), 0, 100)),
      ]..sort((a, b) => b.compareTo(a));
      r
        ..results = [
          for (var i = 0; i < 3; i++)
            () {
              final o = _rivalOwner(gen, rng, f);
              return ResultRow(
                rank: i + 1,
                camelName: w.owners[o]?.name ?? '',
                ownerId: o,
                score: scores[i],
                prize: prizes[i],
                head: r.size,
              );
            }(),
        ]
        ..told = Stage.values.length
        ..paid = true;
    }
    f.rounds.removeWhere((r) => !r.judged);
    sim.emit(
      FestivalIntegrity(
        sim.today,
        festival: f.name,
        cases: cases,
        fines: fines,
      ),
    );
    final prizes = <OwnerId, int>{};
    for (final r in f.rounds) {
      for (final row in r.results!) {
        if (row.prize > 0 && sim.isPlayer(row.ownerId)) {
          prizes[row.ownerId] = (prizes[row.ownerId] ?? 0) + row.prize;
        }
      }
    }
    for (final MapEntry(key: o, value: n) in prizes.entries) {
      sim.emit(
        FestivalSummary(sim.today, owner: o, festival: f.name, prizes: n),
      );
    }
  }
}
