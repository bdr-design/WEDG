// Being away for falcons (task T18, item 3): the trip of days with a camp and
// the day's outing, both by the away call and nothing else (rush_and_
// calendar.md section 5). Each «نام لين الفجر» is one call of the away
// mechanism to tomorrow, landing at the working hour's start; the stops are
// all the calendar's (AwayRun) plus the camp's own, read from the state
// after each day; the camp's daily work is FalconrySystem's (the rule N3).
import 'away.dart';
import 'catalog/falconry.dart';
import 'common/time.dart';
import 'events.dart';
import 'game.dart';
import 'handlers/falconry.dart'
    show arrival, cannotStart, driveMinutes, ready, tripLines, workStart;
import 'model/falconry.dart';
import 'sim.dart';

class Trips {
  const Trips._();

  /// The camp's own stops, at the ground only: its supplies out, the
  /// season's end, the day he chose to be back by. Each a reason's name.
  static String? campStop(Game g) {
    final t = g.me.falconry?.trip;
    if (t == null || t.returning || g.today < t.arriveOn) return null;
    final today = g.today;
    if (!t.oneDay && g.me.hunt.has(Gear.supplies) == 0) return 'suppliesOut';
    final permit = t.kind == TripKind.trapping
        ? PermitKind.trapping
        : PermitKind.hunting;
    if (permit.seasonOn(today) == null) return 'seasonEnd';
    if (today >= t.endOn) return 'tripEnd';
    return null;
  }

  /// The trip's lines in the summary, as the days run.
  static void count(Game g, List<DomainEvent> _, AwaySummary s) {
    final t = g.me.falconry?.trip;
    if (t == null) return;
    s.extra
      ..clear()
      ..addAll(tripLines(t, g.today));
  }

  /// The next leg of a trip by the away call, with the minute it lands on:
  /// - the drive out, to the day it reaches the ground, landing at its
  ///   working hour (the drive as the plan's travel: every stop of the
  ///   calendar read on the way);
  /// - a night at the ground: to tomorrow, landing at the working hour's
  ///   start (the answers' Q-21: trapping at first light, falconry an hour
  ///   after sunrise [135]);
  /// - the drive home, to the day it is over, landing at its minute.
  /// Null when the leg is inside today (a day's outing, a short drive: the
  /// clock runs it) or there is no trip.
  static ({AwayPlan plan, int landing})? leg(Game g) {
    final t = g.me.falconry?.trip;
    if (t == null) return null;
    final today = g.today;
    AwayPlan plan(GameDay to, {bool camp = false}) => AwayPlan(
      to,
      extra: camp ? [campStop] : const [],
      counters: [count],
      card: card(g, t.kind, t.ground, t.endOn.daysSince(today)),
    );
    if (t.returning) {
      return t.homeOn! > today
          ? (plan: plan(t.homeOn!), landing: t.homeMinute!)
          : null;
    }
    if (t.arriveOn > today) {
      return (plan: plan(t.arriveOn), landing: t.arriveMinute);
    }
    if (t.oneDay) return null;
    return (
      plan: plan(today + 1, camp: true),
      landing: workStart(t.kind, today + 1),
    );
  }

  /// A night at camp (the leg to tomorrow), or null.
  static AwayPlan? night(Game g) {
    final l = leg(g);
    final t = g.me.falconry?.trip;
    if (l == null || t == null || t.returning || t.arriveOn > g.today) {
      return null;
    }
    return l.plan;
  }

  /// The trip's lines on the calendar's card before leaving (under its own):
  /// the ground and its distance, the gear he has and lacks, the camp's
  /// supplies, and whether it is a day's outing.
  static Map<String, Object?> card(
    Game g,
    TripKind kind,
    Ground ground,
    int nights, {
    int minute = 360,
  }) {
    final p = g.me;
    final h = p.falconry;
    final region = p.farm.region;
    final gear = kind == TripKind.trapping
        ? Gear.trapping
        : const [Gear.supplies, Gear.tracker];
    return {
      'kind': kind.name,
      'ground': ground.name,
      'groundName': ground.label,
      'km': ground.kmFrom(region),
      'hours': (ground.hoursFrom(region) * 10).round() / 10,
      'nights': nights,
      'driveMinutes': driveMinutes(p, ground),
      'arrive': [
        arrival(p, kind, ground, g.today, minute).$1.value,
        arrival(p, kind, ground, g.today, minute).$2,
      ],
      'oneDay': nights == 0,
      'oneDayPossible': ground.oneDayFrom(region),
      'from': g.today.value,
      'to': (g.today + nights).value,
      'pigeons': h?.has(Gear.pigeon) ?? 0,
      'has': [
        for (final x in gear)
          if ((h?.has(x) ?? 0) > 0) x.label,
      ],
      'lacks': [
        for (final x in gear)
          if ((h?.has(x) ?? 0) == 0) x.label,
      ],
      'supplyDays': h?.has(Gear.supplies) ?? 0,
      'suppliesEnough': nights == 0 || (h?.has(Gear.supplies) ?? 0) >= nights,
      if (kind == TripKind.falconry)
        'falcons': [
          for (final f in h?.falcons ?? const <Falcon>[])
            if (ready(f)) f.name,
        ],
      'refused': cannotStartName(g, kind, ground, nights, minute),
    };
  }

  /// Why «اطلع» would be refused now (a HuntRefusal's name), or null.
  static String? cannotStartName(
    Game g,
    TripKind k,
    Ground gr,
    int n,
    int minute,
  ) {
    final e = cannotStart(Sim(g.state), g.me, k, gr, n, minute);
    return e == null ? null : (e.params['reason'] as String?) ?? e.code.name;
  }
}
