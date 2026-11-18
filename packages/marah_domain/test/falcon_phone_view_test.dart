// The views the phone reads of the hunting season that part A did not give
// (task T18 part B, "engine view for the phone"): what became of his birds
// and lots (falconFacts' 'news'), told after it happened, with no hidden
// value before the engine tells it.
import 'dart:convert';

import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:test/test.dart';

GameDay d(int y, int m, int day) => GameDay.ofDate(DateTime.utc(y, m, day));

Game gameOn(GameDay start) => Game.create(
  seed: 4242,
  playerName: 'p',
  farmName: 'f',
  region: Region.qassim,
  favourite: ColorCategory.wodh,
  startDay: start,
  startedAt: DateTime.utc(2026, 11, 14),
);

void give(Game g, int riyals) =>
    Sim(g.state).pay(g.me, Riyal(riyals), LedgerCategory.opening);

Falcon netBird(Game g, {String name = 'براق', int value = 112000}) {
  final f = Falcon(
    id: g.state.world.ids.falcon(),
    name: name,
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
    value: value,
    caredOn: g.today,
  );
  g.me.hunt.held.add(f);
  return f;
}

List<Map<String, Object?>> news(Game g) =>
    (falconFacts(g.state, g.me.id)['news']! as List)
        .cast<Map<String, Object?>>();

void main() {
  test('a game that never touched falcons has no news', () {
    final g = gameOn(d(2026, 10, 1));
    expect(news(g), isEmpty);
  });

  test('a bird entered: no price before the hammer; sold: its price told, '
      'once, under a key that stays the same', () {
    final g = gameOn(d(2026, 10, 1));
    give(g, 100000);
    final f = netBird(g);
    expect(g.dispatch(EnterTrapAuction(g.me.id, f.id)).ok, isTrue);
    expect(news(g), isEmpty);
    expect(jsonEncode(falconFacts(g.state, g.me.id)), isNot(contains('112')));
    g.advanceDays(1);
    final n = news(g);
    expect(n, hasLength(1));
    expect(n.single['kind'], 'sold');
    expect(n.single['name'], 'براق');
    expect(n.single['price'], 112000);
    final key = n.single['key'];
    g.advanceDays(3);
    expect(news(g).single['key'], key);
  });

  test('neither sold nor kept at the close: set free, told', () {
    final g = gameOn(d(2026, 11, 29));
    give(g, 100000);
    netBird(g);
    g.advanceDays(2); // 1 December: the auction closed on 30 November
    final n = news(g);
    expect(n.map((x) => x['kind']), contains('freedAtClose'));
  });

  test('a lot gone to another bidder: its price told; a lot bought is not '
      'news (the falcon is in his list)', () {
    final g = gameOn(d(2026, 10, 1));
    give(g, 3000000);
    expect(g.dispatch(BuildFacility(g.me.id, Facility.falconRoom)).ok, isTrue);
    g.advanceDays(Balance.buildDays);
    late FalconLot lot;
    for (;;) {
      final l = FalconMarket.lots(
        g.state.world.seed,
        FalconRoute.trapping,
        g.today,
      );
      if (l.length >= 2) {
        lot = l.first;
        expect(g.dispatch(BuyFalcon(g.me.id, l[1].key, 2000000)).ok, isTrue);
        break;
      }
      g.advanceDays(1);
    }
    expect(g.dispatch(BuyFalcon(g.me.id, lot.key, 1)).ok, isTrue);
    final n = news(g);
    expect(n, hasLength(1));
    expect(n.single['kind'], 'lotLost');
    expect(n.single['lot'], lot.key);
    expect(n.single['price'], lot.value);
  });

  test('older than 30 days: no longer told', () {
    final g = gameOn(d(2026, 10, 1));
    give(g, 100000);
    final f = netBird(g);
    g.dispatch(EnterTrapAuction(g.me.id, f.id));
    g.advanceDays(1);
    expect(news(g), hasLength(1));
    g.advanceDays(falconNewsDays + 1);
    expect(news(g), isEmpty);
  });

  Map<String, Object?> permit(Game g, PermitKind k) =>
      ((falconFacts(g.state, g.me.id)['permits']! as List)
              .cast<Map<String, Object?>>())
          .singleWhere((p) => p['kind'] == k.name)
          .cast<String, Object?>();

  test('a permit is held for its season only: a season gone by is not held, '
      'and the next can be bought', () {
    final g = gameOn(d(2026, 10, 1));
    give(g, 100000);
    expect(g.dispatch(BuyPermit(g.me.id, PermitKind.trapping)).ok, isTrue);
    expect(permit(g, PermitKind.trapping)['held'], 2026);
    expect(permit(g, PermitKind.trapping)['cannot'], 'permitHeld');
    g.advanceDays(d(2027, 1, 20).daysSince(g.today));
    final p = permit(g, PermitKind.trapping);
    expect(p['season'], 2027);
    expect(p['held'], isNull, reason: 'the 2026 permit is not this season\'s');
    expect(p['cannot'], isNull);
  });

  test('a permit refused for money says why: its code', () {
    final g = gameOn(d(2026, 10, 1));
    give(g, -g.me.cash.value - 500);
    expect(permit(g, PermitKind.trapping)['cannot'], 'inDebt');
    give(g, 600);
    expect(permit(g, PermitKind.trapping)['cannot'], 'insufficientFunds');
  });

  test('a kept bird says whether it can be set free today', () {
    final g = gameOn(d(2027, 1, 20));
    final f = netBird(g)..keep = true;
    g.me.hunt.held.remove(f);
    g.me.hunt.falcons.add(f);
    Map<String, Object?> mine() =>
        ((falconFacts(g.state, g.me.id)['falcons']! as List)
                .cast<Map<String, Object?>>())
            .single
            .cast<String, Object?>();
    expect(mine()['releaseCannot'], 'releaseMonths');
    g.advanceDays(d(2027, 2, 2).daysSince(g.today));
    expect(mine().containsKey('releaseCannot'), isTrue);
    expect(mine()['releaseCannot'], isNull);
  });

  test('the falconry trip card: a ready falcon\'s own tracker counts; a '
      'day\'s outing needs no supplies', () {
    final g = gameOn(d(2026, 10, 1));
    final f = netBird(g)
      ..dauDays = HuntBalance.dauDaysNeeded
      ..tracker = true;
    g.me.hunt.held.remove(f);
    g.me.hunt.falcons.add(f);
    final day = Trips.card(g, TripKind.falconry, Ground.estate, 0);
    expect(day['lacks'], isEmpty, reason: '${day['lacks']}');
    expect(day['has'], [Gear.tracker.label]);
    final camp = Trips.card(g, TripKind.falconry, Ground.estate, 3);
    expect(camp['lacks'], [Gear.supplies.label]);
  });
}
