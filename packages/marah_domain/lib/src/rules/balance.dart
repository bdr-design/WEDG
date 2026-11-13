/// Every tunable number in the simulation, in one place.
///
/// Values marked (field) follow real husbandry and market practice in Saudi
/// Arabia, each from docs/research-realism.md (its section named); values
/// marked (balance) are game choices. Checked against the GDD and the research
/// on 12 Nov 2026 (docs/plan-gameplay.md, G1 part 2).
library;

import '../model/player.dart';

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
  /// from 3.5 to 6.5 L, مجاهيم a quarter more, over a lactation of a year
  /// from calving ((field) 190 to 404 days across studies), rising to its
  /// peak at six weeks and falling to half of it by the year's end.
  static const milkLevelMin = 3.5;
  static const milkLevelMax = 6.5;
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
  /// half the same, a quarter less, and more so in its first three months.
  static const freeNursingDays = 90;
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

  /// (balance) Selling straight to the broker fetches less than value.
  static const quickSaleFactor = 0.78;

  /// (balance) Bargaining.
  static const maxBargainsPerBuyer = 3;
  static const counterOfferFloor =
      0.85; // offer ≥ 85% of reserve gets a counter

  /// (balance) Player listings.
  static const playerListingDays = 45;
  static const maxOffersPerListing = 3;
  static const offerValidDays = 3;
  static const buyerInterest = 0.32;

  /// (balance) NPC market size.
  static const npcListingsTarget = 26;
  static const studsInSeason = 9;
  static const studsOffSeason = 4;

  // ------------------------------------------------------------ contests
  /// (balance) Ownership must be registered this long before judging unless
  /// the camel was born on the farm.
  static const ownershipDaysBeforeJudging = 30;

  /// (balance) Max entries per owner in one round.
  static const maxEntriesPerOwnerInRound = 3;

  static const registrationClosesBeforeJudging = 7;
  static const registrationOpensBefore = 30;
  static const grandRegistrationOpensBefore = 45;
  static const judgesPerPanel = 5;
}
