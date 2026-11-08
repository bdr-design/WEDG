import 'catalog.dart';

const playerOwnerId = 'player';

/// Short reference to a parent, kept even when the parent itself is not in
/// the save (a stud from another owner, a camel that was sold).
class PedigreeRef {
  const PedigreeRef({
    required this.id,
    required this.name,
    required this.category,
  });

  final String id;
  final String name;
  final ColorCategory category;

  Map<String, dynamic> toJson() => {'id': id, 'n': name, 'c': category.name};

  factory PedigreeRef.fromJson(Map<String, dynamic> j) => PedigreeRef(
        id: j['id'] as String,
        name: j['n'] as String,
        category: ColorCategory.values.byName(j['c'] as String),
      );
}

enum HealthStatus {
  healthy('سليمة'),
  sick('مريضة'),
  treated('تحت العلاج');

  const HealthStatus(this.label);
  final String label;
}

/// A mating and what came of it. The sire's genes are stored here so the calf
/// can be bred even if the stud belongs to someone else.
class Pregnancy {
  Pregnancy({
    required this.sire,
    required this.sireGenes,
    required this.matedDay,
    required this.checkDay,
    required this.dueDay,
    required this.conceived,
    this.confirmed = false,
  });

  final PedigreeRef sire;
  final Map<Trait, double> sireGenes;
  final int matedDay;

  /// Day the pregnancy check (تشويل / فحص) reveals the result.
  final int checkDay;
  final int dueDay;

  /// Hidden until [checkDay]: whether the mating took.
  final bool conceived;
  bool confirmed;

  Map<String, dynamic> toJson() => {
        'sire': sire.toJson(),
        'g': _genesToJson(sireGenes),
        'm': matedDay,
        'k': checkDay,
        'due': dueDay,
        'ok': conceived,
        'cf': confirmed,
      };

  factory Pregnancy.fromJson(Map<String, dynamic> j) => Pregnancy(
        sire: PedigreeRef.fromJson(j['sire'] as Map<String, dynamic>),
        sireGenes: _genesFromJson(j['g'] as Map<String, dynamic>),
        matedDay: j['m'] as int,
        checkDay: j['k'] as int,
        dueDay: j['due'] as int,
        conceived: j['ok'] as bool,
        confirmed: j['cf'] as bool,
      );
}

/// A placing at a contest, kept on the camel's record (سجل المشاركات).
class ContestTitle {
  const ContestTitle({
    required this.festival,
    required this.round,
    required this.rank,
    required this.day,
    required this.tier,
    required this.prize,
  });

  final String festival;
  final String round;
  final int rank;
  final int day;

  /// 1 = local, 2 = regional, 3 = the grand season festival.
  final int tier;
  final int prize;

  Map<String, dynamic> toJson() => {
        'f': festival,
        'r': round,
        'k': rank,
        'd': day,
        't': tier,
        'p': prize,
      };

  factory ContestTitle.fromJson(Map<String, dynamic> j) => ContestTitle(
        festival: j['f'] as String,
        round: j['r'] as String,
        rank: j['k'] as int,
        day: j['d'] as int,
        tier: j['t'] as int,
        prize: j['p'] as int,
      );
}

class Camel {
  Camel({
    required this.id,
    required this.name,
    required this.sex,
    required this.category,
    required this.birthDay,
    required this.ownerId,
    required this.chip,
    required this.genes,
    required this.env,
    required this.condition,
    this.health = HealthStatus.healthy,
    this.sickDays = 0,
    this.illness,
    this.pregnancy,
    this.lastCalvingDay,
    this.calvings = 0,
    this.lastServiceDay,
    this.sire,
    this.dam,
    List<ContestTitle>? titles,
    this.acquiredDay = 0,
    this.purchasePrice = 0,
    this.crossbred = false,
  }) : titles = titles ?? [];

  final String id;
  String name;
  final Sex sex;
  final ColorCategory category;
  final int birthDay;
  String ownerId;

  /// Microchip number (الشريحة الإلكترونية), required to enter contests.
  final String chip;

  /// Breeding values per trait (0–100). Hidden from the player: what the
  /// camel passes on. The player sees only what the body shows.
  final Map<Trait, double> genes;

  /// Permanent non-genetic deviation per trait (rearing, luck), fixed at birth.
  final Map<Trait, double> env;

  /// Body condition (الحالة / السمنة), 0–100; follows feed and care.
  double condition;

  HealthStatus health;
  int sickDays;
  String? illness;

  Pregnancy? pregnancy;
  int? lastCalvingDay;
  int calvings;

  /// For males: last day it covered a female.
  int? lastServiceDay;

  final PedigreeRef? sire;
  final PedigreeRef? dam;
  final List<ContestTitle> titles;

  int acquiredDay;
  int purchasePrice;

  /// Parents from different colour families (خلط).
  final bool crossbred;

  bool get isPlayers => ownerId == playerOwnerId;

  int ageDays(int today) => today - birthDay;
  int ageYears(int today) => ageDays(today) ~/ 365;
  AgeClass ageClass(int today) => AgeClass.fromDays(ageDays(today));
  String ageLabel(int today) => ageClass(today).labelFor(sex);

  bool get isPregnantConfirmed => pregnancy?.confirmed == true;
  bool get awaitingCheck => pregnancy != null && !pregnancy!.confirmed;

  PedigreeRef get ref => PedigreeRef(id: id, name: name, category: category);

  Map<String, dynamic> toJson() => {
        'id': id,
        'n': name,
        's': sex.name,
        'c': category.name,
        'b': birthDay,
        'o': ownerId,
        'chip': chip,
        'g': _genesToJson(genes),
        'e': _genesToJson(env),
        'cond': double.parse(condition.toStringAsFixed(2)),
        'h': health.name,
        'sd': sickDays,
        if (illness != null) 'ill': illness,
        if (pregnancy != null) 'p': pregnancy!.toJson(),
        if (lastCalvingDay != null) 'lc': lastCalvingDay,
        'cv': calvings,
        if (lastServiceDay != null) 'ls': lastServiceDay,
        if (sire != null) 'sire': sire!.toJson(),
        if (dam != null) 'dam': dam!.toJson(),
        't': titles.map((t) => t.toJson()).toList(),
        'ad': acquiredDay,
        'pp': purchasePrice,
        'x': crossbred,
      };

  factory Camel.fromJson(Map<String, dynamic> j) => Camel(
        id: j['id'] as String,
        name: j['n'] as String,
        sex: Sex.values.byName(j['s'] as String),
        category: ColorCategory.values.byName(j['c'] as String),
        birthDay: j['b'] as int,
        ownerId: j['o'] as String,
        chip: j['chip'] as String,
        genes: _genesFromJson(j['g'] as Map<String, dynamic>),
        env: _genesFromJson(j['e'] as Map<String, dynamic>),
        condition: (j['cond'] as num).toDouble(),
        health: HealthStatus.values.byName(j['h'] as String),
        sickDays: j['sd'] as int,
        illness: j['ill'] as String?,
        pregnancy: j['p'] == null
            ? null
            : Pregnancy.fromJson(j['p'] as Map<String, dynamic>),
        lastCalvingDay: j['lc'] as int?,
        calvings: j['cv'] as int,
        lastServiceDay: j['ls'] as int?,
        sire: j['sire'] == null
            ? null
            : PedigreeRef.fromJson(j['sire'] as Map<String, dynamic>),
        dam: j['dam'] == null
            ? null
            : PedigreeRef.fromJson(j['dam'] as Map<String, dynamic>),
        titles: (j['t'] as List)
            .map((e) => ContestTitle.fromJson(e as Map<String, dynamic>))
            .toList(),
        acquiredDay: j['ad'] as int,
        purchasePrice: j['pp'] as int,
        crossbred: j['x'] as bool,
      );
}

Map<String, double> _genesToJson(Map<Trait, double> g) => {
      for (final e in g.entries)
        e.key.name: double.parse(e.value.toStringAsFixed(2)),
    };

Map<Trait, double> _genesFromJson(Map<String, dynamic> j) => {
      for (final t in Trait.values) t: (j[t.name] as num?)?.toDouble() ?? 50,
    };
