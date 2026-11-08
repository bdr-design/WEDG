import 'dart:math' as math;

/// Saudi regions where a player can base the farm (العزبة), each with its
/// camel market. Coordinates are approximate city centres, used only for
/// road-distance (transport cost) estimates.
enum Region {
  riyadh('الرياض', 'سوق إبل الرياض', 24.71, 46.68, feed: 1.00, land: 1.30),
  qassim('القصيم', 'سوق إبل بريدة', 26.33, 43.97, feed: 0.94, land: 1.00),
  hail('حائل', 'سوق إبل حائل', 27.52, 41.69, feed: 0.96, land: 0.90),
  jouf('الجوف', 'سوق إبل سكاكا', 29.97, 40.21, feed: 0.97, land: 0.85),
  northern('الحدود الشمالية', 'سوق إبل رفحاء', 29.63, 43.49,
      feed: 1.04, land: 0.80),
  sharqiya('الشرقية', 'سوق إبل الأحساء', 25.38, 49.59, feed: 1.02, land: 1.15),
  tabuk('تبوك', 'سوق إبل تبوك', 28.38, 36.57, feed: 1.03, land: 0.90),
  najran('نجران', 'سوق إبل نجران', 17.49, 44.13, feed: 1.05, land: 0.85);

  const Region(this.label, this.marketName, this.lat, this.lon,
      {required this.feed, required this.land});

  final String label;
  final String marketName;
  final double lat;
  final double lon;

  /// Multiplier on feed prices (agricultural regions are cheaper).
  final double feed;

  /// Multiplier on construction / expansion costs.
  final double land;

  /// Approximate road distance in km (great-circle × 1.25 road factor).
  int roadKmTo(Region other) {
    if (other == this) return 25; // within the region: farm <-> market
    const r = 6371.0;
    double rad(double d) => d * math.pi / 180;
    final dLat = rad(other.lat - lat);
    final dLon = rad(other.lon - lon);
    final a = math.pow(math.sin(dLat / 2), 2) +
        math.cos(rad(lat)) *
            math.cos(rad(other.lat)) *
            math.pow(math.sin(dLon / 2), 2);
    final c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a));
    return (r * c * 1.25).round();
  }

  static Region byName(String name) =>
      Region.values.firstWhere((r) => r.name == name, orElse: () => riyadh);
}
