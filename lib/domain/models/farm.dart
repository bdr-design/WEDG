import 'region.dart';

/// Feeding programme for the whole herd. Better feed costs more per head per
/// day and keeps the camels in better body condition (الحالة), which judges
/// see on contest day.
enum FeedPlan {
  economy('اقتصادي', 'تبن وأعلاف مركّبة، رعي محدود', costFactor: 0.75,
      conditionTarget: 58),
  standard('متوسط', 'برسيم وشعير وتبن بنسب متوازنة', costFactor: 1.0,
      conditionTarget: 74),
  premium('ممتاز', 'برسيم فاخر وشعير وتمر ومكمّلات', costFactor: 1.55,
      conditionTarget: 90);

  const FeedPlan(this.label, this.detail,
      {required this.costFactor, required this.conditionTarget});

  final String label;
  final String detail;
  final double costFactor;

  /// Body condition the herd converges to on this plan (0–100).
  final int conditionTarget;
}

/// The player's camel farm (العزبة): where the herd lives.
class Farm {
  Farm({
    required this.name,
    required this.region,
    required this.capacity,
    required this.shepherds,
    required this.feedPlan,
  });

  String name;
  Region region;

  /// Head of camels the pens, shades and troughs can hold.
  int capacity;

  /// Hired shepherds (رعاة).
  int shepherds;
  FeedPlan feedPlan;

  Map<String, dynamic> toJson() => {
        'name': name,
        'region': region.name,
        'capacity': capacity,
        'shepherds': shepherds,
        'feed': feedPlan.name,
      };

  factory Farm.fromJson(Map<String, dynamic> j) => Farm(
        name: j['name'] as String,
        region: Region.byName(j['region'] as String),
        capacity: j['capacity'] as int,
        shepherds: j['shepherds'] as int,
        feedPlan: FeedPlan.values.byName(j['feed'] as String),
      );
}
