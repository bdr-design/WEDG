import 'dart:math' as math;

import '../commands.dart';
import '../common/ids.dart';
import '../common/money.dart';
import '../common/result.dart';
import '../common/rng.dart';
import '../events.dart';
import '../model/camel.dart';
import '../model/contest.dart';
import '../model/market.dart';
import '../model/player.dart';
import '../rules/balance.dart';
import '../rules/eligibility.dart';
import '../rules/provisions.dart';
import '../rules/valuation.dart';
import '../sim.dart';
import '../systems/systems.dart';
import '../world_gen.dart';

/// Applies one command. Validation and effects live together per command;
/// nothing outside this file changes state on a player's behalf.
Result handle(Sim sim, Command cmd) {
  final p = sim.player(cmd.actor);
  if (p == null) return const Err(DomainError(ErrorCode.notFound));
  return switch (cmd) {
    BuyListing() => _buy(sim, p, cmd),
    Bargain() => _bargain(sim, p, cmd),
    ListForSale() => _list(sim, p, cmd),
    CancelListing() => _cancel(sim, p, cmd),
    AcceptOffer() => _accept(sim, p, cmd),
    DeclineOffer() => _decline(sim, p, cmd),
    QuickSale() => _quickSale(sim, p, cmd),
    MateWithOwnBull() => _mateOwn(sim, p, cmd),
    MateWithStud() => _mateStud(sim, p, cmd),
    Treat() => _treat(sim, p, cmd),
    RenameCamel() => _rename(sim, p, cmd),
    SetFeedPlan() => _feedPlan(sim, p, cmd),
    OrderSupply() => _order(sim, p, cmd),
    SetShepherds() => _shepherds(sim, p, cmd),
    ExpandFarm() => _expand(sim, p),
    EnterRound() => _enter(sim, p, cmd),
    WithdrawEntry() => _withdraw(sim, p, cmd),
  };
}

Ok _ok(Sim sim) => Ok(sim.drain());
Err _err(Sim sim, ErrorCode code, [Map<String, Object> params = const {}]) =>
    Err(DomainError(code, params), sim.drain());

// ================================================================= market

/// Price to truck one camel from [from] to the player's farm.
int transportToFarm(PlayerState p, Listing l) =>
    Balance.transportCost(l.region.roadKmTo(p.farm.region), 1);

Result _buy(Sim sim, PlayerState p, BuyListing cmd) {
  final l = sim.world.listings[cmd.listing];
  if (l == null) return _err(sim, ErrorCode.notFound);
  return _buyAt(sim, p, l, l.askPrice);
}

Result _buyAt(Sim sim, PlayerState p, Listing l, Riyal price) {
  if (l.sellerId == p.id) return _err(sim, ErrorCode.ownListing);
  final c = sim.world.camels[l.camelId];
  if (c == null || !c.isAlive) return _err(sim, ErrorCode.notFound);
  final move = Riyal(transportToFarm(p, l));
  if (p.cash < price + move) {
    return _err(sim, ErrorCode.insufficientFunds, {
      'needed': (price + move).value,
    });
  }
  if (sim.herdOf(p.id).length >= p.farm.capacity) {
    return _err(sim, ErrorCode.farmFull);
  }
  final seller = sim.player(l.sellerId);
  if (seller != null) {
    _payout(sim, seller, c, price);
  }
  sim.pay(p, -price, LedgerCategory.purchase, ref: c.id.value);
  sim.pay(p, -move, LedgerCategory.transport, ref: c.id.value);
  sim.world.listings.remove(l.id);
  sim.world.offers.removeWhere((_, o) => o.listingId == l.id);
  c
    ..ownerId = p.id
    ..lastPlayerOwner = p.id
    ..acquiredOn = sim.today
    ..purchasePrice = price.value;
  final sellerName = sim.world.owners[l.sellerId]?.name ?? seller?.name ?? '';
  sim.emit(
    CamelBought(
      sim.today,
      owner: p.id,
      camel: c.id,
      name: c.name,
      price: price.value,
      seller: sellerName,
      region: l.region,
    ),
  );
  return _ok(sim);
}

/// Pays a selling player (price minus the broker's commission).
void _payout(Sim sim, PlayerState seller, Camel c, Riyal price) {
  sim.pay(seller, price, LedgerCategory.sale, ref: c.id.value);
  sim.pay(
    seller,
    -price.times(Balance.brokerCommission),
    LedgerCategory.commission,
    ref: c.id.value,
  );
}

Result _bargain(Sim sim, PlayerState p, Bargain cmd) {
  final l = sim.world.listings[cmd.listing];
  if (l == null) return _err(sim, ErrorCode.notFound);
  if (l.sellerId == p.id) return _err(sim, ErrorCode.ownListing);
  if (cmd.amount <= 0) return _err(sim, ErrorCode.invalidAmount);
  final tries = l.bargains[p.id.value] ?? 0;
  if (tries >= Balance.maxBargainsPerBuyer) {
    return _err(sim, ErrorCode.sellerRefusesBargaining);
  }
  final offer = Riyal(cmd.amount);
  if (offer >= l.askPrice) return _buyAt(sim, p, l, l.askPrice);
  if (offer >= l.reservePrice) {
    final r = _buyAt(sim, p, l, offer);
    return r; // a failed purchase does not use up an attempt
  }
  l.bargains[p.id.value] = tries + 1;
  if (offer.value >= l.reservePrice.value * Balance.counterOfferFloor) {
    final counter = marketRound((offer.value + l.askPrice.value) / 2);
    l.askPrice = Riyal(
      math.min(l.askPrice.value, math.max(l.reservePrice.value, counter.value)),
    );
    sim.emit(
      BargainCountered(
        sim.today,
        owner: p.id,
        camel: l.camelId,
        listing: l.id,
        ask: l.askPrice.value,
      ),
    );
    return _err(sim, ErrorCode.bargainCountered, {'ask': l.askPrice.value});
  }
  sim.emit(
    BargainRejected(sim.today, owner: p.id, camel: l.camelId, listing: l.id),
  );
  return _err(sim, ErrorCode.bargainRejected);
}

Result _list(Sim sim, PlayerState p, ListForSale cmd) {
  final c = sim.world.camels[cmd.camel];
  final problem = Eligibility.canSell(sim.world, c, p.id);
  if (problem != null) return Err(problem, sim.drain());
  if (cmd.askPrice < 1000) return _err(sim, ErrorCode.invalidAmount);
  final l = Listing(
    id: sim.world.ids.listing(),
    camelId: c!.id,
    sellerId: p.id,
    region: p.farm.region,
    askPrice: Riyal(cmd.askPrice),
    reservePrice: Riyal(cmd.askPrice),
    listedOn: sim.today,
    expiresOn: sim.today + Balance.playerListingDays,
  );
  sim.world.listings[l.id] = l;
  sim.emit(
    ListingCreated(
      sim.today,
      owner: p.id,
      camel: c.id,
      name: c.name,
      ask: cmd.askPrice,
      listing: l.id,
    ),
  );
  return _ok(sim);
}

Result _cancel(Sim sim, PlayerState p, CancelListing cmd) {
  final l = sim.world.listings[cmd.listing];
  if (l == null) return _err(sim, ErrorCode.notFound);
  if (l.sellerId != p.id) return _err(sim, ErrorCode.notYourListing);
  sim.world.listings.remove(l.id);
  sim.world.offers.removeWhere((_, o) => o.listingId == l.id);
  sim.emit(ListingCancelled(sim.today, owner: p.id, camel: l.camelId));
  return _ok(sim);
}

Result _accept(Sim sim, PlayerState p, AcceptOffer cmd) {
  final o = sim.world.offers[cmd.offer];
  if (o == null) return _err(sim, ErrorCode.notFound);
  final l = sim.world.listings[o.listingId];
  if (l == null) return _err(sim, ErrorCode.notFound);
  if (l.sellerId != p.id) return _err(sim, ErrorCode.notYourListing);
  final c = sim.world.camels[l.camelId]!;
  final buyer = sim.world.owners[o.buyerId];
  _sellTo(sim, p, c, o.amount, o.buyerId, buyer?.name ?? '');
  return _ok(sim);
}

Result _decline(Sim sim, PlayerState p, DeclineOffer cmd) {
  final o = sim.world.offers[cmd.offer];
  if (o == null) return _err(sim, ErrorCode.notFound);
  final l = sim.world.listings[o.listingId];
  if (l == null || l.sellerId != p.id) {
    return _err(sim, ErrorCode.notYourListing);
  }
  sim.world.offers.remove(o.id);
  sim.emit(OfferDeclined(sim.today, owner: p.id, camel: l.camelId));
  return _ok(sim);
}

Riyal quickSalePrice(Camel c, Sim sim) =>
    marketRound(Valuation.value(c, sim.today).value * Balance.quickSaleFactor);

Result _quickSale(Sim sim, PlayerState p, QuickSale cmd) {
  final c = sim.world.camels[cmd.camel];
  final problem = Eligibility.canSell(sim.world, c, p.id);
  if (problem != null) return Err(problem, sim.drain());
  final rng = sim.rng(['broker', c!.id.value]);
  final broker = WorldGen(sim).randomOwner(rng, region: p.farm.region);
  _sellTo(sim, p, c, quickSalePrice(c, sim), broker.id, broker.name);
  return _ok(sim);
}

void _sellTo(
  Sim sim,
  PlayerState seller,
  Camel c,
  Riyal price,
  OwnerId buyerId,
  String buyerName,
) {
  _payout(sim, seller, c, price);
  releaseCamel(sim, c);
  final profit =
      price.value -
      (price.value * Balance.brokerCommission).round() -
      c.purchasePrice;
  c
    ..ownerId = buyerId
    ..acquiredOn = sim.today
    ..purchasePrice = price.value
    ..status = CamelStatus.gone
    ..endedOn = sim.today;
  sim.emit(
    CamelSold(
      sim.today,
      owner: seller.id,
      camel: c.id,
      name: c.name,
      price: price.value,
      buyer: buyerName,
      profit: profit,
    ),
  );
}

// ================================================================ breeding

Result _mateOwn(Sim sim, PlayerState p, MateWithOwnBull cmd) {
  final bull = sim.world.camels[cmd.bull];
  final own = Eligibility.owned(bull, p.id);
  if (own != null) return Err(own, sim.drain());
  return _mate(sim, p, cmd.female, bull!, fee: Riyal.zero, move: Riyal.zero);
}

Result _mateStud(Sim sim, PlayerState p, MateWithStud cmd) {
  final s = sim.world.studs[cmd.stud];
  if (s == null || s.until < sim.today) {
    return _err(sim, ErrorCode.studUnavailable);
  }
  final bull = sim.world.camels[s.camelId];
  if (bull == null || !bull.isAlive || bull.ownerId != s.ownerId) {
    return _err(sim, ErrorCode.studUnavailable);
  }
  final km = p.farm.region.roadKmTo(s.region);
  return _mate(
    sim,
    p,
    cmd.female,
    bull,
    fee: s.fee,
    move: Riyal(Balance.transportCost(km, 1)),
  );
}

Result _mate(
  Sim sim,
  PlayerState p,
  CamelId femaleId,
  Camel bull, {
  required Riyal fee,
  required Riyal move,
}) {
  final f = sim.world.camels[femaleId];
  final own = Eligibility.owned(f, p.id);
  if (own != null) return Err(own, sim.drain());
  final female = f!;
  final fp = Eligibility.femaleCanBreed(female, sim.today);
  if (fp != null) return Err(fp, sim.drain());
  final bp = Eligibility.bullCanServe(bull, sim.today);
  if (bp != null) return Err(bp, sim.drain());
  if (p.cash < fee + move) {
    return _err(sim, ErrorCode.insufficientFunds, {
      'needed': (fee + move).value,
    });
  }
  sim.pay(p, -fee, LedgerCategory.studFee, ref: bull.id.value);
  sim.pay(p, -move, LedgerCategory.transport, ref: female.id.value);

  final rng = sim.rng(['mate', female.id.value]);
  var chance = Balance.conceptionRate;
  if (female.condition < 55) chance -= 0.15;
  if (female.condition > 80) chance += 0.05;
  if (female.ageYears(sim.today) > 16) chance -= 0.15;
  female.pregnancy = Pregnancy(
    sire: bull.asParent,
    sireGenes: Map.of(bull.genes),
    matedOn: sim.today,
    checkOn: sim.today + Balance.pregnancyCheckDays,
    dueOn: sim.today + _gestation(rng),
    conceived: rng.chance(chance),
  );
  bull.lastServiceOn = sim.today;
  sim.emit(
    Mated(
      sim.today,
      owner: p.id,
      camel: female.id,
      name: female.name,
      sire: bull.name,
      checkOn: (sim.today + Balance.pregnancyCheckDays),
      fee: fee.value,
    ),
  );
  return _ok(sim);
}

// ==================================================================== farm

Result _treat(Sim sim, PlayerState p, Treat cmd) {
  final c = sim.world.camels[cmd.camel];
  final own = Eligibility.owned(c, p.id);
  if (own != null) return Err(own, sim.drain());
  final camel = c!;
  final illness = camel.illness;
  if (camel.health != HealthStatus.sick || illness == null) {
    return _err(sim, ErrorCode.notSick);
  }
  final rng = sim.rng(['vet', camel.id.value]);
  final cost = marketRound(
    rng.range(illness.treatMin, illness.treatMax).toDouble(),
  );
  if (p.cash < cost) {
    return _err(sim, ErrorCode.insufficientFunds, {'needed': cost.value});
  }
  sim.pay(p, -cost, LedgerCategory.vet, ref: camel.id.value);
  camel
    ..health = HealthStatus.treated
    ..recoversOn =
        sim.today +
        (illness.recoverDays ~/ 2 + rng.range(0, illness.recoverDays ~/ 2));
  sim.emit(
    Treated(
      sim.today,
      owner: p.id,
      camel: camel.id,
      name: camel.name,
      illness: illness,
      cost: cost.value,
    ),
  );
  return _ok(sim);
}

Result _rename(Sim sim, PlayerState p, RenameCamel cmd) {
  final c = sim.world.camels[cmd.camel];
  final own = Eligibility.owned(c, p.id);
  if (own != null) return Err(own, sim.drain());
  final name = cmd.name.trim();
  if (name.isEmpty || name.length > 24) return _err(sim, ErrorCode.invalidName);
  final old = c!.name;
  c.name = name;
  sim.emit(
    CamelRenamed(sim.today, owner: p.id, camel: c.id, from: old, to: name),
  );
  return _ok(sim);
}

Result _feedPlan(Sim sim, PlayerState p, SetFeedPlan cmd) {
  p.farm.feedPlan = cmd.plan;
  sim.emit(FeedPlanChanged(sim.today, owner: p.id, plan: cmd.plan));
  return _ok(sim);
}

Result _order(Sim sim, PlayerState p, OrderSupply cmd) {
  if (cmd.units < 1) return _err(sim, ErrorCode.invalidAmount);
  final size = Provisions.unitSize(cmd.supply);
  final fits = (Provisions.room(p.farm, cmd.supply) / size).floor();
  if (cmd.units > fits) {
    return _err(sim, ErrorCode.storeFull, {'room': fits < 0 ? 0 : fits});
  }
  final cost = Riyal(
    (Provisions.unitPrice(cmd.supply, p.farm.region) * cmd.units).round(),
  );
  if (p.cash < cost) {
    return _err(sim, ErrorCode.insufficientFunds, {'needed': cost.value});
  }
  sim.pay(
    p,
    -cost,
    cmd.supply == Supply.water ? LedgerCategory.water : LedgerCategory.feed,
  );
  final arrives = sim.today + Balance.deliveryDays;
  p.farm.deliveries.add(
    Delivery(supply: cmd.supply, units: cmd.units, arrivesOn: arrives),
  );
  sim.emit(
    SupplyOrdered(
      sim.today,
      owner: p.id,
      supply: cmd.supply,
      units: cmd.units,
      cost: cost.value,
      arrivesOn: arrives,
    ),
  );
  return _ok(sim);
}

Result _shepherds(Sim sim, PlayerState p, SetShepherds cmd) {
  if (cmd.count < 1 || cmd.count > Balance.maxShepherds) {
    return _err(sim, ErrorCode.invalidAmount);
  }
  p.farm.shepherds = cmd.count;
  sim.emit(ShepherdsChanged(sim.today, owner: p.id, count: cmd.count));
  return _ok(sim);
}

Riyal expansionCost(PlayerState p) =>
    Riyal((Balance.expansionCost * p.farm.region.land / 500).round() * 500);

Result _expand(Sim sim, PlayerState p) {
  final cost = expansionCost(p);
  if (p.cash < cost) {
    return _err(sim, ErrorCode.insufficientFunds, {'needed': cost.value});
  }
  sim.pay(p, -cost, LedgerCategory.construction);
  p.farm
    ..capacity += Balance.expansionStep
    ..storeKg += Balance.expansionStep * Balance.storeKgPerHead
    ..tankL += Balance.expansionStep * Balance.tankLPerHead;
  sim.emit(
    FarmExpanded(
      sim.today,
      owner: p.id,
      capacity: p.farm.capacity,
      cost: cost.value,
    ),
  );
  return _ok(sim);
}

// ================================================================ contests

Result _enter(Sim sim, PlayerState p, EnterRound cmd) {
  final f = sim.world.festivals[cmd.festival];
  final r = f?.rounds.where((x) => x.id == cmd.round).firstOrNull;
  if (f == null || r == null) return _err(sim, ErrorCode.notFound);
  final c = sim.world.camels[cmd.camel];
  final problem = Eligibility.canEnter(sim.world, f, r, c, p.id, sim.today);
  if (problem != null) return Err(problem, sim.drain());
  r.entries.add(Entry(camelId: c!.id, ownerId: p.id));
  sim.emit(
    Entered(
      sim.today,
      owner: p.id,
      camel: c.id,
      name: c.name,
      festival: f.name,
      round: r.id,
    ),
  );
  return _ok(sim);
}

Result _withdraw(Sim sim, PlayerState p, WithdrawEntry cmd) {
  final f = sim.world.festivals[cmd.festival];
  final r = f?.rounds.where((x) => x.id == cmd.round).firstOrNull;
  if (f == null || r == null || f.done) return _err(sim, ErrorCode.notFound);
  final before = r.entries.length;
  r.entries.removeWhere((e) => e.camelId == cmd.camel && e.ownerId == p.id);
  if (r.entries.length == before) return _err(sim, ErrorCode.notEntered);
  sim.emit(
    Withdrawn(sim.today, owner: p.id, camel: cmd.camel, festival: f.name),
  );
  return _ok(sim);
}

/// Days of a pregnancy: about the real average, inside the real range, drawn
/// again when outside it (held at the ends instead, 2% landed on 356 itself).
int _gestation(Rng rng) {
  for (var i = 0; i < 20; i++) {
    final d = (Balance.gestationDays + rng.normal(sd: Balance.gestationSd))
        .round();
    if (d >= Balance.gestationMinDays && d <= Balance.gestationMaxDays) {
      return d;
    }
  }
  return Balance.gestationDays;
}
