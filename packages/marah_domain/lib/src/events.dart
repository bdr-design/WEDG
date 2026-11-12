import 'catalog/catalog.dart';
import 'catalog/region.dart';
import 'common/ids.dart';
import 'common/time.dart';
import 'model/contest.dart';
import 'model/player.dart';

/// Why a camel died.
/// Why a camel died: an illness, old age, or a young calf's death in its first
/// year (the real first-year loss, Balance.calfDeathFirstYear).
enum DeathCause { illness, age, young }

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
      'shepherdsChanged' => ShepherdsChanged(
        day,
        owner: owner,
        camel: camel,
        count: j['count']! as int,
      ),
      'feedPlanChanged' => FeedPlanChanged(
        day,
        owner: owner,
        camel: camel,
        plan: FeedPlan.values.byName(j['plan']! as String),
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
      final other => throw FormatException('unknown event type $other'),
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
  });
  final String name;
  final String festival;
  final RoundId round;
  @override
  String get type => 'entered';
  @override
  Map<String, Object?> fieldsToJson() => {
    'name': name,
    'festival': festival,
    'round': round.value,
  };
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
