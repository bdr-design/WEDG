// البنك's reading of the ledger (views/money.dart): its figures are the
// ledger's own sums, a sale goes with its commission, the biggest kind, the
// months' edges, the day-one state, and ten years.
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:marah_domain/testing.dart';
import 'package:test/test.dart';

Game newGame([int seed = 4242]) => Game.create(
  seed: seed,
  playerName: 'اللاعب',
  farmName: 'العزبة',
  region: Region.qassim,
  favourite: ColorCategory.wodh,
  startedAt: DateTime.utc(2026, 11, 13),
);

/// Feed and water topped up to three weeks when under ten days (the bot's
/// rule), as a player who keeps his herd fed.
void topUp(Game g) {
  final v = GameView(g.state, g.me.id);
  for (final s in Supply.values) {
    final left = v.daysLeft(s);
    if (left == null || left >= 10) continue;
    final n = v.dailyNeeds;
    final need = switch (s) {
      Supply.barley => n.barley,
      Supply.alfalfa => n.alfalfa,
      Supply.water => n.water,
    };
    final want =
        ((need * 21 - Provisions.stocked(v.me.farm, s)) /
                Provisions.unitSize(s))
            .ceil();
    final room = v.roomFor(s);
    final units = want < room ? want : room;
    if (units > 0) {
      g.dispatch(OrderSupply(g.me.id, s, units));
    } else if (s == Supply.water && v.roomFor(s, tanker: Tanker.small) > 0) {
      g.dispatch(OrderSupply(g.me.id, s, 1, tanker: Tanker.small));
    }
  }
}

/// The opening balance and every month's net make the cash; each month's in
/// and out are its lines' sums; the kept past months read as a fresh read.
void expectAddsUp(Game g) {
  final v = GameView(g.state, g.me.id);
  final months = v.moneyMonths;
  final total = months.fold(v.openingBalance.value, (n, m) => n + m.net);
  expect(total, g.me.cash.value, reason: 'opening + nets == cash');
  for (final m in months) {
    final ins = m.lines.where((l) => l.amount > 0);
    final outs = m.lines.where((l) => l.amount <= 0);
    expect(m.income, ins.fold(0, (n, l) => n + l.amount));
    expect(m.spent, -outs.fold(0, (n, l) => n + l.amount));
    final fresh = v.moneyMonth(m.month)!;
    expect(fresh.lines, m.lines, reason: 'kept ${m.month} == read afresh');
  }
  final t = v.moneyToday;
  expect(t.income - t.spent, v.todayNet.value, reason: 'today == todayNet');
}

void main() {
  test('day one: the opening balance and nothing else', () {
    final g = newGame();
    final v = GameView(g.state, g.me.id);
    expect(v.openingBalance.value, Balance.startingCash);
    expect(v.moneyMonths, isEmpty);
    expect(v.moneyToday, (income: 0, spent: 0));
    expect(v.startedOn, g.today);
    expectAddsUp(g);
  });

  test('a beginner\'s half year: sums, the folded commission, the biggest '
      'kind, the trip home', () {
    final g = newGame();
    final me = g.me.id;
    CamelId? bought, calf;
    while (g.today.date.isBefore(DateTime.utc(2027, 4, 15))) {
      final v = GameView(g.state, me);
      final d = g.today.date;
      topUp(g);
      if (d.month == 11 && d.day == 20) {
        final l =
            (v.market.where((l) => l.camel.sex == Sex.female).toList()..sort(
                  (a, b) => (a.askPrice.value + a.transport.value).compareTo(
                    b.askPrice.value + b.transport.value,
                  ),
                ))
                .first;
        expect(g.dispatch(BuyListing(me, l.id)).ok, isTrue);
        bought = l.camel.id;
      }
      if (d.month == 1 && d.day == 20) {
        final c = v.herd.firstWhere((c) => c.ageDays < 400 && c.id != bought);
        calf = c.id;
        final (_, hi) = c.estimate;
        expect(g.dispatch(ListForSale(me, c.id, hi.value)).ok, isTrue);
      }
      if (calf != null) {
        for (final l in v.myListings) {
          final o = v.offersOn(l.id).firstOrNull;
          if (o != null) g.dispatch(AcceptOffer(me, o.id));
        }
      }
      g.advanceDays(1);
      expectAddsUp(g);
    }
    final v = GameView(g.state, me);
    final nov = v.moneyMonth('2026-11')!;
    // the purchase is November's biggest kind, named, and its truck home
    expect(nov.top.kind, MoneyKind.purchase);
    expect(nov.top.name, g.state.world.camels[bought]!.name);
    expect(nov.top.day, GameDay.ofDate(DateTime.utc(2026, 11, 20)));
    final trip = nov.lines.firstWhere((l) => l.kind == MoneyKind.transport);
    expect(trip.trip, TripReason.purchase);
    expect(trip.name, nov.top.name);
    // the calf's sale, if an offer came: what reached the player, its price
    // and the commission apart in the line
    final sales = [
      for (final m in v.moneyMonths)
        ...m.lines.where((l) => l.kind == MoneyKind.sale),
    ];
    for (final s in sales) {
      expect(s.amount, s.price! - s.fee!);
      expect(s.fee, (s.price! * Balance.brokerCommission).round());
      expect(s.name, g.state.world.camels[calf]!.name);
    }
    expect(sales, isNotEmpty, reason: 'an offer came for the calf');
  });

  test('month edges: the last day\'s order in its month, the next day\'s '
      'milk in the next', () {
    final g = newGame();
    final me = g.me.id;
    g.advanceTo(GameDay.ofDate(DateTime.utc(2026, 10, 31)));
    expect(g.dispatch(OrderSupply(me, Supply.alfalfa, 1)).ok, isTrue);
    g.advanceDays(1); // 1 November: the day's milk opens November's row
    final v = GameView(g.state, me);
    final [nov, oct] = v.moneyMonths;
    expect(nov.month, '2026-11');
    expect(oct.month, '2026-10');
    expect(nov.lines.single.kind, MoneyKind.milk);
    expect(nov.income, v.milkIncomeToday);
    final feed = oct.lines.firstWhere((l) => l.kind == MoneyKind.feed);
    expect(feed.day, GameDay.ofDate(DateTime.utc(2026, 10, 31)));
    expectAddsUp(g);
  });

  test('a trip by its reason: to a stud, to a festival', () {
    final g = newGame();
    final sim = Sim(g.state);
    final p = g.me;
    final dam = g.state.world.aliveOwnedBy(p.id).first;
    // (rows as handlers.dart _mate and the festival system write them)
    sim.pay(p, const Riyal(-3000), LedgerCategory.studFee, ref: 'some-bull');
    sim.pay(p, const Riyal(-400), LedgerCategory.transport, ref: dam.id.value);
    var v = GameView(g.state, p.id);
    var trip = v.moneyMonths.first.lines.firstWhere(
      (l) => l.kind == MoneyKind.transport,
    );
    expect((trip.trip, trip.name), (TripReason.mating, dam.name));
    g.advanceTo(GameDay.ofDate(DateTime.utc(2026, 12, 2)));
    sim.pay(p, const Riyal(-900), LedgerCategory.transport, ref: 'f-gone-1');
    v = GameView(g.state, p.id);
    trip = v
        .moneyMonth('2026-12')!
        .lines
        .firstWhere((l) => l.kind == MoneyKind.transport);
    // a festival the world has forgotten: the reason without a name
    expect((trip.trip, trip.name), (TripReason.festival, null));
    expectAddsUp(g);
  });

  test('a balance under zero adds up as any other', () {
    // (no rule of this engine owes money yet: a fine or supplies on account
    // will; here the rows are written as Sim writes any)
    final g = newGame();
    final sim = Sim(g.state);
    final p = g.me;
    sim.bill(p, const Riyal(-26000), LedgerCategory.wages);
    expect(p.cash.value, lessThan(0));
    final v = GameView(g.state, p.id);
    expect(v.moneyToday, (income: 0, spent: 26000));
    expect(v.moneyMonths.single.net, -26000);
    expect(v.moneyMonths.single.top.kind, MoneyKind.wages);
    expectAddsUp(g);
  });

  test('ten years: every figure adds up, a row a month on the main screen, '
      'the past months kept', () {
    final g = newGame(7919);
    grant(g, 580000); // (the long run's money: a herd that trades)
    final bot = Bot(g);
    for (var year = 0; year < 10; year++) {
      expect(bot.run(52), isNull);
      expectAddsUp(g);
    }
    final v = GameView(g.state, g.me.id);
    final months = v.moneyMonths;
    // (two openings here: the test's grant is one)
    expect(v.openingBalance.value, Balance.startingCash + 580000);
    expect(months.length, lessThanOrEqualTo(10 * 12 + 1));
    expect(months.map((m) => m.month).toList(), [
      for (final m
          in months.map((m) => m.month).toList()
            ..sort((a, b) => b.compareTo(a)))
        m,
    ]);
    final watch = Stopwatch()..start();
    for (var i = 0; i < 100; i++) {
      v.moneyMonths;
    }
    // the months before this one are read once (a snapshot reads them)
    expect(watch.elapsedMicroseconds / 100, lessThan(500));
  });
}
