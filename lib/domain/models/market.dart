import 'region.dart';

/// Another camel owner in the world (a seller, buyer, rival or stud owner).
class Owner {
  const Owner({required this.id, required this.name, required this.region});

  final String id;
  final String name;
  final Region region;

  Map<String, dynamic> toJson() => {'id': id, 'n': name, 'r': region.name};

  factory Owner.fromJson(Map<String, dynamic> j) => Owner(
        id: j['id'] as String,
        name: j['n'] as String,
        region: Region.byName(j['r'] as String),
      );
}

/// A camel offered for sale at a regional market (حراج / سوق الإبل).
class Listing {
  Listing({
    required this.id,
    required this.camelId,
    required this.sellerId,
    required this.sellerName,
    required this.region,
    required this.askPrice,
    required this.reservePrice,
    required this.listedDay,
    required this.expiresDay,
    this.bargains = 0,
  });

  final String id;
  final String camelId;
  final String sellerId;
  final String sellerName;
  final Region region;

  /// Price the seller asks (السوم المطلوب).
  int askPrice;

  /// Lowest price the seller will take. Hidden from the player.
  final int reservePrice;
  final int listedDay;
  final int expiresDay;

  /// How many times the player has bargained on this camel. Sellers lose
  /// patience after a few low offers.
  int bargains;

  Map<String, dynamic> toJson() => {
        'id': id,
        'cid': camelId,
        'sid': sellerId,
        'sn': sellerName,
        'r': region.name,
        'ask': askPrice,
        'res': reservePrice,
        'ld': listedDay,
        'xd': expiresDay,
        'b': bargains,
      };

  factory Listing.fromJson(Map<String, dynamic> j) => Listing(
        id: j['id'] as String,
        camelId: j['cid'] as String,
        sellerId: j['sid'] as String,
        sellerName: j['sn'] as String,
        region: Region.byName(j['r'] as String),
        askPrice: j['ask'] as int,
        reservePrice: j['res'] as int,
        listedDay: j['ld'] as int,
        expiresDay: j['xd'] as int,
        bargains: j['b'] as int,
      );
}

/// A buyer's offer on one of the player's listings (سوم من مشتري).
class BuyerOffer {
  BuyerOffer({
    required this.id,
    required this.listingId,
    required this.buyerName,
    required this.buyerRegion,
    required this.amount,
    required this.day,
    required this.expiresDay,
  });

  final String id;
  final String listingId;
  final String buyerName;
  final Region buyerRegion;
  final int amount;
  final int day;
  final int expiresDay;

  Map<String, dynamic> toJson() => {
        'id': id,
        'lid': listingId,
        'bn': buyerName,
        'br': buyerRegion.name,
        'a': amount,
        'd': day,
        'x': expiresDay,
      };

  factory BuyerOffer.fromJson(Map<String, dynamic> j) => BuyerOffer(
        id: j['id'] as String,
        listingId: j['lid'] as String,
        buyerName: j['bn'] as String,
        buyerRegion: Region.byName(j['br'] as String),
        amount: j['a'] as int,
        day: j['d'] as int,
        expiresDay: j['x'] as int,
      );
}

/// A stud bull another owner offers for covering (فحل للتلقيح) for a fee.
class StudOffer {
  StudOffer({
    required this.id,
    required this.camelId,
    required this.ownerName,
    required this.region,
    required this.fee,
    required this.untilDay,
  });

  final String id;
  final String camelId;
  final String ownerName;
  final Region region;
  final int fee;
  final int untilDay;

  Map<String, dynamic> toJson() => {
        'id': id,
        'cid': camelId,
        'on': ownerName,
        'r': region.name,
        'fee': fee,
        'u': untilDay,
      };

  factory StudOffer.fromJson(Map<String, dynamic> j) => StudOffer(
        id: j['id'] as String,
        camelId: j['cid'] as String,
        ownerName: j['on'] as String,
        region: Region.byName(j['r'] as String),
        fee: j['fee'] as int,
        untilDay: j['u'] as int,
      );
}
