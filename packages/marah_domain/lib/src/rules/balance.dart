/// Every tunable number in the simulation, in one place.
///
/// Values marked (field) follow real husbandry and market practice in Saudi
/// Arabia; values marked (balance) are game choices. docs/realism.md lists
/// the sources and open questions for the (field) values.
library;

class Balance {
  const Balance._();

  // ------------------------------------------------------------ biology
  /// (field) Dromedary gestation ≈ 13 months (370–395 days).
  static const gestationDays = 385;
  static const gestationSpread = 10;

  /// (field) Days after mating before the check (tail-cocking / scan).
  static const pregnancyCheckDays = 21;

  /// (balance) Chance one mating conceives, healthy female in condition.
  static const conceptionRate = 0.62;

  /// (field) Camels breed in the cool months.
  static const breedingMonths = {11, 12, 1, 2, 3, 4};

  /// (field) Females are first put to the bull at about 4 years.
  static const femaleMinBreedingYears = 4;

  /// (field) Bulls are used at stud from about 6 years.
  static const maleMinBreedingYears = 6;

  /// (field) Rest after calving before mating again (calving interval ≈ 2y).
  static const postCalvingRestDays = 300;

  /// (balance) Days a bull rests between coverings.
  static const studRestDays = 2;

  /// (field) Oldest age the simulation lets a camel reach.
  static const maxAgeYears = 28;

  /// (balance) Newborn loss chance; higher when the dam is thin.
  static const calfLossBase = 0.03;
  static const calfLossThinDam = 0.05;

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
  /// (balance) Daily chance a healthy camel falls ill (≈ 0.5 times a year).
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

  /// (field) Old-age deaths begin in the early twenties.
  static const oldAgeFromYears = 22;
  static const oldAgeDeathPerYear = 0.0004;

  // ------------------------------------------------------------ economy
  /// (balance) Starting money.
  static const startingCash = 600000;

  /// (field) Feed for one adult on the standard plan, riyals per day
  /// (≈ 10–12 kg mix of alfalfa, barley and straw).
  static const feedPerAdultPerDay = 26.0;

  static double feedAgeFactor(int ageDays) {
    if (ageDays < 180) return 0.2; // suckling
    if (ageDays < 365) return 0.45;
    if (ageDays < 730) return 0.7;
    if (ageDays < 1095) return 0.85;
    return 1.0;
  }

  /// (field) Shepherd monthly wage incl. housing and food.
  static const shepherdMonthlyWage = 2200;
  static const camelsPerShepherd = 25;
  static const maxShepherds = 40;

  /// (balance) Farm building.
  static const startingCapacity = 20;
  static const expansionStep = 10;
  static const expansionCost = 28000;

  /// (balance) Trucking: loading cost plus per km, scaled by head count.
  static int transportCost(int km, int head) =>
      head == 0 ? 0 : ((350 + km * 2.2) * (0.55 + 0.45 * head)).round();

  /// (field) Broker's commission (السعي), share of the sale price.
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
