/// Every tunable number in the simulation, in one place.
///
/// Values marked (field) follow real husbandry and market practice in Saudi
/// Arabia, each from docs/research-realism.md (its section named); values
/// marked (balance) are game choices. Checked against the GDD and the research
/// on 12 Nov 2026 (docs/plan-gameplay.md, G1 part 2).
library;

import '../model/player.dart';
import '../model/tampering.dart';

class Balance {
  const Balance._();

  // ------------------------------------------------------------ biology
  /// (field) Gestation 377 days on average, 356 to 410 (section 6). How the
  /// days spread about the average is a game choice (balance: sd 10).
  static const gestationDays = 377;
  static const gestationMinDays = 356;
  static const gestationMaxDays = 410;
  static const gestationSd = 10.0;

  /// (balance) Days after mating before the check (tail-cocking or a scan).
  static const pregnancyCheckDays = 21;

  /// (balance) Chance one mating conceives, healthy female in condition.
  static const conceptionRate = 0.62;

  /// (field) Camels breed from November to April (section 6).
  static const breedingMonths = {11, 12, 1, 2, 3, 4};

  /// (field) Females are first mated at about 39.75 months, 3.3 years
  /// (section 6): 1,209 days.
  static const femaleMinBreedingDays = 1209;

  /// (field) Bulls are not used before 5 years, fully fertile at about 6
  /// (section 6).
  static const maleMinBreedingYears = 5;

  /// (field) Rest after calving before mating again: with the 377-day
  /// gestation and a mating or two, it gives the real calving interval of 22.6
  /// to 23.5 months (section 6). Mated within 3 months of calving the interval
  /// falls to about 15 months; that is to be the owner's choice, with its cost,
  /// when breeding gets its screens (plan G5), not every camel's (a 60-day
  /// rest made 40% more calves, the review).
  static const postCalvingRestDays = 300;

  /// (balance) Days a bull rests between coverings.
  static const studRestDays = 2;

  /// (balance) Oldest age the simulation lets a camel reach (a weak source
  /// gives a lifespan of about 40 years, section 6).
  static const maxAgeYears = 28;

  /// (balance) Newborn loss chance; higher when the dam is thin.
  static const calfLossBase = 0.03;
  static const calfLossThinDam = 0.05;

  /// (field) About 17% of calves die before their first year (the Qassim
  /// survey, section 6), the losses at birth included. The rest of it is a
  /// daily chance through the first year, a thin calf's doubled (balance),
  /// with the calves' illnesses on top: 0.00033 a day gives a first-year loss
  /// of 16.5 to 18.5% on the scripted player's farms (24 farms, 10 years, the
  /// calves sold young counted only while on the farm; measured 12 Nov 2026).
  static const calfDeathFirstYear = 0.17;
  static const calfDailyDeath = 0.00033;

  // ------------------------------------------------------------ care
  /// (balance) Daily share of the gap to the feed plan's target condition.
  static const conditionPull = 0.035;
  static const understaffedPenalty = 14.0;
  static const crowdedPenalty = 8.0;
  static const sickPenalty = 22.0;
  static const treatedPenalty = 8.0;
  static const latePregnancyPenalty = 4.0;
  static const latePregnancyDays = 90;

  // ------------------------------------------------------------ health
  /// (balance) Daily chance a healthy camel falls ill (≈ 0.5 times a year;
  /// the seasons move it, not the year's total: HealthSystem.seasonFactor).
  static const dailySickChance = 0.0014;
  static const sickChanceThinFactor = 2.0;
  static const sickChanceCrowdedFactor = 1.8;
  static const sickChanceCalfFactor = 1.6;

  /// (balance) Untreated illness: after [untreatedGraceDays], a daily death
  /// chance that grows each day.
  static const untreatedGraceDays = 10;
  static const untreatedDeathBase = 0.006;
  static const untreatedDeathPerDay = 0.0008;
  static const selfRecoveryAfterDays = 25;
  static const selfRecoveryChance = 0.03;

  /// (balance) Old-age deaths begin in the early twenties.
  static const oldAgeFromYears = 22;
  static const oldAgeDeathPerYear = 0.0004;

  // ------------------------------------------------------------ economy
  /// Starting money with the one nursing she-camel and her calf (the
  /// owner's decision of 13 Nov 2026).
  static const startingCash = 20000;

  // ------------------------------------------------------------ provisions
  /// (field) A bag of imported barley: 50 kg, SAR 67.9 (GASTAT's average
  /// prices, February 2026; section 7). Prices scale by the region's feed
  /// factor (balance).
  static const barleyBagKg = 50;
  static const barleyBagPrice = 67.9;

  /// (field) A bale of alfalfa: SAR 28.81 (GASTAT, October 2025; section 7).
  /// (balance) Its weight, 25 kg: small square bales run about 18 to 27 kg
  /// (a weak source).
  static const alfalfaBaleKg = 25;
  static const alfalfaBalePrice = 28.81;

  /// A water tanker (الوايت). (field) They are sold by the tonne: the
  /// National Water Company's 19 t tanker SAR 114 to 135 and its 30 t SAR 225
  /// in town, private 6 t tankers SAR 100 to 150 in Riyadh's adverts (search
  /// summaries of bayut.sa and opensooq.com, 12 Nov 2026; research section 7).
  /// (balance) A 19 t load (19,000 L) to a farm out of town: SAR 200; and a
  /// 6 t one, to top up a tank the large one does not fit (the owner, 12 Nov
  /// 2026): SAR 120, inside the adverts' range.
  static const waterLoadL = 19000;
  static const waterLoadPrice = 200.0;
  static const smallWaterLoadL = 6000;
  static const smallWaterLoadPrice = 120.0;

  /// (field) The share of barley grain and of alfalfa hay that is dry matter:
  /// barley 87 to 90% (Feedipedia's average 87.1%; extension tables 87 to
  /// 90.4%), alfalfa hay 88 to 90% by its cut (research section 7). A ration
  /// is reckoned in dry matter and ordered by the weight delivered.
  static const barleyDryMatter = 0.88;
  static const alfalfaDryMatter = 0.89;

  /// (balance) Days an order takes to arrive.
  static const deliveryDays = 1;

  /// A new farm (the owner, 13 Nov 2026: it starts small and grows by what is
  /// bought): a 6,000 L tank, the size a 6 t tanker fills ((field) a vertical
  /// 6,000 L tank SAR 2,835, research section 7); (balance) a feed shade for
  /// 1,000 kg (twenty bags); 30 days of the herd's needs in them.
  static const startingStoreKg = 1000;
  static const startingTankL = 6000;
  static const startingStockDays = 30;

  /// (balance) The player tends this many head himself; past it the farm
  /// needs shepherds (and their caravan).
  static const ownerTendsUpTo = 10;

  /// Water a day (litres). (field) A nursing camel drinks 37 to 46 L
  /// (section 6): 42. (balance) The others by the season: camels go about 17
  /// days without water in winter and 7 in summer (section 6), so they drink
  /// less in winter. (field, for the range) FAO gives 4.5 L a day on autumn
  /// browse to 13 in spring and 30 on salty pasture; penned camels on dry
  /// feed in Oman drank 17 to 30 L, 24 on average (research section 7).
  static const nursingWaterL = 42.0;
  static double waterL(int month) => switch (month) {
    5 || 6 || 7 || 8 || 9 => 30.0,
    11 || 12 || 1 || 2 || 3 => 15.0,
    _ => 22.0,
  };

  /// Days a camel can go without water (the owner's choice of 12 Nov 2026:
  /// on dry feed, longer on green pasture). (field) About 17 in winter on
  /// grazing and 7 in summer (section 6); on straw and concentrates alone FAO
  /// gives up to ten (section 7), and the game's herd eats barley and alfalfa
  /// hay. So in winter 10, or 17 while the pasture is green; (balance) 8, or
  /// 12 while green, in spring and autumn.
  static int thirstDays(int month, {required bool green}) => switch (month) {
    5 || 6 || 7 || 8 || 9 => 7,
    11 || 12 || 1 || 2 || 3 => green ? 17 : 10,
    _ => green ? 12 : 8,
  };

  /// (field) The rains begin with الوسم about 16 October (section 7) and green
  /// the ground through the winter into spring. (balance) Green from December
  /// to April in a wet season, a season wet with this chance for each region:
  /// Najd's rains vary much from year to year.
  static const greenMonths = {12, 1, 2, 3, 4};
  static const wetSeasonChance = 0.6;

  /// (balance) Without enough water (a day the herd gets under half of it):
  /// body condition held this much lower, and past the days a camel can go
  /// without, a chance of death that climbs by this much each further day
  /// (at 3% a day flat, camels lived 60 and 100 dry days through the summer,
  /// the review).
  static const thirstPenalty = 20.0;
  static const thirstDeathPerDay = 0.15;

  /// (balance) A warning when a store holds this many days or fewer.
  static const lowStockDays = 3;

  static double feedAgeFactor(int ageDays) {
    if (ageDays < 180) return 0.2; // suckling
    if (ageDays < 365) return 0.45;
    if (ageDays < 730) return 0.7;
    if (ageDays < 1095) return 0.85;
    return 1.0;
  }

  /// (field) A shepherd's monthly wage, housing and food on top: SAR 1,500
  /// paid by owners in Sharurah, 1,000 to 1,400 in recruitment ads
  /// (section 6).
  static const shepherdMonthlyWage = 1500;
  static const camelsPerShepherd = 25;
  static const maxShepherds = 40;

  /// (balance) The first pen's room (a pen with a shade and a trough).
  static const startingCapacity = 6;

  /// Days a facility takes to build (balance; the owner approved "it is
  /// done after three days", 13 Nov 2026).
  static const buildDays = 3;

  // ------------------------------------------------------------ milk
  /// (field) A she-camel's common average is no more than about 5 L a day;
  /// high producers give 10 or more, low ones 5 or less; مجاهيم give the most
  /// (research sections 7). (balance) Each nursing camel's own level drawn
  /// from 3.5 to 7 L, مجاهيم a quarter more, over a lactation of a year from
  /// calving ((field) 190 to 404 days across studies), rising to 1.2 of it at
  /// six weeks and falling to half of it by the year's end: the lactation's
  /// average is 0.87 of the level, 4.6 L (5.7 for مجاهيم), and the best
  /// مجاهيم reach 10.5 L at their peak.
  static const milkLevelMin = 3.5;
  static const milkLevelMax = 7.0;
  static const majaheemMilk = 1.25;
  static const lactationDays = 365;
  static const milkPeakDay = 45;

  /// (balance) The litre's price to the buyer who comes each day (the
  /// owner's choice of 13 Nov 2026; no reliable farm-gate price was found:
  /// about SAR 8.5 from a 2019 aggregator, 10 to 15 from a forum).
  static const milkPrice = 10;

  /// (field) In the traditional Saudi system the calf nurses freely for its
  /// first three months (research section 7). (balance) What the milk left
  /// to it does to a suckling calf's condition target: all of it more,
  /// half the same, a quarter less, and more so in its first three months;
  /// a calf under a year without its dam (sold or dead) gets none, the
  /// least of all.
  static const freeNursingDays = 90;
  static double orphanMilkTarget(int ageDays) =>
      ageDays < freeNursingDays ? -20 : -8;
  static double calfMilkTarget(CalfShare share, int ageDays) =>
      ageDays < freeNursingDays
      ? switch (share) {
          CalfShare.all => 6,
          CalfShare.half => -6,
          CalfShare.quarter => -14,
        }
      : switch (share) {
          CalfShare.all => 4,
          CalfShare.half => 0,
          CalfShare.quarter => -5,
        };

  /// (balance) Trucking: loading cost plus per km, scaled by head count.
  static int transportCost(int km, int head) =>
      head == 0 ? 0 : ((350 + km * 2.2) * (0.55 + 0.45 * head)).round();

  /// (balance) Broker's commission (السعي), share of the sale price: set by
  /// custom in the real market (section 5); 2.5% is the game's.
  static const brokerCommission = 0.025;

  /// (balance) Selling straight to the broker fetches less than value: he
  /// buys it himself, so takes no commission, his margin in the price.
  static const quickSaleFactor = 0.78;

  /// (balance) How far the broker's eye is off a camel's true value (one
  /// standard deviation, kept within 2.5 of them): his price, unlike the
  /// market's appraisals (views.dart), is a single figure, so without it the
  /// value would be his price over [quickSaleFactor] exactly.
  static const brokerEyeSd = 0.05;

  /// (balance) A camel bought in the market comes on the truck the next day,
  /// from anywhere in the kingdom: a game choice (by the game's own road
  /// estimate, Region.roadKmTo, Tabuk to Riyadh is 1,356 km, about 17 hours at
  /// a lorry's 80 km/h, but the longest, Jouf to Najran at 1,804 km, would
  /// take longer). Until then it is the
  /// player's but not on the farm: not in the yard, not milked, not for sale
  /// or for breeding.
  static const camelTruckDays = 1;

  /// (balance) Bargaining.
  static const maxBargainsPerBuyer = 3;
  static const counterOfferFloor =
      0.85; // offer ≥ 85% of reserve gets a counter

  /// (balance) Player listings.
  static const playerListingDays = 45;

  /// (balance) The lowest asking price a player may list at.
  static const minAskPrice = 1000;
  static const maxOffersPerListing = 3;
  static const offerValidDays = 3;
  static const buyerInterest = 0.32;

  /// (balance) NPC market size.
  static const npcListingsTarget = 26;
  static const studsInSeason = 9;
  static const studsOffSeason = 4;

  // ------------------------------------------------------------ contests
  // The Saudi round system (GDD 7, research-realism sections 2 to 4); the
  // round types, their sizes and prizes are in RoundKind and ContestRules.

  /// (balance) Ownership must be registered this long before the round
  /// unless the camel was born on the farm (the chip is the only ownership
  /// document, real; how long before is the game's).
  static const ownershipDaysBeforeJudging = 30;

  /// (balance) An owner's camels in one round of مفاريد or دق (القعدان or
  /// البكار); الفردي takes one camel of his a festival (the owner, 13 Nov
  /// 2026), الفحل وإنتاجه one entry.
  static const maxEntriesPerOwnerInRound = 3;

  /// (field) A late entry is taken until 72 hours before its round, with a
  /// fee (research section 4, [43]). (balance) The fee, SAR 1,000 a head
  /// (not found), and the normal closing, 7 days before the festival begins.
  static const lateEntryHoursBefore = 72;
  static const lateEntryFee = 1000;
  static const registrationClosesBeforeStart = 7;

  /// (balance) Registration opens this long before the festival begins.
  static const registrationOpensBefore = 30;
  static const grandRegistrationOpensBefore = 45;
  static const judgesPerPanel = 5;

  /// (field) The grand festival runs from 1 December to 3 January (the 9th
  /// and 10th editions, research section 4). (balance) The regional ones
  /// run four days and the local ones two.
  static const regionalFestivalDays = 4;
  static const localFestivalDays = 2;

  /// (balance) Stage 1: a chip that does not read as the registration's.
  static const chipMismatchChance = 0.002;

  /// (balance) Stage 2: a camel whose coat shows under this (0 to 100) is
  /// not pure in its colour; one within [teethMarginDays] of its age class's
  /// edge on the day may be read by the teeth as the other class, with this
  /// chance (real: the age is checked by the teeth, research section 4).
  static const colourPurityMin = 30.0;
  static const teethMarginDays = 30;
  static const teethMisreadChance = 0.10;

  /// (balance) Stage 3: the preliminary judging keeps this share of the
  /// field, and at least [preliminaryKeepsAtLeast] entries.
  static const preliminaryKeeps = 0.5;
  static const preliminaryKeepsAtLeast = 10;

  /// (field) Results of الفحل وإنتاجه come only after the DNA tests confirm
  /// the offspring are his (research section 2, [17]). (balance) In 10 days.
  static const dnaDays = 10;

  // ------------------------------------------------------------ cheating
  // GDD 7.1 (the owner, 12 Nov 2026). The kinds and their fine caps are real
  // (TamperKind); the rest is the game's.

  /// (balance) What a treatment adds to a camel's weighted look (0 to 100),
  /// for each level of strength (1 to 3), shared among the features it works
  /// on (the owner, 13 Nov 2026: a strong one lifts a middling camel a few
  /// places, as in the real thing). It shows to every eye, the judges' and
  /// the buyers' (she looks finer, and fetches more), while it lasts.
  static const tamperLiftPerLevel = 3.4;

  /// The points it adds to each of its features.
  static double tamperTraitGain(TamperKind kind, int strength) =>
      tamperLiftPerLevel *
      strength /
      kind.traits.fold(0.0, (s, t) => s + t.weight);

  /// (field) Caught at a festival: disqualified, fined, and the owner and
  /// his camels barred from this edition and at least five more (research
  /// section 3, [27][102]); the ban covers every festival in the game (the
  /// owner, 13 Nov 2026).
  static const banEditionsAfter = 5;

  /// (balance) A treatment can be found outside the festivals too, in the
  /// market or by the vet (GDD 7.1; the case is real: in 2018 MEWA fined
  /// five people SAR 67,000 in all, section 7 [100]): a chance a day for each
  /// treatment showing, times its strength; four times that while the camel
  /// is listed for sale; this chance when the vet treats the camel.
  static const outsideCatchPerDay = 0.0004;
  static const outsideCatchListedFactor = 4.0;
  static const vetCatchChance = 0.15;

  /// (balance) The account for the herd's necessities (feed, water, the
  /// vet's treatment; the owner, 13 Nov 2026): a month of the herd's feed and
  /// water at today's ration, at least SAR 5,000 (Account.limit).
  static const creditDays = 30;
  static const minCreditLimit = 5000;

  /// (balance) A vet's look at a camel for sale before buying (not found):
  /// its price, and the chance it finds each treatment (a deliberate look,
  /// more than [vetCatchChance] when treating an illness).
  static const vetCheckFee = 500;
  static const vetCheckChance = 0.6;

  /// (field) Fined outside a festival: the 2018 case's average, SAR 67,000
  /// among five, about 13,400 each (research section 7, [100]).
  static const outsideFine = 13400;

  /// (balance) A rival's entry is treated with this chance (the field's
  /// cheats, GDD 7.1: rivals cheat too), at a strength drawn from 1 to 3.
  static const rivalTamperChance = 0.04;

  /// (balance) A rival's entry the stage 2 check removes (its colour or its
  /// teeth), and how far the final judging's second look moves a mark.
  static const rivalBreedCheckChance = 0.02;
  static const finalLookSd = 0.8;

  /// The fine for a treatment found at a festival: (field) up to the kind's
  /// cap (TamperKind.fineCap); (balance) scaled by its strength, a heavy one
  /// the cap (the director's direction, 13 Nov 2026), to the riyal's
  /// thousand.
  static int tamperFine(TamperKind kind, int strength) =>
      ((kind.fineCap * strength / 3) / 1000).round() * 1000;

  // ------------------------------------------------------------ reputation
  /// (balance) الصيت (GDD 8) in each family, 0 to 100: where it starts;
  /// what a place adds (first, second or third, the rest of the top ten)
  /// times the festival's tier level; what being caught takes.
  static const startingReputation = 10.0;
  static const reputationForFirst = 4.0;
  static const reputationForPodium = 2.0;
  static const reputationForTopTen = 0.5;
  static const reputationCaught = 25.0;
  static const reputationCaughtOutside = 10.0;

  /// (balance) A sale this far over the camel's value is a strong one (GDD
  /// 8: الصيت grows with wins and strong sales), and adds this.
  static const strongSaleOver = 1.1;
  static const reputationForStrongSale = 1.0;

  /// (balance) What الصيت does to what buyers and the broker pay for the
  /// player's camels of the family (GDD 8): 0.2% a point from where it
  /// starts, +18% at 100, -2% at 0.
  static double reputationPriceFactor(double reputation) =>
      1 + 0.002 * (reputation - startingReputation);
}
