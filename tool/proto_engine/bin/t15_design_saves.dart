// The saves the rush and calendar design draws from (task T15: design/ui/phone_rush.cjs and phone_calendar.cjs),
// each a game on seed 4242 (Qassim, وضح, from 1 October 2026) played forward by the engine itself. Only the player's
// choices are scripted; what the engine does is its own.
//
//   dart run bin/t15_design_saves.dart <folder>        (in tool/proto_engine)
//
// writes into <folder>:
//  - short.json: left alone till the first day the herd went short of water and feed (the start's month of stores
//    run out): الوايت and العلف on a short day, where a rush makes good today's loss;
//  - round.json: نورة entered in مزاين حائل's الفردي جل on the first day (stores filled by the phone's orders), played
//    to her round's day: the round judged at dawn and no stage told (the save is ahead of the real clock, and its
//    minute of the day counts from when it was written: draw within the hour, before 7:00 of the game's day);
//  - sick.json and sick_quote.json: the farm kept by its orders (the tank and the shade filled when down to 3 days)
//    till one of the herd falls ill; the quote is the engine's own Treat on a copy (its price and recovery day), the
//    save is before it.
// The saves' clocks start when they are written (startedAt now), so the page opens each without catching up: the
// world is ahead of the real clock and waits for it.
import 'dart:convert';
import 'dart:io';

import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/marah_domain.dart';

Game start(DateTime now) => Game.create(
  seed: 4242,
  playerName: 'اللاعب',
  farmName: 'العزبة',
  region: Region.qassim,
  favourite: ColorCategory.wodh,
  startedAt: now,
);

/// The orders that fill the tank and the shade (the calendar card's «عبّه»).
void fill(Game g) {
  final me = g.me.id, f = g.me.farm;
  final water = Provisions.fits(f, Supply.water, Balance.waterLoadL);
  final small = Provisions.fits(f, Supply.water, Balance.smallWaterLoadL);
  if (water > 0) {
    g.dispatch(OrderSupply(me, Supply.water, water));
  } else if (small > 0) {
    g.dispatch(OrderSupply(me, Supply.water, small, tanker: Tanker.small));
  }
  final bags = Provisions.fits(f, Supply.barley, Balance.barleyBagKg);
  if (bags > 1) g.dispatch(OrderSupply(me, Supply.barley, bags * 3 ~/ 10));
  final bales = Provisions.fits(f, Supply.alfalfa, Balance.alfalfaBaleKg);
  if (bales > 0) g.dispatch(OrderSupply(me, Supply.alfalfa, bales));
}

void write(Directory out, String name, Game g, DateTime now) {
  g.state.lastSeenUtcMs = now.millisecondsSinceEpoch;
  File('${out.path}/$name')
      .writeAsStringSync(const SaveCodec().encode(g.state));
}

void main(List<String> args) {
  final out = Directory(args.first)..createSync(recursive: true);
  final now = DateTime.now().toUtc();

  // ---- short: left alone till a day goes short of water and of feed
  {
    final g = start(now);
    var days = 0;
    while (!(g.me.farm.short.contains(Supply.water) &&
            g.me.farm.short.length >= 2) &&
        days < 120) {
      g.advanceDays(1);
      days++;
    }
    write(out, 'short.json', g, now);
    stdout.writeln(
      'short: ${g.today.date.toIso8601String().substring(0, 10)} after $days days, short ${g.me.farm.short}, '
      'dry days ${g.me.farm.dryDays}, cash ${g.me.cash.value}',
    );
  }

  // ---- round: نورة entered in مزاين حائل's الفردي جل, played to the round's day
  {
    final g = start(now);
    final me = g.me.id;
    final f = g.state.world.festivals.values.firstWhere(
      (x) => x.name == 'مزاين حائل',
    );
    final noura = g.state.world
        .aliveOwnedBy(me)
        .firstWhere((c) => c.sex == Sex.female);
    final r = f.rounds.firstWhere(
      (x) =>
          x.kind == RoundKind.fardiJil &&
          x.category == noura.category &&
          x.sex == Sex.female,
    );
    final entered = g.dispatch(EnterRound(me, f.id, r.id, [noura.id]));
    fill(g);
    g.advanceTo(r.day);
    write(out, 'round.json', g, now);
    stdout.writeln(
      'round: entered ${entered.ok}, ${f.name} ${r.kind.name}, day ${r.day.date.toIso8601String().substring(0, 10)}, '
      'judged ${r.judged}, told ${r.told}, today ${g.today.date.toIso8601String().substring(0, 10)}',
    );
  }

  // ---- sick: kept by its orders till one of the herd falls ill; the vet's quote on a copy
  {
    final g = start(now);
    final me = g.me.id;
    FellSick? sick;
    for (var d = 0; d < 400 && sick == null; d++) {
      for (final e in g.advanceDays(1)) {
        if (e is FellSick && e.owner == me) sick = e;
      }
      final f = g.me.farm;
      final n = Provisions.needs(
        g.state.world.aliveOwnedBy(me),
        f.feedPlan,
        g.today,
      );
      bool low(double have, double need) =>
          need > 0 && have / need <= Balance.lowStockDays;
      if (f.deliveries.isEmpty &&
          (low(f.barleyKg, n.barley) ||
              low(f.alfalfaKg, n.alfalfa) ||
              low(f.waterL, n.water))) {
        fill(g);
      }
    }
    write(out, 'sick.json', g, now);
    final copy = Game(
      (const SaveCodec().decode(
        const SaveCodec().encode(g.state),
      ) as Loaded).state,
    );
    final r = copy.dispatch(Treat(me, sick!.camel!));
    final t = r.events.whereType<Treated>().first;
    final c = copy.state.world.camels[sick.camel!]!;
    final quote = {
      'camel': sick.camel!.value,
      'name': sick.name,
      'illness': sick.illness.name,
      'illnessName': sick.illness.label,
      'sickSince': sick.day.value,
      'cost': t.cost,
      'recoversOn': c.recoversOn!.value,
      'recoverDays': sick.illness.recoverDays,
      'today': g.today.value,
    };
    File('${out.path}/sick_quote.json').writeAsStringSync(jsonEncode(quote));
    stdout.writeln(
      'sick: ${g.today.date.toIso8601String().substring(0, 10)} ${jsonEncode(quote)}',
    );
  }
}
