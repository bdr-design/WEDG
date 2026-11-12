import '../catalog/catalog.dart';
import '../commands.dart';
import '../common/ids.dart';
import '../common/money.dart';
import '../common/result.dart';
import '../events.dart';
import '../game.dart';
import '../invariants.dart';
import '../model/camel.dart';
import '../model/player.dart';
import '../rules/provisions.dart';
import '../views/views.dart';

/// A scripted player that uses every feature, for long-run simulations and
/// tests. It plays sensibly, not optimally.
class Bot {
  Bot(this.game);

  final Game game;
  int commands = 0;
  int refused = 0;

  OwnerId get me => game.me.id;
  GameView get view => GameView(game.state, me);

  Result _do(Command c) {
    final r = game.dispatch(c);
    commands++;
    if (!r.ok) refused++;
    return r;
  }

  /// Plays one week: acts, then advances seven days.
  List<DomainEvent> week() {
    act();
    return game.advanceDays(7);
  }

  void act() {
    final v = view;

    for (final c in v.herd) {
      if (c.health == HealthStatus.sick) _do(Treat(me, c.id));
    }

    // Feed and water: topped up to three weeks when under ten days, as far as
    // the store and the tank hold.
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
      final units = want < v.roomFor(s) ? want : v.roomFor(s);
      if (units > 0) _do(OrderSupply(me, s, units));
    }

    final needed = v.shepherdsNeeded;
    if (v.me.farm.shepherds != needed) _do(SetShepherds(me, needed));

    if (v.herd.length >= v.me.farm.capacity - 1 && v.me.cash.value > 250000) {
      _do(ExpandFarm(me));
    }

    // Breeding season: put eligible females to the best affordable stud.
    if (v.breedingSeason) {
      final studs = v.studs.toList()
        ..sort((a, b) => b.bull.quality.compareTo(a.bull.quality));
      for (final f in v.herd.where((c) => c.sex == Sex.female)) {
        if (v.canBreed(f.id) != null) continue;
        final stud = studs
            .where((s) => s.stud.fee.value < view.me.cash.value * 0.05)
            .firstOrNull;
        if (stud != null) _do(MateWithStud(me, f.id, stud.stud.id));
      }
    }

    // Enter every camel that fits an open round.
    for (final f in v.festivals.where((f) => f.registrationOpen(v.today))) {
      for (final c in view.herd) {
        for (final r in f.rounds) {
          if (view.canEnter(f.id, r.id, c.id) == null) {
            _do(EnterRound(me, f.id, r.id, c.id));
            break;
          }
        }
      }
    }

    // Buy a promising young female when rich.
    if (v.me.cash.value > 400000 && v.herd.length < v.me.farm.capacity) {
      final pick =
          v.market
              .where(
                (l) =>
                    l.camel.sex == Sex.female &&
                    l.camel.ageDays < 5 * 365 &&
                    l.askPrice.value < v.me.cash.value * 0.3,
              )
              .toList()
            ..sort((a, b) => b.camel.quality.compareTo(a.camel.quality));
      if (pick.isNotEmpty) {
        final l = pick.first;
        final r = _do(Bargain(me, l.id, (l.askPrice.value * 0.9).round()));
        if (!r.ok) _do(BuyListing(me, l.id));
      }
    }

    // Sell weak or old stock; accept fair offers.
    for (final c in view.herd) {
      final old = c.ageDays > 16 * 365;
      final weak = c.quality < 46 && c.ageDays > 2 * 365;
      if ((old || weak) && view.canSell(c.id) == null) {
        final (lo, hi) = c.estimate;
        _do(ListForSale(me, c.id, ((lo.value + hi.value) / 2).round()));
      }
    }
    for (final l in view.myListings) {
      final (lo, _) = l.camel.estimate;
      for (final o in view.offersOn(l.id)) {
        if (o.amount >= lo) {
          _do(AcceptOffer(me, o.id));
          break;
        }
      }
    }

    // Short of money: sell the least valuable camel to the broker.
    if (view.me.cash < const Riyal(20000) && view.herd.length > 2) {
      final cheapest = view.herd.toList()
        ..sort((a, b) => a.estimate.$1.compareTo(b.estimate.$1));
      for (final c in cheapest) {
        if (view.canSell(c.id) == null) {
          _do(QuickSale(me, c.id));
          break;
        }
      }
    }
  }

  /// Plays [weeks] weeks and returns the first invariant violation, if any.
  String? run(int weeks) {
    for (var i = 0; i < weeks; i++) {
      week();
      final problems = checkInvariants(game.state);
      if (problems.isNotEmpty) return 'week $i: ${problems.first}';
    }
    return null;
  }
}

extension on Riyal {
  int compareTo(Riyal other) => value.compareTo(other.value);
}
