import '../catalog/catalog.dart';
import '../catalog/region.dart';
import '../common/ids.dart';
import '../common/time.dart';

enum FestivalTier {
  local(1),
  regional(2),
  grand(3);

  const FestivalTier(this.level);
  final int level;
}

class Entry {
  const Entry({required this.camelId, required this.ownerId});
  final CamelId camelId;
  final OwnerId ownerId;

  Map<String, Object?> toJson() => {
    'camel': camelId.value,
    'owner': ownerId.value,
  };

  static Entry fromJson(Map<String, Object?> j) => Entry(
    camelId: CamelId(j['camel']! as String),
    ownerId: OwnerId(j['owner']! as String),
  );
}

/// One placing in a round. Entries from outside the registry (rival camels
/// generated for the day) have no [camelId].
class ResultRow {
  const ResultRow({
    required this.rank,
    required this.camelName,
    required this.ownerId,
    required this.score,
    required this.prize,
    this.camelId,
    this.marks,
  });

  final int rank;
  final String camelName;
  final OwnerId ownerId;

  /// Panel average out of 100.
  final double score;
  final int prize;
  final CamelId? camelId;

  /// Per-trait marks out of 10 (kept for registered entries).
  final Map<Trait, double>? marks;

  Map<String, Object?> toJson() => {
    'rank': rank,
    'name': camelName,
    'owner': ownerId.value,
    'score': score,
    'prize': prize,
    'camel': camelId?.value,
    'marks': marks == null
        ? null
        : {for (final e in marks!.entries) e.key.name: e.value},
  };

  static ResultRow fromJson(Map<String, Object?> j) => ResultRow(
    rank: j['rank']! as int,
    camelName: j['name']! as String,
    ownerId: OwnerId(j['owner']! as String),
    score: (j['score']! as num).toDouble(),
    prize: j['prize']! as int,
    camelId: j['camel'] == null ? null : CamelId(j['camel']! as String),
    marks: j['marks'] == null
        ? null
        : {
            for (final e in (j['marks']! as Map<String, Object?>).entries)
              Trait.values.byName(e.key): (e.value! as num).toDouble(),
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
    required this.rivals,
    List<Entry>? entries,
    this.results,
  }) : entries = entries ?? [];

  final RoundId id;
  final ColorCategory category;
  final Sex sex;
  final AgeClass age;

  /// Rival entries from owners outside the registry, generated on the day.
  final int rivals;
  final List<Entry> entries;
  List<ResultRow>? results;

  Map<String, Object?> toJson() => {
    'id': id.value,
    'cat': category.name,
    'sex': sex.name,
    'age': age.name,
    'rivals': rivals,
    'entries': [for (final e in entries) e.toJson()],
    'results': results == null ? null : [for (final r in results!) r.toJson()],
  };

  static ContestRound fromJson(Map<String, Object?> j) => ContestRound(
    id: RoundId(j['id']! as String),
    category: ColorCategory.values.byName(j['cat']! as String),
    sex: Sex.values.byName(j['sex']! as String),
    age: AgeClass.values.byName(j['age']! as String),
    rivals: j['rivals']! as int,
    entries: [
      for (final e in j['entries']! as List<Object?>)
        Entry.fromJson(e! as Map<String, Object?>),
    ],
    results: j['results'] == null
        ? null
        : [
            for (final r in j['results']! as List<Object?>)
              ResultRow.fromJson(r! as Map<String, Object?>),
          ],
  );
}

class Festival {
  Festival({
    required this.id,
    required this.name,
    required this.region,
    required this.tier,
    required this.opensOn,
    required this.closesOn,
    required this.judgedOn,
    required this.rounds,
    this.done = false,
  });

  final FestivalId id;
  final String name;
  final Region region;
  final FestivalTier tier;
  final GameDay opensOn;
  final GameDay closesOn;
  final GameDay judgedOn;
  final List<ContestRound> rounds;
  bool done;

  bool registrationOpen(GameDay today) =>
      !done && today >= opensOn && today <= closesOn;

  Map<String, Object?> toJson() => {
    'id': id.value,
    'name': name,
    'region': region.name,
    'tier': tier.name,
    'opensOn': opensOn.value,
    'closesOn': closesOn.value,
    'judgedOn': judgedOn.value,
    'rounds': [for (final r in rounds) r.toJson()],
    'done': done,
  };

  static Festival fromJson(Map<String, Object?> j) => Festival(
    id: FestivalId(j['id']! as String),
    name: j['name']! as String,
    region: Region.values.byName(j['region']! as String),
    tier: FestivalTier.values.byName(j['tier']! as String),
    opensOn: GameDay(j['opensOn']! as int),
    closesOn: GameDay(j['closesOn']! as int),
    judgedOn: GameDay(j['judgedOn']! as int),
    rounds: [
      for (final r in j['rounds']! as List<Object?>)
        ContestRound.fromJson(r! as Map<String, Object?>),
    ],
    done: j['done']! as bool,
  );
}
