// ignore_for_file: avoid_print
// The odds of trapping, measured (task T18): seeded seasons played through
// the engine's own commands (StartTrip, SpotFalcon, ReleaseLure) at the two
// ends of the owner's range and a middle setup. Each season is a year of its
// own (the day's falcon is keyed by the day), so the seasons are independent.
// Prints, beside the targets, the share of seasons with a sellable bird and
// with a dear one (300,000 or more), the birds a season, the price's mean
// and median, and the season's net money (sales less the permit, the camp's
// supplies and the pigeons used; the gear bought once is not in it).
//
//   dart run tool/trap_odds.dart [seasons]     (20,000 by default)
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/sim.dart';

class Profile {
  const Profile(
    this.name,
    this.target,
    this.ground,
    this.fromDay,
    this.days,
    this.gear,
    this.windows,
  );
  final String name;
  final String target;
  final Ground ground;

  /// The camp's first day in October (1 = 1 October) and its length.
  final int fromDay;
  final int days;
  final Map<Gear, int> gear;
  final List<TrapWindow> windows;
}

const profiles = [
  Profile(
    'bare beginner',
    'about 1 in 6 (0.167); sources 1 in 12.5 (0.08)',
    Ground.hail,
    15,
    30,
    {Gear.pigeon: 6, Gear.pigeonNet: 1},
    [TrapWindow.dawn],
  ),
  Profile(
    'middle',
    'between',
    Ground.rafha,
    1,
    45,
    {Gear.pigeon: 10, Gear.pigeonNet: 1, Gear.binoculars: 1},
    [TrapWindow.dawn],
  ),
  Profile(
    'well equipped, well placed',
    'about 2 in 3 (0.667), never beyond; sources 1 in 2.98 (0.336)',
    Ground.lith,
    1,
    61,
    {
      Gear.pigeon: 20,
      Gear.pigeonNet: 1,
      Gear.birdNet: 1,
      Gear.binoculars: 1,
      Gear.mobileTent: 1,
    },
    [TrapWindow.dawn, TrapWindow.midday, TrapWindow.evening],
  ),
];

int minuteIn(TrapWindow w, GameDay d) => switch (w) {
  TrapWindow.dawn => HuntSun.dawn(d) + 30,
  TrapWindow.midday => 720,
  TrapWindow.evening => HuntSun.sunset(d) - 30,
};

void main(List<String> args) {
  final seasons = args.isEmpty ? 20000 : int.parse(args.first);
  for (final pr in profiles) {
    final g = Game.create(
      seed: 4242,
      playerName: 'odds',
      farmName: 'odds',
      region: Region.qassim,
      favourite: ColorCategory.wodh,
      startedAt: DateTime.utc(2026, 11, 14),
    );
    Sim(g.state).pay(g.me, const Riyal(1 << 40), LedgerCategory.opening);
    final me = g.me.id;
    var withBird = 0, withDear = 0, birds = 0;
    final prices = <int>[];
    final nets = <int>[];
    for (var s = 0; s < seasons; s++) {
      final year = 2027 + s;
      final h = g.me.hunt
        ..trip = null
        ..held.clear()
        ..gear.clear()
        ..gear.addAll(pr.gear)
        ..gear[Gear.supplies] = pr.days
        ..permits[PermitKind.trapping] = year;
      g.state.world.day =
          GameDay.ofDate(DateTime.utc(year, 10)) + (pr.fromDay - 1);
      final r = g.dispatch(
        StartTrip(
          me,
          TripKind.trapping,
          pr.ground,
          pr.days > HuntBalance.mostNights ? HuntBalance.mostNights : pr.days,
        ),
      );
      if (!r.ok) throw StateError('$r');
      var pigeonsUsed = 0, sales = 0, n = 0;
      var dear = false;
      for (var day = 0; day < pr.days; day++) {
        final today = g.today;
        if (PermitKind.trapping.seasonOn(today) == null) break;
        for (final w in pr.windows) {
          final m = minuteIn(w, today);
          final seen = g
              .dispatch(SpotFalcon(me, HuntAt.ground(pr.ground), minute: m))
              .events
              .whereType<TrapResult>()
              .single;
          if (seen.outcome != TrapOutcome.inSight) continue;
          // he tries what he has: the pigeon, then the bird net, then a
          // pigeon again
          for (final lure in [Lure.pigeon, Lure.birdNet, Lure.pigeon]) {
            final before = h.has(Gear.pigeon);
            final res = g.dispatch(
              ReleaseLure(me, HuntAt.ground(pr.ground), lure, minute: m),
            );
            if (!res.ok) continue; // a lure he has not got
            pigeonsUsed += before - h.has(Gear.pigeon);
            final o = res.events.whereType<TrapResult>().single.outcome;
            if (o != TrapOutcome.refused) break;
          }
        }
        for (final b in [...h.held]) {
          n++;
          sales += b.value!;
          prices.add(b.value!);
          if (b.value! >= 300000) dear = true;
          h.held.remove(b);
        }
        // a well-equipped trapper keeps his pigeons up (plenty)
        if (pr.gear[Gear.pigeon] == 20) h.gear[Gear.pigeon] = 20;
        g.state.world.day = today + 1;
      }
      if (n > 0) withBird++;
      if (dear) withDear++;
      birds += n;
      final cost =
          PermitKind.trapping.fee +
          pr.days * Gear.supplies.price +
          pigeonsUsed * Gear.pigeon.price;
      nets.add(sales - cost);
    }
    prices.sort();
    nets.sort();
    double mean(List<int> l) =>
        l.isEmpty ? 0 : l.fold(0, (a, b) => a + b) / l.length;
    int median(List<int> l) => l.isEmpty ? 0 : l[l.length ~/ 2];
    print(
      '== ${pr.name}: ${pr.ground.label}, ${pr.days} days from '
      '${pr.fromDay} October, ${pr.windows.map((w) => w.name).join('+')}',
    );
    print('   target: ${pr.target}');
    print(
      '   seasons $seasons | with a sellable bird '
      '${(withBird / seasons).toStringAsFixed(4)} (1 in '
      '${(seasons / (withBird == 0 ? 1 : withBird)).toStringAsFixed(2)}) | '
      'with a dear one ${(withDear / seasons).toStringAsFixed(4)} | birds a '
      'season ${(birds / seasons).toStringAsFixed(3)}',
    );
    print(
      '   price mean ${mean(prices).round()} median ${median(prices)} | '
      'dear share of birds '
      '${(prices.where((p) => p >= 300000).length / (prices.isEmpty ? 1 : prices.length)).toStringAsFixed(3)}',
    );
    print('   season net mean ${mean(nets).round()} median ${median(nets)}');
  }
}
