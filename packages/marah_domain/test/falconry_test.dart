// The hunting season, part A items 1 and 2 (task T18): the catalog, the
// permits, the gear, the falcons' room, and buying a falcon at its auction
// in its month.
import 'dart:convert';

import 'package:marah_domain/marah_domain.dart';
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

/// The reason of a hunting refusal, or null.
String? why(Result r) => r is Err && r.error.code == ErrorCode.huntRefused
    ? r.error.params['reason']! as String
    : null;

/// A falcons' room built on [g]'s farm.
void withRoom(Game g) {
  give(g, Facility.falconRoom.price);
  expect(g.dispatch(BuildFacility(g.me.id, Facility.falconRoom)).ok, isTrue);
  g.advanceDays(Balance.buildDays);
  expect(g.me.farm.has(Facility.falconRoom), 1);
}

/// Today's first lot at [route] that has any, moving day by day.
FalconLot firstLot(Game g, FalconRoute route) {
  for (;;) {
    final lots = FalconMarket.lots(g.state.world.seed, route, g.today);
    if (lots.isNotEmpty) return lots.first;
    g.advanceDays(1);
  }
}

void main() {
  group('the seasons and the routes, each edge on both sides', () {
    test('the hunting permit: 1 September to 31 January [127][128]', () {
      const k = PermitKind.hunting;
      expect(k.seasonOn(d(2026, 8, 31)), isNull);
      expect(k.seasonOn(d(2026, 9, 1)), 2026);
      expect(k.seasonOn(d(2027, 1, 31)), 2026);
      expect(k.seasonOn(d(2027, 2, 1)), isNull);
      expect(k.seasonFor(d(2027, 2, 1)), 2027);
      expect(k.seasonFor(d(2026, 8, 31)), 2026);
      expect(k.closes(2026), d(2027, 1, 31));
    });
    test('the trapping permit: 1 October to 30 November [184][185]', () {
      const k = PermitKind.trapping;
      expect(k.seasonOn(d(2026, 9, 30)), isNull);
      expect(k.seasonOn(d(2026, 10, 1)), 2026);
      expect(k.seasonOn(d(2026, 11, 30)), 2026);
      expect(k.seasonOn(d(2026, 12, 1)), isNull);
      expect(k.seasonFor(d(2026, 12, 1)), 2027);
      expect(k.seasonFor(d(2026, 9, 30)), 2026);
      expect(k.fee, 500);
    });
    test('the breeders\' auction 5 to 25 August [158]', () {
      const r = FalconRoute.breeders;
      expect(r.openOn(d(2027, 8, 4)), isFalse);
      expect(r.openOn(d(2027, 8, 5)), isTrue);
      expect(r.openOn(d(2027, 8, 25)), isTrue);
      expect(r.openOn(d(2027, 8, 26)), isFalse);
    });
    test('the exhibition 1 to 10 October [157]', () {
      const r = FalconRoute.exhibition;
      expect(r.openOn(d(2026, 9, 30)), isFalse);
      expect(r.openOn(d(2026, 10, 1)), isTrue);
      expect(r.openOn(d(2026, 10, 10)), isTrue);
      expect(r.openOn(d(2026, 10, 11)), isFalse);
    });
    test('the trapping auction 1 October to 30 November [184]', () {
      const r = FalconRoute.trapping;
      expect(r.openOn(d(2026, 9, 30)), isFalse);
      expect(r.openOn(d(2026, 10, 1)), isTrue);
      expect(r.openOn(d(2026, 11, 30)), isTrue);
      expect(r.openOn(d(2026, 12, 1)), isFalse);
    });
    test('a bird is a فرخ in its first season, a قرناس after', () {
      expect(FalconAge.on(d(2026, 10, 1), 2026), FalconAge.farkh);
      expect(FalconAge.on(d(2027, 8, 31), 2026), FalconAge.farkh);
      expect(FalconAge.on(d(2027, 9, 1), 2026), FalconAge.qarnas);
    });
  });

  group('the grounds', () {
    test('each is a real place with its road from the farm', () {
      for (final g in Ground.values) {
        for (final r in Region.values) {
          expect(g.kmFrom(r), greaterThanOrEqualTo(14), reason: '$g $r');
        }
      }
      // الحماد is far from Qassim (the design: about 600 km in a straight
      // line, so about 700 by road), a trip of days
      // الحماد north-west of Arar: about 843 km by road and 10 hours from
      // Qassim (the approved card said 600 km, the straight line to Arar)
      expect(Ground.hamad.kmFrom(Region.qassim), inInclusiveRange(830, 860));
      expect(Ground.hamad.hoursFrom(Region.qassim), closeTo(9.9, 0.2));
      expect(Ground.hamad.oneDayFrom(Region.qassim), isFalse);
      // the Nafud's edge and the estate are near: a day's outing
      expect(Ground.nafudEdge.oneDayFrom(Region.qassim), isTrue);
      expect(Ground.estate.oneDayFrom(Region.qassim), isTrue);
      // the day's outing reaches 150 km by road, no farther (game choice)
      expect(Ground.oneDayKm, 150);
      final edge = Ground.values
          .expand((g) => [for (final r in Region.values) (g, r)])
          .where((x) => x.$1.trapping)
          .toList();
      for (final (g, r) in edge) {
        expect(g.oneDayFrom(r), g.kmFrom(r) <= 150, reason: '$g $r');
      }
      // Hail's ground from a farm in Hail
      expect(Ground.hail.oneDayFrom(Region.hail), isTrue);
      expect(Ground.hail.kmFrom(Region.hail), 25);
    });
    test('the houbara only in the estate [142]; the stone-curlew [140]', () {
      expect(Ground.estate.quarry, contains(Quarry.houbara));
      expect(Ground.nafudEdge.quarry, [Quarry.stoneCurlew]);
      for (final g in Ground.values.where((g) => g != Ground.estate)) {
        expect(g.quarry, isNot(contains(Quarry.houbara)), reason: '$g');
      }
      for (final g in Ground.values.where((g) => g.trapping)) {
        expect(g.quarry, isEmpty, reason: '$g');
      }
    });
  });

  group('permits', () {
    test('the hunting permit wants a falcon with its passport', () {
      final g = gameOn(d(2026, 10, 1));
      final r = g.dispatch(BuyPermit(g.me.id, PermitKind.hunting));
      expect(why(r), 'needsFalcon');
      expect(g.me.falconry, isNull, reason: 'a refusal changes nothing');
    });
    test('the trapping permit: 500, its own kind, held for its season', () {
      final g = gameOn(d(2026, 9, 20));
      final cash = g.me.cash.value;
      final r = g.dispatch(BuyPermit(g.me.id, PermitKind.trapping));
      expect(r.ok, isTrue, reason: '$r');
      expect(g.me.cash.value, cash - 500);
      expect(g.me.ledger.last.category, LedgerCategory.huntPermit);
      expect(Money.kindOf(LedgerCategory.huntPermit), MoneyKind.permits);
      expect(g.me.falconry!.permits[PermitKind.trapping], 2026);
      // bought on 20 September, valid from 1 October to 30 November
      expect(g.me.falconry!.holds(PermitKind.trapping, g.today), isFalse);
      g.advanceDays(11);
      expect(g.me.falconry!.holds(PermitKind.trapping, g.today), isTrue);
      expect(
        why(g.dispatch(BuyPermit(g.me.id, PermitKind.trapping))),
        'permitHeld',
      );
      g.advanceTo(d(2026, 11, 30));
      expect(g.me.falconry!.holds(PermitKind.trapping, g.today), isTrue);
      g.advanceDays(1);
      expect(g.me.falconry!.holds(PermitKind.trapping, g.today), isFalse);
    });
    test('cash only: no permit on the merchant\'s account', () {
      final g = gameOn(d(2026, 10, 1));
      Sim(g.state).pay(g.me, -g.me.cash, LedgerCategory.opening);
      final r = g.dispatch(BuyPermit(g.me.id, PermitKind.trapping));
      expect((r as Err).error.code, ErrorCode.insufficientFunds);
      expect(g.me.onAccount, 0);
    });
  });

  group('the trapping gear, delivered as feed is', () {
    test('ordered, paid in cash, arrives the next day', () {
      final g = gameOn(d(2026, 9, 20));
      final cash = g.me.cash.value;
      final r = g.dispatch(OrderGear(g.me.id, Gear.pigeon, 6));
      expect(r.ok, isTrue);
      expect(g.me.cash.value, cash - 300);
      expect(g.me.ledger.last.category, LedgerCategory.falconGear);
      expect(g.me.falconry!.has(Gear.pigeon), 0);
      expect(g.me.falconry!.onTheWay(Gear.pigeon), 6);
      final ev = g.advanceDays(Balance.deliveryDays);
      expect(ev.whereType<GearDelivered>().single.units, 6);
      expect(g.me.falconry!.has(Gear.pigeon), 6);
      expect(g.me.falconry!.coming, isEmpty);
    });
    test('no more than he can hold, the way counted', () {
      final g = gameOn(d(2026, 9, 20));
      give(g, 100000);
      expect(g.dispatch(OrderGear(g.me.id, Gear.binoculars, 1)).ok, isTrue);
      final r = g.dispatch(OrderGear(g.me.id, Gear.binoculars, 1));
      expect(why(r), 'gearFull');
      expect((r as Err).error.params['room'], 0);
      expect(FalconLines.refusal(r.error), 'ما تقدر تطلب أكثر منها');
      expect(g.dispatch(OrderGear(g.me.id, Gear.pigeonNet, 1)).ok, isTrue);
      expect(
        why(g.dispatch(OrderGear(g.me.id, Gear.pigeonNet, 1))),
        'gearFull',
      );
      expect(g.dispatch(OrderGear(g.me.id, Gear.pigeon, 15)).ok, isTrue);
      final p = g.dispatch(OrderGear(g.me.id, Gear.pigeon, 6));
      expect((p as Err).error.params['room'], 5);
      expect(FalconLines.refusal(p.error), 'تقدر تطلب 5 بس');
      expect(g.dispatch(OrderGear(g.me.id, Gear.supplies, 60)).ok, isTrue);
      expect(why(g.dispatch(OrderGear(g.me.id, Gear.supplies, 1))), 'gearFull');
      expect(
        (g.dispatch(OrderGear(g.me.id, Gear.pigeon, 0)) as Err).error.code,
        ErrorCode.invalidAmount,
      );
    });
    test('the design\'s prices: the missing three for 8,600', () {
      expect(
        Gear.birdNet.price + Gear.binoculars.price + Gear.mobileTent.price,
        8600,
      );
      expect(Gear.pigeon.price, 50);
      expect(Gear.supplies.price, 150);
    });
  });

  group('the falcons\' room', () {
    test('a facility of 18,000 holding 4', () {
      expect(Facility.falconRoom.price, 18000);
      expect(Facility.falconRoom.most, 1);
      expect(HuntBalance.roomHolds, 4);
      final g = gameOn(d(2026, 10, 1));
      withRoom(g);
      expect(
        g.dispatch(BuildFacility(g.me.id, Facility.falconRoom)).ok,
        isFalse,
      );
    });
  });

  group('the lots', () {
    test('worked out from the seed and the day, none when closed', () {
      final a = FalconMarket.lots(7, FalconRoute.trapping, d(2026, 10, 5));
      final b = FalconMarket.lots(7, FalconRoute.trapping, d(2026, 10, 5));
      expect([for (final l in a) l.value], [for (final l in b) l.value]);
      expect(
        FalconMarket.lots(7, FalconRoute.trapping, d(2026, 12, 1)),
        isEmpty,
      );
      expect(
        FalconMarket.lots(7, FalconRoute.breeders, d(2026, 9, 1)),
        isEmpty,
      );
      expect(
        FalconMarket.lots(7, FalconRoute.breeders, d(2027, 8, 5)),
        hasLength(4),
      );
    });
    test('the trapping auction\'s: a peregrine of the year, the real '
        'openings, the worth\'s spread', () {
      final values = <int>[];
      for (var seed = 1; seed <= 60; seed++) {
        for (var day = d(2026, 10, 1); day <= d(2026, 11, 30); day += 1) {
          for (final l in FalconMarket.lots(seed, FalconRoute.trapping, day)) {
            expect(l.species, FalconSpecies.passagePeregrine);
            expect(FalconAge.on(day, l.hatched), FalconAge.farkh);
            expect(l.opening, inInclusiveRange(30000, 150000));
            expect(l.opening, lessThanOrEqualTo(l.value));
            expect(l.value, inInclusiveRange(50000, 650000));
            expect(l.ground!.trapping, isTrue);
            values.add(l.value);
          }
        }
      }
      values.sort();
      final dear = values.where((v) => v >= 300000).length / values.length;
      final mean = values.reduce((a, b) => a + b) / values.length;
      expect(values.length, greaterThan(4000));
      // at least 6 of 40 dear [185][211][213]: the share kept at 0.15
      expect(dear, closeTo(0.15, 0.02));
      // the seasons' mean 88,000 [200] to 160,000 [213]
      expect(mean, inInclusiveRange(88000, 160000));
    });
    test('the breeders\': farm-bred sakers about 19,000 [158]', () {
      final values = <int>[];
      for (var seed = 1; seed <= 100; seed++) {
        for (var day = d(2027, 8, 5); day <= d(2027, 8, 25); day += 1) {
          for (final l in FalconMarket.lots(seed, FalconRoute.breeders, day)) {
            expect(l.species, FalconSpecies.saker);
            values.add(l.value);
          }
        }
      }
      values.sort();
      expect(values[values.length ~/ 2], closeTo(19000, 1500));
      // a farm-bred saker's tail kept near its one figure (finding 5)
      expect(values.last, lessThanOrEqualTo(60000));
      expect(values.first, greaterThanOrEqualTo(12000));
    });
  });

  group('buying a falcon up to his ceiling (Q-17 revised)', () {
    test('out of its month: refused with the route', () {
      final g = gameOn(d(2026, 9, 15));
      withRoom(g);
      final r = g.dispatch(
        BuyFalcon(g.me.id, 'breeders:${g.today.value}:0', 50000),
      );
      expect(why(r), 'routeClosed');
      expect((r as Err).error.params['route'], 'breeders');
      expect(FalconLines.refusal(r.error), contains('أغسطس'));
    });
    test('no room: refused, the lot still for sale', () {
      final g = gameOn(d(2026, 10, 1));
      give(g, 2000000);
      final lot = firstLot(g, FalconRoute.trapping);
      final r = g.dispatch(BuyFalcon(g.me.id, lot.key, 1000000));
      expect(why(r), 'noRoom');
      expect(
        FalconLines.refusal((r as Err).error),
        startsWith('ابنِ غرفة الصقور'),
      );
      expect(g.me.falconry?.lotsGone ?? {}, isEmpty);
    });
    test('a ceiling above his money: refused, nothing told, the lot stays', () {
      final g = gameOn(d(2026, 10, 1));
      withRoom(g);
      final lot = firstLot(g, FalconRoute.trapping);
      final r = g.dispatch(BuyFalcon(g.me.id, lot.key, g.me.cash.value + 1));
      expect((r as Err).error.code, ErrorCode.insufficientFunds);
      expect(r.events, isEmpty);
      expect(g.me.falconry?.lotsGone ?? {}, isEmpty);
    });
    test('a ceiling under the hammer: lost, its price told, gone for good, '
        'nothing paid', () {
      final g = gameOn(d(2026, 10, 1));
      give(g, 2000000);
      withRoom(g);
      final lot = firstLot(g, FalconRoute.trapping);
      final cash = g.me.cash.value;
      final r = g.dispatch(BuyFalcon(g.me.id, lot.key, lot.value - 1));
      expect(r.ok, isTrue);
      expect(r.events.whereType<FalconLotLost>().single.price, lot.value);
      expect(g.me.cash.value, cash);
      expect(g.me.falconry!.falcons, isEmpty);
      expect(why(g.dispatch(BuyFalcon(g.me.id, lot.key, 9000000))), 'lotGone');
    });
    test('in debt: refused', () {
      final g = gameOn(d(2026, 10, 1));
      withRoom(g);
      final lot = firstLot(g, FalconRoute.trapping);
      Sim(g.state).pay(g.me, Riyal(-g.me.cash.value - 10), LedgerCategory.fine);
      final r = g.dispatch(BuyFalcon(g.me.id, lot.key, 100));
      expect((r as Err).error.code, ErrorCode.inDebt);
    });
    test('a ceiling at the hammer exactly, with exactly that money: bought at '
        'the hammer, in cash, its own kind', () {
      final g = gameOn(d(2026, 10, 1));
      withRoom(g);
      final lot = firstLot(g, FalconRoute.trapping);
      Sim(
        g.state,
      ).pay(g.me, Riyal(lot.value - g.me.cash.value), LedgerCategory.opening);
      final r = g.dispatch(BuyFalcon(g.me.id, lot.key, lot.value));
      expect(r.ok, isTrue, reason: '$r');
      expect(r.events.whereType<FalconBought>().single.price, lot.value);
      expect(g.me.cash.value, 0);
      expect(g.me.ledger.last.category, LedgerCategory.falconPurchase);
      expect(g.me.onAccount, 0);
      final f = g.me.falconry!.falcons.single;
      expect(f.species, FalconSpecies.passagePeregrine);
      expect(f.female, isTrue, reason: 'females only for now');
      expect(f.passport, isNotNull);
      expect(f.ring, isTrue);
      expect(f.how, FalconHow.bought);
      expect(f.route, FalconRoute.trapping);
      expect(f.price, lot.value);
    });
    test('a ceiling above the hammer pays the hammer only', () {
      final g = gameOn(d(2026, 10, 1));
      give(g, 5000000);
      withRoom(g);
      final lot = firstLot(g, FalconRoute.trapping);
      final cash = g.me.cash.value;
      g.dispatch(BuyFalcon(g.me.id, lot.key, 4000000));
      expect(g.me.cash.value, cash - lot.value);
      // the same lot is not sold twice
      expect(why(g.dispatch(BuyFalcon(g.me.id, lot.key, 4000000))), 'lotGone');
    });
    test('a stale or a malformed key: its own words', () {
      final g = gameOn(d(2026, 10, 2));
      give(g, 5000000);
      withRoom(g);
      final y = FalconMarket.lots(
        g.state.world.seed,
        FalconRoute.trapping,
        g.today - 1,
      );
      for (final k in [
        if (y.isNotEmpty) y.first.key,
        'trapping:${g.today.value - 1}:0',
        'trapping:${g.today.value + 1}:0',
        'trapping:${g.today.value}:99',
        'nonsense',
      ]) {
        final r = g.dispatch(BuyFalcon(g.me.id, k, 1000));
        expect(why(r), 'notALot', reason: k);
        expect(
          FalconLines.refusal((r as Err).error),
          'هالطير مو من طيور اليوم',
        );
      }
    });
    test('the breeders\' saker: no ring', () {
      final g = gameOn(d(2027, 8, 5));
      give(g, 5000000);
      withRoom(g);
      final lot = firstLot(g, FalconRoute.breeders);
      expect(g.dispatch(BuyFalcon(g.me.id, lot.key, 100000)).ok, isTrue);
      final f = g.me.falconry!.falcons.single;
      expect(f.species, FalconSpecies.saker);
      expect(f.ring, isFalse);
      expect(f.passport, isNotNull);
    });
    test(
      'the room holds 4; then the hunting permit; the keep 20 a day each',
      () {
        final g = gameOn(d(2026, 10, 1));
        give(g, 50000000);
        withRoom(g);
        var n = 0;
        while (n < 4) {
          for (final l in FalconMarket.lots(
            g.state.world.seed,
            FalconRoute.trapping,
            g.today,
          )) {
            if (n < 4 && g.dispatch(BuyFalcon(g.me.id, l.key, 9000000)).ok) n++;
          }
          g.advanceDays(1);
        }
        expect(g.me.falconry!.falcons, hasLength(4));
        final lot = firstLot(g, FalconRoute.trapping);
        final r = g.dispatch(BuyFalcon(g.me.id, lot.key, 9000000));
        expect(why(r), 'roomFull');
        expect(FalconLines.refusal((r as Err).error), contains('4'));
        expect(g.dispatch(BuyPermit(g.me.id, PermitKind.hunting)).ok, isTrue);
        g.advanceTo(d(2026, 12, 1));
        int keep() => g.me.ledger
            .where(
              (e) =>
                  e.category == LedgerCategory.falconUpkeep &&
                  e.month == '2026-12',
            )
            .fold(0, (n, e) => n + e.amount.value);
        final before = keep();
        g.advanceDays(1);
        expect(keep() - before, -80, reason: '4 falcons at 20 riyals');
        expect(HuntBalance.upkeepPerDay, 20);
        expect(checkInvariants(g.state), isEmpty);
      },
    );
  });

  group('the lots tell only what bidders see', () {
    test('the opening tells little of the worth (finding 2)', () {
      final bands = {
        'low': [0, 0],
        'high': [0, 0],
      };
      for (var seed = 1; seed <= 120; seed++) {
        for (var day = d(2026, 10, 1); day <= d(2026, 11, 30); day += 1) {
          for (final l in FalconMarket.lots(seed, FalconRoute.trapping, day)) {
            final b = l.opening < 50000 ? 'low' : 'high';
            bands[b]![0]++;
            if (l.value >= 300000) bands[b]![1]++;
          }
        }
      }
      final low = bands['low']!, high = bands['high']!;
      final all = (low[1] + high[1]) / (low[0] + high[0]);
      expect(all, closeTo(0.15, 0.02));
      // three in four openings are 30,000 to 45,000 and tell nothing
      expect(low[0] / (low[0] + high[0]), closeTo(0.75, 0.03));
      expect(low[1] / low[0], closeTo(all, 0.02));
      // the rest a weak tie: an opening above 50,000 says the worth is above
      // it, no more (measured: about twice the dear share)
      expect(high[1] / high[0], lessThan(0.4));
    });
    test('lots a night at the trapping auction: 0 to 3, as weighted', () {
      final n = [0, 0, 0, 0];
      for (var seed = 1; seed <= 200; seed++) {
        for (var day = d(2026, 10, 1); day <= d(2026, 11, 30); day += 1) {
          n[FalconMarket.lots(seed, FalconRoute.trapping, day).length]++;
        }
      }
      final all = n.fold(0, (a, b) => a + b);
      for (final (i, w) in [(0, 0.2), (1, 0.35), (2, 0.3), (3, 0.15)]) {
        expect(n[i] / all, closeTo(w, 0.02), reason: '$i lots');
      }
    });
    test('the trapping auction\'s lots: females, trapped 1 to 5 days ago', () {
      for (var seed = 1; seed <= 30; seed++) {
        for (var day = d(2026, 10, 1); day <= d(2026, 11, 30); day += 1) {
          for (final l in FalconMarket.lots(seed, FalconRoute.trapping, day)) {
            expect(l.female, isTrue);
            expect(l.trappedDaysAgo, inInclusiveRange(1, 5));
          }
        }
      }
    });
  });

  group('views and saves', () {
    test('no hidden value in the views: each falcon\'s skill, every lot\'s '
        'worth, a whitelist of the falcons\' keys (finding 3)', () {
      final g = gameOn(d(2026, 10, 1));
      give(g, 5000000);
      withRoom(g);
      final lot = firstLot(g, FalconRoute.trapping);
      g.dispatch(BuyFalcon(g.me.id, lot.key, 4000000));
      final facts = falconFacts(g.state, g.me.id);
      final text = jsonEncode(facts);
      bool has(String number) => RegExp('[:\\[,]$number[,\\]}]').hasMatch(text);
      for (final f in g.me.hunt.falcons) {
        expect(has('${f.skill}'), isFalse, reason: 'skill ${f.skill}');
      }
      for (final r in FalconRoute.values) {
        for (final l in FalconMarket.lots(g.state.world.seed, r, g.today)) {
          if (l.key == lot.key) continue; // his own: the price he paid
          for (final n in [l.value, l.value ~/ 1000, l.value * 100]) {
            expect(has('$n'), isFalse, reason: '${l.key} worth $n');
          }
          expect(has('${l.skill}'), isFalse, reason: '${l.key} skill');
        }
      }
      const allowed = {
        'id',
        'name',
        'species',
        'speciesName',
        'female',
        'age',
        'how',
        'on',
        'route',
        'price',
        'ground',
        'size',
        'weight',
        'passport',
        'ring',
        'trapDoc',
        'dauDays',
        'dauNeeded',
        'caredOn',
        'flights',
        'taken',
        'where',
        'keep',
        'ready',
        'tracker',
        'stepsBackOn',
        'entered',
      };
      for (final k in ['falcons', 'held']) {
        for (final f in facts[k]! as List) {
          expect(allowed.containsAll((f as Map).keys), isTrue, reason: '$f');
        }
      }
      const lotKeys = {
        'lot',
        'route',
        'species',
        'female',
        'age',
        'size',
        'weight',
        'opening',
        'ground',
        'trappedDaysAgo',
        'gone',
      };
      for (final l in facts['lots']! as List) {
        expect(lotKeys.containsAll((l as Map).keys), isTrue, reason: '$l');
      }
      expect(
        (facts['falcons']! as List).single,
        containsPair('speciesName', 'شاهين بحري'),
      );
    });
    test('a game that never touched falcons saves no falconry', () {
      final g = gameOn(d(2026, 10, 1))..advanceDays(60);
      expect(jsonEncode(g.state.toJson()), isNot(contains('falconry')));
    });
    test('the falconry round-trips through the save', () {
      final g = gameOn(d(2026, 10, 1));
      give(g, 5000000);
      withRoom(g);
      g.dispatch(OrderGear(g.me.id, Gear.pigeon, 3));
      g.dispatch(BuyPermit(g.me.id, PermitKind.trapping));
      final lot = firstLot(g, FalconRoute.trapping);
      g.dispatch(BuyFalcon(g.me.id, lot.key, 4000000));
      final a = jsonEncode(g.state.toJson());
      final b = jsonEncode(
        GameState.fromJson(jsonDecode(a) as Map<String, Object?>).toJson(),
      );
      expect(b, a);
      expect(checkInvariants(g.state), isEmpty);
      for (final e in g.state.inboxOf(g.me.id)) {
        expect(
          jsonEncode(DomainEvent.fromJson(e.toJson()).toJson()),
          jsonEncode(e.toJson()),
        );
      }
    });
  });
}
