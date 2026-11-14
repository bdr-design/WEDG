// Being away: the one mechanism (task T15, docs/proposals/rush_and_calendar.md
// section 5). The calendar's jump uses it, and the hunting design's trip and
// camp of days will. It only advances days and reads conditions: what the
// days do is the daily pipeline's, the same code a played day runs (a
// caller's daily work belongs there too, keyed by state, never here).
import 'common/result.dart';
import 'common/time.dart';
import 'events.dart';
import 'game.dart';
import 'model/camel.dart';
import 'model/contest.dart';
import 'model/player.dart';
import 'rules/account.dart';
import 'rules/eligibility.dart';

/// Why a stretch away ended before its day, or that it reached it.
enum AwayStopKind {
  /// A camel fell ill (no vet's contract treated her).
  illness,

  /// A camel died of illness or thirst.
  death,

  /// A store came down to its last days, or a day went short (no standing
  /// order covers it).
  supply,

  /// The money went below zero.
  money,

  /// The merchant's account reached its limit, or the standing order or
  /// the vet's contract was refused.
  account,

  /// A fine: a treatment found in his herd, at a sale or outside one.
  fine,

  /// An offer on his listing (it lasts Balance.offerValidDays).
  offer,

  /// His round's day: landed before its first stage is told.
  round,

  /// A festival's registration closes in 3 days, he could enter and has not
  /// (once a festival).
  registration,

  /// The breeding season opens with a female the engine lets him breed
  /// (once a year).
  breeding,

  /// The herd outgrew its pens.
  crowded,

  /// A caller's own condition (the hunt: the camp's supplies out, the
  /// trapping season's end, the trip's chosen end, his falcon's care).
  extra,

  /// The player stopped it («وقّف هنا»).
  cancelled,

  /// The day asked was reached.
  target,
}

/// Where a stretch stopped: the kind, the day, and what it is about (a
/// camel, a festival, a supply), with a name to say.
class AwayStop {
  const AwayStop(this.kind, this.day, {this.subject, this.name, this.extra});
  final AwayStopKind kind;
  final GameDay day;
  final String? subject;
  final String? name;

  /// A caller's own reason, for [AwayStopKind.extra].
  final String? extra;

  Map<String, Object?> toJson() => {
    'kind': kind.name,
    'day': day.value,
    'subject': subject,
    'name': name,
    'extra': extra,
  };
}

/// What happened over a stretch, counted as it ran (never a list of every
/// event: 14,000 of them over a year at 10,000 head).
class AwaySummary {
  int days = 0;
  int milk = 0;
  final Map<LedgerCategory, int> spent = {};
  final List<String> born = [];
  int calvesLost = 0;
  final List<String> fellIll = [];
  int recovered = 0;
  int treated = 0;
  final Map<DeathCause, int> deaths = {};
  final List<String> diedOfIllnessOrThirst = [];
  int delivered = 0;
  final List<Facility> built = [];
  final List<String> registrationsOpened = [];
  int offers = 0;
  int wagesPaid = 0;
  int listingsExpired = 0;
  int pregnanciesConfirmed = 0;
  int pregnanciesFailed = 0;
  int standingOrders = 0;

  /// A caller's own lines (the hunt: days out, birds seen and caught,
  /// released): name to count.
  final Map<String, int> extra = {};

  Map<String, Object?> toJson() => {
    'days': days,
    'milk': milk,
    'spent': {for (final e in spent.entries) e.key.name: e.value},
    'born': born,
    'calvesLost': calvesLost,
    'fellIll': fellIll,
    'recovered': recovered,
    'treated': treated,
    'deaths': {for (final e in deaths.entries) e.key.name: e.value},
    'diedOfIllnessOrThirst': diedOfIllnessOrThirst,
    'delivered': delivered,
    'built': [for (final f in built) f.name],
    'registrationsOpened': registrationsOpened,
    'offers': offers,
    'wagesPaid': wagesPaid,
    'listingsExpired': listingsExpired,
    'pregnanciesConfirmed': pregnanciesConfirmed,
    'pregnanciesFailed': pregnanciesFailed,
    'standingOrders': standingOrders,
    'extra': extra,
  };
}

/// A caller's own stop condition, read after each day: a reason when it
/// should stop, else null.
typedef AwayCondition = String? Function(Game game);

/// A stretch away: a [target] day and the stops (section 5's plan). The
/// landing minute is the runtime's (EngineCore.away), not the domain's.
/// A caller's own counting of a day (the hunt: days out, birds seen and
/// caught, released), into [AwaySummary.extra]; it reads the game and the
/// day's events and changes nothing (a caller's daily work is a daily
/// system, never this).
typedef AwayCounter = void Function(
  Game game,
  List<DomainEvent> dayEvents,
  AwaySummary summary,
);

class AwayPlan {
  const AwayPlan(
    this.target, {
    this.extra = const [],
    this.counters = const [],
    this.card = const {},
  });
  final GameDay target;

  /// A caller's own stop conditions, read after each day with the others.
  final List<AwayCondition> extra;

  /// A caller's own lines for the summary, counted as the days run.
  final List<AwayCounter> counters;

  /// A caller's own lines for the card before leaving (gear, camp supplies,
  /// distance), carried to the result for the phone to show with its own.
  final Map<String, Object?> card;
}

/// One stretch, a day at a time: [step] simulates the next day, counts it,
/// and says whether a stop came. The runtime yields between days.
class AwayRun {
  AwayRun(this.game, this.plan)
    : from = game.today,
      _wasNegative = game.me.cash.isNegative,
      _wasFull = _accountFull(game),
      _wasCrowded = _crowded(game),
      _spentBefore = _spentByKind(game.me);

  final Game game;
  final AwayPlan plan;
  final GameDay from;
  final AwaySummary summary = AwaySummary();
  AwayStop? stop;
  bool _wasNegative;
  bool _wasFull;
  bool _wasCrowded;
  final Map<LedgerCategory, int> _spentBefore;
  final Set<String> _told = {};

  bool get done => stop != null;

  /// The days of the stretch.
  int get total => plan.target.daysSince(from);
  int get doneDays => game.today.daysSince(from);

  /// Why [game] cannot go to [target] now, or null (the go button's guard).
  static DomainError? refusal(Game game, GameDay target) {
    final today = game.today;
    if (target <= today) {
      return const DomainError(ErrorCode.cannotJump, {'reason': 'notAhead'});
    }
    if (target.daysSince(today) > 365) {
      return const DomainError(ErrorCode.cannotJump, {'reason': 'tooFar'});
    }
    final me = game.me;
    if (me.farm.vet == null &&
        game.state.world
            .aliveOwnedBy(me.id)
            .any((c) => c.health == HealthStatus.sick)) {
      return const DomainError(ErrorCode.cannotJump, {'reason': 'sick'});
    }
    for (final f in game.state.world.festivals.values) {
      for (final r in f.rounds) {
        if (r.day == today &&
            !r.over &&
            r.entries.any((e) => e.ownerId == me.id)) {
          return const DomainError(ErrorCode.cannotJump, {'reason': 'round'});
        }
      }
    }
    return null;
  }

  /// Simulates the next day and reads the stops. Returns the stop, if any.
  AwayStop? step() {
    if (done) return stop;
    final events = game.advanceDays(1);
    final today = game.today;
    final me = game.me;
    summary.days++;
    if (me.farm.milkOn == today) summary.milk += me.farm.milkIncome;
    // every stop the day gave, in the order they were read; the first is
    // the one told, except that his round's day comes before all (landed
    // before its first stage), the others said with it (the money its trip
    // took below zero, the review's L2)
    final found = <AwayStop>[];
    void at(AwayStopKind k, {String? subject, String? name, String? extra}) =>
        found.add(
          AwayStop(k, today, subject: subject, name: name, extra: extra),
        );
    final covered = me.farm.standing;
    for (final e in events) {
      if (e.owner != null && e.owner != me.id) continue;
      switch (e) {
        case FellSick(:final name):
          summary.fellIll.add(name);
          final c = game.state.world.camels[e.camel!];
          if (c != null && c.health == HealthStatus.sick) {
            at(AwayStopKind.illness, subject: c.id.value, name: name);
          }
        case Treated():
          summary.treated++;
        case Recovered():
          summary.recovered++;
        case Died(:final cause, :final name):
          summary.deaths[cause] = (summary.deaths[cause] ?? 0) + 1;
          if (cause == DeathCause.illness || cause == DeathCause.thirst) {
            summary.diedOfIllnessOrThirst.add(name);
            at(AwayStopKind.death, subject: e.camel?.value, name: name);
          }
        case CalfBorn(:final name):
          summary.born.add(name);
        case CalfLost():
          summary.calvesLost++;
        case PregnancyConfirmed():
          summary.pregnanciesConfirmed++;
        case PregnancyFailed():
          summary.pregnanciesFailed++;
        case SupplyDelivered():
          summary.delivered++;
        case SupplyOrdered(:final standing):
          if (standing) summary.standingOrders++;
        case SupplyLow(:final supply):
          final kind = supply == Supply.water
              ? StandingOrder.water
              : StandingOrder.feed;
          if (!covered.contains(kind) || me.farm.dryDays > 0) {
            at(AwayStopKind.supply, subject: supply.name);
          }
        case StandingOrderRefused(:final supply):
          at(AwayStopKind.account, subject: supply.name);
        case VetRefused(:final name):
          at(AwayStopKind.account, subject: e.camel?.value, name: name);
        case FacilityBuilt(:final facility):
          summary.built.add(facility);
        case RegistrationOpened(:final name):
          summary.registrationsOpened.add(name);
        case OfferReceived(:final name):
          summary.offers++;
          at(AwayStopKind.offer, subject: e.camel?.value, name: name);
        case WagesPaid(:final amount):
          summary.wagesPaid += amount;
        case ListingExpired():
          summary.listingsExpired++;
        case TamperingFound(:final name):
          at(AwayStopKind.fine, subject: e.camel?.value, name: name);
        case SaleRefused():
          at(AwayStopKind.fine, subject: e.camel?.value);
        default:
          break;
      }
    }
    // read from the state: money, the account, the pens
    final negative = me.cash.isNegative;
    if (negative && !_wasNegative) at(AwayStopKind.money);
    _wasNegative = negative;
    final full = _accountFull(game);
    if (full && !_wasFull) at(AwayStopKind.account);
    _wasFull = full;
    final herd = game.state.world.aliveOwnedBy(me.id).toList();
    final crowded = herd.length > me.farm.capacity;
    if (crowded && !_wasCrowded) at(AwayStopKind.crowded);
    _wasCrowded = crowded;
    // the festivals: his round's day; a registration closing he could make
    for (final f in game.state.world.festivals.values) {
      if (f.done) continue;
      for (final r in f.rounds) {
        if (r.day == today && r.entries.any((x) => x.ownerId == me.id)) {
          at(AwayStopKind.round, subject: f.id.value, name: f.name);
        }
      }
      if (f.closesOn.daysSince(today) == 3 && _told.add('reg ${f.id.value}')) {
        final entered = f.rounds.any(
          (r) => r.entries.any((x) => x.ownerId == me.id),
        );
        if (!entered && _couldEnter(game, f, herd)) {
          at(AwayStopKind.registration, subject: f.id.value, name: f.name);
        }
      }
    }
    // the breeding season's first day, with a female he can breed
    if (Eligibility.isBreedingSeason(today) &&
        !Eligibility.isBreedingSeason(today - 1) &&
        herd.any((c) => Eligibility.femaleCanBreed(c, today) == null)) {
      at(AwayStopKind.breeding);
    }
    for (final c in plan.extra) {
      final why = c(game);
      if (why != null) at(AwayStopKind.extra, extra: why);
    }
    for (final c in plan.counters) {
      c(game, events, summary);
    }
    AwayStop? first;
    final round = found.where((x) => x.kind == AwayStopKind.round).firstOrNull;
    if (round != null) {
      // with what else the day gave (the money below zero, a store low...)
      final also = {
        for (final x in found)
          if (x.kind != AwayStopKind.round) x.kind.name,
      };
      first = AwayStop(
        AwayStopKind.round,
        today,
        subject: round.subject,
        name: round.name,
        extra: also.isEmpty ? null : also.join(','),
      );
    } else if (found.isNotEmpty) {
      first = found.first;
    } else if (today >= plan.target) {
      first = AwayStop(AwayStopKind.target, today);
    }
    if (first != null) finish(first);
    return stop;
  }

  /// Ends the stretch at today with [why] (a stop, the target, or the
  /// player's «وقّف هنا»), counting what was spent.
  void finish(AwayStop why) {
    stop = why;
    final after = _spentByKind(game.me);
    for (final k in after.keys) {
      final d = after[k]! - (_spentBefore[k] ?? 0);
      if (d != 0) summary.spent[k] = d;
    }
  }

  void cancel() => finish(AwayStop(AwayStopKind.cancelled, game.today));

  static bool _accountFull(Game g) =>
      g.me.onAccount > 0 &&
      g.me.onAccount >=
          Account.limit(g.state.world.aliveOwnedBy(g.me.id), g.me, g.today);

  static bool _crowded(Game g) =>
      g.state.world.aliveOwnedBy(g.me.id).length > g.me.farm.capacity;

  static bool _couldEnter(Game g, Festival f, List<Camel> herd) => f.rounds.any(
    (r) =>
        r.size == 1 &&
        herd.any(
          (c) =>
              // (the cheap tests first: a herd of thousands is not put to the
              // full rules for every round)
              (r.category == null || r.category == c.category) &&
              (r.sex == null || r.sex == c.sex) &&
              Eligibility.canEnter(
                    g.state.world,
                    f,
                    r,
                    [c],
                    g.me.id,
                    g.today,
                  ) ==
                  null,
        ),
  );

  /// Money out by kind, the ledger's own sums (a month's roll-up rows grow
  /// in place, so the difference over the stretch is what it cost).
  static Map<LedgerCategory, int> _spentByKind(PlayerState p) {
    final out = <LedgerCategory, int>{};
    for (final e in p.ledger) {
      if (e.amount.value < 0) {
        out[e.category] = (out[e.category] ?? 0) - e.amount.value;
      }
    }
    return out;
  }

  Map<String, Object?> toJson() => {
    'from': from.value,
    'to': game.today.value,
    'target': plan.target.value,
    'stop': stop?.toJson(),
    'summary': summary.toJson(),
    if (plan.card.isNotEmpty) 'card': plan.card,
  };
}
