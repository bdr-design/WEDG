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
  final List<CamelCard> herd;
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
