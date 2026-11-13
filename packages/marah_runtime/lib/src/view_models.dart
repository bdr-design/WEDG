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
    this.onTheWay = false,
    this.quickSale,
    this.suckling = false,
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

  /// The player's, bought today: the truck brings it tomorrow.
  final bool onTheWay;

  /// What the broker pays for it now (the player's own camel, free to sell),
  /// else null.
  final int? quickSale;

  /// A calf still suckling its mother: named حوار whatever its age class.
  final bool suckling;

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
      other.crossbred == crossbred &&
      other.onTheWay == onTheWay &&
      other.quickSale == quickSale &&
      other.suckling == suckling;

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
    onTheWay,
    quickSale,
    suckling,
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
    this.knownTreatments = const [],
    this.timesChecked = 0,
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

  /// Treatments in her the player's vet found (never one he was not told).
  final List<TamperKind> knownTreatments;

  /// How many times the player's vet has looked at her.
  final int timesChecked;

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
      _listEquals(other.offers, offers) &&
      _listEquals(other.knownTreatments, knownTreatments) &&
      other.timesChecked == timesChecked;

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

/// A festival on the player's list (GDD 7).
class FestivalCard {
  const FestivalCard({
    required this.id,
    required this.name,
    required this.region,
    required this.tier,
    required this.season,
    required this.opensOn,
    required this.closesOn,
    required this.startsOn,
    required this.endsOn,
    required this.done,
    required this.rounds,
    required this.myEntries,
    required this.topPrize,
    required this.myBestRank,
    required this.myPrizes,
    required this.late,
    required this.bannedThrough,
  });

  final FestivalId id;
  final String name;
  final Region region;
  final FestivalTier tier;
  final int season;
  final GameDay opensOn;

  /// The closing: after it an entry is late, with its fee.
  final GameDay closesOn;
  final GameDay startsOn;
  final GameDay endsOn;
  final bool done;
  final int rounds;
  final int myEntries;
  final int topPrize;
  final int? myBestRank;
  final int myPrizes;
  final bool late;

  /// The player is barred from it, through this season (GDD 7.1).
  final int? bannedThrough;

  @override
  bool operator ==(Object other) =>
      other is FestivalCard &&
      other.id == id &&
      other.name == name &&
      other.region == region &&
      other.tier == tier &&
      other.season == season &&
      other.opensOn == opensOn &&
      other.closesOn == closesOn &&
      other.startsOn == startsOn &&
      other.endsOn == endsOn &&
      other.done == done &&
      other.rounds == rounds &&
      other.myEntries == myEntries &&
      other.topPrize == topPrize &&
      other.myBestRank == myBestRank &&
      other.myPrizes == myPrizes &&
      other.late == late &&
      other.bannedThrough == bannedThrough;

  @override
  int get hashCode => Object.hashAll([
    id,
    name,
    region,
    tier,
    season,
    opensOn,
    closesOn,
    startsOn,
    endsOn,
    done,
    rounds,
    myEntries,
    topPrize,
    myBestRank,
    myPrizes,
    late,
    bannedThrough,
  ]);
}

/// One of the player's own secret treatments and its risk (GDD 7.1): never
/// in anyone else's snapshot.
class TamperingCard {
  const TamperingCard({
    required this.camel,
    required this.camelName,
    required this.kind,
    required this.strength,
    required this.until,
    required this.festivalRisk,
    required this.outsideRisk,
    required this.foundMostlyBy,
    required this.fineIfFound,
  });

  final CamelId camel;
  final String camelName;
  final TamperKind kind;
  final int strength;
  final GameDay until;

  /// The risk a festival finds it, outside one in a month, and who finds
  /// it most: in words, never the odds.
  final RiskBand festivalRisk;
  final RiskBand outsideRisk;
  final Stage foundMostlyBy;
  final int fineIfFound;

  @override
  bool operator ==(Object other) =>
      other is TamperingCard &&
      other.camel == camel &&
      other.camelName == camelName &&
      other.kind == kind &&
      other.strength == strength &&
      other.until == until;

  @override
  int get hashCode => Object.hash(camel, camelName, kind, strength, until);
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
    this.doneOns = const [],
  });

  final Facility facility;
  final int price;
  final int has;
  final int most;

  /// How many are being built, and the day the first of them is done.
  final int building;
  final GameDay? doneOn;
  final ErrorCode? cannot;

  /// The day each one being built is done, in the order they were ordered
  /// (each takes Balance.buildDays from its own order).
  final List<GameDay> doneOns;

  @override
  bool operator ==(Object other) =>
      other is FacilitySummary &&
      other.facility == facility &&
      other.price == price &&
      other.has == has &&
      other.most == most &&
      other.building == building &&
      other.doneOn == doneOn &&
      other.cannot == cannot &&
      _sameDays(other.doneOns, doneOns);

  static bool _sameDays(List<GameDay> a, List<GameDay> b) {
    if (a.length != b.length) return false;
    for (var i = 0; i < a.length; i++) {
      if (a[i] != b[i]) return false;
    }
    return true;
  }

  @override
  int get hashCode => Object.hash(
    facility,
    price,
    has,
    most,
    building,
    doneOn,
    cannot,
    Object.hashAll(doneOns),
  );
}

/// One nursing camel's milk today.
class MilkCamel {
  const MilkCamel({
    required this.id,
    required this.name,
    required this.days,
    required this.calfId,
    required this.calfName,
    required this.litres,
    required this.sold,
    this.calfSex,
  });

  final CamelId id;
  final String name;

  /// Her calf's sex (the words for it: حوارها, حوارتها), or null.
  final Sex? calfSex;

  /// Days since she calved.
  final int days;

  /// Her calf while it suckles, or null (sold, dead or weaned: all her milk
  /// is sold).
  final CamelId? calfId;
  final String? calfName;
  final double litres;
  final double sold;

  @override
  bool operator ==(Object other) =>
      other is MilkCamel &&
      other.id == id &&
      other.name == name &&
      other.days == days &&
      other.calfId == calfId &&
      other.calfSex == calfSex &&
      other.calfName == calfName &&
      other.litres == litres &&
      other.sold == sold;

  @override
  int get hashCode =>
      Object.hash(id, name, days, calfId, calfSex, calfName, litres, sold);
}

/// The farm's milk (the owner, 13 Nov 2026: sold every day; the player
/// chooses how much the calves keep).
class MilkSummary {
  const MilkSummary({
    required this.camels,
    required this.nursing,
    required this.litres,
    required this.sold,
    required this.calfShare,
    required this.price,
    required this.incomeToday,
    required this.thisMonth,
  });

  /// The nursing camels, at most Presenter.milkCount of them (the review:
  /// at 2,442 nursing camels the list was 277 KB of the snapshot); [nursing]
  /// counts them all, and [litres] and [sold] are the whole farm's today.
  final List<MilkCamel> camels;
  final int nursing;
  final double litres;
  final double sold;
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
      other.nursing == nursing &&
      other.litres == litres &&
      other.sold == sold &&
      other.calfShare == calfShare &&
      other.price == price &&
      other.incomeToday == incomeToday &&
      other.thisMonth == thisMonth;

  @override
  int get hashCode => Object.hashAll([
    ...camels,
    nursing,
    litres,
    sold,
    calfShare,
    price,
    incomeToday,
    thisMonth,
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
    required this.onAccount,
    required this.accountLimit,
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

  /// Feed, water and vet treatments bought on account and not yet paid, and
  /// the account's limit (past it the player must sell: the owner, 13 Nov).
  final int onAccount;
  final int accountLimit;

  @override
  bool operator ==(Object other) =>
      other is FarmSummary &&
      other.onAccount == onAccount &&
      other.accountLimit == accountLimit &&
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
    required this.yard,
    required this.herdSignature,
    required this.sections,
    required this.market,
    required this.myListings,
    required this.studs,
    required this.festivals,
    required this.reputation,
    required this.bannedThrough,
    required this.tamperings,
    required this.openOffers,
    required this.breedingSeason,
    required this.recentEvents,
    required this.bank,
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

  /// The camels the 3D farm shows (the owner, 13 Nov 2026: the camels in
  /// the farm are the player's own): the first Presenter.yardCount to come
  /// to the farm, in that order (by the day they came, then id).
  final List<CamelCard> yard;

  /// Changes whenever any camel in the herd changes (not only the top
  /// few), so herd lists know to refresh their pages.
  final int herdSignature;

  /// What changed since the previous snapshot.
  final SectionRevisions sections;
  final List<ListingCard> market;
  final List<ListingCard> myListings;
  final List<StudCard> studs;
  final List<FestivalCard> festivals;

  /// الصيت in each family (GDD 8), 0 to 100.
  final Map<ColorCategory, double> reputation;

  /// The player is barred from festivals through this season, or null.
  final int? bannedThrough;

  /// The player's own secret treatments showing now.
  final List<TamperingCard> tamperings;
  final int openOffers;
  final bool breedingSeason;

  /// The player's latest news, newest last.
  final List<DomainEvent> recentEvents;

  /// البنك's main screen.
  final BankSummary bank;
}

/// البنك's main screen (the owner's approved design of 13 Nov 2026,
/// design/ui/phone_bank.jpg): the opening balance, today's money in and out
/// (their net is [PlayerSnapshot.todayNet]), and every month's net with the
/// kind that moved the most money. A month's kinds are asked for when it is
/// opened (EngineCore.bankMonth), so the snapshot grows by one short row a
/// game month.
class BankSummary {
  const BankSummary({
    required this.opening,
    required this.startedOn,
    required this.todayIn,
    required this.todayOut,
    required this.months,
  });

  final int opening;
  final GameDay startedOn;
  final int todayIn;
  final int todayOut;

  /// The newest first.
  final List<BankMonthRow> months;

  @override
  bool operator ==(Object other) =>
      other is BankSummary &&
      other.opening == opening &&
      other.startedOn == startedOn &&
      other.todayIn == todayIn &&
      other.todayOut == todayOut &&
      _listEquals(other.months, months);

  @override
  int get hashCode => Object.hash(
    opening,
    startedOn,
    todayIn,
    todayOut,
    Object.hashAll(months),
  );
}

/// One month on البنك's main screen: its net and its biggest kind.
class BankMonthRow {
  const BankMonthRow({
    required this.month,
    required this.net,
    required this.top,
  });

  /// 'YYYY-MM'.
  final String month;
  final int net;
  final MoneyLine top;

  @override
  bool operator ==(Object other) =>
      other is BankMonthRow &&
      other.month == month &&
      other.net == net &&
      other.top == top;

  @override
  int get hashCode => Object.hash(month, net, top);
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

/// A round as the player sees it (GDD 7).
class RoundCard {
  const RoundCard({
    required this.id,
    required this.kind,
    required this.category,
    required this.sex,
    required this.size,
    required this.day,
    required this.lastEntryDay,
    required this.legacyAge,
    required this.enterable,
    required this.prizes,
    required this.rivals,
    required this.myEntries,
    required this.eligible,
    required this.entryFee,
    required this.judged,
    required this.announced,
    required this.announceOn,
    required this.field,
    required this.caught,
    required this.results,
  });

  final RoundId id;
  final RoundKind kind;
  final ColorCategory? category;
  final Sex? sex;

  /// The head an entry shows (الفحل وإنتاجه: the bull and his offspring).
  final int size;
  final GameDay day;
  final GameDay lastEntryDay;

  /// A round planned before save v8: its one age class.
  final AgeClass? legacyAge;

  /// A player may enter it now (the group rounds come later).
  final bool enterable;
  final List<int> prizes;
  final int rivals;

  /// The player's entries, each its camels.
  final List<List<CamelCard>> myEntries;

  /// The player's camels that may enter now: for a single round each alone;
  /// for الفحل وإنتاجه the bulls that may, with their offspring.
  final List<CamelCard> eligible;

  /// A head's fee if entered today (a late entry's), else 0.
  final int entryFee;
  final bool judged;
  final bool announced;
  final GameDay? announceOn;

  /// Entries left after each stage (Stage order).
  final List<int>? field;
  final int caught;

  /// The places once announced (others' rows without marks), and the
  /// player's own removals.
  final List<ResultView>? results;
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
    required this.bank,
  });

  final int farm;
  final int herd;
  final int market;
  final int studs;
  final int festivals;
  final int news;
  final int bank;
}
