import 'catalog.dart';
import 'region.dart';

enum FestivalTier {
  local(1, 'محلي'),
  regional(2, 'إقليمي'),
  grand(3, 'المهرجان الكبير');

  const FestivalTier(this.level, this.label);
  final int level;
  final String label;
}

/// One placing in a round's results.
class ResultRow {
  const ResultRow({
    required this.rank,
    required this.camelName,
    required this.ownerName,
    required this.score,
    required this.prize,
    this.camelId,
    this.isPlayer = false,
    this.breakdown,
  });

  final int rank;
  final String camelName;
  final String ownerName;

  /// Score out of 100 (average of the judges' panel).
  final double score;
  final int prize;
  final String? camelId;
  final bool isPlayer;

  /// Per-trait marks out of 10 (kept for the player's camels).
  final Map<Trait, double>? breakdown;

  Map<String, dynamic> toJson() => {
        'k': rank,
        'n': camelName,
        'o': ownerName,
        's': double.parse(score.toStringAsFixed(2)),
        'p': prize,
        if (camelId != null) 'id': camelId,
        if (isPlayer) 'me': true,
        if (breakdown != null)
          'b': {
            for (final e in breakdown!.entries)
              e.key.name: double.parse(e.value.toStringAsFixed(2)),
          },
      };

  factory ResultRow.fromJson(Map<String, dynamic> j) => ResultRow(
        rank: j['k'] as int,
        camelName: j['n'] as String,
        ownerName: j['o'] as String,
        score: (j['s'] as num).toDouble(),
        prize: j['p'] as int,
        camelId: j['id'] as String?,
        isPlayer: j['me'] == true,
        breakdown: j['b'] == null
            ? null
            : {
                for (final e in (j['b'] as Map<String, dynamic>).entries)
                  Trait.values.byName(e.key): (e.value as num).toDouble(),
              },
      );
}

/// A round (شوط): one colour family, one sex, one age class.
class ContestRound {
  ContestRound({
    required this.id,
    required this.category,
    required this.sex,
    required this.age,
    required this.prizes,
    required this.fieldSize,
    List<String>? entries,
    this.results,
  }) : entries = entries ?? [];

  final String id;
  final ColorCategory category;
  final Sex sex;
  final AgeClass age;

  /// Prize money for 1st, 2nd, ... place.
  final List<int> prizes;

  /// Rival entries from other owners.
  final int fieldSize;

  /// Player camel ids entered in this round.
  final List<String> entries;
  List<ResultRow>? results;

  String get title {
    final ageName = _plural[age] ?? age.male;
    final sexName = sex == Sex.male ? ' (قعدان)' : '';
    return 'شوط $ageName$sexName - ${category.label}';
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'c': category.name,
        's': sex.name,
        'a': age.name,
        'p': prizes,
        'f': fieldSize,
        'e': entries,
        if (results != null) 'r': results!.map((r) => r.toJson()).toList(),
      };

  factory ContestRound.fromJson(Map<String, dynamic> j) => ContestRound(
        id: j['id'] as String,
        category: ColorCategory.values.byName(j['c'] as String),
        sex: Sex.values.byName(j['s'] as String),
        age: AgeClass.values.byName(j['a'] as String),
        prizes: (j['p'] as List).cast<int>(),
        fieldSize: j['f'] as int,
        entries: (j['e'] as List).cast<String>(),
        results: j['r'] == null
            ? null
            : (j['r'] as List)
                .map((e) => ResultRow.fromJson(e as Map<String, dynamic>))
                .toList(),
      );
}

const _plural = {
  AgeClass.hwar: 'الحيران',
  AgeClass.mafrood: 'المفاريد',
  AgeClass.laqi: 'اللقايا',
  AgeClass.haq: 'الحقايق',
  AgeClass.jatha: 'الجذاع',
  AgeClass.thani: 'الثنايا',
  AgeClass.rubaa: 'الرباع',
  AgeClass.sedees: 'السدس',
  AgeClass.mature: 'الحيل',
};

class Festival {
  Festival({
    required this.id,
    required this.name,
    required this.region,
    required this.tier,
    required this.registrationOpens,
    required this.registrationCloses,
    required this.judgingDay,
    required this.rounds,
    this.done = false,
  });

  final String id;
  final String name;
  final Region region;
  final FestivalTier tier;
  final int registrationOpens;
  final int registrationCloses;
  final int judgingDay;
  final List<ContestRound> rounds;
  bool done;

  bool isRegistrationOpen(int today) =>
      !done && today >= registrationOpens && today <= registrationCloses;

  Map<String, dynamic> toJson() => {
        'id': id,
        'n': name,
        'r': region.name,
        't': tier.name,
        'ro': registrationOpens,
        'rc': registrationCloses,
        'j': judgingDay,
        'rs': rounds.map((r) => r.toJson()).toList(),
        'done': done,
      };

  factory Festival.fromJson(Map<String, dynamic> j) => Festival(
        id: j['id'] as String,
        name: j['n'] as String,
        region: Region.byName(j['r'] as String),
        tier: FestivalTier.values.byName(j['t'] as String),
        registrationOpens: j['ro'] as int,
        registrationCloses: j['rc'] as int,
        judgingDay: j['j'] as int,
        rounds: (j['rs'] as List)
            .map((e) => ContestRound.fromJson(e as Map<String, dynamic>))
            .toList(),
        done: j['done'] as bool,
      );
}
