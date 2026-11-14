import 'catalog/catalog.dart';
import 'catalog/falconry.dart';
import 'catalog/region.dart';
import 'common/ids.dart';
import 'common/time.dart';
import 'model/contest.dart';
import 'model/player.dart';
import 'model/tampering.dart';

part 'hunt_events.dart';

/// Why a camel died.
/// Why a camel died: an illness, old age, a young calf's death in its first
/// year (the real first-year loss, Balance.calfDeathFirstYear), or thirst.
enum DeathCause { illness, age, young, thirst }

/// Everything that can happen in the world, as typed, immutable values.
/// Events carry no display text: the app turns each type into words with an
/// exhaustive `switch`. Notifications, the activity log and (later) server
/// sync all read the same events.
sealed class DomainEvent {
  const DomainEvent(this.day, {this.owner, this.camel});

  final GameDay day;

  /// Whose news this is; null for public world news.
  final OwnerId? owner;
  final CamelId? camel;

  /// Stable name used in saves.
  String get type;

  Map<String, Object?> fieldsToJson();

  Map<String, Object?> toJson() => {
    'type': type,
    'day': day.value,
    'owner': owner?.value,
    'camel': camel?.value,
    ...fieldsToJson(),
  };

  static DomainEvent fromJson(Map<String, Object?> j) {
    final day = GameDay(j['day']! as int);
    final owner = j['owner'] == null ? null : OwnerId(j['owner']! as String);
    final camel = j['camel'] == null ? null : CamelId(j['camel']! as String);
    return switch (j['type']! as String) {
      'wagesPaid' => WagesPaid(
        day,
        owner: owner,
        camel: camel,
        amount: j['amount']! as int,
        shepherds: j['shepherds']! as int,
      ),
      'testMoneySet' => TestMoneySet(
        day,
        owner: owner,
        camel: camel,
        on: j['on']! as bool,
      ),
      'testMoneyAdded' => TestMoneyAdded(
        day,
        owner: owner,
        camel: camel,
        amount: j['amount']! as int,
      ),
      'cashNegative' => CashNegative(
        day,
        owner: owner,
        camel: camel,
        cash: j['cash']! as int,
      ),
      'camelBought' => CamelBought(
        day,
        owner: owner,
        camel: camel,
        name: j['name']! as String,
        price: j['price']! as int,
        seller: j['seller']! as String,
        region: Region.values.byName(j['region']! as String),
      ),
      'camelSold' => CamelSold(
        day,
        owner: owner,
        camel: camel,
        name: j['name']! as String,
        price: j['price']! as int,
        buyer: j['buyer']! as String,
        profit: j['profit']! as int,
      ),
      'bargainCountered' => BargainCountered(
        day,
        owner: owner,
        camel: camel,
        listing: ListingId(j['listing']! as String),
        ask: j['ask']! as int,
      ),
      'bargainRejected' => BargainRejected(
        day,
        owner: owner,
        camel: camel,
        listing: ListingId(j['listing']! as String),
      ),
      'listingCreated' => ListingCreated(
        day,
        owner: owner,
        camel: camel,
        name: j['name']! as String,
        ask: j['ask']! as int,
        listing: ListingId(j['listing']! as String),
      ),
      'listingCancelled' => ListingCancelled(day, owner: owner, camel: camel),
      'listingExpired' => ListingExpired(
        day,
        owner: owner,
        camel: camel,
        name: j['name']! as String,
      ),
      'offerReceived' => OfferReceived(
        day,
        owner: owner,
        camel: camel,
        name: j['name']! as String,
        buyer: j['buyer']! as String,
        region: Region.values.byName(j['region']! as String),
        amount: j['amount']! as int,
        offer: OfferId(j['offer']! as String),
      ),
      'offerDeclined' => OfferDeclined(day, owner: owner, camel: camel),
      'farmExpanded' => FarmExpanded(
        day,
        owner: owner,
        camel: camel,
        capacity: j['capacity']! as int,
        cost: j['cost']! as int,
      ),
      'facilityOrdered' => FacilityOrdered(
        day,
        owner: owner,
        camel: camel,
        facility: Facility.values.byName(j['facility']! as String),
        cost: j['cost']! as int,
        doneOn: GameDay(j['doneOn']! as int),
      ),
      'facilityBuilt' => FacilityBuilt(
        day,
        owner: owner,
        camel: camel,
        facility: Facility.values.byName(j['facility']! as String),
      ),
      'shepherdsChanged' => ShepherdsChanged(
        day,
        owner: owner,
        camel: camel,
        count: j['count']! as int,
      ),
      'supplyOrdered' => SupplyOrdered(
        day,
        owner: owner,
        supply: Supply.values.byName(j['supply']! as String),
        units: j['units']! as int,
        size: j['size'] as int?,
        cost: j['cost']! as int,
        arrivesOn: GameDay(j['arrivesOn']! as int),
        standing: (j['standing'] as bool?) ?? false,
      ),
      'rushed' => Rushed(
        day,
        owner: owner,
        camel: camel,
        what: j['what']! as String,
        ref: j['ref']! as String,
        fee: j['fee']! as int,
      ),
      'standingOrderChanged' => StandingOrderChanged(
        day,
        owner: owner,
        kind: StandingOrder.values.byName(j['kind']! as String),
        on: j['on']! as bool,
      ),
      'standingOrderRefused' => StandingOrderRefused(
        day,
        owner: owner,
        supply: Supply.values.byName(j['supply']! as String),
      ),
      'vetContractChanged' => VetContractChanged(
        day,
        owner: owner,
        on: j['on']! as bool,
        fee: j['fee']! as int,
        endsOn: j['endsOn'] == null ? null : GameDay(j['endsOn']! as int),
      ),
      'vetRefused' => VetRefused(
        day,
        owner: owner,
        camel: camel,
        name: j['name']! as String,
      ),
      'supplyDelivered' => SupplyDelivered(
        day,
        owner: owner,
        supply: Supply.values.byName(j['supply']! as String),
        units: j['units']! as int,
        size: j['size'] as int?,
        returned: (j['returned'] as int?) ?? 0,
      ),
      'supplyLow' => SupplyLow(
        day,
        owner: owner,
        supply: Supply.values.byName(j['supply']! as String),
        days: j['days']! as int,
      ),
      'feedPlanChanged' => FeedPlanChanged(
        day,
        owner: owner,
        camel: camel,
        plan: FeedPlan.values.byName(j['plan']! as String),
      ),
      'calfShareChanged' => CalfShareChanged(
        day,
        owner: owner,
        camel: camel,
        share: CalfShare.values.byName(j['share']! as String),
      ),
      'camelRenamed' => CamelRenamed(
        day,
        owner: owner,
        camel: camel,
        from: j['from']! as String,
        to: j['to']! as String,
      ),
      'fellSick' => FellSick(
        day,
        owner: owner,
        camel: camel,
        name: j['name']! as String,
        illness: Illness.values.byName(j['illness']! as String),
      ),
      'treated' => Treated(
        day,
        owner: owner,
        camel: camel,
        name: j['name']! as String,
        illness: Illness.values.byName(j['illness']! as String),
        cost: j['cost']! as int,
      ),
      'recovered' => Recovered(
        day,
        owner: owner,
        camel: camel,
        name: j['name']! as String,
      ),
      'died' => Died(
        day,
        owner: owner,
        camel: camel,
        name: j['name']! as String,
        cause: DeathCause.values.byName(j['cause']! as String),
        age: AgeClass.values.byName(j['age']! as String),
      ),
      'mated' => Mated(
        day,
        owner: owner,
        camel: camel,
        name: j['name']! as String,
        sire: j['sire']! as String,
        checkOn: GameDay(j['checkOn']! as int),
        fee: j['fee']! as int,
      ),
      'pregnancyConfirmed' => PregnancyConfirmed(
        day,
        owner: owner,
        camel: camel,
        name: j['name']! as String,
        sire: j['sire']! as String,
        due: GameDay(j['due']! as int),
      ),
      'pregnancyFailed' => PregnancyFailed(
        day,
        owner: owner,
        camel: camel,
        name: j['name']! as String,
        sire: j['sire']! as String,
      ),
      'calfBorn' => CalfBorn(
        day,
        owner: owner,
        camel: camel,
        dam: j['dam']! as String,
        sire: j['sire']! as String,
        name: j['name']! as String,
        sex: Sex.values.byName(j['sex']! as String),
      ),
      'calfLost' => CalfLost(
        day,
        owner: owner,
        camel: camel,
        name: j['name']! as String,
      ),
      'seasonPlanned' => SeasonPlanned(
        day,
        owner: owner,
        camel: camel,
        year: j['year']! as int,
      ),
      'registrationOpened' => RegistrationOpened(
        day,
        owner: owner,
        camel: camel,
        festival: FestivalId(j['festival']! as String),
        name: j['name']! as String,
        tier: FestivalTier.values.byName(j['tier']! as String),
        judgedOn: GameDay(j['judgedOn']! as int),
      ),
      'registrationClosingSoon' => RegistrationClosingSoon(
        day,
        owner: owner,
        camel: camel,
        festival: FestivalId(j['festival']! as String),
        name: j['name']! as String,
      ),
      'entered' => Entered(
        day,
        owner: owner,
        camel: camel,
        name: j['name']! as String,
        festival: j['festival']! as String,
        round: RoundId(j['round']! as String),
        head: (j['head'] as int?) ?? 1,
        fee: (j['fee'] as int?) ?? 0,
      ),
      'messagesRead' => MessagesRead(
        day,
        owner: owner,
        camel: camel,
        count: j['count']! as int,
      ),
      'findingsTold' => FindingsTold(
        day,
        owner: owner,
        camel: camel,
        count: j['count']! as int,
      ),
      'withdrawn' => Withdrawn(
        day,
        owner: owner,
        camel: camel,
        festival: j['festival']! as String,
      ),
      'disqualifiedSick' => DisqualifiedSick(
        day,
        owner: owner,
        camel: camel,
        name: j['name']! as String,
        festival: j['festival']! as String,
      ),
      'placed' => Placed(
        day,
        owner: owner,
        camel: camel,
        name: j['name']! as String,
        festival: j['festival']! as String,
        round: RoundId(j['round']! as String),
        rank: j['rank']! as int,
        of: j['of']! as int,
        score: (j['score']! as num).toDouble(),
        prize: j['prize']! as int,
      ),
      'festivalSummary' => FestivalSummary(
        day,
        owner: owner,
        camel: camel,
        festival: j['festival']! as String,
        prizes: j['prizes']! as int,
      ),
      'entryRemoved' => EntryRemoved(
        day,
        owner: owner,
        camel: camel,
        name: j['name']! as String,
        festival: j['festival']! as String,
        round: RoundId(j['round']! as String),
        stage: Stage.values.byName(j['stage']! as String),
        reason: RemovalReason.values.byName(j['reason']! as String),
      ),
      'resultsPending' => ResultsPending(
        day,
        owner: owner,
        camel: camel,
        festival: j['festival']! as String,
        round: RoundId(j['round']! as String),
        announceOn: GameDay(j['announceOn']! as int),
      ),
      'tampered' => Tampered(
        day,
        owner: owner,
        camel: camel,
        name: j['name']! as String,
        kind: TamperKind.values.byName(j['kind']! as String),
        strength: j['strength']! as int,
        price: j['price']! as int,
      ),
      'tamperingFound' => TamperingFound(
        day,
        owner: owner,
        camel: camel,
        name: j['name']! as String,
        kind: TamperKind.values.byName(j['kind']! as String),
        festival: j['festival'] as String?,
        stage: j['stage'] == null
            ? null
            : Stage.values.byName(j['stage']! as String),
        fine: j['fine']! as int,
        bannedThrough: j['bannedThrough'] as int?,
      ),
      'cheatNews' => CheatNews(
        day,
        owner: owner,
        camel: camel,
        ownerName: j['ownerName']! as String,
        name: j['name']! as String,
        kind: TamperKind.values.byName(j['kind']! as String),
        festival: j['festival'] as String?,
        fine: j['fine']! as int,
      ),
      'saleRefused' => SaleRefused(
        day,
        owner: owner,
        camel: camel,
        name: j['name']! as String,
        buyer: j['buyer']! as String,
        kinds: [
          for (final k in j['kinds']! as List<Object?>)
            TamperKind.values.byName(k! as String),
        ],
        fine: j['fine']! as int,
      ),
      'listingChecked' => ListingChecked(
        day,
        owner: owner,
        camel: camel,
        name: j['name']! as String,
        listing: ListingId(j['listing']! as String),
        found: [
          for (final k in j['found']! as List<Object?>)
            TamperKind.values.byName(k! as String),
        ],
      ),
      'festivalIntegrity' => FestivalIntegrity(
        day,
        owner: owner,
        camel: camel,
        festival: j['festival']! as String,
        cases: j['cases']! as int,
        fines: j['fines']! as int,
      ),
      final other =>
        _huntEvent(other, day, owner, camel, j) ??
            (throw FormatException('unknown event type $other')),
    };
  }

  @override
  String toString() => '$type(day ${day.value}, ${fieldsToJson()})';
}

final class WagesPaid extends DomainEvent {
  const WagesPaid(
    super.day, {
    super.owner,
    super.camel,
    required this.amount,
    required this.shepherds,
  });
  final int amount;
  final int shepherds;
  @override
  String get type => 'wagesPaid';
  @override
  Map<String, Object?> fieldsToJson() => {
    'amount': amount,
    'shepherds': shepherds,
  };
}

/// Money without limit for testing turned on or off (TestMoney).
final class TestMoneySet extends DomainEvent {
  const TestMoneySet(super.day, {super.owner, super.camel, required this.on});
  final bool on;
  @override
  String get type => 'testMoneySet';
  @override
  Map<String, Object?> fieldsToJson() => {'on': on};
}

/// The money topped up for testing (TestMoney): [amount] riyals in.
final class TestMoneyAdded extends DomainEvent {
  const TestMoneyAdded(
    super.day, {
    super.owner,
    super.camel,
    required this.amount,
  });
  final int amount;
  @override
  String get type => 'testMoneyAdded';
  @override
  Map<String, Object?> fieldsToJson() => {'amount': amount};
}

final class CashNegative extends DomainEvent {
  const CashNegative(super.day, {super.owner, super.camel, required this.cash});
  final int cash;
  @override
  String get type => 'cashNegative';
  @override
  Map<String, Object?> fieldsToJson() => {'cash': cash};
}

final class CamelBought extends DomainEvent {
  const CamelBought(
    super.day, {
    super.owner,
    super.camel,
    required this.name,
    required this.price,
    required this.seller,
    required this.region,
  });
  final String name;
  final int price;
  final String seller;
  final Region region;
  @override
  String get type => 'camelBought';
  @override
  Map<String, Object?> fieldsToJson() => {
    'name': name,
    'price': price,
    'seller': seller,
    'region': region.name,
  };
}

final class CamelSold extends DomainEvent {
  const CamelSold(
    super.day, {
    super.owner,
    super.camel,
    required this.name,
    required this.price,
    required this.buyer,
    required this.profit,
  });
  final String name;
  final int price;
  final String buyer;
  final int profit;
  @override
  String get type => 'camelSold';
  @override
  Map<String, Object?> fieldsToJson() => {
    'name': name,
    'price': price,
    'buyer': buyer,
    'profit': profit,
  };
}

final class BargainCountered extends DomainEvent {
  const BargainCountered(
    super.day, {
    super.owner,
    super.camel,
    required this.listing,
    required this.ask,
  });
  final ListingId listing;
  final int ask;
  @override
  String get type => 'bargainCountered';
  @override
  Map<String, Object?> fieldsToJson() => {'listing': listing.value, 'ask': ask};
}

final class BargainRejected extends DomainEvent {
  const BargainRejected(
    super.day, {
    super.owner,
    super.camel,
    required this.listing,
  });
  final ListingId listing;
  @override
  String get type => 'bargainRejected';
  @override
  Map<String, Object?> fieldsToJson() => {'listing': listing.value};
}

final class ListingCreated extends DomainEvent {
  const ListingCreated(
    super.day, {
    super.owner,
    super.camel,
    required this.name,
    required this.ask,
    required this.listing,
  });
  final String name;
  final int ask;
  final ListingId listing;
  @override
  String get type => 'listingCreated';
  @override
  Map<String, Object?> fieldsToJson() => {
    'name': name,
    'ask': ask,
    'listing': listing.value,
  };
}

final class ListingCancelled extends DomainEvent {
  const ListingCancelled(super.day, {super.owner, super.camel});

  @override
  String get type => 'listingCancelled';
  @override
  Map<String, Object?> fieldsToJson() => {};
}

final class ListingExpired extends DomainEvent {
  const ListingExpired(
    super.day, {
    super.owner,
    super.camel,
    required this.name,
  });
  final String name;
  @override
  String get type => 'listingExpired';
  @override
  Map<String, Object?> fieldsToJson() => {'name': name};
}

final class OfferReceived extends DomainEvent {
  const OfferReceived(
    super.day, {
    super.owner,
    super.camel,
    required this.name,
    required this.buyer,
    required this.region,
    required this.amount,
    required this.offer,
  });
  final String name;
  final String buyer;
  final Region region;
  final int amount;
  final OfferId offer;
  @override
  String get type => 'offerReceived';
  @override
  Map<String, Object?> fieldsToJson() => {
    'name': name,
    'buyer': buyer,
    'region': region.name,
    'amount': amount,
    'offer': offer.value,
  };
}

final class OfferDeclined extends DomainEvent {
  const OfferDeclined(super.day, {super.owner, super.camel});

  @override
  String get type => 'offerDeclined';
  @override
  Map<String, Object?> fieldsToJson() => {};
}

/// The farm grew by a block of room (before the facilities of 13 Nov 2026;
/// kept so the event logs of saves from then still read).
final class FarmExpanded extends DomainEvent {
  const FarmExpanded(
    super.day, {
    super.owner,
    super.camel,
    required this.capacity,
    required this.cost,
  });
  final int capacity;
  final int cost;
  @override
  String get type => 'farmExpanded';
  @override
  Map<String, Object?> fieldsToJson() => {'capacity': capacity, 'cost': cost};
}

/// A facility paid for and begun; done on [doneOn].
final class FacilityOrdered extends DomainEvent {
  const FacilityOrdered(
    super.day, {
    super.owner,
    super.camel,
    required this.facility,
    required this.cost,
    required this.doneOn,
  });
  final Facility facility;
  final int cost;
  final GameDay doneOn;
  @override
  String get type => 'facilityOrdered';
  @override
  Map<String, Object?> fieldsToJson() => {
    'facility': facility.name,
    'cost': cost,
    'doneOn': doneOn.value,
  };
}

/// A facility finished: it stands on the farm from today.
final class FacilityBuilt extends DomainEvent {
  const FacilityBuilt(
    super.day, {
    super.owner,
    super.camel,
    required this.facility,
  });
  final Facility facility;
  @override
  String get type => 'facilityBuilt';
  @override
  Map<String, Object?> fieldsToJson() => {'facility': facility.name};
}

final class ShepherdsChanged extends DomainEvent {
  const ShepherdsChanged(
    super.day, {
    super.owner,
    super.camel,
    required this.count,
  });
  final int count;
  @override
  String get type => 'shepherdsChanged';
  @override
  Map<String, Object?> fieldsToJson() => {'count': count};
}

final class SupplyOrdered extends DomainEvent {
  const SupplyOrdered(
    super.day, {
    super.owner,
    super.camel,
    required this.supply,
    required this.units,
    this.size,
    required this.cost,
    required this.arrivesOn,
    this.standing = false,
  });
  final Supply supply;
  final int units;

  /// Kilograms or litres in each unit (null in events kept before v6).
  final int? size;
  final int cost;
  final GameDay arrivesOn;

  /// Sent by the standing order (UpkeepSystem), not by the player's tap.
  final bool standing;
  @override
  String get type => 'supplyOrdered';
  @override
  Map<String, Object?> fieldsToJson() => {
    'supply': supply.name,
    'units': units,
    'size': size,
    'cost': cost,
    'arrivesOn': arrivesOn.value,
    if (standing) 'standing': true,
  };
}

/// Something finished now for more (the rush, T15): [what] is 'facility',
/// 'water', 'feed' or 'camel'; [ref] the facility's name, or the camel's
/// id (also [camel]); [fee] what the rush cost.
final class Rushed extends DomainEvent {
  const Rushed(
    super.day, {
    super.owner,
    super.camel,
    required this.what,
    required this.ref,
    required this.fee,
  });
  final String what;
  final String ref;
  final int fee;
  @override
  String get type => 'rushed';
  @override
  Map<String, Object?> fieldsToJson() => {'what': what, 'ref': ref, 'fee': fee};
}

/// A standing order turned on or off.
final class StandingOrderChanged extends DomainEvent {
  const StandingOrderChanged(
    super.day, {
    super.owner,
    super.camel,
    required this.kind,
    required this.on,
  });
  final StandingOrder kind;
  final bool on;
  @override
  String get type => 'standingOrderChanged';
  @override
  Map<String, Object?> fieldsToJson() => {'kind': kind.name, 'on': on};
}

/// A standing order the supplier could not send: the money and the
/// merchant's account did not cover it ([supply]).
final class StandingOrderRefused extends DomainEvent {
  const StandingOrderRefused(
    super.day, {
    super.owner,
    super.camel,
    required this.supply,
  });
  final Supply supply;
  @override
  String get type => 'standingOrderRefused';
  @override
  Map<String, Object?> fieldsToJson() => {'supply': supply.name};
}

/// The vet's contract signed ([fee]: this month's part), cancelled
/// ([endsOn]: the month's end), or ended (neither).
final class VetContractChanged extends DomainEvent {
  const VetContractChanged(
    super.day, {
    super.owner,
    super.camel,
    required this.on,
    this.fee = 0,
    this.endsOn,
  });
  final bool on;
  final int fee;
  final GameDay? endsOn;
  @override
  String get type => 'vetContractChanged';
  @override
  Map<String, Object?> fieldsToJson() => {
    'on': on,
    'fee': fee,
    'endsOn': endsOn?.value,
  };
}

/// Under the vet's contract a camel fell ill and could not be treated: the
/// merchant's account is at its limit ([name]).
final class VetRefused extends DomainEvent {
  const VetRefused(super.day, {super.owner, super.camel, required this.name});
  final String name;
  @override
  String get type => 'vetRefused';
  @override
  Map<String, Object?> fieldsToJson() => {'name': name};
}

final class SupplyDelivered extends DomainEvent {
  const SupplyDelivered(
    super.day, {
    super.owner,
    super.camel,
    required this.supply,
    required this.units,
    this.size,
    this.returned = 0,
  });
  final Supply supply;
  final int units;

  /// Kilograms or litres in each unit (null in events kept before v6).
  final int? size;

  /// Litres of a tanker that did not fit the tank and went back with it
  /// (paid all the same).
  final int returned;
  @override
  String get type => 'supplyDelivered';
  @override
  Map<String, Object?> fieldsToJson() => {
    'supply': supply.name,
    'units': units,
    'size': size,
    if (returned > 0) 'returned': returned,
  };
}

/// A store holds [days] or fewer days of the herd's needs (0: it ran out).
final class SupplyLow extends DomainEvent {
  const SupplyLow(
    super.day, {
    super.owner,
    super.camel,
    required this.supply,
    required this.days,
  });
  final Supply supply;
  final int days;
  @override
  String get type => 'supplyLow';
  @override
  Map<String, Object?> fieldsToJson() => {'supply': supply.name, 'days': days};
}

final class FeedPlanChanged extends DomainEvent {
  const FeedPlanChanged(
    super.day, {
    super.owner,
    super.camel,
    required this.plan,
  });
  final FeedPlan plan;
  @override
  String get type => 'feedPlanChanged';
  @override
  Map<String, Object?> fieldsToJson() => {'plan': plan.name};
}

/// The calves' share of the milk changed (saved, and the screens drawn
/// again, as for every change).
final class CalfShareChanged extends DomainEvent {
  const CalfShareChanged(
    super.day, {
    super.owner,
    super.camel,
    required this.share,
  });
  final CalfShare share;
  @override
  String get type => 'calfShareChanged';
  @override
  Map<String, Object?> fieldsToJson() => {'share': share.name};
}

final class CamelRenamed extends DomainEvent {
  const CamelRenamed(
    super.day, {
    super.owner,
    super.camel,
    required this.from,
    required this.to,
  });
  final String from;
  final String to;
  @override
  String get type => 'camelRenamed';
  @override
  Map<String, Object?> fieldsToJson() => {'from': from, 'to': to};
}

final class FellSick extends DomainEvent {
  const FellSick(
    super.day, {
    super.owner,
    super.camel,
    required this.name,
    required this.illness,
  });
  final String name;
  final Illness illness;
  @override
  String get type => 'fellSick';
  @override
  Map<String, Object?> fieldsToJson() => {
    'name': name,
    'illness': illness.name,
  };
}

final class Treated extends DomainEvent {
  const Treated(
    super.day, {
    super.owner,
    super.camel,
    required this.name,
    required this.illness,
    required this.cost,
  });
  final String name;
  final Illness illness;
  final int cost;
  @override
  String get type => 'treated';
  @override
  Map<String, Object?> fieldsToJson() => {
    'name': name,
    'illness': illness.name,
    'cost': cost,
  };
}

final class Recovered extends DomainEvent {
  const Recovered(super.day, {super.owner, super.camel, required this.name});
  final String name;
  @override
  String get type => 'recovered';
  @override
  Map<String, Object?> fieldsToJson() => {'name': name};
}

final class Died extends DomainEvent {
  const Died(
    super.day, {
    super.owner,
    super.camel,
    required this.name,
    required this.cause,
    required this.age,
  });
  final String name;
  final DeathCause cause;
  final AgeClass age;
  @override
  String get type => 'died';
  @override
  Map<String, Object?> fieldsToJson() => {
    'name': name,
    'cause': cause.name,
    'age': age.name,
  };
}

final class Mated extends DomainEvent {
  const Mated(
    super.day, {
    super.owner,
    super.camel,
    required this.name,
    required this.sire,
    required this.checkOn,
    required this.fee,
  });
  final String name;
  final String sire;
  final GameDay checkOn;
  final int fee;
  @override
  String get type => 'mated';
  @override
  Map<String, Object?> fieldsToJson() => {
    'name': name,
    'sire': sire,
    'checkOn': checkOn.value,
    'fee': fee,
  };
}

final class PregnancyConfirmed extends DomainEvent {
  const PregnancyConfirmed(
    super.day, {
    super.owner,
    super.camel,
    required this.name,
    required this.sire,
    required this.due,
  });
  final String name;
  final String sire;
  final GameDay due;
  @override
  String get type => 'pregnancyConfirmed';
  @override
  Map<String, Object?> fieldsToJson() => {
    'name': name,
    'sire': sire,
    'due': due.value,
  };
}

final class PregnancyFailed extends DomainEvent {
  const PregnancyFailed(
    super.day, {
    super.owner,
    super.camel,
    required this.name,
    required this.sire,
  });
  final String name;
  final String sire;
  @override
  String get type => 'pregnancyFailed';
  @override
  Map<String, Object?> fieldsToJson() => {'name': name, 'sire': sire};
}

final class CalfBorn extends DomainEvent {
  const CalfBorn(
    super.day, {
    super.owner,
    super.camel,
    required this.dam,
    required this.sire,
    required this.name,
    required this.sex,
  });
  final String dam;
  final String sire;
  final String name;
  final Sex sex;
  @override
  String get type => 'calfBorn';
  @override
  Map<String, Object?> fieldsToJson() => {
    'dam': dam,
    'sire': sire,
    'name': name,
    'sex': sex.name,
  };
}

final class CalfLost extends DomainEvent {
  const CalfLost(super.day, {super.owner, super.camel, required this.name});
  final String name;
  @override
  String get type => 'calfLost';
  @override
  Map<String, Object?> fieldsToJson() => {'name': name};
}

final class SeasonPlanned extends DomainEvent {
  const SeasonPlanned(
    super.day, {
    super.owner,
    super.camel,
    required this.year,
  });
  final int year;
  @override
  String get type => 'seasonPlanned';
  @override
  Map<String, Object?> fieldsToJson() => {'year': year};
}

final class RegistrationOpened extends DomainEvent {
  const RegistrationOpened(
    super.day, {
    super.owner,
    super.camel,
    required this.festival,
    required this.name,
    required this.tier,
    required this.judgedOn,
  });
  final FestivalId festival;
  final String name;
  final FestivalTier tier;
  final GameDay judgedOn;
  @override
  String get type => 'registrationOpened';
  @override
  Map<String, Object?> fieldsToJson() => {
    'festival': festival.value,
    'name': name,
    'tier': tier.name,
    'judgedOn': judgedOn.value,
  };
}

final class RegistrationClosingSoon extends DomainEvent {
  const RegistrationClosingSoon(
    super.day, {
    super.owner,
    super.camel,
    required this.festival,
    required this.name,
  });
  final FestivalId festival;
  final String name;
  @override
  String get type => 'registrationClosingSoon';
  @override
  Map<String, Object?> fieldsToJson() => {
    'festival': festival.value,
    'name': name,
  };
}

final class Entered extends DomainEvent {
  const Entered(
    super.day, {
    super.owner,
    super.camel,
    required this.name,
    required this.festival,
    required this.round,
    this.head = 1,
    this.fee = 0,
  });
  final String name;
  final String festival;
  final RoundId round;

  /// Camels in the entry (a group's head).
  final int head;

  /// A late entry's fee (0 for one in time).
  final int fee;
  @override
  String get type => 'entered';
  @override
  Map<String, Object?> fieldsToJson() => {
    'name': name,
    'festival': festival,
    'round': round.value,
    'head': head,
    'fee': fee,
  };
}

/// The secret treatment man's [count] unread messages read.
final class MessagesRead extends DomainEvent {
  const MessagesRead(
    super.day, {
    super.owner,
    super.camel,
    required this.count,
  });
  final int count;
  @override
  String get type => 'messagesRead';
  @override
  Map<String, Object?> fieldsToJson() => {'count': count};
}

/// [count] of the player's untold findings told by the phone.
final class FindingsTold extends DomainEvent {
  const FindingsTold(
    super.day, {
    super.owner,
    super.camel,
    required this.count,
  });
  final int count;
  @override
  String get type => 'findingsTold';
  @override
  Map<String, Object?> fieldsToJson() => {'count': count};
}

final class Withdrawn extends DomainEvent {
  const Withdrawn(
    super.day, {
    super.owner,
    super.camel,
    required this.festival,
  });
  final String festival;
  @override
  String get type => 'withdrawn';
  @override
  Map<String, Object?> fieldsToJson() => {'festival': festival};
}

final class DisqualifiedSick extends DomainEvent {
  const DisqualifiedSick(
    super.day, {
    super.owner,
    super.camel,
    required this.name,
    required this.festival,
  });
  final String name;
  final String festival;
  @override
  String get type => 'disqualifiedSick';
  @override
  Map<String, Object?> fieldsToJson() => {'name': name, 'festival': festival};
}

final class Placed extends DomainEvent {
  const Placed(
    super.day, {
    super.owner,
    super.camel,
    required this.name,
    required this.festival,
    required this.round,
    required this.rank,
    required this.of,
    required this.score,
    required this.prize,
  });
  final String name;
  final String festival;
  final RoundId round;
  final int rank;
  final int of;
  final double score;
  final int prize;
  @override
  String get type => 'placed';
  @override
  Map<String, Object?> fieldsToJson() => {
    'name': name,
    'festival': festival,
    'round': round.value,
    'rank': rank,
    'of': of,
    'score': score,
    'prize': prize,
  };
}

final class FestivalSummary extends DomainEvent {
  const FestivalSummary(
    super.day, {
    super.owner,
    super.camel,
    required this.festival,
    required this.prizes,
  });
  final String festival;
  final int prizes;
  @override
  String get type => 'festivalSummary';
  @override
  Map<String, Object?> fieldsToJson() => {
    'festival': festival,
    'prizes': prizes,
  };
}

/// A stage of the festival day removed one of the owner's entries ([camel]
/// is the entry's first camel).
final class EntryRemoved extends DomainEvent {
  const EntryRemoved(
    super.day, {
    super.owner,
    super.camel,
    required this.name,
    required this.festival,
    required this.round,
    required this.stage,
    required this.reason,
  });
  final String name;
  final String festival;
  final RoundId round;
  final Stage stage;
  final RemovalReason reason;
  @override
  String get type => 'entryRemoved';
  @override
  Map<String, Object?> fieldsToJson() => {
    'name': name,
    'festival': festival,
    'round': round.value,
    'stage': stage.name,
    'reason': reason.name,
  };
}

/// الفحل وإنتاجه judged: its places come on [announceOn], once the DNA tests
/// are back.
final class ResultsPending extends DomainEvent {
  const ResultsPending(
    super.day, {
    super.owner,
    super.camel,
    required this.festival,
    required this.round,
    required this.announceOn,
  });
  final String festival;
  final RoundId round;
  final GameDay announceOn;
  @override
  String get type => 'resultsPending';
  @override
  Map<String, Object?> fieldsToJson() => {
    'festival': festival,
    'round': round.value,
    'announceOn': announceOn.value,
  };
}

/// The owner had a camel secretly treated (his own news only).
final class Tampered extends DomainEvent {
  const Tampered(
    super.day, {
    super.owner,
    super.camel,
    required this.name,
    required this.kind,
    required this.strength,
    required this.price,
  });
  final String name;
  final TamperKind kind;
  final int strength;
  final int price;
  @override
  String get type => 'tampered';
  @override
  Map<String, Object?> fieldsToJson() => {
    'name': name,
    'kind': kind.name,
    'strength': strength,
    'price': price,
  };
}

/// A treatment on one of the owner's camels was found: at a festival
/// ([festival], [stage]; with the ban through [bannedThrough]) or outside
/// one, in the market or by the vet ([festival] null).
final class TamperingFound extends DomainEvent {
  const TamperingFound(
    super.day, {
    super.owner,
    super.camel,
    required this.name,
    required this.kind,
    required this.festival,
    required this.stage,
    required this.fine,
    required this.bannedThrough,
  });
  final String name;
  final TamperKind kind;
  final String? festival;
  final Stage? stage;
  final int fine;
  final int? bannedThrough;
  @override
  String get type => 'tamperingFound';
  @override
  Map<String, Object?> fieldsToJson() => {
    'name': name,
    'kind': kind.name,
    'festival': festival,
    'stage': stage?.name,
    'fine': fine,
    'bannedThrough': bannedThrough,
  };
}

/// Public news: an owner's camel found treated (GDD 7.1: the news reaches
/// the rivals; the rivals' own cases come this way too).
final class CheatNews extends DomainEvent {
  const CheatNews(
    super.day, {
    super.owner,
    super.camel,
    required this.ownerName,
    required this.name,
    required this.kind,
    required this.festival,
    required this.fine,
  });
  final String ownerName;
  final String name;
  final TamperKind kind;
  final String? festival;
  final int fine;
  @override
  String get type => 'cheatNews';
  @override
  Map<String, Object?> fieldsToJson() => {
    'ownerName': ownerName,
    'name': name,
    'kind': kind.name,
    'festival': festival,
    'fine': fine,
  };
}

/// Public news at a festival's end: how many treatments its committees
/// found and the fines (as the real festivals report, GDD 7.1).
final class FestivalIntegrity extends DomainEvent {
  const FestivalIntegrity(
    super.day, {
    super.owner,
    super.camel,
    required this.festival,
    required this.cases,
    required this.fines,
  });
  final String festival;
  final int cases;
  final int fines;
  @override
  String get type => 'festivalIntegrity';
  @override
  Map<String, Object?> fieldsToJson() => {
    'festival': festival,
    'cases': cases,
    'fines': fines,
  };
}

/// The vet looked at a camel for sale for the owner: the treatments he found
/// in her (none, or what he found; never what he missed).
final class ListingChecked extends DomainEvent {
  const ListingChecked(
    super.day, {
    super.owner,
    super.camel,
    required this.name,
    required this.listing,
    required this.found,
  });
  final String name;
  final ListingId listing;
  final List<TamperKind> found;
  @override
  String get type => 'listingChecked';
  @override
  Map<String, Object?> fieldsToJson() => {
    'name': name,
    'listing': listing.value,
    'found': [for (final k in found) k.name],
  };
}

/// The buyer or the broker examined the owner's camel before paying and
/// found [kinds] in her: the sale is off, and [fine] taken (the owner, 13
/// Nov 2026).
final class SaleRefused extends DomainEvent {
  const SaleRefused(
    super.day, {
    super.owner,
    super.camel,
    required this.name,
    required this.buyer,
    required this.kinds,
    required this.fine,
  });
  final String name;
  final String buyer;
  final List<TamperKind> kinds;
  final int fine;
  @override
  String get type => 'saleRefused';
  @override
  Map<String, Object?> fieldsToJson() => {
    'name': name,
    'buyer': buyer,
    'kinds': [for (final k in kinds) k.name],
    'fine': fine,
  };
}
