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
import 'handlers/falconry.dart' show cannotStart, ready, tripLines;
import 'model/falconry.dart';
import 'sim.dart';

class Trips {
  const Trips._();

  /// The minute a night lands on (the answers' Q-21): trapping at first
  /// light, falconry when the hunting day opens, an hour after sunrise
  /// [135]; home at 06:00 as the calendar does.
  static int landingMinute(Trip? t, GameDay day) => switch (t?.kind) {
    TripKind.trapping => HuntSun.dawn(day),
    TripKind.falconry => HuntSun.sunrise(day) + 60,
    null => 360,
  };

  /// The camp's own stops: its supplies out, the season's end, the day he
  /// chose to be back by. Each a reason's name.
  static String? campStop(Game g) {
    final t = g.me.falconry?.trip;
    if (t == null) return null;
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

  /// A night at camp: the plan of one away call to tomorrow (null when he
  /// is not on a trip of days).
  static AwayPlan? night(Game g) {
    final t = g.me.falconry?.trip;
    if (t == null || t.oneDay) return null;
    return AwayPlan(
      g.today + 1,
      extra: [campStop],
      counters: [count],
      card: card(g, t.kind, t.ground, t.endOn.daysSince(g.today)),
    );
  }

  /// The trip's lines on the calendar's card before leaving (under its own):
  /// the ground and its distance, the gear he has and lacks, the camp's
  /// supplies, and whether it is a day's outing.
  static Map<String, Object?> card(
    Game g,
    TripKind kind,
    Ground ground,
    int nights,
  ) {
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
      'refused': cannotStartName(g, kind, ground, nights),
    };
  }

  /// Why «اطلع» would be refused now (a HuntRefusal's name), or null.
  static String? cannotStartName(Game g, TripKind k, Ground gr, int n) {
    final e = cannotStart(Sim(g.state), g.me, k, gr, n);
    return e == null ? null : (e.params['reason'] as String?) ?? e.code.name;
  }
}
