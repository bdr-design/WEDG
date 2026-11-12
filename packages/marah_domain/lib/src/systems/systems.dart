import '../catalog/catalog.dart';
import '../common/ids.dart';
import '../common/money.dart';
import '../common/rng.dart';
import '../events.dart';
import '../model/camel.dart';
import '../model/contest.dart';
import '../model/market.dart';
import '../model/player.dart';
import '../rules/balance.dart';
import '../rules/contest_rules.dart';
import '../rules/genetics.dart';
import '../rules/judging.dart';
import '../rules/names.dart';
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
  HealthSystem(),
  BreedingSystem(),
  MarketSystem(),
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
        (_, f) => f.done && sim.today.daysSince(f.judgedOn) > 400,
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
    final r = p.farm.region;
    return Riyal(
      (n.barley / Balance.barleyBagKg * Provisions.unitPrice(Supply.barley, r) +
              n.alfalfa /
                  Balance.alfalfaBaleKg *
                  Provisions.unitPrice(Supply.alfalfa, r))
          .round(),
    );
  }

  @override
  void run(Sim sim) {
    for (final p in sim.state.players.values) {
      _deliver(sim, p);
      _consume(sim, p);
      if (sim.today.date.day == 1) {
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

  static void _deliver(Sim sim, PlayerState p) {
    final f = p.farm;
    for (final d in f.deliveries.where((d) => d.arrivesOn <= sim.today)) {
      final amount = (d.units * Provisions.unitSize(d.supply)).toDouble();
      switch (d.supply) {
        case Supply.barley:
          f.barleyKg += amount;
        case Supply.alfalfa:
          f.alfalfaKg += amount;
        case Supply.water:
          f.waterL += amount;
      }
      sim.emit(
        SupplyDelivered(
          sim.today,
          owner: p.id,
          supply: d.supply,
          units: d.units,
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
      // what is left is drunk; under half the herd's water is a dry day
      final half = f.waterL >= n.water / 2;
      f
        ..waterL = 0
        ..dryDays = half ? 0 : f.dryDays + 1;
    }
  }
}

// ------------------------------------------------------------- care

/// Body condition drifts toward what the feed plan and care allow.
class CareSystem implements DailySystem {
  const CareSystem();

  static int shepherdsNeeded(int head) =>
      head == 0 ? 1 : (head / Balance.camelsPerShepherd).ceil();

  @override
  void run(Sim sim) {
    for (final p in sim.state.players.values) {
      final herd = sim.herdOf(p.id).toList();
      final needed = shepherdsNeeded(herd.length);
      final short = p.farm.shepherds < needed;
      final crowded = herd.length > p.farm.capacity;
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
        final pastThirst = p.farm.dryDays - Balance.thirstDays(sim.today.month);
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
      r.entries.removeWhere((e) => e.camelId == c.id);
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
      final value = Valuation.value(c, sim.today).value;
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

// ------------------------------------------------------------- contests

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
            judgedOn: f.judgedOn,
          ),
        );
      }
      if (f.closesOn.daysSince(sim.today) == 3) {
        sim.emit(
          RegistrationClosingSoon(sim.today, festival: f.id, name: f.name),
        );
      }
      if (sim.today >= f.judgedOn) _judge(sim, f);
    }
  }

  static void _judge(Sim sim, Festival f) {
    f.done = true;
    final w = sim.world;

    // Each player trucks their entries to the festival and back.
    final byOwner = <String, int>{};
    for (final r in f.rounds) {
      for (final e in r.entries) {
        byOwner[e.ownerId.value] = (byOwner[e.ownerId.value] ?? 0) + 1;
      }
    }
    for (final entry in byOwner.entries) {
      final p = sim.player(OwnerId(entry.key));
      if (p == null) continue;
      final km = p.farm.region.roadKmTo(f.region);
      sim.pay(
        p,
        Riyal(-Balance.transportCost(km, entry.value) * 2),
        LedgerCategory.transport,
        ref: f.id.value,
      );
    }

    final prizesByOwner = <String, int>{};
    for (final r in f.rounds) {
      if (r.entries.isEmpty) continue;
      final rng = sim.rng(['judge', f.id.value, r.id.value]);
      final prizes = ContestRules.prizes(f.tier, r.age);
      final rows = <_Scored>[];
      for (final e in r.entries) {
        final c = w.camels[e.camelId];
        if (c == null || !c.isAlive || c.ownerId != e.ownerId) continue;
        if (c.health == HealthStatus.sick) {
          sim.emit(
            DisqualifiedSick(
              sim.today,
              owner: c.ownerId,
              camel: c.id,
              name: c.name,
              festival: f.name,
            ),
          );
          continue;
        }
        final js = Judging.judge(
          rng,
          Judging.observedAll(c, sim.today),
          judges: Balance.judgesPerPanel,
        );
        rows.add(
          _Scored(js.total, c.name, c.ownerId.value, c.id.value, js.marks),
        );
      }
      final (mean, sd) = ContestRules.rivalQuality(f.tier);
      final gen = WorldGen(sim);
      for (var i = 0; i < r.rivals; i++) {
        final q = rng.normal(mean: mean, sd: sd);
        final observed = {
          for (final t in Trait.values)
            t: clampDouble(q + rng.normal(sd: 6), 0, 100),
        };
        final js = Judging.judge(rng, observed, judges: Balance.judgesPerPanel);
        final owner = gen.randomOwner(rng);
        rows.add(
          _Scored(
            js.total,
            randomCamelName(rng, female: r.sex == Sex.female),
            owner.id.value,
            null,
            null,
          ),
        );
      }
      rows.sort((a, b) => b.score.compareTo(a.score));

      final results = <ResultRow>[];
      for (var i = 0; i < rows.length; i++) {
        final row = rows[i];
        final rank = i + 1;
        final prize = rank <= prizes.length ? prizes[rank - 1] : 0;
        if (row.camelId != null || rank <= 10) {
          results.add(
            ResultRow(
              rank: rank,
              camelName: row.name,
              ownerId: OwnerId(row.owner),
              score: row.score,
              prize: prize,
              camelId: row.camelId == null ? null : CamelId(row.camelId!),
              marks: row.marks,
            ),
          );
        }
        if (row.camelId == null) continue;
        final c = w.camels[CamelId(row.camelId!)]!;
        final p = sim.player(c.ownerId);
        c.placings.add(
          Placing(
            festivalId: f.id,
            festivalName: f.name,
            roundId: r.id,
            rank: rank,
            of: rows.length,
            day: sim.today,
            tier: f.tier.level,
            prize: prize,
          ),
        );
        if (p != null && prize > 0) {
          sim.pay(p, Riyal(prize), LedgerCategory.prize, ref: f.id.value);
          prizesByOwner[p.id.value] = (prizesByOwner[p.id.value] ?? 0) + prize;
        }
        sim.emit(
          Placed(
            sim.today,
            owner: c.ownerId,
            camel: c.id,
            name: c.name,
            festival: f.name,
            round: r.id,
            rank: rank,
            of: rows.length,
            score: row.score,
            prize: prize,
          ),
        );
      }
      r.results = results;
    }
    // Only judged rounds are worth keeping in the record.
    f.rounds.removeWhere((r) => r.results == null);
    for (final e in prizesByOwner.entries) {
      sim.emit(
        FestivalSummary(
          sim.today,
          owner: OwnerId(e.key),
          festival: f.name,
          prizes: e.value,
        ),
      );
    }
  }
}

class _Scored {
  _Scored(this.score, this.name, this.owner, this.camelId, this.marks);
  final double score;
  final String name;
  final String owner;
  final String? camelId;
  final Map<Trait, double>? marks;
}
