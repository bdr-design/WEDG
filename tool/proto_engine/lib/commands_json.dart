import 'package:marah_domain/marah_domain.dart';

/// The commands the prototype's screens send, from JSON (`{"type": ..., ...}`;
/// the actor is always the player). Unknown or malformed ones are null.
Command? commandFromJson(OwnerId me, Map<String, Object?> j) {
  try {
    return switch (j['type']) {
      'orderSupply' => OrderSupply(
        me,
        Supply.values.byName(_str(j['supply'])),
        _int(j['units']),
      ),
      'setFeedPlan' => SetFeedPlan(me, FeedPlan.values.byName(_str(j['plan']))),
      'buyListing' => BuyListing(me, ListingId(_str(j['listing']))),
      'bargain' => Bargain(
        me,
        ListingId(_str(j['listing'])),
        _int(j['amount']),
      ),
      'listForSale' => ListForSale(
        me,
        CamelId(_str(j['camel'])),
        _int(j['askPrice']),
      ),
      'cancelListing' => CancelListing(me, ListingId(_str(j['listing']))),
      'acceptOffer' => AcceptOffer(me, OfferId(_str(j['offer']))),
      'declineOffer' => DeclineOffer(me, OfferId(_str(j['offer']))),
      'quickSale' => QuickSale(me, CamelId(_str(j['camel']))),
      'mateWithOwnBull' => MateWithOwnBull(
        me,
        CamelId(_str(j['female'])),
        CamelId(_str(j['bull'])),
      ),
      'mateWithStud' => MateWithStud(
        me,
        CamelId(_str(j['female'])),
        StudId(_str(j['stud'])),
      ),
      'treat' => Treat(me, CamelId(_str(j['camel']))),
      'renameCamel' => RenameCamel(
        me,
        CamelId(_str(j['camel'])),
        _str(j['name']),
      ),
      'setShepherds' => SetShepherds(me, _int(j['count'])),
      'expandFarm' => ExpandFarm(me),
      'enterRound' => EnterRound(
        me,
        FestivalId(_str(j['festival'])),
        RoundId(_str(j['round'])),
        CamelId(_str(j['camel'])),
      ),
      'withdrawEntry' => WithdrawEntry(
        me,
        FestivalId(_str(j['festival'])),
        RoundId(_str(j['round'])),
        CamelId(_str(j['camel'])),
      ),
      _ => null,
    };
  } on Object {
    return null;
  }
}

/// A whole number, or a throw (2.5 units is a malformed command, not 2).
int _int(Object? v) {
  final n = v! as num;
  if (n != n.roundToDouble()) throw FormatException('not whole: $n');
  return n.toInt();
}

String _str(Object? v) => v! as String;

/// The other way, for tests and tools. Its switch is exhaustive over the
/// sealed [Command], so a new command does not compile until it is given a
/// JSON form here and in [commandFromJson] (the round-trip test checks both).
Map<String, Object?> commandToJson(Command c) => switch (c) {
  OrderSupply(:final supply, :final units) => {
    'type': 'orderSupply',
    'supply': supply.name,
    'units': units,
  },
  SetFeedPlan(:final plan) => {'type': 'setFeedPlan', 'plan': plan.name},
  BuyListing(:final listing) => {
    'type': 'buyListing',
    'listing': listing.value,
  },
  Bargain(:final listing, :final amount) => {
    'type': 'bargain',
    'listing': listing.value,
    'amount': amount,
  },
  ListForSale(:final camel, :final askPrice) => {
    'type': 'listForSale',
    'camel': camel.value,
    'askPrice': askPrice,
  },
  CancelListing(:final listing) => {
    'type': 'cancelListing',
    'listing': listing.value,
  },
  AcceptOffer(:final offer) => {'type': 'acceptOffer', 'offer': offer.value},
  DeclineOffer(:final offer) => {'type': 'declineOffer', 'offer': offer.value},
  QuickSale(:final camel) => {'type': 'quickSale', 'camel': camel.value},
  MateWithOwnBull(:final female, :final bull) => {
    'type': 'mateWithOwnBull',
    'female': female.value,
    'bull': bull.value,
  },
  MateWithStud(:final female, :final stud) => {
    'type': 'mateWithStud',
    'female': female.value,
    'stud': stud.value,
  },
  Treat(:final camel) => {'type': 'treat', 'camel': camel.value},
  RenameCamel(:final camel, :final name) => {
    'type': 'renameCamel',
    'camel': camel.value,
    'name': name,
  },
  SetShepherds(:final count) => {'type': 'setShepherds', 'count': count},
  ExpandFarm() => {'type': 'expandFarm'},
  EnterRound(:final festival, :final round, :final camel) => {
    'type': 'enterRound',
    'festival': festival.value,
    'round': round.value,
    'camel': camel.value,
  },
  WithdrawEntry(:final festival, :final round, :final camel) => {
    'type': 'withdrawEntry',
    'festival': festival.value,
    'round': round.value,
    'camel': camel.value,
  },
};
