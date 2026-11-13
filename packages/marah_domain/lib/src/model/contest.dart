import '../catalog/catalog.dart';
import '../catalog/region.dart';
import '../common/ids.dart';
import '../common/time.dart';
import 'tampering.dart';

enum FestivalTier {
  local(1),
  regional(2),
  grand(3);

  const FestivalTier(this.level);
  final int level;
}

/// Which of the owner's registrations a round counts against (GDD 7: one
/// فردي and one جمل round per owner at a festival; the owner's decision of
/// 13 Nov 2026: one camel in one فردي round, المفاريد, the دق of القعدان and
/// البكار and الفحل وإنتاجه being other rounds).
enum RoundClass { fardi, jamal, other }

/// The Saudi round types (GDD 7, research-realism section 2). Who may enter
/// each is in Eligibility, their ages and prizes in ContestRules; numbers
/// marked (balance) there are game choices where the sources are silent.
///
/// The owner's decision of 13 Nov 2026: the individual rounds are built now;
/// the group ones ([enterable] false) come later with more farms. They are
/// on the festival's programme and the rivals show in them, but a player's
/// entry is refused ([ErrorCode.notYet]).
enum RoundKind {
  /// الفردي دق, by colour: a she-camel from after مفرود up to جذعة (real).
  fardiDiq('الفردي دق', RoundClass.fardi),

  /// الفردي جل, by colour: a she-camel from her second calf up to middle
  /// age (real).
  fardiJil('الفردي جل', RoundClass.fardi),

  /// مفاريد القعدان والبكار: the young, a year to two (real).
  mafareed('مفاريد', RoundClass.other),

  /// دق القعدان والبكار: from after مفرود up to جذعة (real).
  diq('دق', RoundClass.other),

  /// الفحل وإنتاجه: a bull shown with his offspring; the results only after
  /// the DNA tests confirm they are his (real).
  fahal('الفحل وإنتاجه', RoundClass.other),

  /// الجمل: a group from one owner, counted in متن (real: 20 to 100 head).
  jamal('الجمل', RoundClass.jamal),

  /// المنقية: the owner's picked herd of 15, 20 or 30 (real).
  manqiya('المنقية', RoundClass.other),

  /// منقية الجزيرة: the top منقية, with جائزة الشداد (real).
  jazeera('منقية الجزيرة', RoundClass.other),

  /// الهجيج: 15 she-camels with no lead camel; the first herd to finish an
  /// 18 to 20 km course wins (real).
  hajij('الهجيج', RoundClass.other),

  /// الطبع: how the herd answers its owner's call (real).
  tabaa('الطبع', RoundClass.other),

  /// البداوة: 40 head, مفرودة or older; its entrants cannot also enter
  /// فردي or جمل (real; built with the group rounds).
  badawa('البداوة', RoundClass.other);

  const RoundKind(this.label, this.roundClass);
  final String label;
  final RoundClass roundClass;

  /// Judged by the eye (the panel's marks); the others are run (الهجيج)
  /// or called (الطبع).
  bool get beauty => this != hajij && this != tabaa;

  /// One camel an entry.
  bool get single =>
      this == fardiDiq || this == fardiJil || this == mafareed || this == diq;

  /// A player may enter it now (the owner, 13 Nov 2026).
  bool get enterable => single || this == fahal;
}

/// The six checks of the festival day, in their order (GDD 7; research
/// section 3, the 2019 judging stages). Each can remove an entry.
enum Stage {
  /// الشريحة والشاهد: the camel is the one registered, by its chip, the only
  /// ownership document since 2020 (research section 2, [20]; the owner,
  /// 13 Nov 2026).
  chipWitness,

  /// فحص الهجين واللون والعمر: the colour's purity and the age by the teeth
  /// (a crossbred camel is refused at registration: its record shows it).
  breedColourAge,

  /// التحكيم الأولي: the preliminary judging, which keeps the best part of
  /// the field.
  preliminary,

  /// خبراء التلاعب: the tampering experts' clinical check.
  tamperingExperts,

  /// اللجنة الطبية: the medical committee (ultrasound, X-ray, thermal
  /// imaging, the lab and hormone tests) and the camel's health.
  medical,

  /// التحكيم النهائي: the final judging and the places.
  finalJudging,
}

/// Why a stage removed an entry.
enum RemovalReason {
  /// Stage 1: the chip did not read as the registration's.
  chip,

  /// Stage 1: a group short of its head (one of its camels died or left).
  short,

  /// Stage 2: the colour not pure for its family.
  colour,

  /// Stage 2: the teeth read as another age class.
  teeth,

  /// Stage 3: below the preliminary cut.
  cut,

  /// Stages 4 and 5: a treatment found.
  tampering,

  /// Stage 5: ill on the day.
  sick,

  /// The owner was barred, a treatment found on another of his camels.
  banned,
}

/// One owner's registration in a round: one camel in a فردي round, a group
/// in the others (for الفحل وإنتاجه the bull first, then his offspring).
/// [late] was registered after the festival's closing, with its fee.
class Entry {
  Entry({required this.ownerId, required this.camels, this.late = false});
  final OwnerId ownerId;
  final List<CamelId> camels;
  final bool late;

  /// The entry's first camel (a فردي round's only one, الفحل's bull).
  CamelId get camelId => camels.first;

  Map<String, Object?> toJson() => {
    'owner': ownerId.value,
    'camels': [for (final c in camels) c.value],
    'late': late,
  };

  static Entry fromJson(Map<String, Object?> j) => Entry(
    ownerId: OwnerId(j['owner']! as String),
    camels: [
      for (final c in j['camels']! as List<Object?>) CamelId(c! as String),
    ],
    late: j['late']! as bool,
  );
}

/// One entry's outcome in a round: placed ([rank]) or removed at a stage
/// ([removedAt], [reason]). Rival entries (generated for the day, not in the
/// registry) have no [camelId]; only the top ten of them are kept.
class ResultRow {
  const ResultRow({
    required this.rank,
    required this.camelName,
    required this.ownerId,
    required this.score,
    required this.prize,
    this.camelId,
    this.marks,
    this.removedAt,
    this.reason,
    this.head = 1,
  });

  /// The place in the final judging; null when a stage removed the entry.
  final int? rank;
  final String camelName;
  final OwnerId ownerId;

  /// Out of 100: the panel's average (a group's over its camels), or the
  /// run's or the call's mark (الهجيج, الطبع). 0 for an entry removed
  /// before it was judged.
  final double score;
  final int prize;
  final CamelId? camelId;

  /// Per-trait marks out of 10, for a registered single camel judged.
  final Map<Trait, double>? marks;
  final Stage? removedAt;
  final RemovalReason? reason;

  /// Camels in the entry.
  final int head;

  Map<String, Object?> toJson() => {
    'rank': rank,
    'name': camelName,
    'owner': ownerId.value,
    'score': score,
    'prize': prize,
    // the empty fields left out: most rows are rivals' places
    if (camelId != null) 'camel': camelId!.value,
    if (marks != null)
      'marks': {for (final e in marks!.entries) e.key.name: e.value},
    if (removedAt != null) 'removedAt': removedAt!.name,
    if (reason != null) 'reason': reason!.name,
    'head': head,
  };

  static ResultRow fromJson(Map<String, Object?> j) => ResultRow(
    rank: j['rank'] as int?,
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
    removedAt: j['removedAt'] == null
        ? null
        : Stage.values.byName(j['removedAt']! as String),
    reason: j['reason'] == null
        ? null
        : RemovalReason.values.byName(j['reason']! as String),
    head: j['head']! as int,
  );
}

/// A treatment the clinical check found on the day, kept with the round
/// until its stage is told (the owner, 13 Nov 2026: the six stages told one
/// by one through the day): then the fine, the ban and the news, for a
/// player ([camel] his camel), or the news, for a rival (no [camel]).
class Caught {
  const Caught({
    required this.stage,
    required this.owner,
    required this.name,
    required this.kind,
    required this.strength,
    required this.fine,
    this.camel,
  });

  /// The tampering experts or the medical committee.
  final Stage stage;
  final OwnerId owner;

  /// The camel's name.
  final String name;
  final TamperKind kind;
  final int strength;
  final int fine;
  final CamelId? camel;

  Map<String, Object?> toJson() => {
    'stage': stage.name,
    'owner': owner.value,
    'name': name,
    'kind': kind.name,
    'strength': strength,
    'fine': fine,
    if (camel != null) 'camel': camel!.value,
  };

  static Caught fromJson(Map<String, Object?> j) => Caught(
    stage: Stage.values.byName(j['stage']! as String),
    owner: OwnerId(j['owner']! as String),
    name: j['name']! as String,
    kind: TamperKind.values.byName(j['kind']! as String),
    strength: j['strength']! as int,
    fine: j['fine']! as int,
    camel: j['camel'] == null ? null : CamelId(j['camel']! as String),
  );
}

/// A round (شوط) on its own day of the festival. [category] and [sex] are
/// null where the round takes any; [size] is the head an entry shows.
class ContestRound {
  ContestRound({
    required this.id,
    required this.kind,
    required this.day,
    required this.rivals,
    this.category,
    this.sex,
    this.size = 1,
    this.legacyAge,
    List<Entry>? entries,
    this.results,
    this.field,
    this.entrants = 0,
    this.caught = 0,
    this.fines = 0,
    this.announceOn,
    this.paid = false,
    this.told = 0,
    List<Caught>? found,
  }) : entries = entries ?? [],
       found = found ?? [];

  final RoundId id;
  final RoundKind kind;
  final ColorCategory? category;
  final Sex? sex;
  final int size;
  final GameDay day;

  /// A round planned before save v8 (colour, sex and one age class, its
  /// eldest class taking every older camel): kept to that age rule.
  final AgeClass? legacyAge;

  /// Rival entries from owners outside the registry, generated on the day.
  final int rivals;
  final List<Entry> entries;
  List<ResultRow>? results;

  /// How many entries were left after each stage (index = Stage.index), the
  /// whole field counted: the day's story for the screens.
  List<int>? field;

  /// Entries on the day, before the first stage: the N of "5th of N".
  int entrants;

  /// Entries the tampering experts and the medical committee caught.
  int caught;

  /// Their fines, all owners'.
  int fines;

  /// For الفحل وإنتاجه: the day the results are announced, once the DNA
  /// tests are back; null for the others (announced on the day).
  GameDay? announceOn;

  /// The places announced and the prizes paid.
  bool paid;

  /// How many of the day's six stages have been told (Stage order): the
  /// round is judged at dawn, and each stage's outcome, its fines, bans,
  /// news and, at the last, the places, come at its hour
  /// (Balance.stageMinutes), or when the day is over. Nothing of a stage not
  /// told is in any view.
  int told;

  /// The treatments found on the day, until their stage is told.
  final List<Caught> found;

  bool get judged => results != null;

  /// Judged, and every stage of its day told.
  bool get over => judged && told >= Stage.values.length;

  Map<String, Object?> toJson() => {
    'id': id.value,
    'kind': kind.name,
    'cat': category?.name,
    'sex': sex?.name,
    'size': size,
    'day': day.value,
    'legacyAge': legacyAge?.name,
    'rivals': rivals,
    'entries': [for (final e in entries) e.toJson()],
    'results': results == null ? null : [for (final r in results!) r.toJson()],
    'field': field,
    'entrants': entrants,
    'caught': caught,
    'fines': fines,
    'announceOn': announceOn?.value,
    'paid': paid,
    'told': told,
    if (found.isNotEmpty) 'found': [for (final c in found) c.toJson()],
  };

  static ContestRound fromJson(Map<String, Object?> j) => ContestRound(
    id: RoundId(j['id']! as String),
    kind: RoundKind.values.byName(j['kind']! as String),
    category: j['cat'] == null
        ? null
        : ColorCategory.values.byName(j['cat']! as String),
    sex: j['sex'] == null ? null : Sex.values.byName(j['sex']! as String),
    size: j['size']! as int,
    day: GameDay(j['day']! as int),
    legacyAge: j['legacyAge'] == null
        ? null
        : AgeClass.values.byName(j['legacyAge']! as String),
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
    field: j['field'] == null
        ? null
        : [for (final n in j['field']! as List<Object?>) n! as int],
    entrants: j['entrants']! as int,
    caught: j['caught']! as int,
    fines: j['fines']! as int,
    announceOn: j['announceOn'] == null
        ? null
        : GameDay(j['announceOn']! as int),
    paid: j['paid']! as bool,
    told: j['told']! as int,
    found: [
      for (final c in (j['found'] as List<Object?>?) ?? const <Object?>[])
        Caught.fromJson(c! as Map<String, Object?>),
    ],
  );
}

/// A festival: registration opens on [opensOn] and closes on [closesOn]; a
/// late entry, with its fee, is taken until 72 hours before its round. The
/// rounds run from [startsOn] to [endsOn]. [season] is the year of the
/// autumn its season begins: the edition a ban counts (GDD 7.1).
class Festival {
  Festival({
    required this.id,
    required this.name,
    required this.region,
    required this.tier,
    required this.season,
    required this.opensOn,
    required this.closesOn,
    required this.startsOn,
    required this.endsOn,
    required this.rounds,
    this.done = false,
    List<CamelId>? scratched,
    Map<String, int>? trucked,
  }) : scratched = scratched ?? [],
       trucked = trucked ?? {};

  final FestivalId id;
  final String name;
  final Region region;
  final FestivalTier tier;
  final int season;
  final GameDay opensOn;
  final GameDay closesOn;
  final GameDay startsOn;
  final GameDay endsOn;
  final List<ContestRound> rounds;
  bool done;

  /// Camels withdrawn after the closing: their class was fixed then (GDD 7),
  /// so they are not entered again at this festival.
  final List<CamelId> scratched;

  /// The camels each player has trucked here (by owner id): they stay for
  /// the festival's days.
  final Map<String, int> trucked;

  /// Some round still takes entries (each until 72 hours before it).
  bool registrationOpen(GameDay today) =>
      !done && today >= opensOn && today <= endsOn;

  ContestRound? round(RoundId id) =>
      rounds.where((r) => r.id == id).firstOrNull;

  Map<String, Object?> toJson() => {
    'id': id.value,
    'name': name,
    'region': region.name,
    'tier': tier.name,
    'season': season,
    'opensOn': opensOn.value,
    'closesOn': closesOn.value,
    'startsOn': startsOn.value,
    'endsOn': endsOn.value,
    'rounds': [for (final r in rounds) r.toJson()],
    'done': done,
    'scratched': [for (final c in scratched) c.value],
    if (trucked.isNotEmpty) 'trucked': trucked,
  };

  static Festival fromJson(Map<String, Object?> j) => Festival(
    id: FestivalId(j['id']! as String),
    name: j['name']! as String,
    region: Region.values.byName(j['region']! as String),
    tier: FestivalTier.values.byName(j['tier']! as String),
    season: j['season']! as int,
    opensOn: GameDay(j['opensOn']! as int),
    closesOn: GameDay(j['closesOn']! as int),
    startsOn: GameDay(j['startsOn']! as int),
    endsOn: GameDay(j['endsOn']! as int),
    rounds: [
      for (final r in j['rounds']! as List<Object?>)
        ContestRound.fromJson(r! as Map<String, Object?>),
    ],
    done: j['done']! as bool,
    scratched: [
      for (final c in j['scratched']! as List<Object?>) CamelId(c! as String),
    ],
    trucked: {
      for (final e
          in ((j['trucked'] as Map<String, Object?>?) ?? const {}).entries)
        e.key: e.value! as int,
    },
  );
}
