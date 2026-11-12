import '../catalog/catalog.dart';
import '../common/money.dart';
import '../model/contest.dart';

/// Contest numbers derived from the festival tier and the round, so they
/// are never stored per round.
class ContestRules {
  const ContestRules._();

  /// (balance) Prize money for places 1–10.
  static List<int> prizes(FestivalTier tier, AgeClass age) {
    final top = switch (tier) {
      FestivalTier.grand => 800000,
      FestivalTier.regional => 150000,
      FestivalTier.local => 40000,
    };
    final ageFactor = switch (age) {
      AgeClass.mafrood || AgeClass.haq => 0.6,
      AgeClass.laqi || AgeClass.jatha => 0.8,
      _ => 1.0,
    };
    const shares = [1.0, 0.6, 0.42, 0.3, 0.22, 0.16, 0.12, 0.09, 0.07, 0.05];
    return [for (final s in shares) marketRound(top * ageFactor * s).value];
  }

  /// (balance) Typical look of the rivals each tier attracts.
  static (double, double) rivalQuality(FestivalTier tier) => switch (tier) {
    FestivalTier.grand => (76, 7),
    FestivalTier.regional => (68, 7),
    FestivalTier.local => (61, 7),
  };
}
