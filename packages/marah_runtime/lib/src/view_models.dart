import 'package:marah_domain/marah_domain.dart';

/// Screen-ready data, built off the UI thread. Every class here is
/// immutable and made only of values, so it can cross isolates cheaply and
/// the UI never computes anything itself.
///
/// These are the contracts between the engine and the screens. When the
/// approved design needs more, add fields here, not computations in widgets.

class CamelCard {
  const CamelCard({
    required this.id,
    required this.name,
    required this.sex,
    required this.category,
    required this.ageClass,
    required this.ageDays,
    required this.quality,
    required this.estimateLow,
    required this.estimateHigh,
    required this.condition,
    required this.health,
    required this.illness,
    required this.pregnant,
    required this.dueOn,
    required this.awaitingCheck,
    required this.listed,
    required this.entered,
    required this.bestRank,
    required this.crossbred,
  });

  final CamelId id;
  final String name;
  final Sex sex;
  final ColorCategory category;
  final AgeClass ageClass;
  final int ageDays;

  /// Overall look 0–100.
  final double quality;
  final int estimateLow;
  final int estimateHigh;
  final double condition;
  final HealthStatus health;
  final Illness? illness;
  final bool pregnant;
  final GameDay? dueOn;
  final bool awaitingCheck;
  final bool listed;
  final bool entered;
  final int? bestRank;
  final bool crossbred;

  @override
  bool operator ==(Object other) =>
      other is CamelCard &&
      other.id == id &&
      other.name == name &&
      other.sex == sex &&
      other.category == category &&
      other.ageClass == ageClass &&
      other.ageDays == ageDays &&
      other.quality == quality &&
      other.estimateLow == estimateLow &&
      other.estimateHigh == estimateHigh &&
      other.condition == condition &&
      other.health == health &&
      other.illness == illness &&
      other.pregnant == pregnant &&
      other.dueOn == dueOn &&
      other.awaitingCheck == awaitingCheck &&
      other.listed == listed &&
      other.entered == entered &&
      other.bestRank == bestRank &&
      other.crossbred == crossbred;

  @override
  int get hashCode => Object.hashAll([
    id,
    name,
    sex,
    category,
    ageClass,
    ageDays,
    quality,
    estimateLow,
    estimateHigh,
    condition,
    health,
    illness,
    pregnant,
    dueOn,
    awaitingCheck,
    listed,
    entered,
    bestRank,
    crossbred,
  ]);
}

class OfferCard {
  const OfferCard({
    required this.id,
    required this.buyerName,
    required this.amount,
    required this.expiresOn,
  });

  final OfferId id;
  final String buyerName;
  final int amount;
  final GameDay expiresOn;

  @override
  bool operator ==(Object other) =>
      other is OfferCard &&
      other.id == id &&
      other.buyerName == buyerName &&
      other.amount == amount &&
      other.expiresOn == expiresOn;

  @override
  int get hashCode => Object.hashAll([id, buyerName, amount, expiresOn]);
}

class ListingCard {
  const ListingCard({
    required this.id,
    required this.camel,
    required this.askPrice,
    required this.region,
    required this.sellerName,
    required this.transport,
    required this.listedOn,
    required this.expiresOn,
    required this.bargainsLeft,
    required this.isMine,
    required this.offers,
  });

  final ListingId id;
  final CamelCard camel;
  final int askPrice;
  final Region region;
  final String sellerName;

  /// Trucking to the player's farm.
  final int transport;
  final GameDay listedOn;
  final GameDay expiresOn;
  final int bargainsLeft;
  final bool isMine;

  /// Buyers' offers (only on the player's own listings).
  final List<OfferCard> offers;

  @override
  bool operator ==(Object other) =>
      other is ListingCard &&
      other.id == id &&
      other.camel == camel &&
      other.askPrice == askPrice &&
      other.region == region &&
      other.sellerName == sellerName &&
      other.transport == transport &&
      other.listedOn == listedOn &&
      other.expiresOn == expiresOn &&
      other.bargainsLeft == bargainsLeft &&
      other.isMine == isMine &&
      _listEquals(other.offers, offers);

  @override
  int get hashCode => Object.hash(
    id,
    camel,
    askPrice,
    region,
    sellerName,
    transport,
    listedOn,
    expiresOn,
    bargainsLeft,
    isMine,
    Object.hashAll(offers),
  );
}

class StudCard {
  const StudCard({
    required this.id,
    required this.bull,
    required this.ownerName,
    required this.region,
    required this.fee,
    required this.transport,
    required this.until,
  });

  final StudId id;
  final CamelCard bull;
  final String ownerName;
  final Region region;
  final int fee;
  final int transport;
  final GameDay until;

  @override
  bool operator ==(Object other) =>
      other is StudCard &&
      other.id == id &&
      other.bull == bull &&
      other.ownerName == ownerName &&
      other.region == region &&
      other.fee == fee &&
      other.transport == transport &&
      other.until == until;

  @override
  int get hashCode =>
      Object.hashAll([id, bull, ownerName, region, fee, transport, until]);
}

class FestivalCard {
  const FestivalCard({
    required this.id,
    required this.name,
    required this.region,
    required this.tier,
    required this.opensOn,
    required this.closesOn,
    required this.judgedOn,
    required this.done,
    required this.rounds,
    required this.myEntries,
    required this.topPrize,
    required this.myBestRank,
    required this.myPrizes,
  });

  final FestivalId id;
  final String name;
  final Region region;
  final FestivalTier tier;
  final GameDay opensOn;
  final GameDay closesOn;
  final GameDay judgedOn;
  final bool done;
  final int rounds;
  final int myEntries;
  final int topPrize;
  final int? myBestRank;
  final int myPrizes;

  @override
  bool operator ==(Object other) =>
      other is FestivalCard &&
      other.id == id &&
      other.name == name &&
      other.region == region &&
      other.tier == tier &&
      other.opensOn == opensOn &&
      other.closesOn == closesOn &&
      other.judgedOn == judgedOn &&
      other.done == done &&
      other.rounds == rounds &&
      other.myEntries == myEntries &&
      other.topPrize == topPrize &&
      other.myBestRank == myBestRank &&
      other.myPrizes == myPrizes;

  @override
  int get hashCode => Object.hashAll([
    id,
    name,
    region,
    tier,
    opensOn,
    closesOn,
    judgedOn,
    done,
    rounds,
    myEntries,
    topPrize,
    myBestRank,
    myPrizes,
  ]);
}

/// One supply in the farm's store or tank (GDD 4.3: feed and water run out
/// and are ordered).
class SupplySummary {
  const SupplySummary({
    required this.supply,
    required this.amount,
    required this.daysLeft,
    required this.room,
    required this.unitPrice,
    required this.unitSize,
    required this.onTheWay,
    required this.onTheWayAmount,
    required this.need,
    required this.short,
  });

  final Supply supply;

  /// Kilograms or litres in store now.
  final int amount;

  /// Whole days it lasts at today's needs (null when nothing is needed).
  final int? daysLeft;

  /// Units that still fit, orders on the way counted.
  final int room;
  final int unitPrice;
  final int unitSize;

  /// Units ordered and not yet delivered.
  final int onTheWay;

  /// Kilograms or litres on their way (tankers of two sizes).
  final int onTheWayAmount;

  /// The herd's need a day now (kg or L).
  final double need;

  /// It did not cover the day's need.
  final bool short;

  @override
  bool operator ==(Object other) =>
      other is SupplySummary &&
      other.supply == supply &&
      other.amount == amount &&
      other.daysLeft == daysLeft &&
      other.room == room &&
      other.unitPrice == unitPrice &&
      other.unitSize == unitSize &&
      other.onTheWay == onTheWay &&
      other.onTheWayAmount == onTheWayAmount &&
      other.need == need &&
      other.short == short;

  @override
  int get hashCode => Object.hash(
    supply,
    amount,
    daysLeft,
    room,
    unitPrice,
    unitSize,
    onTheWay,
    onTheWayAmount,
    need,
    short,
  );
}

/// A ration the player can choose: what it feeds, what it costs the herd a
/// day, and the body condition it brings the herd to with good care.
class RationSummary {
  const RationSummary({
    required this.plan,
    required this.dryMatterKg,
    required this.asFedKg,
    required this.barleyShare,
    required this.costPerDay,
    required this.conditionTarget,
  });

  final FeedPlan plan;
  final double dryMatterKg;

  /// The feed a grown head eats a day, as delivered (kg).
  final double asFedKg;
  final double barleyShare;
  final int costPerDay;
  final int conditionTarget;

  @override
  bool operator ==(Object other) =>
      other is RationSummary &&
      other.plan == plan &&
      other.dryMatterKg == dryMatterKg &&
      other.asFedKg == asFedKg &&
      other.barleyShare == barleyShare &&
      other.costPerDay == costPerDay &&
      other.conditionTarget == conditionTarget;

  @override
  int get hashCode => Object.hash(
    plan,
    dryMatterKg,
    asFedKg,
    barleyShare,
    costPerDay,
    conditionTarget,
  );
}

/// A water tanker the farm can order (the owner, 12 Nov 2026: a 19 t and a
/// 6 t), and how many fit in the tank now.
class TankerSummary {
  const TankerSummary({
    required this.tanker,
    required this.litres,
    required this.price,
    required this.room,
  });

  final Tanker tanker;
  final int litres;
  final int price;

  /// Loads that fit, orders on the way counted.
  final int room;

  @override
  bool operator ==(Object other) =>
      other is TankerSummary &&
      other.tanker == tanker &&
      other.litres == litres &&
      other.price == price &&
      other.room == room;

  @override
  int get hashCode => Object.hash(tanker, litres, price, room);
}

/// A facility the farm can build (the owner, 13 Nov 2026), how many it has
/// and is building, and why it cannot be built now (a [DomainError] code, or
/// null).
class FacilitySummary {
  const FacilitySummary({
    required this.facility,
    required this.price,
    required this.has,
    required this.most,
    required this.building,
    required this.doneOn,
    required this.cannot,
  });

  final Facility facility;
  final int price;
  final int has;
  final int most;

  /// How many are being built, and the day the first of them is done.
  final int building;
  final GameDay? doneOn;
  final ErrorCode? cannot;

  @override
  bool operator ==(Object other) =>
      other is FacilitySummary &&
      other.facility == facility &&
      other.price == price &&
      other.has == has &&
      other.most == most &&
      other.building == building &&
      other.doneOn == doneOn &&
      other.cannot == cannot;

  @override
  int get hashCode =>
      Object.hash(facility, price, has, most, building, doneOn, cannot);
}

/// One nursing camel's milk today.
class MilkCamel {
  const MilkCamel({
    required this.id,
    required this.name,
    required this.days,
    required this.calfName,
    required this.litres,
    required this.sold,
  });

  final CamelId id;
  final String name;

  /// Days since she calved.
  final int days;

  /// Her calf while it suckles, or null (sold, dead or weaned: all her milk
  /// is sold).
  final String? calfName;
  final double litres;
  final double sold;

  @override
  bool operator ==(Object other) =>
      other is MilkCamel &&
      other.id == id &&
      other.name == name &&
      other.days == days &&
      other.calfName == calfName &&
      other.litres == litres &&
      other.sold == sold;

  @override
  int get hashCode => Object.hash(id, name, days, calfName, litres, sold);
}

/// The farm's milk (the owner, 13 Nov 2026: sold every day; the player
/// chooses how much the calves keep).
class MilkSummary {
  const MilkSummary({
    required this.camels,
    required this.calfShare,
    required this.price,
    required this.incomeToday,
    required this.thisMonth,
  });

  final List<MilkCamel> camels;
  final CalfShare calfShare;

  /// A litre's price.
  final int price;

  /// What today's milk brought (0 before the day's milking), and this
  /// month's.
  final int incomeToday;
  final int thisMonth;

  @override
  bool operator ==(Object other) =>
      other is MilkSummary &&
      _listEquals(other.camels, camels) &&
      other.calfShare == calfShare &&
      other.price == price &&
      other.incomeToday == incomeToday &&
      other.thisMonth == thisMonth;

  @override
  int get hashCode =>
      Object.hashAll([...camels, calfShare, price, incomeToday, thisMonth]);
}

class FarmSummary {
  const FarmSummary({
    required this.name,
    required this.region,
    required this.capacity,
    required this.shepherds,
    required this.shepherdsNeeded,
    required this.feedPlan,
    required this.dailyFeed,
    required this.monthlyWages,
    required this.supplies,
    required this.storeKg,
    required this.tankL,
    required this.dryDays,
    required this.tankers,
    required this.pastureGreen,
    required this.thirstDays,
    required this.rations,
    required this.facilities,
    required this.milk,
  });

  final String name;
  final Region region;
  final int capacity;
  final int shepherds;
  final int shepherdsNeeded;
  final FeedPlan feedPlan;
  final int dailyFeed;
  final int monthlyWages;

  /// Barley, alfalfa and water, in that order.
  final List<SupplySummary> supplies;
  final int storeKg;
  final int tankL;

  /// Days in a row the herd has gone without enough water.
  final int dryDays;

  /// The tankers, large first.
  final List<TankerSummary> tankers;

  /// Whether the farm's grazing is green, and the days the herd can go
  /// without water now (10 on dry feed in winter, 17 on green pasture).
  final bool pastureGreen;
  final int thirstDays;

  /// The three rations, light first.
  final List<RationSummary> rations;

  /// What the farm can build, in Facility's order.
  final List<FacilitySummary> facilities;
  final MilkSummary milk;

  @override
  bool operator ==(Object other) =>
      other is FarmSummary &&
      other.name == name &&
      other.region == region &&
      other.capacity == capacity &&
      other.shepherds == shepherds &&
      other.shepherdsNeeded == shepherdsNeeded &&
      other.feedPlan == feedPlan &&
      other.dailyFeed == dailyFeed &&
      other.monthlyWages == monthlyWages &&
      _listEquals(other.supplies, supplies) &&
      other.storeKg == storeKg &&
      other.tankL == tankL &&
      other.dryDays == dryDays &&
      _listEquals(other.tankers, tankers) &&
      other.pastureGreen == pastureGreen &&
      other.thirstDays == thirstDays &&
      _listEquals(other.rations, rations) &&
      _listEquals(other.facilities, facilities) &&
      other.milk == milk;

  @override
  int get hashCode => Object.hashAll([
    name,
    region,
    capacity,
    shepherds,
    shepherdsNeeded,
    feedPlan,
    dailyFeed,
    monthlyWages,
    ...supplies,
    storeKg,
    tankL,
    dryDays,
    ...tankers,
    pastureGreen,
    thirstDays,
    ...rations,
    ...facilities,
    milk,
  ]);
}

/// Everything the main screens show, sent after every change.
class PlayerSnapshot {
  const PlayerSnapshot({
    required this.revision,
    required this.today,
    required this.playerId,
    required this.playerName,
    required this.cash,
    required this.herdValue,
    required this.todayNet,
    required this.farm,
    required this.herd,
    required this.herdTop,
    required this.herdSignature,
    required this.sections,
    required this.market,
    required this.myListings,
    required this.studs,
    required this.festivals,
    required this.openOffers,
    required this.breedingSeason,
    required this.recentEvents,
  });

  /// Increases with every snapshot; older ones can be dropped.
  final int revision;
  final GameDay today;

  /// The player's own id: the actor of every command the UI sends.
  final OwnerId playerId;
  final String playerName;
  final int cash;
  final int herdValue;

  /// The money in and out today.
  final int todayNet;
  final FarmSummary farm;

  /// Counts over the whole herd; screens page through it with `herdPage`.
  final HerdSummary herd;

  /// The best few camels by look, for the farm screen.
  final List<CamelCard> herdTop;

  /// Changes whenever any camel in the herd changes (not only the top
  /// few), so herd lists know to refresh their pages.
  final int herdSignature;

  /// What changed since the previous snapshot.
  final SectionRevisions sections;
  final List<ListingCard> market;
  final List<ListingCard> myListings;
  final List<StudCard> studs;
  final List<FestivalCard> festivals;
  final int openOffers;
  final bool breedingSeason;

  /// The player's latest news, newest last.
  final List<DomainEvent> recentEvents;
}

/// One camel in full, requested when its page opens.
class CamelDetail {
  const CamelDetail({
    required this.card,
    required this.isMine,
    required this.looks,
    required this.chip,
    required this.sire,
    required this.dam,
    required this.calvings,
    required this.lastCalvedOn,
    required this.pregnantBy,
    required this.placings,
    required this.purchasePrice,
    required this.listing,
    required this.canSell,
    required this.canBreed,
    required this.quickSalePrice,
  });

  final CamelCard card;
  final bool isMine;

  /// Observed features 0–100.
  final Map<Trait, double> looks;
  final String chip;
  final ParentRef? sire;
  final ParentRef? dam;
  final int calvings;
  final GameDay? lastCalvedOn;
  final String? pregnantBy;
  final List<Placing> placings;
  final int purchasePrice;

  /// The listing this camel is on, if any.
  final ListingCard? listing;

  /// Null when allowed; otherwise why not (for disabled buttons).
  final DomainError? canSell;
  final DomainError? canBreed;
  final int? quickSalePrice;
}

class RoundCard {
  const RoundCard({
    required this.id,
    required this.category,
    required this.sex,
    required this.age,
    required this.prizes,
    required this.rivals,
    required this.myEntries,
    required this.eligible,
    required this.results,
  });

  final RoundId id;
  final ColorCategory category;
  final Sex sex;
  final AgeClass age;
  final List<int> prizes;
  final int rivals;
  final List<CamelCard> myEntries;

  /// The player's camels that may enter this round right now.
  final List<CamelCard> eligible;
  final List<ResultRow>? results;
}

class FestivalDetail {
  const FestivalDetail({
    required this.card,
    required this.rounds,
    required this.distanceKm,
    required this.transportPerHead,
  });

  final FestivalCard card;
  final List<RoundCard> rounds;
  final int distanceKm;

  /// Round trip for one camel.
  final int transportPerHead;
}

bool _listEquals<T>(List<T> a, List<T> b) {
  if (identical(a, b)) return true;
  if (a.length != b.length) return false;
  for (var i = 0; i < a.length; i++) {
    if (a[i] != b[i]) return false;
  }
  return true;
}

/// Counts over the whole herd (cheap to send; the UI pages for details).
class HerdSummary {
  const HerdSummary({
    required this.total,
    required this.females,
    required this.males,
    required this.young,
    required this.pregnant,
    required this.awaitingCheck,
    required this.sick,
    required this.listed,
    required this.entered,
    required this.byCategory,
    required this.byAge,
  });

  final int total;
  final int females;
  final int males;

  /// Under two years old.
  final int young;
  final int pregnant;
  final int awaitingCheck;
  final int sick;
  final int listed;
  final int entered;
  final Map<ColorCategory, int> byCategory;
  final Map<AgeClass, int> byAge;

  @override
  bool operator ==(Object other) =>
      other is HerdSummary &&
      other.total == total &&
      other.females == females &&
      other.males == males &&
      other.young == young &&
      other.pregnant == pregnant &&
      other.awaitingCheck == awaitingCheck &&
      other.sick == sick &&
      other.listed == listed &&
      other.entered == entered &&
      _mapEquals(other.byCategory, byCategory) &&
      _mapEquals(other.byAge, byAge);

  @override
  int get hashCode => Object.hash(
    total,
    females,
    males,
    young,
    pregnant,
    awaitingCheck,
    sick,
    listed,
    entered,
    // Order-independent, matching ==.
    byCategory.entries.fold<int>(0, (h, e) => h ^ Object.hash(e.key, e.value)),
    byAge.entries.fold<int>(0, (h, e) => h ^ Object.hash(e.key, e.value)),
  );
}

bool _mapEquals<K, V>(Map<K, V> a, Map<K, V> b) {
  if (a.length != b.length) return false;
  for (final e in a.entries) {
    if (b[e.key] != e.value) return false;
  }
  return true;
}

enum HerdFilter { all, females, males, young, pregnant, sick, listed }

enum HerdSort { quality, value, oldest, youngest }

/// A page of the player's herd, filtered and sorted in the engine.
class HerdQuery {
  const HerdQuery({
    this.filter = HerdFilter.all,
    this.sort = HerdSort.quality,
    this.category,
    this.offset = 0,
    this.limit = 50,
  });

  final HerdFilter filter;
  final HerdSort sort;
  final ColorCategory? category;
  final int offset;
  final int limit;
}

class HerdPage {
  const HerdPage({
    required this.cards,
    required this.total,
    required this.offset,
  });
  final List<CamelCard> cards;

  /// How many camels match the query in all.
  final int total;
  final int offset;
}

/// Which parts of the snapshot changed. A screen rebuilds only when the
/// revision of the section it shows moves.
class SectionRevisions {
  const SectionRevisions({
    required this.farm,
    required this.herd,
    required this.market,
    required this.studs,
    required this.festivals,
    required this.news,
  });

  final int farm;
  final int herd;
  final int market;
  final int studs;
  final int festivals;
  final int news;
}
