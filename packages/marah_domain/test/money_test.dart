// البنك's reading of the ledger (views/money.dart): its figures are the
// ledger's own sums, a sale goes with its commission, the biggest kind, the
// months' edges, the day-one state, and ten years.
import 'dart:convert';

import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:marah_domain/src/world_gen.dart';
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
    expect(v.moneyMonth(m.month)!.lines, m.lines, reason: 'row == opened');
  }
  // the kept months read as the whole ledger read afresh (a game opened again)
  final again = GameView(
    GameState.fromJson(
      jsonDecode(jsonEncode(g.state.toJson())) as Map<String, Object?>,
    ),
    g.me.id,
  );
  expect(
    [for (final m in again.moneyMonths) m.lines],
    [for (final m in months) m.lines],
    reason: 'kept == read afresh',
  );
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

  test('the festivals\' money: a trip there reads as the festival\'s, a late '
      'fee, a treatment and each fine by what it was for', () {
    final g = newGame();
    grant(g, 1000000);
    g.me.farm
      ..storeKg = 1 << 30
      ..tankL = 1 << 30
      ..barleyKg = 1e8
      ..alfalfaKg = 1e8
      ..waterL = 1e9;
    final w = g.state.world;
    final f = w.festivals.values.firstWhere(
      (f) => f.tier == FestivalTier.grand,
    );
    final r = f.rounds.firstWhere(
      (r) => r.kind == RoundKind.mafareed && r.sex == Sex.female,
    );
    final sim = Sim(g.state);
    final c = WorldGen(sim).makeCamel(
      sim.rng(['money-fest']),
      owner: g.me.id,
      mean: 75,
      category: r.category,
      sex: Sex.female,
      ageDays: AgeClass.mafrood.minDays + 150 - r.day.daysSince(g.today),
    )..acquiredOn = g.today - 200;
    c.genes[Trait.coat] = 80;
    // a late entry (after the closing), so its fee is in the ledger too
    g.advanceTo(f.closesOn + 1);
    expect(g.dispatch(EnterRound(g.me.id, f.id, r.id, [c.id])).ok, isTrue);
    g.advanceTo(r.day);
    final month = Money.monthOf(r.day);
    MoneyLine line(MoneyKind k) => GameView(
      g.state,
      g.me.id,
    ).moneyMonth(month)!.lines.firstWhere((l) => l.kind == k);
    final trip = line(MoneyKind.transport);
    expect((trip.trip, trip.name), (TripReason.festival, f.name));
    final fee = GameView(g.state, g.me.id)
        .moneyMonth(Money.monthOf(f.closesOn + 1))!
        .lines
        .firstWhere((l) => l.kind == MoneyKind.entryFee);
    expect((fee.name, fee.amount), (f.name, -Balance.lateEntryFee));
    // a treatment, and a fine of each reason, each its own month's one row
    final s0 = Sim(g.state);
    g.advanceTo(GameDay.ofDate(DateTime.utc(2027, 2, 2)));
    s0.pay(g.me, const Riyal(-5000), LedgerCategory.tampering, ref: c.id.value);
    expect(line2(g, '2027-02', MoneyKind.tampering).name, c.name);
    g.advanceTo(GameDay.ofDate(DateTime.utc(2027, 3, 2)));
    s0.pay(g.me, const Riyal(-13400), LedgerCategory.fine, ref: c.id.value);
    final out = line2(g, '2027-03', MoneyKind.fine);
    expect((out.fineFor, out.name), (FineReason.outside, c.name));
    g.advanceTo(GameDay.ofDate(DateTime.utc(2027, 4, 2)));
    s0.pay(
      g.me,
      const Riyal(-13400),
      LedgerCategory.fineAtSale,
      ref: c.id.value,
    );
    final sale = line2(g, '2027-04', MoneyKind.fine);
    expect((sale.fineFor, sale.name), (FineReason.sale, c.name));
    final f2 = w.festivals.values.firstWhere((x) => !x.done);
    g.advanceTo(GameDay.ofDate(DateTime.utc(2027, 5, 2)));
    s0.pay(g.me, const Riyal(-30000), LedgerCategory.fine, ref: f2.id.value);
    final fest = line2(g, '2027-05', MoneyKind.fine);
    expect((fest.fineFor, fest.name), (FineReason.festival, f2.name));
    expect(checkInvariants(g.state), isEmpty);
    expectAddsUp(g);
  });

  test('a camel renamed reads the same on the month\'s row and opened', () {
    final g = newGame();
    final me = g.me.id;
    final v0 = GameView(g.state, me);
    final l =
        (v0.market.toList()
              ..sort((a, b) => a.askPrice.value.compareTo(b.askPrice.value)))
            .first;
    expect(g.dispatch(BuyListing(me, l.id)).ok, isTrue);
    g.advanceTo(GameDay.ofDate(DateTime.utc(2026, 11, 3)));
    String rowName() => GameView(
      g.state,
      me,
    ).moneyMonths.firstWhere((m) => m.month == '2026-10').top.name!;
    expect(rowName(), l.camel.name); // (October kept)
    expect(g.dispatch(RenameCamel(me, l.camel.id, 'غزالة')).ok, isTrue);
    expect(rowName(), 'غزالة');
    final opened = GameView(g.state, me).moneyMonth('2026-10')!;
    expect(opened.top.name, 'غزالة');
  });

  test('the ledger never goes back: a row with an earlier day is caught', () {
    final g = newGame();
    g.advanceDays(3);
    expect(g.dispatch(OrderSupply(g.me.id, Supply.alfalfa, 1)).ok, isTrue);
    expect(checkInvariants(g.state), isEmpty);
    g.me.ledger.add(
      LedgerEntry(
        day: g.today - 1,
        category: LedgerCategory.vet,
        amount: const Riyal(-10),
      ),
    );
    g.me.cash = g.me.cash + const Riyal(-10);
    expect(checkInvariants(g.state), contains(startsWith('ledger goes back')));
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
    // the months before this one are read once, not again at every snapshot
    // (counted, not timed: the work itself)
    final read = Money.keptRowsRead;
    for (var i = 0; i < 100; i++) {
      GameView(g.state, g.me.id).moneyMonths;
    }
    expect(Money.keptRowsRead, read, reason: '100 reads, no row read again');
    // a new row this month does not read the past again
    expect(g.dispatch(OrderSupply(g.me.id, Supply.alfalfa, 1)).ok, isTrue);
    GameView(g.state, g.me.id).moneyMonths;
    expect(Money.keptRowsRead, read, reason: 'a row this month');
    // a month that ends reads its own rows only, not the whole ledger
    final rows = g.me.ledger.length;
    g.advanceTo(
      GameDay.ofDate(
        DateTime.utc(g.today.date.year, g.today.date.month + 1, 2),
      ),
    );
    GameView(g.state, g.me.id).moneyMonths;
    expect(
      Money.keptRowsRead - read,
      inInclusiveRange(1, g.me.ledger.length - rows + 60),
    );
    expect(Money.keptRowsRead - read, lessThan(rows ~/ 4));
    expectAddsUp(g);
  });
}

MoneyLine line2(Game g, String month, MoneyKind k) => GameView(
  g.state,
  g.me.id,
).moneyMonth(month)!.lines.firstWhere((l) => l.kind == k);
