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
        tanker: j['tanker'] == null
            ? Tanker.large
            : Tanker.values.byName(_str(j['tanker'])),
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
        declared: _bool(j['declared']),
      ),
      'cancelListing' => CancelListing(me, ListingId(_str(j['listing']))),
      'acceptOffer' => AcceptOffer(me, OfferId(_str(j['offer']))),
      'declineOffer' => DeclineOffer(me, OfferId(_str(j['offer']))),
      'quickSale' => QuickSale(
        me,
        CamelId(_str(j['camel'])),
        declared: _bool(j['declared']),
      ),
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
      'buildFacility' => BuildFacility(
        me,
        Facility.values.byName(_str(j['facility'])),
      ),
      'setCalfShare' => SetCalfShare(
        me,
        CalfShare.values.byName(_str(j['share'])),
      ),
      'enterRound' => EnterRound(
        me,
        FestivalId(_str(j['festival'])),
        RoundId(_str(j['round'])),
        [for (final c in j['camels']! as List<Object?>) CamelId(_str(c))],
      ),
      'withdrawEntry' => WithdrawEntry(
        me,
        FestivalId(_str(j['festival'])),
        RoundId(_str(j['round'])),
        CamelId(_str(j['camel'])),
      ),
      'checkListing' => CheckListing(me, ListingId(_str(j['listing']))),
      'tamper' => Tamper(
        me,
        CamelId(_str(j['camel'])),
        TamperKind.values.byName(_str(j['kind'])),
        _int(j['strength']),
      ),
      'readMessages' => ReadMessages(me),
      'markFindingsTold' => MarkFindingsTold(me, _int(j['count'])),
      // (sent only by the test meter, #fps: TestMoney)
      'setTestMoney' => SetTestMoney(me, on: _bool(j['on'])),
      _ => null,
    };
  } on Object {
    return null;
  }
}

/// A whole number JavaScript holds exactly, or a throw: 2.5 units is a
/// malformed command, not 2, and 1e300 riyals is not a price (the VM would
/// clamp it, JavaScript would keep a double the VM cannot read back).
int _int(Object? v) {
  final n = v! as num;
  if (n != n.roundToDouble() || n.abs() > 9007199254740991) {
    throw FormatException('not a whole number in range: $n');
  }
  return n.toInt();
}

String _str(Object? v) => v! as String;

/// An optional flag: absent is false; anything but a bool is malformed.
bool _bool(Object? v) => v == null ? false : v as bool;

/// The other way, for tests and tools. Its switch is exhaustive over the
/// sealed [Command], so a new command does not compile until it is given a
/// JSON form here and in [commandFromJson] (the round-trip test checks both).
Map<String, Object?> commandToJson(Command c) => switch (c) {
  OrderSupply(:final supply, :final units, :final tanker) => {
    'type': 'orderSupply',
    'supply': supply.name,
    'units': units,
    if (supply == Supply.water) 'tanker': tanker.name,
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
  ListForSale(:final camel, :final askPrice, :final declared) => {
    'type': 'listForSale',
    'camel': camel.value,
    'askPrice': askPrice,
    if (declared) 'declared': true,
  },
  CancelListing(:final listing) => {
    'type': 'cancelListing',
    'listing': listing.value,
  },
  AcceptOffer(:final offer) => {'type': 'acceptOffer', 'offer': offer.value},
  DeclineOffer(:final offer) => {'type': 'declineOffer', 'offer': offer.value},
  QuickSale(:final camel, :final declared) => {
    'type': 'quickSale',
    'camel': camel.value,
    if (declared) 'declared': true,
  },
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
  BuildFacility(:final facility) => {
    'type': 'buildFacility',
    'facility': facility.name,
  },
  SetCalfShare(:final share) => {'type': 'setCalfShare', 'share': share.name},
  EnterRound(:final festival, :final round, :final camels) => {
    'type': 'enterRound',
    'festival': festival.value,
    'round': round.value,
    'camels': [for (final c in camels) c.value],
  },
  WithdrawEntry(:final festival, :final round, :final camel) => {
    'type': 'withdrawEntry',
    'festival': festival.value,
    'round': round.value,
    'camel': camel.value,
  },
  CheckListing(:final listing) => {
    'type': 'checkListing',
    'listing': listing.value,
  },
  Tamper(:final camel, :final kind, :final strength) => {
    'type': 'tamper',
    'camel': camel.value,
    'kind': kind.name,
    'strength': strength,
  },
  ReadMessages() => {'type': 'readMessages'},
  MarkFindingsTold(:final count) => {
    'type': 'markFindingsTold',
    'count': count,
  },
  SetTestMoney(:final on) => {'type': 'setTestMoney', 'on': on},
};
