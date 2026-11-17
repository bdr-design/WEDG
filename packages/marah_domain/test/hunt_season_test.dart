// The hunting season, part A items 3 to 6 (task T18): being away, trapping,
// a trapped bird's fate, falconry.
import 'dart:convert';

import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/handlers/falconry.dart' show driveMinutes;
import 'package:marah_domain/src/sim.dart';
import 'package:test/test.dart';

GameDay d(int y, int m, int day) => GameDay.ofDate(DateTime.utc(y, m, day));

Game gameOn(GameDay start, {int seed = 4242}) => Game.create(
  seed: seed,
  playerName: 'p',
  farmName: 'f',
  region: Region.qassim,
  favourite: ColorCategory.wodh,
  startDay: start,
  startedAt: DateTime.utc(2026, 11, 14),
);

void give(Game g, int riyals) =>
    Sim(g.state).pay(g.me, Riyal(riyals), LedgerCategory.opening);

String? why(Result r) => r is Err && r.error.code == ErrorCode.huntRefused
    ? r.error.params['reason']! as String
    : null;

/// Gear in hand at once (as if delivered).
void hand(Game g, Gear x, int n) => g.me.hunt.gear[x] = n;

/// A trapper ready on 1 October: room, permit, gear, money.
Game trapper({int seed = 4242, bool full = true}) {
  final g = gameOn(d(2026, 9, 26), seed: seed);
  give(g, 3000000);
  expect(g.dispatch(BuildFacility(g.me.id, Facility.falconRoom)).ok, isTrue);
  expect(g.dispatch(BuyPermit(g.me.id, PermitKind.trapping)).ok, isTrue);
  g.advanceTo(d(2026, 10, 1));
  hand(g, Gear.pigeon, 20);
  hand(g, Gear.pigeonNet, 1);
  hand(g, Gear.supplies, 60);
  if (full) {
    hand(g, Gear.birdNet, 1);
    hand(g, Gear.binoculars, 1);
    hand(g, Gear.mobileTent, 1);
  }
  return g;
}

/// A falcon of his, trained, in the room.
Falcon trainedFalcon(Game g) {
  final f = Falcon(
    id: g.state.world.ids.falcon(),
    name: 'غيث',
    species: FalconSpecies.saker,
    female: true,
    hatched: 2026,
    how: FalconHow.bought,
    on: g.today,
    route: FalconRoute.breeders,
    price: 19000,
    lengthQ: 66,
    widthQ: 66,
    weightG: 1100,
    passport: '1234567890',
    skill: 0.6,
    dauDays: HuntBalance.dauDaysNeeded,
    caredOn: g.today,
  );
  g.me.hunt.falcons.add(f);
  return f;
}

/// Runs one night at camp by the away call, as the engine does.
AwayRun night(Game g) {
  final plan = Trips.night(g)!;
  final run = AwayRun(g, plan);
  while (!run.done) {
    run.step();
  }
  return run;
}

/// Runs the trip's next leg by the away call (the drive out, a night, the
/// drive home), as the engine's tripNight does.
AwayRun leg(Game g) {
  final l = Trips.leg(g)!;
  final run = AwayRun(g, l.plan);
  while (!run.done) {
    run.step();
  }
  return run;
}

/// Starts a trip at midnight and runs its legs till he is at the ground at
/// [minute] (the drive out is game time: task T18, finding 1).
Trip camp(Game g, TripKind k, Ground gr, int nights, {int minute = 400}) {
  final r = g.dispatch(StartTrip(g.me.id, k, gr, nights));
  expect(r.ok, isTrue, reason: '${why(r)}');
  final t = g.me.hunt.trip!;
  while (!t.there(g.today, minute)) {
    leg(g);
  }
  return t;
}

/// Breaks camp and drives home, the days passing as the game's own (the
/// drive home is game time too).
void goHome(Game g) {
  expect(g.dispatch(EndTrip(g.me.id)).ok, isTrue);
  while (g.me.hunt.trip != null) {
    if (Trips.leg(g) != null) {
      leg(g);
    } else {
      g.advanceDays(1);
    }
  }
}

const at = HuntAt.ground;
const dawn = 400; // 06:40, in October's dawn window (first light 05:39)

void main() {
  group('the sun and the hours (Q-1, Q-2)', () {
    test('hunting from an hour after sunrise to an hour before sunset', () {
      final day = d(2026, 10, 15);
      final rise = HuntSun.sunrise(day), set = HuntSun.sunset(day);
      expect(HuntSun.huntingHours(day, rise + 59), isFalse);
      expect(HuntSun.huntingHours(day, rise + 60), isTrue);
      expect(HuntSun.huntingHours(day, set - 60), isTrue);
      expect(HuntSun.huntingHours(day, set - 59), isFalse);
    });
    test('trapping from first light to sunset; its windows', () {
      final day = d(2026, 10, 15);
      expect(HuntSun.trappingHours(day, HuntSun.dawn(day) - 1), isFalse);
      expect(HuntSun.window(day, HuntSun.dawn(day)), TrapWindow.dawn);
      expect(HuntSun.window(day, 599), TrapWindow.dawn);
      expect(HuntSun.window(day, 600), TrapWindow.midday);
      expect(HuntSun.window(day, HuntSun.sunset(day) - 60), TrapWindow.evening);
      expect(HuntSun.window(day, HuntSun.sunset(day) + 1), isNull);
    });
  });

  group('being away (item 3)', () {
    test('a trip\'s refusals, each with its words', () {
      final g = trapper();
      final me = g.me.id;
      expect(
        why(g.dispatch(StartTrip(me, TripKind.trapping, Ground.nafudEdge, 3))),
        'offGround',
      );
      expect(
        why(g.dispatch(StartTrip(me, TripKind.trapping, Ground.hamad, 0))),
        'tooFar',
      );
      expect(
        why(g.dispatch(StartTrip(me, TripKind.falconry, Ground.hamad, 3))),
        'notHuntingGround',
      );
      expect(
        why(g.dispatch(StartTrip(me, TripKind.falconry, Ground.estate, 3))),
        'noPermit',
      );
      hand(g, Gear.supplies, 0);
      expect(
        why(g.dispatch(StartTrip(me, TripKind.trapping, Ground.hamad, 3))),
        'noSupplies',
      );
      hand(g, Gear.supplies, 10);
      expect(
        g.dispatch(StartTrip(me, TripKind.trapping, Ground.hamad, 3)).ok,
        isTrue,
      );
      expect(
        why(g.dispatch(StartTrip(me, TripKind.trapping, Ground.hamad, 3))),
        'onTrip',
      );
      for (final r in HuntRefusal.values) {
        expect(
          FalconLines.refusal(
            DomainError(ErrorCode.huntRefused, {
              'reason': r.name,
              'route': 'trapping',
              'kind': 'hunting',
              'lure': 'pigeon',
            }),
          ),
          isNotEmpty,
          reason: r.name,
        );
      }
    });
    test('the trapping trip out of its season or with no permit', () {
      final g = gameOn(d(2026, 9, 30));
      give(g, 100000);
      hand(g, Gear.supplies, 5);
      final me = g.me.id;
      expect(
        why(g.dispatch(StartTrip(me, TripKind.trapping, Ground.hamad, 3))),
        'outOfSeason',
      );
      g.advanceDays(1);
      expect(
        why(g.dispatch(StartTrip(me, TripKind.trapping, Ground.hamad, 3))),
        'noPermit',
      );
    });
    test('each night one away call, landing at first light; supplies a day '
        'a night; the farm runs', () {
      final g = trapper();
      hand(g, Gear.supplies, 10);
      g.dispatch(StartTrip(g.me.id, TripKind.trapping, Ground.hamad, 5));
      final start = g.today;
      final run = night(g);
      expect(run.stop!.kind, AwayStopKind.target);
      expect(g.today, start + 1);
      expect(g.me.hunt.has(Gear.supplies), 9);
      expect(run.summary.extra['nights'], 1);
      expect(run.summary.milk, greaterThanOrEqualTo(0));
      expect(Trips.leg(g)!.landing, HuntSun.dawn(g.today + 1));
      expect(Trips.night(g)!.card['groundName'], 'الحماد');
    });
    test('the camp\'s own stops: the chosen end, supplies out, the season\'s '
        'end', () {
      final g = trapper();
      hand(g, Gear.supplies, 10);
      g.dispatch(StartTrip(g.me.id, TripKind.trapping, Ground.hamad, 2));
      expect(night(g).stop!.kind, AwayStopKind.target);
      final r = night(g);
      expect(r.stop!.kind, AwayStopKind.extra);
      expect(r.stop!.extra, 'tripEnd');
      goHome(g);

      hand(g, Gear.supplies, 1);
      g.dispatch(StartTrip(g.me.id, TripKind.trapping, Ground.hamad, 10));
      expect(night(g).stop!.extra, 'suppliesOut');
      goHome(g);

      g.advanceTo(d(2026, 11, 29));
      hand(g, Gear.supplies, 10);
      g.dispatch(StartTrip(g.me.id, TripKind.trapping, Ground.hamad, 9));
      expect(night(g).stop!.kind, AwayStopKind.target); // 30 November
      expect(night(g).stop!.extra, 'seasonEnd'); // 1 December
    });
    test('a falcon left at the farm stops a jump the morning before it would '
        'step back (Q-22)', () {
      final g = trapper();
      final f = trainedFalcon(g);
      late AwayRun run;
      do {
        run = AwayRun(g, AwayPlan(g.today + 30));
        while (!run.done) {
          run.step();
        }
      } while (run.stop!.kind != AwayStopKind.falconCare &&
          run.stop!.kind != AwayStopKind.target);
      expect(run.stop!.kind, AwayStopKind.falconCare);
      expect(run.stop!.name, f.name);
      expect(g.today.daysSince(f.caredOn!), HuntBalance.stepBackDays - 1);
      expect(f.dauDays, HuntBalance.dauDaysNeeded);
      g.advanceDays(1);
      expect(f.dauDays, HuntBalance.dauDaysNeeded - HuntBalance.stepBack);
    });
    test(
      'a day\'s outing ends with its day; EndTrip tells the trip\'s lines',
      () {
        final g = trapper();
        g.dispatch(BuyPermit(g.me.id, PermitKind.hunting)).ok;
        trainedFalcon(g);
        expect(g.dispatch(BuyPermit(g.me.id, PermitKind.hunting)).ok, isTrue);
        final r = g.dispatch(
          StartTrip(g.me.id, TripKind.falconry, Ground.nafudEdge, 0),
        );
        expect(r.ok, isTrue, reason: '$r');
        expect(Trips.night(g), isNull, reason: 'a day\'s outing has no night');
        final ev = g.advanceDays(1);
        final end = ev.whereType<TripChanged>().single;
        expect(end.what, TripChange.ended);
        expect(end.lines['nights'], 0);
        expect(g.me.falconry!.trip, isNull);
      },
    );
  });

  group('trapping (item 4)', () {
    test('the net off its ground, at night, out of season: refused, nothing '
        'happens, no fine', () {
      final g = trapper();
      g.dispatch(StartTrip(g.me.id, TripKind.trapping, Ground.hamad, 5));
      final cash = g.me.cash.value;
      final pigeons = g.me.hunt.has(Gear.pigeon);
      final off = g.dispatch(
        ReleaseLure(
          g.me.id,
          const HuntAt.off(HuntOff.farm),
          Lure.pigeon,
          minute: dawn,
        ),
      );
      expect(why(off), 'offGround');
      expect(FalconLines.refusal((off as Err).error), contains('100,000'));
      expect(
        why(
          g.dispatch(
            SpotFalcon(g.me.id, const HuntAt.ground(Ground.lith), minute: dawn),
          ),
        ),
        'notOnTrip',
      );
      expect(
        why(g.dispatch(SpotFalcon(g.me.id, at(Ground.hamad), minute: 100))),
        'night',
      );
      expect(g.me.cash.value, cash);
      expect(g.me.hunt.has(Gear.pigeon), pigeons);
      expect(
        g.me.ledger.where((e) => e.category == LedgerCategory.fine),
        isEmpty,
      );
    });
    test('a lure with no falcon seen: nothing came, the pigeon back', () {
      final g = trapper();
      camp(g, TripKind.trapping, Ground.hamad, 5);
      final r = g.dispatch(
        ReleaseLure(g.me.id, at(Ground.hamad), Lure.pigeon, minute: dawn),
      );
      expect(
        r.events.whereType<TrapResult>().single.outcome,
        TrapOutcome.nothingCame,
      );
      expect(g.me.hunt.has(Gear.pigeon), 20);
    });
    test('every bird the net can hold, by the rules: the فرخ held, the rest '
        'released with their lines', () {
      final seen = <String>{};
      const want = {
        'netted',
        'passagePeregrineQ',
        'mountainPeregrineQ',
        'lannerQ',
      };
      for (
        var seed = 1;
        seed < 400 &&
            !(seen.containsAll(want) && seen.any((x) => x.startsWith('saker')));
        seed++
      ) {
        final g = trapper(seed: seed);
        camp(g, TripKind.trapping, Ground.lith, 60);
        for (var day = 0; day < 60; day++) {
          final p = TrapOdds.passer(g.state.world.seed, Ground.lith, g.today);
          if (p != null) {
            final minute = switch (p.window) {
              TrapWindow.dawn => dawn,
              TrapWindow.midday => 700,
              TrapWindow.evening => HuntSun.sunset(g.today) - 30,
            };
            g.dispatch(SpotFalcon(g.me.id, at(Ground.lith), minute: minute));
            for (final l in [Lure.pigeon, Lure.birdNet, Lure.pigeon]) {
              final r = g.dispatch(
                ReleaseLure(g.me.id, at(Ground.lith), l, minute: minute),
              );
              final o = r.events.whereType<TrapResult>().firstOrNull;
              if (o == null) break;
              if (o.outcome == TrapOutcome.netted) {
                expect(p.sellable, isTrue);
                final bird = g.me.hunt.held.last;
                expect(bird.species, FalconSpecies.passagePeregrine);
                expect(bird.how, FalconHow.trapped);
                expect(bird.value, inInclusiveRange(50000, 650000));
                seen.add('netted');
              }
              if (o.outcome == TrapOutcome.released) {
                expect(p.sellable, isFalse);
                expect(FalconLines.release(o.species!, o.farkh!), isNotNull);
                seen.add('${o.species!.name}${o.farkh! ? '' : 'Q'}');
              }
              if (o.outcome != TrapOutcome.refused) break;
            }
          }
          g.state.world.day = g.today + 1; // (the next day, untimed)
        }
      }
      expect(
        seen,
        containsAll([
          'netted',
          'passagePeregrineQ',
          'mountainPeregrineQ',
          'lannerQ',
        ]),
      );
      expect(seen.where((s) => s.startsWith('saker')), isNotEmpty);
      expect(
        FalconLines.release(FalconSpecies.saker, false),
        'طلقته: الحر مهدد، والمزاد ما يقبل إلا فرخ الشاهين البحري',
        reason: 'a saker قرناس takes the saker\'s line (Q-12)',
      );
      expect(
        FalconLines.release(FalconSpecies.passagePeregrine, false),
        'طلقته: المزاد ما يقبل إلا الفرخ',
      );
      expect(FalconLines.release(FalconSpecies.passagePeregrine, true), isNull);
    });
    test('the best day can never pass the owner\'s two in 3 a season', () {
      // the most a day can give: a falcon passes the coast in October, it
      // is the most sellable share, it is seen, takes a lure in three tries
      // and is held
      final take =
          1 -
          (1 - TrapOdds.takePigeon) *
              (1 - TrapOdds.takeBirdNet) *
              (1 - TrapOdds.takePigeon / 2);
      final best = TrapOdds.passCoast * 0.6 * take * TrapOdds.hold;
      expect(best, lessThanOrEqualTo(TrapOdds.bestDay + 1e-5));
      final season = 1 - _pow(1 - TrapOdds.bestDay, 61);
      expect(season, lessThanOrEqualTo(2 / 3 + 1e-3));
      for (final g in Ground.values.where((g) => g.trapping)) {
        final m = TrapOdds.mix(g);
        expect(m.fold(0.0, (a, x) => a + x.$3), closeTo(1, 1e-9));
        expect(m.first.$3, lessThanOrEqualTo(0.6));
      }
    });
    test('the numbers the odds rest on, pinned', () {
      expect(TrapOdds.triesMost, 3);
      expect(TrapOdds.november, 0.92);
      expect(TrapOdds.groundSouth, 0.92);
      expect(TrapOdds.groundNorth, 0.9);
      expect(TrapOdds.passCoast, 0.0412);
      expect(TrapOdds.passChance(Ground.lith, d(2026, 10, 10)), 0.0412);
      expect(
        TrapOdds.passChance(Ground.lith, d(2026, 11, 10)),
        closeTo(0.0412 * 0.92, 1e-12),
      );
    });
    test('the net at a hunting ground: the off-ground words', () {
      final g = trapper();
      final r = g.dispatch(
        SpotFalcon(g.me.id, at(Ground.nafudEdge), minute: dawn),
      );
      expect(why(r), 'offGround');
    });
    test('one trapping ground a day: a camp moved or remade finds the same '
        'day', () {
      final g = trapper();
      camp(g, TripKind.trapping, Ground.hail, 10);
      expect(
        g.dispatch(SpotFalcon(g.me.id, at(Ground.hail), minute: dawn)).ok,
        isTrue,
      );
      final day = g.today;
      expect(g.dispatch(MoveCamp(g.me.id, Ground.dibdibah)).ok, isTrue);
      final t = g.me.hunt.trip!;
      expect(
        t.arriveOn > day || t.arriveMinute > HuntSun.sunset(day),
        isTrue,
        reason: 'the drive to the new ground is game time',
      );
    });
    test('the same day gives the same falcon however often he looks', () {
      final g = trapper();
      camp(g, TripKind.trapping, Ground.hamad, 5);
      final a = [
        for (var i = 0; i < 3; i++)
          g
              .dispatch(SpotFalcon(g.me.id, at(Ground.hamad), minute: dawn))
              .events
              .whereType<TrapResult>()
              .single
              .outcome,
      ];
      expect(a.toSet(), hasLength(1));
    });
  });

  group('a trapped bird\'s fate (item 5)', () {
    Falcon netBird(Game g) {
      final f = Falcon(
        id: g.state.world.ids.falcon(),
        name: 'براق',
        species: FalconSpecies.passagePeregrine,
        female: true,
        hatched: 2026,
        how: FalconHow.trapped,
        on: g.today,
        ground: Ground.hamad,
        lengthQ: 60,
        widthQ: 62,
        weightG: 1010,
        skill: 0.5,
        value: 112000,
        caredOn: g.today,
      );
      g.me.hunt.held.add(f);
      return f;
    }

    test('sold that night at the hammer, in full, no fee, its own kind', () {
      final g = trapper();
      final f = netBird(g);
      final cash = g.me.cash.value;
      final r = g.dispatch(EnterTrapAuction(g.me.id, f.id));
      expect(r.ok, isTrue);
      expect(f.trapDoc, isNotNull, reason: 'the club\'s check');
      g.advanceDays(1);
      final sale = g.me.ledger.where(
        (e) => e.category == LedgerCategory.falconSale,
      );
      expect(sale.single.amount.value, 112000);
      expect(
        g.me.ledger.where(
          (e) => e.category == LedgerCategory.commission && e.day == g.today,
        ),
        isEmpty,
      );
      expect(Money.kindOf(LedgerCategory.falconSale), MoneyKind.falconSale);
      expect(g.me.hunt.held, isEmpty);
      // the day's keep for the bird (20) the only other money
      expect(g.me.cash.value, greaterThan(cash + 112000 - 1000));
    });
    test('kept: the check, the registration and the passport, a place in '
        'the room; never offered for sale again', () {
      final g = trapper();
      g.advanceDays(Balance.buildDays);
      final f = netBird(g);
      expect(g.dispatch(KeepBird(g.me.id, f.id)).ok, isTrue);
      expect(f.keep, isTrue);
      expect(f.passport, isNotNull);
      expect(f.trapDoc, isNotNull);
      expect(g.me.hunt.falcons, contains(f));
      expect(
        why(g.dispatch(EnterTrapAuction(g.me.id, f.id))),
        'keptNotForSale',
      );
    });
    test(
      'kept needs a free place; held without a room till sold (Q-13/15)',
      () {
        final g = trapper();
        for (var i = 0; i < HuntBalance.roomHolds; i++) {
          trainedFalcon(g);
        }
        final f = netBird(g); // the room full: held all the same
        expect(why(g.dispatch(KeepBird(g.me.id, f.id))), 'roomFull');
        expect(g.me.hunt.held, contains(f));
      },
    );
    test('neither sold nor kept when the auction closes: set free', () {
      final g = trapper();
      g.advanceTo(d(2026, 11, 30));
      final f = netBird(g);
      final ev = g.advanceDays(1);
      expect(
        ev.whereType<FalconFate>().where((x) => x.fate == Fate.freedAtClose),
        hasLength(1),
      );
      expect(g.me.hunt.held, isEmpty);
      expect(f.value, 112000);
    });
    test('a kept peregrine set free from 1 February to 30 April only', () {
      final g = trapper();
      g.advanceDays(Balance.buildDays);
      final f = netBird(g);
      g.dispatch(KeepBird(g.me.id, f.id));
      g.state.world.day = d(2027, 1, 31);
      expect(why(g.dispatch(ReleaseFalcon(g.me.id, f.id))), 'releaseMonths');
      g.state.world.day = d(2027, 5, 1);
      expect(why(g.dispatch(ReleaseFalcon(g.me.id, f.id))), 'releaseMonths');
      g.state.world.day = d(2027, 4, 30);
      expect(g.dispatch(ReleaseFalcon(g.me.id, f.id)).ok, isTrue);
      expect(g.me.hunt.falcons, isNot(contains(f)));
    });
    test('a bought falcon cannot be set free or sold (Q-20)', () {
      final g = trapper();
      final f = trainedFalcon(g);
      g.state.world.day = d(2027, 2, 10);
      expect(why(g.dispatch(ReleaseFalcon(g.me.id, f.id))), 'notKept');
      expect(why(g.dispatch(EnterTrapAuction(g.me.id, f.id))), 'notHeld');
    });
  });

  group('falconry (item 6)', () {
    Game falconer({GameDay? on}) {
      final g = trapper();
      trainedFalcon(g);
      expect(g.dispatch(BuyPermit(g.me.id, PermitKind.hunting)).ok, isTrue);
      if (on != null) g.state.world.day = on;
      return g;
    }

    int noon(Game g) => HuntSun.sunrise(g.today) + 120;

    /// On a falconry trip at [gr], there by the hunting day's first hour.
    void out(Game g, Ground gr, {int nights = 3}) => camp(
      g,
      TripKind.falconry,
      gr,
      nights,
      minute: HuntSun.sunrise(g.today) + 60,
    );

    test('banned places, each with its words; no fine', () {
      final g = falconer();
      final f = g.me.hunt.falcons.single;
      for (final (where, reason) in [
        (const HuntAt.off(HuntOff.farm), 'nearFarm'),
        (const HuntAt.off(HuntOff.coast), 'coast'),
        (const HuntAt.off(HuntOff.reserve), 'reserve'),
        (at(Ground.hamad), 'notHuntingGround'),
      ]) {
        final r = g.dispatch(CastFalcon(g.me.id, f.id, where, minute: noon(g)));
        expect(why(r), reason);
      }
      final farm = g.dispatch(
        CastFalcon(
          g.me.id,
          f.id,
          const HuntAt.off(HuntOff.farm),
          minute: noon(g),
        ),
      );
      expect(FalconLines.refusal((farm as Err).error), contains('5,000'));
      expect(f.flights, 0);
      expect(
        g.me.ledger.where((e) => e.category == LedgerCategory.fine),
        isEmpty,
      );
    });
    test('by day only, and never from a moving car (Q-26)', () {
      final g = falconer();
      final f = g.me.hunt.falcons.single;
      out(g, Ground.nafudEdge);
      final rise = HuntSun.sunrise(g.today);
      expect(
        why(
          g.dispatch(
            CastFalcon(g.me.id, f.id, at(Ground.nafudEdge), minute: rise + 59),
          ),
        ),
        'notByDay',
      );
      expect(
        why(
          g.dispatch(
            CastFalcon(
              g.me.id,
              f.id,
              at(Ground.nafudEdge),
              inCar: true,
              moving: true,
              minute: rise + 60,
            ),
          ),
        ),
        'movingCar',
      );
      expect(
        g
            .dispatch(
              CastFalcon(
                g.me.id,
                f.id,
                at(Ground.nafudEdge),
                inCar: true,
                minute: rise + 60,
              ),
            )
            .ok,
        isTrue,
      );
    });
    test('the quarry by its dates (Q-10)', () {
      expect(quarryAtDay(null, d(2026, 9, 1)), Quarry.stoneCurlew);
      expect(quarryAtDay(null, d(2026, 11, 30)), Quarry.stoneCurlew);
      expect(quarryAtDay(null, d(2026, 12, 1)), isNull);
      expect(quarryAtDay(Ground.estate, d(2026, 10, 31)), Quarry.stoneCurlew);
      expect(quarryAtDay(Ground.estate, d(2026, 11, 1)), Quarry.houbara);
      expect(quarryAtDay(Ground.estate, d(2027, 1, 31)), Quarry.houbara);
      expect(quarryAtDay(Ground.nafudEdge, d(2026, 12, 15)), isNull);
      final g0 = falconer(on: d(2026, 12, 15));
      // no lawful quarry there in its dates: the trip itself is refused
      expect(
        why(
          g0.dispatch(
            StartTrip(g0.me.id, TripKind.falconry, Ground.nafudEdge, 3),
          ),
        ),
        'noQuarry',
      );
      final g = falconer(on: d(2026, 12, 15));
      final f = g.me.hunt.falcons.single;
      out(g, Ground.estate);
      expect(
        g
            .dispatch(
              CastFalcon(g.me.id, f.id, at(Ground.estate), minute: noon(g)),
            )
            .ok,
        isTrue,
      );
      g.state.world.day = d(2027, 2, 1);
      expect(
        why(
          g.dispatch(
            CastFalcon(g.me.id, f.id, at(Ground.estate), minute: noon(g)),
          ),
        ),
        'outOfSeason',
      );
    });
    test('a falcon not through its الدعو is not cast', () {
      final g = falconer();
      out(g, Ground.nafudEdge);
      final f = g.me.hunt.falcons.single..dauDays = 27;
      expect(
        why(
          g.dispatch(
            CastFalcon(g.me.id, f.id, at(Ground.nafudEdge), minute: noon(g)),
          ),
        ),
        'notReady',
      );
    });
    test('three flights a day on a trip', () {
      final g = falconer();
      final f = g.me.hunt.falcons.single;
      out(g, Ground.nafudEdge);
      var ok = 0;
      for (var i = 0; i < 5; i++) {
        final r = g.dispatch(
          CastFalcon(g.me.id, f.id, at(Ground.nafudEdge), minute: noon(g)),
        );
        if (r.ok) ok++;
        if (f.where == FalconWhere.lost) break;
      }
      expect(ok, lessThanOrEqualTo(3));
      expect(TrapOdds.flightsADay, 3);
    });
    test('a falconry trip with no falcon ready: refused', () {
      final g = trapper();
      trainedFalcon(g).dauDays = 10;
      g.dispatch(BuyPermit(g.me.id, PermitKind.hunting));
      expect(
        why(
          g.dispatch(
            StartTrip(g.me.id, TripKind.falconry, Ground.nafudEdge, 2),
          ),
        ),
        'notReady',
      );
    });
    test(
      'a cast off a trip, or at another ground than the trip\'s: refused',
      () {
        final g = falconer();
        final f = g.me.hunt.falcons.single;
        final m = HuntSun.sunrise(g.today) + 60;
        expect(
          why(
            g.dispatch(CastFalcon(g.me.id, f.id, at(Ground.estate), minute: m)),
          ),
          'noTrip',
        );
        expect(
          why(
            g.dispatch(
              CastFalcon(
                g.me.id,
                f.id,
                const HuntAt.off(HuntOff.open),
                minute: m,
              ),
            ),
          ),
          'noTrip',
        );
        out(g, Ground.nafudEdge);
        expect(
          why(
            g.dispatch(CastFalcon(g.me.id, f.id, at(Ground.estate), minute: m)),
          ),
          'notOnTrip',
        );
      },
    );
    test('the cast\'s draw is the falcon\'s, the day\'s and the flight\'s: '
        'no hour re-rolls it', () {
      CastOutcome first(int minute) {
        final g = falconer();
        final f = g.me.hunt.falcons.single;
        out(g, Ground.nafudEdge);
        return g
            .dispatch(
              CastFalcon(g.me.id, f.id, at(Ground.nafudEdge), minute: minute),
            )
            .events
            .whereType<CastResult>()
            .single
            .outcome;
      }

      final g = falconer();
      final a = first(HuntSun.sunrise(g.today) + 60);
      for (final m in [noon(g), noon(g) + 60, HuntSun.sunset(g.today) - 61]) {
        expect(first(m), a);
      }
    });
    test('lost rarely, found mostly, more with the tracker', () {
      var lost = 0, flights = 0;
      final found = {
        true: [0, 0],
        false: [0, 0],
      };
      for (var seed = 1; seed <= 60; seed++) {
        final g = trapper(seed: seed);
        final f = trainedFalcon(g);
        g.dispatch(BuyPermit(g.me.id, PermitKind.hunting));
        final tracked = seed.isEven;
        f.tracker = tracked;
        out(g, Ground.nafudEdge, nights: 50);
        for (var day = 0; day < 40 && f.where != FalconWhere.lost; day++) {
          for (var i = 0; i < TrapOdds.flightsADay; i++) {
            final r = g.dispatch(
              CastFalcon(g.me.id, f.id, at(Ground.nafudEdge), minute: noon(g)),
            );
            if (!r.ok) break;
            flights++;
            if (f.where == FalconWhere.lost) {
              lost++;
              final s = g.dispatch(
                SearchFalcon(g.me.id, f.id, minute: noon(g)),
              );
              final fate = s.events.whereType<FalconFate>().single.fate;
              found[tracked]![0]++;
              if (fate == Fate.found) found[tracked]![1]++;
              break;
            }
          }
          g.state.world.day = g.today + 1; // (the next day, untimed)
        }
      }
      expect(lost / flights, closeTo(TrapOdds.lost, 0.01));
      final w = found[true]!, wo = found[false]!;
      expect(w[1] / w[0], greaterThan(wo[1] / wo[0]));
      expect(wo[1] / wo[0], greaterThan(0.4));
    });
    test('الدعو: the days since count; two weeks left, a week back; none in '
        'the moult', () {
      final g = trapper();
      final f = trainedFalcon(g)..dauDays = 0;
      g.advanceDays(7);
      expect(g.dispatch(CareFalcons(g.me.id)).ok, isTrue);
      expect(f.dauDays, 7);
      g.advanceDays(14); // two weeks without
      expect(f.dauDays, 0, reason: 'stepped back from 7');
      g.dispatch(CareFalcons(g.me.id));
      expect(f.dauDays, 1);
      g.state.world.day = d(2027, 6, 1);
      expect(why(g.dispatch(CareFalcons(g.me.id))), 'moult');
    });
  });

  group('the fix round\'s pins (reviewer B)', () {
    String js(Game g) => jsonEncode(g.state.toJson());
    test('الدعو refused on the road out, at camp, on the road home and on a '
        'day\'s outing; at the minute he is home it works; each refusal '
        'changes nothing', () {
      final g = trapper();
      final f = trainedFalcon(g)
        ..dauDays = 3
        ..caredOn = g.today - 1;
      final me = g.me.id;
      expect(
        g.dispatch(StartTrip(me, TripKind.trapping, Ground.hamad, 5)).ok,
        isTrue,
      );
      final t = g.me.hunt.trip!;
      var s = js(g);
      final r = g.dispatch(CareFalcons(me, minute: 300));
      expect(why(r), 'awayFromFarm');
      expect(
        FalconLines.refusal((r as Err).error),
        'الدعو بغرفة الصقور، وانت برا العزبة',
      );
      expect(js(g), s);
      leg(g);
      s = js(g);
      expect(why(g.dispatch(CareFalcons(me, minute: 600))), 'awayFromFarm');
      expect(js(g), s);
      expect(g.dispatch(EndTrip(me, minute: 600)).ok, isTrue);
      final home = t.homeMinute!;
      while (g.today < t.homeOn!) {
        leg(g);
      }
      s = js(g);
      expect(
        why(g.dispatch(CareFalcons(me, minute: home - 1))),
        'awayFromFarm',
      );
      expect(js(g), s);
      final before = f.dauDays;
      expect(g.dispatch(CareFalcons(me, minute: home)).ok, isTrue);
      expect(g.me.hunt.trip, isNull);
      expect(f.dauDays, greaterThan(before));
      g.dispatch(BuyPermit(me, PermitKind.hunting));
      f.dauDays = HuntBalance.dauDaysNeeded;
      g.advanceDays(1);
      final m = HuntSun.sunrise(g.today);
      expect(
        g
            .dispatch(
              StartTrip(me, TripKind.falconry, Ground.nafudEdge, 0, minute: m),
            )
            .ok,
        isTrue,
      );
      s = js(g);
      expect(why(g.dispatch(CareFalcons(me, minute: m + 120))), 'awayFromFarm');
      expect(js(g), s);
    });
    test('a refusal settles nothing, even with a drive home over', () {
      final g = trapper();
      final me = g.me.id;
      g.dispatch(StartTrip(me, TripKind.trapping, Ground.hail, 2));
      g.dispatch(EndTrip(me));
      final t = g.me.hunt.trip!;
      final s = js(g);
      final r = g.dispatch(CareFalcons(me, minute: t.homeMinute! + 1));
      expect(why(r), 'noFalcons');
      expect(js(g), s);
      expect(r.events.whereType<TripChanged>(), isEmpty);
    });
    test('a tracker fitted to a named falcon shows on that falcon only; the '
        'gear rows hold no tracker', () {
      final g = trapper();
      final f = trainedFalcon(g);
      final f2 = trainedFalcon(g);
      final me = g.me.id;
      expect(
        g.dispatch(OrderGear(me, Gear.tracker, 1, falcon: f2.id)).ok,
        isTrue,
      );
      var facts = falconFacts(g.state, me);
      var fs = {for (final x in facts['falcons']! as List) (x as Map)['id']: x};
      expect(fs[f2.id.value]!['trackerComing'], isTrue);
      expect(
        why(g.dispatch(OrderGear(me, Gear.tracker, 1, falcon: f2.id))),
        'trackerComing',
      );
      g.advanceDays(Balance.deliveryDays);
      facts = falconFacts(g.state, me);
      fs = {for (final x in facts['falcons']! as List) (x as Map)['id']: x};
      expect(fs[f2.id.value]!['tracker'], isTrue);
      expect(fs[f.id.value]!.containsKey('tracker'), isFalse);
      expect((facts['gear']! as Map).containsKey('tracker'), isFalse);
      expect(
        why(g.dispatch(OrderGear(me, Gear.tracker, 1, falcon: f2.id))),
        'hasTracker',
      );
    });
    test('three flights a day exactly, the fourth refused; three again the '
        'next day', () {
      var checked = 0;
      for (var seed = 1; seed <= 40 && checked < 5; seed++) {
        final g = trapper(seed: seed);
        final f = trainedFalcon(g);
        g.dispatch(BuyPermit(g.me.id, PermitKind.hunting));
        camp(
          g,
          TripKind.falconry,
          Ground.nafudEdge,
          3,
          minute: HuntSun.sunrise(g.today) + 60,
        );
        final m = HuntSun.sunrise(g.today) + 120;
        final res = <String>[];
        for (var i = 0; i < 4 && f.where != FalconWhere.lost; i++) {
          final r = g.dispatch(
            CastFalcon(g.me.id, f.id, at(Ground.nafudEdge), minute: m),
          );
          res.add(r.ok ? 'ok' : why(r)!);
        }
        if (f.where == FalconWhere.lost) continue;
        expect(res, ['ok', 'ok', 'ok', 'flownOut']);
        checked++;
        leg(g);
        final m2 = HuntSun.sunrise(g.today) + 120;
        final r = g.dispatch(
          CastFalcon(g.me.id, f.id, at(Ground.nafudEdge), minute: m2),
        );
        expect(r.ok, isTrue, reason: '${why(r)}');
      }
      expect(checked, 5);
    });
    test('the lure: three tries, the third refusal sends it away, no fourth '
        'draw; a pigeon used only on a draw', () {
      var seen = 0;
      for (var seed = 1; seed <= 400 && seen < 3; seed++) {
        final g = trapper(seed: seed);
        const gr = Ground.lith;
        GameDay? day;
        Passer? p;
        for (var i = 0; i < 60 && p == null; i++) {
          p = TrapOdds.passer(g.state.world.seed, gr, g.today + i);
          if (p != null) day = g.today + i;
        }
        if (p == null || day!.daysSince(g.today) < 2) continue;
        g.advanceTo(day - 2);
        hand(g, Gear.pigeon, 20);
        hand(g, Gear.supplies, 30);
        g.dispatch(StartTrip(g.me.id, TripKind.trapping, gr, 5));
        final t = g.me.hunt.trip!;
        while (g.today < day && Trips.leg(g) != null) {
          leg(g);
        }
        final m = switch (p.window) {
          TrapWindow.dawn => HuntSun.dawn(day) + 30,
          TrapWindow.midday => 720,
          TrapWindow.evening => HuntSun.sunset(day) - 30,
        };
        if (g.today != day || !t.there(day, m)) continue;
        final spot = g.dispatch(SpotFalcon(g.me.id, at(gr), minute: m));
        if (spot.events.whereType<TrapResult>().single.outcome !=
            TrapOutcome.inSight) {
          continue;
        }
        final out = <TrapOutcome>[];
        final pig0 = g.me.hunt.has(Gear.pigeon);
        for (var i = 0; i < 5; i++) {
          out.add(
            g
                .dispatch(ReleaseLure(g.me.id, at(gr), Lure.pigeon, minute: m))
                .events
                .whereType<TrapResult>()
                .single
                .outcome,
          );
        }
        final draws = out.where((o) => o != TrapOutcome.nothingCame).length;
        expect(draws, lessThanOrEqualTo(3));
        expect(pig0 - g.me.hunt.has(Gear.pigeon), draws);
        if (out.contains(TrapOutcome.refusedAndWent)) {
          expect(out.indexOf(TrapOutcome.refusedAndWent), 2);
          seen++;
        }
      }
      expect(seen, greaterThan(0));
    });
    test('on a falconry trip a falcon that has not flown stops a night the '
        'morning before it would step back', () {
      final g = trapper();
      final f = trainedFalcon(g);
      final f2 = trainedFalcon(g)..dauDays = 10;
      g.dispatch(BuyPermit(g.me.id, PermitKind.hunting));
      camp(
        g,
        TripKind.falconry,
        Ground.nafudEdge,
        30,
        minute: HuntSun.sunrise(g.today) + 60,
      );
      AwayRun? run;
      for (var i = 0; i < 20; i++) {
        g.dispatch(
          CastFalcon(
            g.me.id,
            f.id,
            at(Ground.nafudEdge),
            minute: HuntSun.sunrise(g.today) + 120,
          ),
        );
        run = leg(g);
        if (run.stop!.kind == AwayStopKind.falconCare) break;
      }
      expect(run!.stop!.kind, AwayStopKind.falconCare);
      expect(run.stop!.name, f2.name);
    });
  });

  group('the fix round\'s pins (reviewer A)', () {
    String js(Game g) => jsonEncode(g.state.toJson());
    test('one trapping ground a day: worked at dawn, home, out to another the '
        'same day: the net refused there, nothing changed', () {
      final g = trapper();
      final me = g.me.id;
      camp(g, TripKind.trapping, Ground.hail, 3);
      expect(
        g.dispatch(SpotFalcon(me, at(Ground.hail), minute: dawn)).ok,
        isTrue,
      );
      final day = g.today;
      g.dispatch(EndTrip(me, minute: dawn + 1));
      final home = g.me.hunt.trip!.homeMinute!;
      expect(g.me.hunt.trip!.homeOn, day);
      final r = g.dispatch(
        StartTrip(me, TripKind.trapping, Ground.rafha, 3, minute: home),
      );
      expect(r.ok, isTrue, reason: '${why(r)}');
      final t = g.me.hunt.trip!;
      expect(t.arriveOn, day, reason: 'there the same afternoon');
      final m = t.arriveMinute;
      final s = js(g);
      expect(
        why(g.dispatch(SpotFalcon(me, at(Ground.rafha), minute: m + 10))),
        'oneGroundADay',
      );
      expect(js(g), s);
    });
    test('the day\'s trapping is the day\'s, at any ground: what was looked '
        'at is not looked at again after moving', () {
      final g = trapper();
      camp(g, TripKind.trapping, Ground.hail, 3);
      g.dispatch(SpotFalcon(g.me.id, at(Ground.hail), minute: dawn));
      final w = g.me.hunt.work!;
      expect(w.day, g.today);
      expect(w.ground, Ground.hail);
      expect(w.looked, contains(TrapWindow.dawn));
    });
    test(
      'the drive home takes its hours: home only when the road is driven',
      () {
        final g = trapper();
        final me = g.me.id;
        camp(g, TripKind.trapping, Ground.hamad, 3);
        g.dispatch(EndTrip(me, minute: 600));
        final t = g.me.hunt.trip!;
        final drive = driveMinutes(g.me, Ground.hamad);
        expect(
          t.homeOn!.value * 1440 + t.homeMinute!,
          g.today.value * 1440 + 600 + drive,
        );
        expect(drive, greaterThan(9 * 60));
        // StartTrip settles a drive home already over (and only then)
        final early = g.dispatch(
          StartTrip(
            me,
            TripKind.trapping,
            Ground.hail,
            2,
            minute: t.homeMinute! - 1,
          ),
        );
        expect(why(early), 'onTrip');
        final r = g.dispatch(
          StartTrip(
            me,
            TripKind.trapping,
            Ground.hail,
            2,
            minute: t.homeMinute,
          ),
        );
        expect(r.ok, isTrue, reason: '${why(r)}');
        expect(
          r.events.whereType<TripChanged>().map((e) => e.what),
          containsAll([TripChange.ended, TripChange.started]),
        );
      },
    );
    test('the drive out lands at the arrival minute, not the day\'s first '
        'working minute', () {
      final g = trapper();
      g.dispatch(
        StartTrip(g.me.id, TripKind.trapping, Ground.hamad, 3, minute: 300),
      );
      final t = g.me.hunt.trip!;
      final drive = driveMinutes(g.me, Ground.hamad);
      expect(t.arriveOn, g.today);
      expect(t.arriveMinute, 300 + drive);
      expect(t.arriveMinute, greaterThan(HuntSun.dawn(g.today)));
    });
    test('the camp\'s supplies out: the camp is broken that morning and he '
        'drives home; the stop said', () {
      final g = trapper();
      hand(g, Gear.supplies, 1);
      camp(g, TripKind.trapping, Ground.hail, 20);
      final first = leg(g);
      expect(first.stop!.extra, 'suppliesOut', reason: 'the last one eaten');
      expect(g.me.hunt.has(Gear.supplies), 0);
      expect(
        g.me.hunt.trip!.returning,
        isFalse,
        reason: 'today he still works',
      );
      final r = leg(g);
      expect(r.stop!.kind, AwayStopKind.extra);
      expect(r.stop!.extra, 'suppliesOut');
      final t = g.me.hunt.trip!;
      expect(t.returning, isTrue);
      expect(
        why(g.dispatch(SpotFalcon(g.me.id, at(Ground.hail), minute: 600))),
        'notOnTrip',
      );
      while (g.me.hunt.trip != null) {
        if (Trips.leg(g) != null) {
          leg(g);
        } else {
          g.advanceDays(1);
        }
      }
      expect(g.me.hunt.trip, isNull);
    });
    test('gear ordered from the camp waits at the farm till he is home', () {
      final g = trapper(full: false);
      final me = g.me.id;
      camp(g, TripKind.trapping, Ground.hail, 5);
      expect(g.dispatch(OrderGear(me, Gear.binoculars, 1)).ok, isTrue);
      leg(g);
      leg(g);
      expect(g.me.hunt.has(Gear.binoculars), 0);
      goHome(g);
      g.advanceDays(1);
      expect(g.me.hunt.has(Gear.binoculars), 1);
    });
    test('a tracker for a lost falcon is refused; one on its way is fitted '
        'only once the falcon is home', () {
      final g = trapper();
      final f = trainedFalcon(g)..where = FalconWhere.lost;
      expect(
        why(g.dispatch(OrderGear(g.me.id, Gear.tracker, 1, falcon: f.id))),
        'falconAway',
      );
      f.where = FalconWhere.home;
      expect(
        g.dispatch(OrderGear(g.me.id, Gear.tracker, 1, falcon: f.id)).ok,
        isTrue,
      );
      f.where = FalconWhere.lost;
      g.advanceDays(Balance.deliveryDays);
      expect(f.tracker, isFalse);
      f.where = FalconWhere.home;
      g.advanceDays(1);
      expect(f.tracker, isTrue);
    });
    test('a lost falcon: looked for where it was lost, by day; the chance '
        'halves each day; gone after the third', () {
      final g = trapper();
      final f = trainedFalcon(g);
      g.dispatch(BuyPermit(g.me.id, PermitKind.hunting));
      camp(
        g,
        TripKind.falconry,
        Ground.nafudEdge,
        10,
        minute: HuntSun.sunrise(g.today) + 60,
      );
      final lost = g.today;
      f
        ..where = FalconWhere.lost
        ..lostOn = lost
        ..lostAt = Ground.nafudEdge;
      expect(TrapOdds.searchDays, 3);
      expect(TrapOdds.lost, 0.02);
      // at night: refused
      expect(
        why(g.dispatch(SearchFalcon(g.me.id, f.id, minute: 60))),
        'searchThere',
      );
      for (var day = 1; day <= 3; day++) {
        leg(g);
        expect(f.where, FalconWhere.lost, reason: 'day $day');
      }
      leg(g);
      expect(g.me.hunt.falcons, isNot(contains(f)), reason: 'gone on day 4');
      expect(g.today.daysSince(lost), 4);
    });
    test('moving the camp drives from the camp, at the engine\'s minute', () {
      final g = trapper();
      camp(g, TripKind.trapping, Ground.wajh, 5);
      final km = Ground.wajh.kmTo(Ground.sharurah);
      expect(km, greaterThan(Ground.sharurah.kmFrom(Region.qassim)));
      g.dispatch(MoveCamp(g.me.id, Ground.sharurah, minute: 600));
      final t = g.me.hunt.trip!;
      final drive = (km / Ground.kmPerHour * 60).round();
      final reach = g.today.value * 1440 + 600 + drive;
      expect(
        t.arriveOn.value * 1440 + t.arriveMinute,
        greaterThanOrEqualTo(reach),
      );
    });
  });

  group('the second fix round (reviewer B)', () {
    test('his only falcon lost on a day\'s outing: he may go back to that '
        'ground to look for it', () {
      final g = trapper();
      final f = trainedFalcon(g);
      g.dispatch(BuyPermit(g.me.id, PermitKind.hunting));
      f
        ..where = FalconWhere.lost
        ..lostOn = g.today
        ..lostAt = Ground.nafudEdge;
      final m = HuntSun.sunrise(g.today);
      expect(
        why(
          g.dispatch(
            StartTrip(g.me.id, TripKind.falconry, Ground.estate, 0, minute: m),
          ),
        ),
        'notReady',
      );
      final r = g.dispatch(
        StartTrip(g.me.id, TripKind.falconry, Ground.nafudEdge, 0, minute: m),
      );
      expect(r.ok, isTrue, reason: '${why(r)}');
      final s = g.dispatch(SearchFalcon(g.me.id, f.id, minute: m + 120));
      expect(s.ok, isTrue, reason: '${why(s)}');
    });
    test('gear ordered the day of a day\'s outing comes the next day', () {
      final g = trapper();
      trainedFalcon(g);
      g.dispatch(BuyPermit(g.me.id, PermitKind.hunting));
      final before = g.me.hunt.has(Gear.pigeon);
      expect(g.dispatch(OrderGear(g.me.id, Gear.pigeon, 0 + 1)).ok, isFalse);
      hand(g, Gear.pigeon, 10);
      expect(g.dispatch(OrderGear(g.me.id, Gear.pigeon, 2)).ok, isTrue);
      final m = HuntSun.sunrise(g.today);
      g.dispatch(
        StartTrip(g.me.id, TripKind.falconry, Ground.nafudEdge, 0, minute: m),
      );
      g.advanceDays(Balance.deliveryDays);
      expect(g.me.hunt.trip, isNull);
      expect(g.me.hunt.has(Gear.pigeon), 12);
      expect(before, 20);
    });
    test('the words for breaking or moving camp on the road home', () {
      final g = trapper();
      camp(g, TripKind.trapping, Ground.hamad, 3);
      g.dispatch(EndTrip(g.me.id, minute: 600));
      expect(why(g.dispatch(EndTrip(g.me.id, minute: 601))), 'homeward');
      expect(
        why(g.dispatch(MoveCamp(g.me.id, Ground.hail, minute: 601))),
        'homeward',
      );
      final t = g.me.hunt.trip!;
      expect(
        why(g.dispatch(EndTrip(g.me.id, minute: t.homeMinute! + 1))),
        'noTrip',
      );
      expect(
        why(
          g.dispatch(MoveCamp(g.me.id, Ground.hail, minute: t.homeMinute! + 1)),
        ),
        'noTrip',
      );
    });
  });

  group('views', () {
    test('no hidden value: a held bird\'s worth, a falcon\'s skill', () {
      final g = trapper();
      g.me.hunt.held.add(
        Falcon(
          id: g.state.world.ids.falcon(),
          name: 'براق',
          species: FalconSpecies.passagePeregrine,
          female: true,
          hatched: 2026,
          how: FalconHow.trapped,
          on: g.today,
          ground: Ground.hamad,
          lengthQ: 60,
          widthQ: 62,
          weightG: 1010,
          skill: 0.4321,
          value: 377777,
        ),
      );
      trainedFalcon(g);
      g.dispatch(StartTrip(g.me.id, TripKind.trapping, Ground.hamad, 3));
      final text = jsonEncode(falconFacts(g.state, g.me.id));
      expect(text, isNot(contains('377777')));
      expect(text, isNot(contains('0.4321')));
      expect(text, isNot(contains('skill')));
      expect(text, isNot(contains('"value"')));
      final cat = jsonEncode(falconCatalogOf(g.state, g.me.id));
      expect(cat, contains('طلقته: الوكري طير مقيم، وطرحه ممنوع'));
    });
  });
}

Quarry? quarryAtDay(Ground? g, GameDay day) {
  final kinds = g == null ? const [Quarry.stoneCurlew] : g.quarry;
  for (final q in kinds) {
    if (q.openOn(day)) return q;
  }
  return null;
}

double _pow(double b, int e) {
  var r = 1.0;
  for (var i = 0; i < e; i++) {
    r *= b;
  }
  return r;
}
