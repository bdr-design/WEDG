import '../catalog/region.dart';
import '../common/ids.dart';
import '../common/money.dart';
import '../common/time.dart';

/// Another camel owner in the world (computer-run today; real players later
/// are owners too).
class Owner {
  const Owner({required this.id, required this.name, required this.region});

  final OwnerId id;
  final String name;
  final Region region;

  Map<String, Object?> toJson() => {
    'id': id.value,
    'name': name,
    'region': region.name,
  };

  static Owner fromJson(Map<String, Object?> j) => Owner(
    id: OwnerId(j['id']! as String),
    name: j['name']! as String,
    region: Region.values.byName(j['region']! as String),
  );
}

/// A camel offered at a regional market (الحراج).
class Listing {
  Listing({
    required this.id,
    required this.camelId,
    required this.sellerId,
    required this.region,
    required this.askPrice,
    required this.reservePrice,
    required this.listedOn,
    required this.expiresOn,
    Map<String, int>? bargains,
  }) : bargains = bargains ?? {};

  final ListingId id;
  final CamelId camelId;
  final OwnerId sellerId;
  final Region region;
  Riyal askPrice;

  /// The lowest price the seller accepts. Hidden from buyers.
  final Riyal reservePrice;
  final GameDay listedOn;
  final GameDay expiresOn;

  /// Bargaining attempts per buyer (owner id -> count).
  final Map<String, int> bargains;

  Map<String, Object?> toJson() => {
    'id': id.value,
    'camel': camelId.value,
    'seller': sellerId.value,
    'region': region.name,
    'ask': askPrice.value,
    'reserve': reservePrice.value,
    'listedOn': listedOn.value,
    'expiresOn': expiresOn.value,
    'bargains': bargains,
  };

  static Listing fromJson(Map<String, Object?> j) => Listing(
    id: ListingId(j['id']! as String),
    camelId: CamelId(j['camel']! as String),
    sellerId: OwnerId(j['seller']! as String),
    region: Region.values.byName(j['region']! as String),
    askPrice: Riyal(j['ask']! as int),
    reservePrice: Riyal(j['reserve']! as int),
    listedOn: GameDay(j['listedOn']! as int),
    expiresOn: GameDay(j['expiresOn']! as int),
    bargains: (j['bargains']! as Map<String, Object?>).map(
      (k, v) => MapEntry(k, v! as int),
    ),
  );
}

/// A buyer's offer on a listing (سوم).
class Offer {
  const Offer({
    required this.id,
    required this.listingId,
    required this.buyerId,
    required this.amount,
    required this.madeOn,
    required this.expiresOn,
  });

  final OfferId id;
  final ListingId listingId;
  final OwnerId buyerId;
  final Riyal amount;
  final GameDay madeOn;
  final GameDay expiresOn;

  Map<String, Object?> toJson() => {
    'id': id.value,
    'listing': listingId.value,
    'buyer': buyerId.value,
    'amount': amount.value,
    'madeOn': madeOn.value,
    'expiresOn': expiresOn.value,
  };

  static Offer fromJson(Map<String, Object?> j) => Offer(
    id: OfferId(j['id']! as String),
    listingId: ListingId(j['listing']! as String),
    buyerId: OwnerId(j['buyer']! as String),
    amount: Riyal(j['amount']! as int),
    madeOn: GameDay(j['madeOn']! as int),
    expiresOn: GameDay(j['expiresOn']! as int),
  );
}

/// A bull offered for covering for a fee (فحل للتلقيح).
class StudOffer {
  const StudOffer({
    required this.id,
    required this.camelId,
    required this.ownerId,
    required this.region,
    required this.fee,
    required this.until,
  });

  final StudId id;
  final CamelId camelId;
  final OwnerId ownerId;
  final Region region;
  final Riyal fee;
  final GameDay until;

  Map<String, Object?> toJson() => {
    'id': id.value,
    'camel': camelId.value,
    'owner': ownerId.value,
    'region': region.name,
    'fee': fee.value,
    'until': until.value,
  };

  static StudOffer fromJson(Map<String, Object?> j) => StudOffer(
    id: StudId(j['id']! as String),
    camelId: CamelId(j['camel']! as String),
    ownerId: OwnerId(j['owner']! as String),
    region: Region.values.byName(j['region']! as String),
    fee: Riyal(j['fee']! as int),
    until: GameDay(j['until']! as int),
  );
}
