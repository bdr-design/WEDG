import '../catalog/catalog.dart';
import '../common/ids.dart';
import '../common/result.dart';
import '../common/time.dart';
import '../model/camel.dart';
import '../model/contest.dart';
import '../model/game_state.dart';
import 'balance.dart';

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
    if (m.ageYears(today) < Balance.maleMinBreedingYears) {
      return const DomainError(ErrorCode.tooYoungToBreed, {
        'years': Balance.maleMinBreedingYears,
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

  static bool isListed(WorldState w, CamelId id) =>
      w.listings.values.any((l) => l.camelId == id);

  static bool isEntered(WorldState w, CamelId id) => w.festivals.values.any(
    (f) =>
        !f.done && f.rounds.any((r) => r.entries.any((e) => e.camelId == id)),
  );

  static DomainError? canSell(WorldState w, Camel? c, OwnerId actor) {
    final own = owned(c, actor);
    if (own != null) return own;
    if (isListed(w, c!.id)) return const DomainError(ErrorCode.alreadyListed);
    if (isEntered(w, c.id))
      return const DomainError(ErrorCode.enteredInContest);
    return null;
  }

  static DomainError? canEnter(
    WorldState w,
    Festival f,
    ContestRound r,
    Camel? c,
    OwnerId actor,
    GameDay today,
  ) {
    final own = owned(c, actor);
    if (own != null) return own;
    final camel = c!;
    if (!f.registrationOpen(today)) {
      return const DomainError(ErrorCode.registrationClosed);
    }
    if (camel.category != r.category) {
      return DomainError(ErrorCode.wrongCategory, {
        'category': r.category.name,
      });
    }
    if (camel.sex != r.sex) return const DomainError(ErrorCode.wrongSex);
    final ageThen = AgeClass.fromDays(f.judgedOn.daysSince(camel.born));
    // the eldest round (فاطر) stays open to every older camel, as the old
    // "mature" round was, until the Saudi rounds replace these (plan G1.4)
    final senior =
        r.age == AgeClass.fater && ageThen.index > AgeClass.fater.index;
    if (ageThen != r.age && !senior) {
      return DomainError(ErrorCode.wrongAgeClass, {'age': ageThen.name});
    }
    if (!camel.homeBred &&
        f.judgedOn.daysSince(camel.acquiredOn) <
            Balance.ownershipDaysBeforeJudging) {
      return const DomainError(ErrorCode.ownershipTooRecent, {
        'days': Balance.ownershipDaysBeforeJudging,
      });
    }
    if (f.rounds.any((x) => x.entries.any((e) => e.camelId == camel.id))) {
      return const DomainError(ErrorCode.alreadyEnteredInFestival);
    }
    if (isListed(w, camel.id))
      return const DomainError(ErrorCode.listedForSale);
    if (camel.health == HealthStatus.sick)
      return const DomainError(ErrorCode.sick);
    final mine = r.entries.where((e) => e.ownerId == actor).length;
    if (mine >= Balance.maxEntriesPerOwnerInRound) {
      return const DomainError(ErrorCode.roundOwnerLimit, {
        'max': Balance.maxEntriesPerOwnerInRound,
      });
    }
    return null;
  }
}
