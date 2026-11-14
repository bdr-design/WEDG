import 'dart:collection';

import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/testing.dart';

import 'commands_json.dart';

/// The scripted bot plays a fixed seed, and every [every] weeks the whole
/// state is written in a canonical form and hashed. bin/same_seed.dart prints
/// these lines on the Dart VM and compiled to JavaScript; CI fails if the two
/// differ, because the prototype's engine must be the app's, day for day.
/// [end] gets the game after the last week.
Iterable<String> sameSeedLines({
  int seed = 7,
  int weeks = 104,
  int every = 4,
  void Function(Game game)? end,
}) sync* {
  final game = Game.create(
    seed: seed,
    playerName: 'اللاعب',
    farmName: 'العزبة',
    region: Region.qassim,
    favourite: ColorCategory.majaheem,
    startedAt: DateTime.utc(2026, 11, 1),
  );
  // the old start's money (SAR 600,000), so the rich farm's paths run too:
  // a bull bought, festivals entered and withdrawn from
  grant(game, 580000);
  final bot = Bot(game);
  var extras = 0;
  final done = SplayTreeMap<String, int>();
  for (var w = 0; ; w++) {
    if (w % every == 0 || w == weeks) {
      yield 'week $w day ${game.today.value} cash ${game.me.cash.value} '
          'commands ${bot.commands} refused ${bot.refused} extras $extras '
          '${stateLine(game.state)}';
    }
    if (w == weeks) {
      yield 'extras ${[for (final e in done.entries) '${e.key} ${e.value}'].join(', ')}';
      end?.call(game);
      return;
    }
    extras += _extras(game, w, done);
    bot.week();
  }
}

/// The commands the bot never sends, so the check runs them too: the feed
/// plan changed, the calves' share of the milk, a camel renamed, a camel listed and its offers declined, then
/// taken off the market, a female put to the farm's own bull, an entry
/// withdrawn, a camel secretly treated. Returns how many went through, and counts them by kind in
/// [done].
int _extras(Game game, int week, Map<String, int> done) {
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
  if (week == 6) send(BuildFacility(me, Facility.pen, now: true));
  if (week == 12) {
    send(SetStandingOrder(me, StandingOrder.water, on: true));
    send(SetStandingOrder(me, StandingOrder.feed, on: true));
    send(SignVetContract(me));
  }
  if (week == 40) send(CancelVetContract(me));
  if (week == 60) send(SetStandingOrder(me, StandingOrder.feed, on: false));
  for (final c in v.herd) {
    if (c.onTheWay) send(RushTruck(me, c.id, hour: week % 24));
  }
  if (game.me.farm.today?.waterShort ?? false) {
    send(OrderSupply(me, Supply.water, 1, tanker: Tanker.small, now: true));
  }
  if (week % 26 == 13) {
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

/// The state's canonical length and hash, the part of a line that a save
/// read back on the other platform must reproduce (bin/read_save.dart).
String stateLine(GameState state) {
  final text = canonicalJson(state.toJson());
  return 'length ${text.length} hash ${textHash(text)}';
}

/// JSON with numbers written the same way on both platforms: each number's
/// shortest text that reads back the same, without a trailing `.0` (the VM
/// writes the double 1.0 as `1.0` and 2e20 as `200000000000000000000.0`,
/// JavaScript without the `.0`; otherwise the two agree, the test checks a
/// spread of values on both). Key order is kept: it is part of the state.
String canonicalJson(Object? v) {
  final b = StringBuffer();
  void write(Object? v) {
    switch (v) {
      case null:
        b.write('null');
      case bool():
        b.write(v);
      case num():
        final t = '$v';
        b.write(t.endsWith('.0') ? t.substring(0, t.length - 2) : t);
      case String():
        b.write('"');
        for (final u in v.codeUnits) {
          if (u == 0x22 || u == 0x5C) {
            b.write(r'\');
            b.writeCharCode(u);
          } else if (u < 0x20) {
            b.write(r'\u');
            b.write(u.toRadixString(16).padLeft(4, '0'));
          } else {
            b.writeCharCode(u);
          }
        }
        b.write('"');
      case List():
        b.write('[');
        for (var i = 0; i < v.length; i++) {
          if (i > 0) b.write(',');
          write(v[i]);
        }
        b.write(']');
      case Map():
        b.write('{');
        var first = true;
        for (final e in v.entries) {
          if (!first) b.write(',');
          first = false;
          write('${e.key}');
          b.write(':');
          write(e.value);
        }
        b.write('}');
      default:
        throw ArgumentError('not JSON: ${v.runtimeType}');
    }
  }

  write(v);
  return b.toString();
}

/// A 30-bit rolling hash of the UTF-16 code units, exact in JavaScript too
/// (every product stays far below 2^53).
int textHash(String s) {
  var h = 0;
  for (final u in s.codeUnits) {
    h = (h * 31 + u) & 0x3FFFFFFF;
  }
  return h;
}
