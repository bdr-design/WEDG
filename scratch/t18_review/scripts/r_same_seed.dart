// ignore_for_file: avoid_print, unused_import
// Reviewer's T18 baseline driver: the base's same-seed bot and extras (copied
// verbatim from tool/proto_engine/lib/same_seed.dart at b079dce, so phase 2
// drives the worker's engine with the BASE's script), seeds 7, 11, 4242, every
// week for a year (weeks 0..52). Each line: raw state hash and a "strip" hash
// with the keys in [strip] removed (the worker's new falcon keys, phase 2).
// Then the save's size after the year. Copy into <checkout>/tool/proto_engine/bin/.
import 'dart:collection';
import 'dart:convert';

import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/testing.dart';
import 'package:marah_proto_engine/commands_json.dart';
import 'package:marah_proto_engine/same_seed.dart';

const strip = <String>{
  // phase 2: the worker's new keys go here
};

Object? _strip(Object? v) {
  if (v is Map) {
    return {
      for (final e in v.entries)
        if (!strip.contains('${e.key}')) '${e.key}': _strip(e.value),
    };
  }
  if (v is List) return [for (final x in v) _strip(x)];
  return v;
}

String h(Object? j) {
  final t = canonicalJson(j);
  return '${t.length} ${textHash(t)}';
}

void main() {
  for (final seed in const [7, 11, 4242]) {
    final game = Game.create(
      seed: seed,
      playerName: 'اللاعب',
      farmName: 'العزبة',
      region: Region.qassim,
      favourite: ColorCategory.majaheem,
      startedAt: DateTime.utc(2026, 11, 1),
    );
    grant(game, 580000);
    final bot = Bot(game);
    var extras = 0;
    final done = SplayTreeMap<String, int>();
    for (var w = 0; w <= 52; w++) {
      final j = game.state.toJson();
      print('seed $seed week $w day ${game.today.value} cash '
          '${game.me.cash.value} cmd ${bot.commands} ref ${bot.refused} '
          'ext $extras raw ${h(j)} strip ${h(_strip(j))}');
      if (w == 52) break;
      extras += _extras(game, w, done);
      bot.week();
    }
    print('seed $seed extras ${[for (final e in done.entries) '${e.key} ${e.value}'].join(', ')}');
    final save = const SaveCodec().encode(game.state, savedAt: DateTime.utc(2026, 11, 1));
    print('seed $seed save-bytes ${utf8.encode(save).length}');
  }
}

/// The commands the bot never sends, so the check runs them too: the feed
/// plan changed, the calves' share of the milk, a camel renamed, a camel listed and its offers declined, then
/// taken off the market, a female put to the farm's own bull, an entry
/// withdrawn, a camel secretly treated. Returns how many went through, and counts them by kind in
/// [done].
int _extras(Game game, int week, Map<String, int> done, {bool rush = true}) {
  final me = game.me.id;
  var ok = 0;
  void send(Command c) {
    if (!game.dispatch(c).ok) return;
    ok++;
    final kind = commandToJson(c)['type']! as String;
    done[kind] = (done[kind] ?? 0) + 1;
  }

  // a round's day the bot's last week ended on, told hour by hour (as the
  // engine does by the clock), and the treatment man's messages read and the
  // findings told, as the phone does
  if (game.nextTelling != null) {
    for (final m in Balance.stageMinutes) {
      if (game.tellTo(m).isNotEmpty || m == Balance.stageMinutes.last) {
        done['tellTo'] = (done['tellTo'] ?? 0) + 1;
      }
    }
  }
  if (week % 3 == 0 && game.me.dealer.any((m) => !m.read)) {
    send(ReadMessages(me));
  }
  if (game.me.untold.isNotEmpty) send(MarkFindingsTold(me, 1));
  var v = GameView(game.state, me);
  if (week % 8 == 0) {
    send(
      SetFeedPlan(me, week % 16 == 0 ? FeedPlan.premium : FeedPlan.standard),
    );
  }
  // the calves' share of the milk, each of the three in turn
  if (week % 6 == 3) {
    send(SetCalfShare(me, CalfShare.values[(week ~/ 6) % 3]));
  }
  if (week % 4 == 1 && v.herd.isNotEmpty) {
    send(RenameCamel(me, v.herd.first.id, 'ناقة $week'));
  }
  // one camel on the market for four weeks at its dearer estimate: offers come,
  // and every one is declined, then it is taken off
  if (week % 8 == 0) {
    for (final c in v.herd) {
      if (v.canSell(c.id) == null && v.listingOf(c.id) == null) {
        send(ListForSale(me, c.id, c.estimate.$2.value));
        break;
      }
    }
  } else if (week % 8 == 4) {
    for (final l in v.myListings) {
      send(CancelListing(me, l.id));
    }
  }
  v = GameView(game.state, me);
  for (final l in v.myListings) {
    for (final o in v.offersOn(l.id)) {
      send(DeclineOffer(me, o.id));
    }
  }
  // the farm's own bull: bought grown when there is none, then used
  if (v.breedingSeason) {
    bool serves(CamelView c) => c.sex == Sex.male && v.canServe(c.id) == null;
    if (!v.herd.any(serves) && v.me.cash.value > 100000) {
      final bulls =
          v.market
              .where(
                (l) =>
                    l.camel.sex == Sex.male &&
                    l.camel.ageDays > 6 * 365 &&
                    l.askPrice.value < v.me.cash.value * 0.4,
              )
              .toList()
            ..sort((a, b) => a.askPrice.value.compareTo(b.askPrice.value));
      if (bulls.isNotEmpty) send(BuyListing(me, bulls.first.id));
      v = GameView(game.state, me);
    }
    final bull = v.herd.where(serves).firstOrNull;
    if (bull != null) {
      for (final f in v.herd.where((c) => c.sex == Sex.female)) {
        if (v.canBreed(f.id) == null) {
          send(MateWithOwnBull(me, f.id, bull.id));
          break;
        }
      }
    }
  }
  // secret treatments after the run's last festival (Tabuk's, June 2028),
  // so the bot's festivals are not cut short by a ban, while the treatment,
  // its wearing off and a catch outside the festivals run on both platforms
  if (week >= 86 && week % 4 == 2 && v.herd.isNotEmpty) {
    send(Tamper(me, v.herd.last.id, TamperKind.values[week % 7], 1 + week % 3));
  }
  // the rush and being away (T15), so their paths run on both platforms: a
  // pen built now, a camel rushed home, the standing orders and the vet's
  // contract switched on and off, a short day's tanker, and a week away
  if (rush && week == 6) send(BuildFacility(me, Facility.pen, now: true));
  if (rush && week == 12) {
    send(SetStandingOrder(me, StandingOrder.water, on: true));
    send(SetStandingOrder(me, StandingOrder.feed, on: true));
    send(SignVetContract(me));
  }
  if (rush && week == 40) send(CancelVetContract(me));
  if (rush && week == 60) {
    send(SetStandingOrder(me, StandingOrder.feed, on: false));
  }
  for (final c in v.herd) {
    if (rush && c.onTheWay) send(RushTruck(me, c.id, hour: week % 24));
  }
  if (rush && (game.me.farm.today?.waterShort ?? false)) {
    send(OrderSupply(me, Supply.water, 1, tanker: Tanker.small, now: true));
  }
  if (rush && week == 101) {
    final run = AwayRun(game, AwayPlan(game.today + 7));
    while (!run.done) {
      run.step();
    }
    done['away'] = (done['away'] ?? 0) + 1;
  }
  if (week % 5 == 2) {
    for (final f in v.festivals.where((f) => f.registrationOpen(v.today))) {
      for (final r in f.rounds) {
        final mine = r.myEntries;
        if (mine.isNotEmpty) {
          send(WithdrawEntry(me, f.id, r.id, mine.first.camelId));
          return ok;
        }
      }
    }
  }
  return ok;
}

