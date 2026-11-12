/// Every tunable number in the simulation, in one place.
///
/// Values marked (field) follow real husbandry and market practice in Saudi
/// Arabia, each from docs/research-realism.md (its section named); values
/// marked (balance) are game choices. Checked against the GDD and the research
/// on 12 Nov 2026 (docs/plan-gameplay.md, G1 part 2).
library;

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
  /// (balance) Starting money.
  static const startingCash = 600000;

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

  /// (balance) A water tanker's load (الوايت) and its price: no source found.
  static const waterLoadL = 20000;
  static const waterLoadPrice = 450.0;

  /// (balance) Each head of room built adds a month of an adult's standard
  /// ration to the feed store (30 x 11 kg) and of summer water to the tank
  /// (30 x 30 L).
  static const storeKgPerHead = 330;
  static const tankLPerHead = 900;

  /// (balance) Days an order takes to arrive.
  static const deliveryDays = 1;

  /// (balance) The feed store's and the water tank's sizes on a new farm, and
  /// what a new farm starts with (30 days of the herd's needs).
  static const startingStoreKg = 20000;
  static const startingTankL = 40000;
  static const startingStockDays = 30;

  /// Water a day (litres). (field) A nursing camel drinks 37 to 46 L
  /// (section 6): 42. (balance) The others by the season: camels go about 17
  /// days without water in winter and 7 in summer (section 6), so they drink
  /// less in winter.
  static const nursingWaterL = 42.0;
  static double waterL(int month) => switch (month) {
    5 || 6 || 7 || 8 || 9 => 30.0,
    11 || 12 || 1 || 2 || 3 => 15.0,
    _ => 22.0,
  };

  /// (field) Days a camel can go without water: about 17 in winter, 7 in
  /// summer (section 6); (balance) 12 in between.
  static int thirstDays(int month) => switch (month) {
    5 || 6 || 7 || 8 || 9 => 7,
    11 || 12 || 1 || 2 || 3 => 17,
    _ => 12,
  };

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

  /// (balance) Farm building.
  static const startingCapacity = 20;
  static const expansionStep = 10;
  static const expansionCost = 28000;

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
