// The bank design's data (design/ui/phone_bank.cjs): a new game played forward by the rules engine itself, its
// ledger read at three moments: day one, a month in (milk and feed only), and six and a half months in. Nothing here
// is example content: every row is one the engine wrote (Sim.pay, Sim.bill). Only the player's choices are scripted,
// a careful beginner's (a game choice, for the picture):
//   * feed and water topped up to three weeks when under ten days, as the bot does (packages/marah_domain/lib/src/
//     testing/bot.dart), the 6 t tanker while the start's 6,000 L tank cannot take the 19 t one;
//   * on 20 November, the cheapest young she-camel at الحراج that leaves SAR 5,000 in hand: haggled at 90% once,
//     else bought at the asking price;
//   * on 20 January, her calf (weaned: a year old on 15 January) listed at the top of its estimate, and the first
//     offer at or above the bottom of it accepted (else sold to the broker on 10 February).
// Run from the repository's root (the workspace's packages, no pub get needed once .dart_tool is there):
//   dart --packages=.dart_tool/package_config.json design/ui/phone_bank_data.dart > out.json
// Seed 4242, Qassim, وضح: the prototype's fixed game (`newGame: { seed: 4242 }`, worker_host.dart's defaults).
import 'dart:convert';
import 'dart:io';

import 'package:marah_domain/marah_domain.dart';

void main(List<String> args) {
  final seed = args.isEmpty ? 4242 : int.parse(args.first);
  final game = Game.create(
    seed: seed,
    playerName: 'اللاعب',
    farmName: 'العزبة',
    region: Region.qassim,
    favourite: ColorCategory.wodh,
    startedAt: DateTime.utc(2026, 11, 13),
  );
  final me = game.me.id;
  GameView view() => GameView(game.state, me);
  final out = <String, Object?>{
    'seed': seed,
    'moments': <Map<String, Object?>>[],
  };
  final log = <String>[];

  // the moment as the bank would show it: the balance, today's net (GameView.todayNet, as the home widget has it),
  // and every ledger row, its camel or festival named where it has one
  void take(String key) {
    final v = view();
    final w = game.state.world;
    String? refName(String? ref) {
      if (ref == null) return null;
      for (final c in w.camels.values) {
        if (c.id.value == ref) return c.name;
      }
      for (final f in w.festivals.values) {
        if (f.id.value == ref) return f.name;
      }
      return ref; // (a facility's name)
    }

    (out['moments']! as List).add({
      'key': key,
      'today': v.today.value,
      'date': v.today.date.toIso8601String().substring(0, 10),
      'cash': v.me.cash.value,
      'todayNet': v.todayNet.value,
      'milkIncomeToday': v.milkIncomeToday,
      'milkThisMonth': v.milkThisMonth.value,
      'herd': v.herd.length,
      'ledger': [
        for (final l in v.me.ledger)
          {
            'day': l.day.value,
            'date': l.day.date.toIso8601String().substring(0, 10),
            'cat': l.category.name,
            'amount': l.amount.value,
            'ref': l.ref,
            'refName': refName(l.ref),
            'month': l.month,
          },
      ],
    });
  }

  void topUp() {
    final v = view();
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
      Result? r;
      if (units > 0) {
        r = game.dispatch(OrderSupply(me, s, units));
      } else if (s == Supply.water && v.roomFor(s, tanker: Tanker.small) > 0) {
        r = game.dispatch(OrderSupply(me, s, 1, tanker: Tanker.small));
      }
      if (r != null)
        log.add(
          '${v.today.date} order ${s.name} ${r is Err ? r.error.code.name : 'ok'}',
        );
    }
  }

  CamelId? bought;
  CamelId? calf;
  ListingId? calfListing;

  take('day1');
  final start = game.today;
  final end = GameDay.ofDate(DateTime.utc(2027, 4, 15));
  while (game.today.value < end.value) {
    final v = view();
    final d = v.today.date;
    topUp();
    if (d.month == 11 && d.day == 20) {
      final cash = v.me.cash.value;
      final pick =
          v.market
              .where(
                (l) =>
                    l.camel.sex == Sex.female &&
                    l.camel.ageDays < 6 * 365 &&
                    l.askPrice.value + l.transport.value <= cash - 5000,
              )
              .toList()
            ..sort(
              (a, b) => (a.askPrice.value + a.transport.value).compareTo(
                b.askPrice.value + b.transport.value,
              ),
            );
      if (pick.isNotEmpty) {
        final l = pick.first;
        final r = game.dispatch(
          Bargain(me, l.id, (l.askPrice.value * 0.9 / 500).round() * 500),
        );
        log.add(
          '${d} bargain ${l.camel.name} ask ${l.askPrice.value}: ${r.ok} ${r.events.map((e) => e.runtimeType).join(',')}',
        );
        if (!view().herd.any((c) => c.id == l.camel.id)) {
          final b = game.dispatch(BuyListing(me, l.id));
          log.add('${d} buy ${l.camel.name}: ${b.ok}');
        }
        if (view().herd.any((c) => c.id == l.camel.id)) bought = l.camel.id;
      }
    }
    if (d.month == 1 && d.day == 20) {
      final young = v.herd
          .where((c) => c.ageDays < 400 && c.id != bought)
          .toList();
      if (young.isNotEmpty) {
        final c = young.first;
        calf = c.id;
        final (_, hi) = c.estimate;
        final r = game.dispatch(
          ListForSale(me, c.id, (hi.value / 500).round() * 500),
        );
        log.add('${d} list ${c.name} at ${hi.value}: ${r.ok}');
        calfListing = view().myListings
            .where((l) => l.camel.id == c.id)
            .firstOrNull
            ?.id;
      }
    }
    if (calfListing != null) {
      final l = v.myListings.where((x) => x.id == calfListing).firstOrNull;
      if (l == null) {
        calfListing = null;
      } else {
        final (lo, _) = l.camel.estimate;
        for (final o in v.offersOn(l.id)) {
          if (o.amount >= lo) {
            final r = game.dispatch(AcceptOffer(me, o.id));
            log.add('${d} accept ${o.amount}: ${r.ok}');
            calfListing = null;
            break;
          }
        }
        if (calfListing != null && d.month == 2 && d.day == 10) {
          game.dispatch(CancelListing(me, l.id));
          final r = game.dispatch(QuickSale(me, calf!));
          log.add('${d} quick sale: ${r.ok}');
          calfListing = null;
        }
      }
    }
    game.advanceDays(1);
    final problems = checkInvariants(game.state);
    if (problems.isNotEmpty) throw StateError(problems.first);
    final t = game.today.date;
    if (t.month == 10 && t.day == 27) take('october');
  }
  take('april');
  out['log'] = log;
  out['days'] = game.today.value - start.value;
  stdout.writeln(const JsonEncoder.withIndent(' ').convert(out));
}
