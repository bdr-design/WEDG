/// Real-world husbandry and economy figures the simulation is built on.
///
/// Where a figure comes from field practice it is noted; where it is a game
/// balance choice it says so. Keep all tunable numbers here.
library;

// ---------------------------------------------------------------- biology

/// Gestation of the dromedary: about 13 months (≈ 370–395 days).
const gestationDays = 385;
const gestationSpread = 10;

/// Days after mating before the pregnancy check (رفع الذيل / فحص) is reliable.
const pregnancyCheckDays = 21;

/// Chance a mating conceives for a healthy female in good condition.
const baseConceptionRate = 0.62;

/// Camels breed in the cool season. Months (1–12) when females take the bull.
const breedingMonths = {11, 12, 1, 2, 3, 4};

/// Youngest age (years) a female is put to the bull; first calf ≈ 5 years.
const femaleMinBreedingYears = 4;

/// Youngest age (years) a bull is used at stud.
const maleMinBreedingYears = 6;

/// Rest a female needs after calving before she is mated again (days).
/// Herders usually wait until the calf is well grown; calving interval ≈ 2y.
const postCalvingRestDays = 300;

/// Days a bull rests between coverings (game balance).
const studRestDays = 2;

/// Calves are weaned at about 12 months (يُفرد الحوار ويصير مفرود).
const weaningDays = 365;

/// Oldest age the simulation lets a camel reach; productive life ≈ 20–25 y.
const maxAgeYears = 28;

// ---------------------------------------------------------------- economy

/// Starting money for a new owner (game balance).
const startingCash = 600000;

/// Feed for one adult on the standard plan, riyals per day (≈ 10–12 kg of
/// alfalfa, barley and straw mix).
const feedPerAdultPerDay = 26.0;

/// Feed share by age (حوار mostly suckles its dam).
double feedAgeFactor(int ageDays) {
  if (ageDays < 180) return 0.2;
  if (ageDays < 365) return 0.45;
  if (ageDays < 730) return 0.7;
  if (ageDays < 1095) return 0.85;
  return 1.0;
}

/// A shepherd's (راعي) monthly wage incl. housing and food, riyals.
const shepherdMonthlyWage = 2200;

/// Camels one shepherd can look after properly.
const camelsPerShepherd = 25;

/// Cost to add 10 places to the farm: fencing, shade, troughs (game balance).
const expansionCostPer10 = 28000;
const expansionStep = 10;
const startingCapacity = 20;

/// Vet visit and treatment, riyals (range).
const vetTreatmentMin = 350;
const vetTreatmentMax = 1800;

/// Daily chance a camel falls ill (≈ 0.5 times a year in good care).
const dailySickChance = 0.0014;

/// Trucking camels: fixed loading cost plus per-km, per head (game balance
/// on top of typical camel-truck rental prices).
int transportCost(int km, int head) =>
    head == 0 ? 0 : ((350 + km * 2.2) * (0.55 + 0.45 * head)).round();

/// The broker's commission at the market (السعي), share of the price.
const brokerCommission = 0.025;

/// Selling straight to the broker (بيع على الدلال) fetches less than value.
const quickSaleFactor = 0.78;
