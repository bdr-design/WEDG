import 'dart:math' as math;

import '../catalog/catalog.dart';
import '../common/money.dart';
import '../model/contest.dart';
import '../model/tampering.dart';
import 'balance.dart';

/// Contest numbers derived from the festival tier and the round, so they
/// are never stored per round.
class ContestRules {
  const ContestRules._();

  /// (balance) The first prize of a round at the grand festival. The real
  /// numbers known are the festival's whole purse (SAR 200 to 300 million,
  /// research section 4) and الفحل وإنتاجه's first prize, SAR 1 million
  /// (real, [42]); every other round's is the game's, in proportion.
  static int grandFirstPrize(RoundKind kind, int size) => switch (kind) {
    RoundKind.mafareed => 300000,
    RoundKind.diq => 400000,
    RoundKind.fardiDiq => 500000,
    RoundKind.fardiJil => 800000,
    RoundKind.fahal => 1000000,
    // a group's by its head: SAR 50,000 a head
    RoundKind.jamal || RoundKind.manqiya => size * 50000,
    // the top منقية (جائزة الشداد; in 2024 a private jet, real)
    RoundKind.jazeera => 5000000,
    RoundKind.hajij => 500000,
    RoundKind.tabaa => 300000,
    RoundKind.badawa => 1000000,
  };

  /// (balance) A regional festival pays this share of the grand one's, a
  /// local one this (the regional festival at Tabuk paid SAR 13 million in
  /// all, real, research section 4).
  static double tierShare(FestivalTier tier) => switch (tier) {
    FestivalTier.grand => 1.0,
    FestivalTier.regional => 0.19,
    FestivalTier.local => 0.05,
  };

  /// (balance) Each place's share of the first prize, places 1 to 10.
  static const placeShares = [
    1.0,
    0.6,
    0.42,
    0.3,
    0.22,
    0.16,
    0.12,
    0.09,
    0.07,
    0.05,
  ];

  /// (balance) Prize money for places 1–10.
  static List<int> prizes(FestivalTier tier, RoundKind kind, int size) {
    final top = grandFirstPrize(kind, size) * tierShare(tier);
    return [for (final s in placeShares) marketRound(top * s).value];
  }

  /// (balance) Typical look of the rivals each tier attracts.
  static (double, double) rivalQuality(FestivalTier tier) => switch (tier) {
    FestivalTier.grand => (76, 7),
    FestivalTier.regional => (68, 7),
    FestivalTier.local => (61, 7),
  };

  /// The ages a round takes on its day (real where research section 2
  /// gives them: مفاريد a year to two, دق after مفرود up to جذعة, البداوة
  /// مفرودة or older). (balance) جل to 15 years ("to middle age"), the
  /// groups from حق, الهجيج from جذع to 15 years (a run of 18 to 20 km).
  static bool ageFits(RoundKind kind, AgeClass age, int ageDays) =>
      switch (kind) {
        RoundKind.mafareed => age == AgeClass.mafrood,
        RoundKind.diq || RoundKind.fardiDiq =>
          age == AgeClass.haq || age == AgeClass.laqi || age == AgeClass.jatha,
        RoundKind.fardiJil => ageDays < 15 * 365,
        RoundKind.fahal => true,
        RoundKind.badawa => age.index >= AgeClass.mafrood.index,
        RoundKind.hajij =>
          age.index >= AgeClass.jatha.index && ageDays < 15 * 365,
        RoundKind.jamal ||
        RoundKind.manqiya ||
        RoundKind.jazeera ||
        RoundKind.tabaa => age.index >= AgeClass.haq.index,
      };

  /// (field) A جل camel is one from her second calf (research section 2).
  static const jilCalvings = 2;

  /// (balance) الفحل وإنتاجه: the bull and this many of his offspring.
  static const fahalOffspring = 5;

  /// (balance) The share of the bull's own marks in الفحل وإنتاجه's score;
  /// the rest is his offspring's average.
  static const fahalBullShare = 0.4;

  /// The chance a treatment is found at [stage] (the tampering experts or
  /// the medical committee): the kind's chance for a light one (TamperKind,
  /// balance), each further level of strength a fresh look:
  /// 1 - (1 - p)^strength.
  static double detectChance(TamperKind kind, int strength, Stage stage) {
    final p = switch (stage) {
      Stage.tamperingExperts => kind.experts,
      Stage.medical => kind.medical,
      _ => 0.0,
    };
    return 1 - math.pow(1 - p, strength).toDouble();
  }

  /// The chance a festival finds the treatment at all (both stages).
  static double festivalCatchChance(TamperKind kind, int strength) =>
      1 -
      (1 - detectChance(kind, strength, Stage.tamperingExperts)) *
          (1 - detectChance(kind, strength, Stage.medical));

  /// The chance one is found outside the festivals in 30 days (not listed
  /// for sale, never treated by the vet).
  static double monthlyOutsideChance(int strength) =>
      1 - math.pow(1 - Balance.outsideCatchPerDay * strength, 30).toDouble();

  /// The risk as the player hears it (the review of e2775ff: the views say
  /// the risk in words, never the odds): (balance) low under 30%, high from
  /// 60%.
  static RiskBand band(double chance) => chance < 0.3
      ? RiskBand.low
      : chance < 0.6
      ? RiskBand.medium
      : RiskBand.high;

  /// The risk a festival finds [kind] at [strength].
  static RiskBand festivalRisk(TamperKind kind, int strength) =>
      band(festivalCatchChance(kind, strength));

  /// The risk it is found outside the festivals in a month (not listed for
  /// sale, never treated by the vet).
  static RiskBand outsideRisk(int strength) =>
      band(monthlyOutsideChance(strength));

  /// Who finds [kind] most: the tampering experts or the medical committee.
  static Stage foundMostlyBy(TamperKind kind) =>
      kind.experts >= kind.medical ? Stage.tamperingExperts : Stage.medical;

  /// The chance a buyer's or the broker's examination before paying finds a
  /// treatment of [strength] (balance, Balance.saleCheckPerLevel).
  static double saleCheckChance(int strength) =>
      1 - math.pow(1 - Balance.saleCheckPerLevel, strength).toDouble();

  /// What the secret vet takes for a treatment.
  static int tamperPrice(TamperKind kind, int strength) =>
      kind.price * strength;
}

/// A risk in words: what a player is told of a chance (never the number).
enum RiskBand { low, medium, high }
