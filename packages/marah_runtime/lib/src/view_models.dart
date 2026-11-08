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
    required this.expansionCost,
  });

  final String name;
  final Region region;
  final int capacity;
  final int shepherds;
  final int shepherdsNeeded;
  final FeedPlan feedPlan;
  final int dailyFeed;
  final int monthlyWages;
  final int expansionCost;

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
      other.expansionCost == expansionCost;

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
    expansionCost,
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
    required this.farm,
    required this.herd,
    required this.herdTop,
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
  final FarmSummary farm;

  /// Counts over the whole herd; screens page through it with `herdPage`.
  final HerdSummary herd;

  /// The best few camels by look, for the farm screen.
  final List<CamelCard> herdTop;

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
    Object.hashAll(byCategory.entries.map((e) => Object.hash(e.key, e.value))),
    Object.hashAll(byAge.entries.map((e) => Object.hash(e.key, e.value))),
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
