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
import '../model/tampering.dart';
import '../rules/account.dart';
import '../rules/balance.dart';
import '../rules/contest_rules.dart';
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
    BuildFacility() => _build(sim, p, cmd),
    SetCalfShare() => _calfShare(sim, p, cmd),
    EnterRound() => _enter(sim, p, cmd),
    WithdrawEntry() => _withdraw(sim, p, cmd),
    Tamper() => _tamper(sim, p, cmd),
    CheckListing() => _checkListing(sim, p, cmd),
  };
}

Ok _ok(Sim sim) => Ok(sim.drain());

/// The limit of [p]'s account for the herd's necessities today.
int accountLimit(Sim sim, PlayerState p) =>
    Account.limit(sim.herdOf(p.id), p, sim.today);

/// The balance is below zero (a fine larger than the money, GDD 7.1): no
/// camel is bought and nothing built till it is paid (the owner, 13 Nov
/// 2026).
Err _inDebt(Sim sim, PlayerState p) =>
    _err(sim, ErrorCode.inDebt, {'debt': -p.cash.value});
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
  if (p.cash.isNegative) return _inDebt(sim, p);
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

/// Pays a selling player: the price, less the broker's commission on a
/// sale he brokered (none when he buys the camel himself: [_quickSale]).
void _payout(
  Sim sim,
  PlayerState seller,
  Camel c,
  Riyal price, {
  bool commission = true,
}) {
  sim.pay(seller, price, LedgerCategory.sale, ref: c.id.value);
  // a strong sale raises the seller's name in the family (GDD 8)
  if (price.value >=
      Valuation.value(c, sim.today).value * Balance.strongSaleOver) {
    raiseReputation(seller, c.category, Balance.reputationForStrongSale);
  }
  if (!commission) return;
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
  // the money and the room are checked first, whatever the bid, so a refusal
  // for them says nothing of where the seller's floor is (the review: a bid
  // over the floor was refused for money without using a try, one under it
  // was answered, and the floor could be found by halving)
  final move = Riyal(transportToFarm(p, l));
  if (p.cash.isNegative) return _inDebt(sim, p);
  if (p.cash < offer + move) {
    return _err(sim, ErrorCode.insufficientFunds, {
      'needed': (offer + move).value,
    });
  }
  if (sim.herdOf(p.id).length >= p.farm.capacity) {
    return _err(sim, ErrorCode.farmFull);
  }
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
  if (cmd.askPrice < Balance.minAskPrice) {
    return _err(sim, ErrorCode.invalidAmount);
  }
  if (cmd.declared) {
    final cannot = cannotDeclare(sim, p, c!);
    if (cannot != null) return Err(cannot, sim.drain());
  }
  final l = Listing(
    id: sim.world.ids.listing(),
    camelId: c!.id,
    sellerId: p.id,
    region: p.farm.region,
    askPrice: Riyal(cmd.askPrice),
    reservePrice: Riyal(cmd.askPrice),
    listedOn: sim.today,
    expiresOn: sim.today + Balance.playerListingDays,
    declared: cmd.declared,
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
  // a declared treated camel is not examined: the buyer knows (decision 15)
  final refused = l.declared
      ? null
      : _examined(sim, p, c, buyer?.name ?? '', 'offer');
  if (refused != null) {
    sim.world.offers.remove(o.id); // the buyer walks away
    return refused;
  }
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

/// What the broker pays for [c] now: less than the market
/// ([Balance.quickSaleFactor]), by his own eye, which is off the true value
/// by a few percent and the same all week (his price is the one the player
/// is shown and the one paid; the exact value cannot be read back from it,
/// as from the appraisals: views.dart).
Riyal quickSalePrice(Camel c, Sim sim, {bool declared = false}) {
  final eye = Rng.keyed(sim.world.seed, [
    'broker',
    c.id.value,
    sim.today.value ~/ 7,
  ]).normal(sd: Balance.brokerEyeSd);
  final rep = sim.player(c.ownerId)?.reputationIn(c.category);
  return marketRound(
    Valuation.value(c, sim.today, natural: declared).value *
        (rep == null ? 1 : Balance.reputationPriceFactor(rep)) *
        Balance.quickSaleFactor *
        (1 +
            clampDouble(
              eye,
              -2.5 * Balance.brokerEyeSd,
              2.5 * Balance.brokerEyeSd,
            )),
  );
}

Result _quickSale(Sim sim, PlayerState p, QuickSale cmd) {
  final c = sim.world.camels[cmd.camel];
  final problem = Eligibility.canSell(sim.world, c, p.id);
  if (problem != null) return Err(problem, sim.drain());
  final rng = sim.rng(['broker', c!.id.value]);
  final broker = WorldGen(sim).randomOwner(rng, region: p.farm.region);
  if (cmd.declared) {
    final cannot = cannotDeclare(sim, p, c);
    if (cannot != null) return Err(cannot, sim.drain());
  } else {
    final refused = _examined(sim, p, c, broker.name, 'broker');
    if (refused != null) return refused;
  }
  // he buys it himself, so takes no commission (السعي is the fee for
  // finding a buyer); his lower price is his margin
  _sellTo(
    sim,
    p,
    c,
    quickSalePrice(c, sim, declared: cmd.declared),
    broker.id,
    broker.name,
    commission: false,
  );
  return _ok(sim);
}

/// Why [c] cannot be sold declared as treated: no treatment showing in her
/// that her owner knows of (he had it done, or was told). Null when he can
/// (the owner's decision 15: any owner who knows, the one who treated her
/// included; he gains nothing, the natural price).
DomainError? cannotDeclare(Sim sim, PlayerState p, Camel c) {
  final knows = c.treatments.any(
    (t) => t.activeOn(sim.today) && (t.by == p.id || t.knownBy.contains(p.id)),
  );
  return knows ? null : const DomainError(ErrorCode.nothingToDeclare);
}

/// The buyer's or the broker's examination before paying (the owner, 13
/// Nov 2026; they look at no cost to themselves): each treatment showing in
/// her is found with its chance (stronger, easier); found, the sale is off,
/// the seller fined MEWA's fine for each kind found and his name lowered
/// (TamperingSystem.foundOutside), and the refusal says the fine. Null when
/// nothing is found: the sale goes on.
Err? _examined(
  Sim sim,
  PlayerState seller,
  Camel c,
  String buyerName,
  String path,
) {
  final rng = sim.rng(['sale-check', c.id.value, path]);
  final found = [
    for (final t in c.treatments)
      if (t.activeOn(sim.today) &&
          rng.chance(ContestRules.saleCheckChance(t.strength)))
        t,
  ];
  if (found.isEmpty) return null;
  var fine = 0;
  for (final t in found) {
    fine += TamperingSystem.foundOutside(sim, seller, c, t);
  }
  sim.emit(
    SaleRefused(
      sim.today,
      owner: seller.id,
      camel: c.id,
      name: c.name,
      buyer: buyerName,
      kinds: [for (final t in found) t.kind],
      fine: fine,
    ),
  );
  return _err(sim, ErrorCode.saleRefused, {'fine': fine});
}

void _sellTo(
  Sim sim,
  PlayerState seller,
  Camel c,
  Riyal price,
  OwnerId buyerId,
  String buyerName, {
  bool commission = true,
}) {
  _payout(sim, seller, c, price, commission: commission);
  releaseCamel(sim, c);
  final profit =
      price.value -
      (commission ? price.times(Balance.brokerCommission).value : 0) -
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
  // a stud's fee is no necessity: cash, not the account
  final money = cashFor(p, (fee + move).value);
  if (money != null) return Err(money, sim.drain());
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
  // a sick camel's treatment goes on account like feed (the owner, 13 Nov)
  final short = Account.canPay(p, cost.value, accountLimit(sim, p));
  if (short != null) return Err(short, sim.drain());
  Account.book(p, cost.value);
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
  // the vet may see a treatment on it (GDD 7.1)
  for (final t in [...camel.treatments]) {
    if (t.activeOn(sim.today) && rng.chance(Balance.vetCatchChance)) {
      TamperingSystem.foundOutside(sim, p, camel, t);
      break;
    }
  }
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
  final water = cmd.supply == Supply.water;
  final size = water
      ? Provisions.tankerSize(cmd.tanker)
      : Provisions.unitSize(cmd.supply);
  final fits = Provisions.fits(p.farm, cmd.supply, size);
  if (cmd.units > fits) {
    return _err(sim, ErrorCode.storeFull, {'room': fits});
  }
  final unit = water
      ? Provisions.tankerPrice(cmd.tanker)
      : Provisions.unitPrice(cmd.supply, p.farm.region);
  final cost = Riyal((unit * cmd.units).round());
  // what the money does not cover goes on account, up to its limit (the
  // owner, 13 Nov 2026: the herd does not go hungry for want of riyals)
  final short = Account.canPay(p, cost.value, accountLimit(sim, p));
  if (short != null) return Err(short, sim.drain());
  Account.book(p, cost.value);
  sim.pay(
    p,
    -cost,
    cmd.supply == Supply.water ? LedgerCategory.water : LedgerCategory.feed,
  );
  final arrives = sim.today + Balance.deliveryDays;
  p.farm.deliveries.add(
    Delivery(
      supply: cmd.supply,
      units: cmd.units,
      arrivesOn: arrives,
      size: size,
    ),
  );
  sim.emit(
    SupplyOrdered(
      sim.today,
      owner: p.id,
      supply: cmd.supply,
      units: cmd.units,
      size: size,
      cost: cost.value,
      arrivesOn: arrives,
    ),
  );
  return _ok(sim);
}

Result _shepherds(Sim sim, PlayerState p, SetShepherds cmd) {
  if (cmd.count < 0 || cmd.count > Balance.maxShepherds) {
    return _err(sim, ErrorCode.invalidAmount);
  }
  // a shepherd lives in his caravan on the farm (none: the player tends the
  // herd himself)
  if (cmd.count > 0 && p.farm.has(Facility.caravan) == 0) {
    return _err(sim, ErrorCode.needsFacility, {
      'facility': Facility.caravan.name,
    });
  }
  p.farm.shepherds = cmd.count;
  sim.emit(ShepherdsChanged(sim.today, owner: p.id, count: cmd.count));
  return _ok(sim);
}

/// Why [f] cannot be built now, or null.
DomainError? cannotBuild(PlayerState p, Facility f) {
  if (p.farm.hasOrBuilding(f) >= f.most) {
    return const DomainError(ErrorCode.alreadyBuilt);
  }
  if (p.cash.isNegative) {
    return DomainError(ErrorCode.inDebt, {'debt': -p.cash.value});
  }
  if (p.cash.value < f.price) {
    return DomainError(ErrorCode.insufficientFunds, {'needed': f.price});
  }
  return null;
}

Result _build(Sim sim, PlayerState p, BuildFacility cmd) {
  final f = cmd.facility;
  final no = cannotBuild(p, f);
  if (no != null) return _err(sim, no.code, no.params);
  sim.pay(p, Riyal(-f.price), LedgerCategory.construction, ref: f.name);
  final done = sim.today + Balance.buildDays;
  p.farm.building.add(Construction(f, done));
  sim.emit(
    FacilityOrdered(
      sim.today,
      owner: p.id,
      facility: f,
      cost: f.price,
      doneOn: done,
    ),
  );
  return _ok(sim);
}

Result _calfShare(Sim sim, PlayerState p, SetCalfShare cmd) {
  p.farm.calfShare = cmd.share;
  sim.emit(CalfShareChanged(sim.today, owner: p.id, share: cmd.share));
  return _ok(sim);
}

// ================================================================ contests

Result _enter(Sim sim, PlayerState p, EnterRound cmd) {
  final f = sim.world.festivals[cmd.festival];
  final r = f?.round(cmd.round);
  if (f == null || r == null) return _err(sim, ErrorCode.notFound);
  final camels = [for (final id in cmd.camels) sim.world.camels[id]];
  final problem = cannotEnter(sim, p, f, r, camels);
  if (problem != null) return Err(problem, sim.drain());
  final late = Eligibility.isLate(f, sim.today);
  final fee = late ? Balance.lateEntryFee * camels.length : 0;
  sim.pay(p, Riyal(-fee), LedgerCategory.entryFee, ref: f.id.value);
  r.entries.add(
    Entry(ownerId: p.id, camels: [for (final c in camels) c!.id], late: late),
  );
  sim.emit(
    Entered(
      sim.today,
      owner: p.id,
      camel: camels.first!.id,
      name: camels.first!.name,
      festival: f.name,
      round: r.id,
      head: camels.length,
      fee: fee,
    ),
  );
  return _ok(sim);
}

Result _withdraw(Sim sim, PlayerState p, WithdrawEntry cmd) {
  final f = sim.world.festivals[cmd.festival];
  final r = f?.round(cmd.round);
  if (f == null || r == null || f.done || r.judged || sim.today >= r.day) {
    return _err(sim, ErrorCode.notFound);
  }
  final e = r.entries
      .where((e) => e.ownerId == p.id && e.camels.contains(cmd.camel))
      .firstOrNull;
  if (e == null) return _err(sim, ErrorCode.notEntered);
  r.entries.remove(e);
  // after the closing the class was fixed: not entered again here
  if (Eligibility.isLate(f, sim.today)) f.scratched.addAll(e.camels);
  sim.emit(
    Withdrawn(sim.today, owner: p.id, camel: cmd.camel, festival: f.name),
  );
  return _ok(sim);
}

/// Why [camels] cannot be entered in [r] now: the rules (Eligibility), then
/// the money, which must cover a late entry's fee and the trucking of the
/// camels not yet there (a festival entry is no necessity: no account; the
/// owner's decisions 8 to 10). Null when allowed.
DomainError? cannotEnter(
  Sim sim,
  PlayerState p,
  Festival f,
  ContestRound r,
  List<Camel?> camels,
) {
  final rules = Eligibility.canEnter(sim.world, f, r, camels, p.id, sim.today);
  if (rules != null) return rules;
  final fee = Eligibility.isLate(f, sim.today)
      ? Balance.lateEntryFee * camels.length
      : 0;
  final trip = ContestSystem.festivalTrip(f, p, more: camels.length);
  return cashFor(p, fee + trip);
}

/// The money for a cost that is no necessity: inDebt below zero, else
/// insufficientFunds when it does not cover [cost]; null when it does.
DomainError? cashFor(PlayerState p, int cost) {
  if (p.cash.isNegative) {
    return DomainError(ErrorCode.inDebt, {'debt': -p.cash.value});
  }
  if (p.cash.value < cost) {
    return DomainError(ErrorCode.insufficientFunds, {'needed': cost});
  }
  return null;
}

/// Why [kind] at [strength] cannot be done on [c] now, or null.
DomainError? cannotTamper(
  Sim sim,
  PlayerState p,
  Camel? c,
  TamperKind kind,
  int strength,
) {
  final own = Eligibility.owned(c, p.id);
  if (own != null) return own;
  if (Eligibility.onTheWay(c!, sim.today)) {
    return const DomainError(ErrorCode.onTheWay);
  }
  if (strength < 1 || strength > 3) {
    return const DomainError(ErrorCode.invalidAmount);
  }
  // (one he knows of; a kind already in her unknown to him is not told)
  if (c.treatments.any(
    (t) => t.kind == kind && t.activeOn(sim.today) && t.knownBy.contains(p.id),
  )) {
    return const DomainError(ErrorCode.alreadyTreated);
  }
  final price = ContestRules.tamperPrice(kind, strength);
  if (p.cash.value < price) {
    return DomainError(ErrorCode.insufficientFunds, {'needed': price});
  }
  return null;
}

Result _tamper(Sim sim, PlayerState p, Tamper cmd) {
  final c = sim.world.camels[cmd.camel];
  final problem = cannotTamper(sim, p, c, cmd.kind, cmd.strength);
  if (problem != null) return Err(problem, sim.drain());
  final price = ContestRules.tamperPrice(cmd.kind, cmd.strength);
  sim.pay(p, Riyal(-price), LedgerCategory.tampering, ref: c!.id.value);
  c.treatments.add(
    Tampering(
      kind: cmd.kind,
      strength: cmd.strength,
      on: sim.today,
      until: sim.today + (cmd.kind.lastsDays - 1),
      by: p.id,
      knownBy: [p.id],
    ),
  );
  sim.emit(
    Tampered(
      sim.today,
      owner: p.id,
      camel: c.id,
      name: c.name,
      kind: cmd.kind,
      strength: cmd.strength,
      price: price,
    ),
  );
  return _ok(sim);
}

/// A vet's look at a camel for sale before buying (GDD 7.1; the owner, 13
/// Nov 2026): paid, and each treatment in her found with the vet's chance;
/// what he finds the buyer knows from then on. Nothing is reported: he is
/// the buyer's vet.
Result _checkListing(Sim sim, PlayerState p, CheckListing cmd) {
  final l = sim.world.listings[cmd.listing];
  final c = l == null ? null : sim.world.camels[l.camelId];
  if (l == null || c == null || !c.isAlive) {
    return _err(sim, ErrorCode.notFound);
  }
  if (l.sellerId == p.id) return _err(sim, ErrorCode.ownListing);
  if (p.cash.value < Balance.vetCheckFee) {
    return _err(sim, ErrorCode.insufficientFunds, {
      'needed': Balance.vetCheckFee,
    });
  }
  sim.pay(
    p,
    const Riyal(-Balance.vetCheckFee),
    LedgerCategory.vet,
    ref: c.id.value,
  );
  // each look on its own day is a fresh one (a second opinion; the same
  // day's looks agree)
  l.checks[p.id.value] = (l.checks[p.id.value] ?? 0) + 1;
  final rng = sim.rng(['vet-check', c.id.value, p.id.value]);
  final found = <TamperKind>[];
  for (final t in c.treatments) {
    if (!t.activeOn(sim.today)) continue;
    if (t.knownBy.contains(p.id) || rng.chance(Balance.vetCheckChance)) {
      if (!t.knownBy.contains(p.id)) t.knownBy.add(p.id);
      found.add(t.kind);
    }
  }
  sim.emit(
    ListingChecked(
      sim.today,
      owner: p.id,
      camel: c.id,
      name: c.name,
      listing: l.id,
      found: found,
    ),
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
