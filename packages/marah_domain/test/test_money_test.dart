import 'dart:convert';

import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/persistence.dart';
import 'package:test/test.dart';

// Money without limit for the owner's testing (TestMoney): on, the money never
// runs short and the ledger still adds up; off, nothing changes; the save
// keeps the mark.

Game newGame([int seed = 42]) => Game.create(
  seed: seed,
  playerName: 'بدر',
  farmName: 'عزبة الصفوة',
  region: Region.qassim,
  favourite: ColorCategory.majaheem,
  startedAt: DateTime.utc(2026, 11, 8),
);

int ledgerSum(PlayerState p) => p.ledger.fold(0, (n, e) => n + e.amount.value);

/// The dearest listing, made dearer than the money can pay.
Listing dearest(Game g, int price) {
  final l = g.state.world.listings.values.reduce(
    (a, b) => a.askPrice.value >= b.askPrice.value ? a : b,
  );
  l.askPrice = Riyal(price);
  return l;
}

void main() {
  test('off (as every game starts): an order it cannot afford is refused, '
      'and the save carries nothing new', () {
    final g = newGame();
    final me = g.me;
    expect(me.testMoney, isFalse);
    final l = dearest(g, 900000);
    final before = jsonEncode(g.state.toJson());
    final r = g.dispatch(BuyListing(me.id, l.id));
    expect(r.ok, isFalse);
    expect((r as Err).error.code, ErrorCode.insufficientFunds);
    expect(jsonEncode(g.state.toJson()), before);
    final pj = me.toJson();
    expect(pj.containsKey('testMoney'), isFalse);
    expect(pj.containsKey('testedFrom'), isFalse);
    g.advanceDays(40);
    expect(
      me.ledger.where((e) => e.category == LedgerCategory.testMoney),
      isEmpty,
    );
  });

  test('on: the money at its floor at once, as a row of its own kind; the '
      'game marked', () {
    final g = newGame();
    final me = g.me, start = me.cash.value;
    final r = g.dispatch(SetTestMoney(me.id, on: true));
    expect(r.ok, isTrue);
    expect(me.cash.value, TestMoney.floor);
    expect(me.testMoney, isTrue);
    expect(me.testedFrom, g.today);
    final rows = me.ledger.where((e) => e.category == LedgerCategory.testMoney);
    expect(rows.single.amount.value, TestMoney.floor - start);
    expect(ledgerSum(me), me.cash.value);
    expect(r.events.whereType<TestMoneySet>().single.on, isTrue);
    expect(
      r.events.whereType<TestMoneyAdded>().single.amount,
      TestMoney.floor - start,
    );
    expect(checkInvariants(g.state), isEmpty);
  });

  test(
    'on: an order dearer than the floor goes through, the ledger adds up',
    () {
      final g = newGame();
      final me = g.me;
      g.dispatch(SetTestMoney(me.id, on: true));
      final l = dearest(g, 15000000);
      final r = g.dispatch(BuyListing(me.id, l.id));
      expect(r.ok, isTrue, reason: '$r');
      expect(r.events.whereType<CamelBought>(), hasLength(1));
      expect(me.cash.value, greaterThanOrEqualTo(TestMoney.floor));
      expect(ledgerSum(me), me.cash.value);
      // prices are as they were: the purchase row is the asking price
      expect(
        me.ledger
            .where((e) => e.category == LedgerCategory.purchase)
            .last
            .amount,
        const Riyal(-15000000),
      );
      expect(checkInvariants(g.state), isEmpty);
    },
  );

  test('on: a refusal that is not for money is refused as before', () {
    final g = newGame();
    final me = g.me;
    g.dispatch(SetTestMoney(me.id, on: true));
    final r = g.dispatch(BuyListing(me.id, const ListingId('none')));
    expect((r as Err).error.code, ErrorCode.notFound);
    expect(checkInvariants(g.state), isEmpty);
  });

  test('on, over months: never under the floor at a day\'s end, one row a '
      'month, every invariant holds', () {
    final g = newGame();
    final me = g.me;
    g.dispatch(SetTestMoney(me.id, on: true));
    for (var d = 0; d < 120; d++) {
      g.advanceDays(1);
      expect(me.cash.value, greaterThanOrEqualTo(TestMoney.floor));
      expect(me.onAccount, 0);
    }
    expect(checkInvariants(g.state), isEmpty);
    final months = me.ledger
        .where((e) => e.category == LedgerCategory.testMoney)
        .map((e) => e.month ?? Money.monthOf(e.day))
        .toList();
    expect(months.toSet().length, months.length);
    expect(ledgerSum(me), me.cash.value);
  });

  test('off again: the money and the mark stay, no more top-ups, the game '
      'plays on', () {
    final g = newGame();
    final me = g.me;
    g.dispatch(SetTestMoney(me.id, on: true));
    final marked = me.testedFrom;
    g.advanceDays(3);
    final r = g.dispatch(SetTestMoney(me.id, on: false));
    expect(r.events.whereType<TestMoneySet>().single.on, isFalse);
    final cash = me.cash.value;
    expect(me.testMoney, isFalse);
    expect(me.testedFrom, marked);
    expect(cash, greaterThanOrEqualTo(TestMoney.floor - 50000));
    final rows = me.ledger
        .where((e) => e.category == LedgerCategory.testMoney)
        .length;
    g.advanceDays(30);
    expect(
      me.ledger.where((e) => e.category == LedgerCategory.testMoney).length,
      rows,
    );
    expect(ledgerSum(me), me.cash.value);
    expect(checkInvariants(g.state), isEmpty);
  });

  test('the save keeps the switch and the mark, and reads them back', () {
    final g = newGame();
    final me = g.me;
    g.dispatch(SetTestMoney(me.id, on: true));
    g.advanceDays(2);
    final text = jsonEncode(g.state.toJson());
    final back = GameState.fromJson(jsonDecode(text) as Map<String, Object?>);
    final p = back.players[me.id]!;
    expect(p.testMoney, isTrue);
    expect(p.testedFrom, me.testedFrom);
    expect(jsonEncode(back.toJson()), text);
    g.dispatch(SetTestMoney(me.id, on: false));
    final pj = me.toJson();
    expect(pj.containsKey('testMoney'), isFalse);
    expect(pj['testedFrom'], me.testedFrom!.value);
  });

  test('the bank names it its own kind, and today\'s net leaves it out', () {
    final g = newGame();
    final me = g.me;
    final net = GameView(g.state, me.id).todayNet;
    g.dispatch(SetTestMoney(me.id, on: true));
    expect(GameView(g.state, me.id).todayNet, net);
    expect(Money.kindOf(LedgerCategory.testMoney), MoneyKind.testMoney);
  });

  test('the bank\'s month: its net and its biggest line are the farm\'s, the '
      'test money listed apart', () {
    final g = newGame();
    final me = g.me;
    g.advanceDays(3);
    final before = GameView(g.state, me.id).moneyMonths.first;
    g.dispatch(SetTestMoney(me.id, on: true));
    g.advanceDays(2);
    final v = GameView(g.state, me.id);
    final m = v.moneyMonths.first;
    expect(m.testMoney, greaterThan(9000000));
    expect(
      m.lines.where((l) => l.kind == MoneyKind.testMoney).single.amount,
      m.testMoney,
    );
    expect(m.top.kind, isNot(MoneyKind.testMoney));
    expect(m.net.abs(), lessThan(100000)); // (two days of the farm)
    expect(m.income, lessThan(before.income + 100000));
    final total = v.moneyMonths.fold(
      v.openingBalance.value,
      (n, x) => n + x.net + x.testMoney,
    );
    expect(total, me.cash.value);
    expect(v.moneyMonth(m.month)!.testMoney, m.testMoney);
  });
}
