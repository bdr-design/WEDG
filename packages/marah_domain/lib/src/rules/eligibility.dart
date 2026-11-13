import '../catalog/catalog.dart';
import '../common/ids.dart';
import '../common/result.dart';
import '../common/time.dart';
import '../model/camel.dart';
import '../model/contest.dart';
import '../model/game_state.dart';
import 'balance.dart';
import 'contest_rules.dart';

/// Checks shared by command handlers and by the views the app shows, so the
/// buttons and the rules can never disagree. Each returns null when allowed.
class Eligibility {
  const Eligibility._();

  static bool isBreedingSeason(GameDay day) =>
      Balance.breedingMonths.contains(day.month);

  static DomainError? owned(Camel? c, OwnerId actor) {
    if (c == null || !c.isAlive) return const DomainError(ErrorCode.notFound);
    if (c.ownerId != actor) return const DomainError(ErrorCode.notYourCamel);
    return null;
  }

  static DomainError? femaleCanBreed(Camel f, GameDay today) {
    if (f.sex != Sex.female) return const DomainError(ErrorCode.notFemale);
    if (onTheWay(f, today)) return const DomainError(ErrorCode.onTheWay);
    if (f.ageDays(today) < Balance.femaleMinBreedingDays) {
      return const DomainError(ErrorCode.tooYoungToBreed, {
        'days': Balance.femaleMinBreedingDays,
      });
    }
    final p = f.pregnancy;
    if (p != null) {
      return DomainError(
        p.confirmed
            ? ErrorCode.alreadyPregnant
            : ErrorCode.awaitingPregnancyCheck,
      );
    }
    final calved = f.lastCalvedOn;
    if (calved != null &&
        today.daysSince(calved) < Balance.postCalvingRestDays) {
      return DomainError(ErrorCode.restingAfterCalving, {
        'days': Balance.postCalvingRestDays - today.daysSince(calved),
      });
    }
    if (f.health != HealthStatus.healthy) {
      return const DomainError(ErrorCode.sick);
    }
    if (!isBreedingSeason(today)) {
      return const DomainError(ErrorCode.notBreedingSeason);
    }
    return null;
  }

  static DomainError? bullCanServe(Camel m, GameDay today) {
    if (!m.isAlive) return const DomainError(ErrorCode.notFound);
    if (m.sex != Sex.male) return const DomainError(ErrorCode.notMale);
    if (onTheWay(m, today)) return const DomainError(ErrorCode.onTheWay);
    if (m.ageYears(today) < Balance.maleMinBreedingYears) {
      return const DomainError(ErrorCode.tooYoungToBreed, {
        'days': Balance.maleMinBreedingYears * 365,
      });
    }
    if (m.health != HealthStatus.healthy) {
      return const DomainError(ErrorCode.sick);
    }
    final last = m.lastServiceOn;
    if (last != null && today.daysSince(last) < Balance.studRestDays) {
      return const DomainError(ErrorCode.bullResting);
    }
    return null;
  }

  /// Bought in the market and still on the truck to the farm
  /// ([Balance.camelTruckDays]): the player's, but not there yet.
  static bool onTheWay(Camel c, GameDay today) =>
      !c.homeBred && today.daysSince(c.acquiredOn) < Balance.camelTruckDays;

  static bool isListed(WorldState w, CamelId id) =>
      w.listings.values.any((l) => l.camelId == id);

  /// In a round of a festival still running, not yet judged.
  static bool isEntered(WorldState w, CamelId id) => w.festivals.values.any(
    (f) =>
        !f.done &&
        f.rounds.any(
          (r) => !r.judged && r.entries.any((e) => e.camels.contains(id)),
        ),
  );

  static DomainError? canSell(WorldState w, Camel? c, OwnerId actor) {
    final own = owned(c, actor);
    if (own != null) return own;
    if (onTheWay(c!, w.day)) return const DomainError(ErrorCode.onTheWay);
    if (isListed(w, c.id)) return const DomainError(ErrorCode.alreadyListed);
    if (isEntered(w, c.id)) {
      return const DomainError(ErrorCode.enteredInContest);
    }
    return null;
  }

  /// The last day [r] takes an entry: 72 hours before it (real).
  static GameDay lastEntryDay(ContestRound r) =>
      r.day - (Balance.lateEntryHoursBefore + 23) ~/ 24;

  /// Registered after the festival's closing (with the late fee).
  static bool isLate(Festival f, GameDay today) => today > f.closesOn;

  /// The owner is barred from [f]'s edition (GDD 7.1).
  static int? ownerBan(WorldState w, OwnerId owner, Festival f) {
    final through = w.bans[owner];
    return through != null && through >= f.season ? through : null;
  }

  /// The checks of [canEnter] that are the owner's, whatever camels he
  /// brings: the round taking entries today, a ban, the group rounds not yet
  /// open, his one فردي camel and his entries in the round.
  static DomainError? ownerMayEnter(
    WorldState w,
    Festival f,
    ContestRound r,
    OwnerId actor,
    GameDay today,
  ) {
    if (f.done || today < f.opensOn || today > lastEntryDay(r)) {
      return const DomainError(ErrorCode.registrationClosed);
    }
    final ban = ownerBan(w, actor, f);
    if (ban != null) {
      return DomainError(ErrorCode.banned, {'through': ban});
    }
    if (!r.kind.enterable) return const DomainError(ErrorCode.notYet);
    final mine = r.entries.where((e) => e.ownerId == actor).length;
    if (r.kind.roundClass == RoundClass.fardi) {
      // one camel in one فردي round a festival (the owner, 13 Nov 2026)
      if (f.rounds.any(
        (x) =>
            x.kind.roundClass == RoundClass.fardi &&
            x.entries.any((e) => e.ownerId == actor),
      )) {
        return const DomainError(ErrorCode.oneFardiRound);
      }
    } else {
      final most = r.kind == RoundKind.fahal
          ? 1
          : Balance.maxEntriesPerOwnerInRound;
      if (mine >= most) {
        return DomainError(ErrorCode.roundOwnerLimit, {'max': most});
      }
    }
    return null;
  }

  /// Why [camels] may not be entered by [actor] in [r] of [f] today, or
  /// null (GDD 7, research section 4: the round's type, colour, sex and age
  /// on its day, the owner's one فردي and one جمل round, no camel in two
  /// rounds, the closing and the late entry till 72 hours before).
  static DomainError? canEnter(
    WorldState w,
    Festival f,
    ContestRound r,
    List<Camel?> camels,
    OwnerId actor,
    GameDay today,
  ) {
    final owner = ownerMayEnter(w, f, r, actor, today);
    if (owner != null) return owner;
    if (camels.length != r.size) {
      return DomainError(ErrorCode.wrongGroupSize, {'size': r.size});
    }
    final ids = <CamelId>{};
    for (final c in camels) {
      final problem = _camelFits(w, f, r, c, actor);
      if (problem != null) return problem;
      if (!ids.add(c!.id)) {
        return const DomainError(ErrorCode.alreadyEnteredInFestival);
      }
    }
    if (r.kind == RoundKind.fahal) {
      final bull = camels.first!;
      if (bull.sex != Sex.male) return const DomainError(ErrorCode.notMale);
      if (bull.ageYears(r.day) < Balance.maleMinBreedingYears) {
        return const DomainError(ErrorCode.tooYoungToBreed, {
          'days': Balance.maleMinBreedingYears * 365,
        });
      }
      for (final c in camels.skip(1)) {
        if (c!.sire?.id != bull.id) {
          return const DomainError(ErrorCode.notOffspring);
        }
      }
    }
    return null;
  }

  static DomainError? _camelFits(
    WorldState w,
    Festival f,
    ContestRound r,
    Camel? c,
    OwnerId actor,
  ) {
    final own = owned(c, actor);
    if (own != null) return own;
    final camel = c!;
    if ((camel.bannedThrough ?? -1) >= f.season) {
      return DomainError(ErrorCode.camelBanned, {
        'through': camel.bannedThrough!,
      });
    }
    if (camel.crossbred) return const DomainError(ErrorCode.crossbred);
    final cat = r.category;
    if (cat != null && camel.category != cat) {
      return DomainError(ErrorCode.wrongCategory, {'category': cat.name});
    }
    final sex = r.sex;
    final fahalBull = r.kind == RoundKind.fahal;
    if (sex != null && camel.sex != sex) {
      return const DomainError(ErrorCode.wrongSex);
    }
    final ageDays = r.day.daysSince(camel.born);
    final age = AgeClass.fromDays(ageDays);
    final legacy = r.legacyAge;
    final fits = legacy != null
        // a round from before save v8: its class, the eldest (فاطر) taking
        // every older camel
        ? age == legacy ||
              (legacy == AgeClass.fater && age.index > legacy.index)
        : fahalBull || ContestRules.ageFits(r.kind, age, ageDays);
    if (!fits) {
      return DomainError(ErrorCode.wrongAgeClass, {'age': age.name});
    }
    if (legacy == null &&
        r.kind == RoundKind.fardiJil &&
        camel.calvings < ContestRules.jilCalvings) {
      return const DomainError(ErrorCode.tooFewCalvings, {
        'calvings': ContestRules.jilCalvings,
      });
    }
    if (!camel.homeBred &&
        r.day.daysSince(camel.acquiredOn) <
            Balance.ownershipDaysBeforeJudging) {
      return const DomainError(ErrorCode.ownershipTooRecent, {
        'days': Balance.ownershipDaysBeforeJudging,
      });
    }
    if (f.scratched.contains(camel.id)) {
      return const DomainError(ErrorCode.scratched);
    }
    if (f.rounds.any(
      (x) => x.entries.any((e) => e.camels.contains(camel.id)),
    )) {
      return const DomainError(ErrorCode.alreadyEnteredInFestival);
    }
    if (isListed(w, camel.id)) {
      return const DomainError(ErrorCode.listedForSale);
    }
    if (camel.health == HealthStatus.sick) {
      return const DomainError(ErrorCode.sick);
    }
    return null;
  }
}
