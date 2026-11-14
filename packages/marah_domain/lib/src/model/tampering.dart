import '../catalog/catalog.dart';
import '../common/ids.dart';
import '../common/time.dart';

/// The secret treatments that make a camel look better on judging day (GDD
/// 7.1, the owner's decision of 12 Nov 2026: cheating is allowed, with its
/// risk). All are banned in the Kingdom, at festivals and outside them
/// (research section 3; MEWA under the animal welfare law).
///
/// (field) [fineCap] is the most a festival fines for one camel: SAR 100,000
/// for Botox, fillers (silicone oil, hyaluronic acid), hormones and
/// stretching the lip (doubled from 50,000 in December 2021), SAR 30,000 for
/// filing the teeth, cutting the tail or dyeing (research section 3, [33]
/// [95]). Botox is the cheat caught most, then the fillers (real).
///
/// (balance) Everything else is a game choice: [traits], the features it
/// raises: the region of the body it works on (the head and neck for the
/// face's treatments, the top line and legs for hormones, the hindquarters
/// for the tail, the coat for dye) and the overall bearing, الوقفة; spread so
/// no one feature stands out (Balance.tamperFeatureCapPerLevel); [experts] and [medical], the chance the tampering experts and
/// the medical committee find a light treatment (a stronger one is found
/// more often: Tampering.detectChance); [lastsDays], how long it shows and
/// can be found; [price], what the secret vet takes for a light one.
enum TamperKind {
  botox(
    'بوتوكس',
    fineCap: 100000,
    traits: {
      Trait.head,
      Trait.nose,
      Trait.lips,
      Trait.ears,
      Trait.neck,
      Trait.stance,
    },
    experts: 0.20,
    medical: 0.25,
    lastsDays: 120,
    price: 5000,
  ),
  filler(
    'فيلر',
    fineCap: 100000,
    traits: {
      Trait.head,
      Trait.nose,
      Trait.lips,
      Trait.ears,
      Trait.neck,
      Trait.stance,
    },
    experts: 0.15,
    medical: 0.22,
    lastsDays: 180,
    price: 6000,
  ),
  hormones(
    'هرمونات',
    fineCap: 100000,
    traits: {Trait.hump, Trait.back, Trait.fore, Trait.hind, Trait.stance},
    experts: 0.04,
    medical: 0.25,
    lastsDays: 45,
    price: 4000,
  ),
  lipStretch(
    'شد الشفة',
    fineCap: 100000,
    traits: {
      Trait.head,
      Trait.nose,
      Trait.lips,
      Trait.ears,
      Trait.neck,
      Trait.stance,
    },
    experts: 0.22,
    medical: 0.08,
    lastsDays: 365,
    price: 8000,
  ),
  teethFiling(
    'برد الأسنان',
    fineCap: 30000,
    traits: {
      Trait.head,
      Trait.nose,
      Trait.lips,
      Trait.ears,
      Trait.neck,
      Trait.stance,
    },
    experts: 0.18,
    medical: 0.10,
    lastsDays: 365,
    price: 2000,
  ),
  tailCut(
    'قص الذيل',
    fineCap: 30000,
    traits: {Trait.hind, Trait.back, Trait.hump, Trait.stance},
    experts: 0.28,
    medical: 0.0,
    lastsDays: 365,
    price: 1000,
  ),
  dye(
    'الصبغ',
    fineCap: 30000,
    traits: {Trait.coat, Trait.stance},
    experts: 0.20,
    medical: 0.10,
    lastsDays: 30,
    price: 1500,
  );

  const TamperKind(
    this.label, {
    required this.fineCap,
    required this.traits,
    required this.experts,
    required this.medical,
    required this.lastsDays,
    required this.price,
  });

  final String label;
  final int fineCap;
  final Set<Trait> traits;
  final double experts;
  final double medical;
  final int lastsDays;
  final int price;
}

/// One secret treatment on a camel: [strength] 1 (light) to 3 (heavy). It
/// is in the camel itself and goes with her when she is sold (the owner, 13
/// Nov 2026); [by] had it done (null: an owner outside the game's players),
/// [knownBy] are the players who know of it (he, and a buyer whose vet
/// found it). No view shows it to anyone else; what anyone sees is how she
/// looks.
class Tampering {
  Tampering({
    required this.kind,
    required this.strength,
    required this.on,
    required this.until,
    this.by,
    List<OwnerId>? knownBy,
    List<OwnerId>? boughtKnowing,
  }) : knownBy = knownBy ?? [],
       boughtKnowing = boughtKnowing ?? [];

  final TamperKind kind;
  final int strength;
  final GameDay on;

  /// The last day it shows (and can be found).
  final GameDay until;
  final OwnerId? by;
  final List<OwnerId> knownBy;

  /// The players who bought her knowing of it (since save v12): they may not
  /// sell her declared (the owner, 14 Nov 2026, item 12).
  final List<OwnerId> boughtKnowing;

  bool activeOn(GameDay day) => day >= on && day <= until;

  Map<String, Object?> toJson() => {
    'kind': kind.name,
    'strength': strength,
    'on': on.value,
    'until': until.value,
    if (by != null) 'by': by!.value,
    if (knownBy.isNotEmpty) 'knownBy': [for (final o in knownBy) o.value],
    if (boughtKnowing.isNotEmpty)
      'boughtKnowing': [for (final o in boughtKnowing) o.value],
  };

  static Tampering fromJson(Map<String, Object?> j) => Tampering(
    kind: TamperKind.values.byName(j['kind']! as String),
    strength: j['strength']! as int,
    on: GameDay(j['on']! as int),
    until: GameDay(j['until']! as int),
    by: j['by'] == null ? null : OwnerId(j['by']! as String),
    knownBy: [
      for (final o in (j['knownBy'] as List<Object?>?) ?? const <Object?>[])
        OwnerId(o! as String),
    ],
    boughtKnowing: [
      for (final o
          in (j['boughtKnowing'] as List<Object?>?) ?? const <Object?>[])
        OwnerId(o! as String),
    ],
  );
}
