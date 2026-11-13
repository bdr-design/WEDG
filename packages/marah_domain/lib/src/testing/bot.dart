import '../catalog/catalog.dart';
import '../commands.dart';
import '../common/ids.dart';
import '../common/money.dart';
import '../common/result.dart';
import '../events.dart';
import '../game.dart';
import '../invariants.dart';
import '../model/camel.dart';
import '../model/contest.dart';
import '../model/player.dart';
import '../model/tampering.dart';
import '../rules/provisions.dart';
import '../sim.dart';
import '../views/views.dart';

/// Gives the player [amount] more money, recorded in the ledger as the
/// opening balance is (the invariants hold): for checks that need a rich
/// farm's paths (a bull bought, festivals entered) now that a game starts
/// with SAR 20,000.
void grant(Game game, int amount) =>
    Sim(game.state).pay(game.me, Riyal(amount), LedgerCategory.opening);

/// A scripted player that uses every feature, for long-run simulations and
/// tests. It plays sensibly, not optimally.
class Bot {
  Bot(this.game, {this.cheats = false});

  final Game game;

  /// Treats its فردي camel now and then (GDD 7.1). Off by default: a bot
  /// caught is barred six seasons, and the long runs would stop testing the
  /// festivals (the review of e2775ff).
  final bool cheats;
  int commands = 0;
  int refused = 0;

  OwnerId get me => game.me.id;
  GameView get view => GameView(game.state, me);

  /// Its festival entries, by season (the year the season's autumn is in).
  final Map<int, int> entriesBySeason = {};

  Result _do(Command c) {
    final r = game.dispatch(c);
    commands++;
    if (!r.ok) refused++;
    for (final e in r.events.whereType<Entered>()) {
      final d = e.day.date;
      final season = d.month >= 9 ? d.year : d.year - 1;
      entriesBySeason[season] = (entriesBySeason[season] ?? 0) + 1;
    }
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
      if (units > 0) {
        _do(OrderSupply(me, s, units));
      } else if (s == Supply.water && v.roomFor(s, tanker: Tanker.small) > 0) {
        // a tank the 19 t tanker does not fit: the 6 t one
        _do(OrderSupply(me, s, 1, tanker: Tanker.small));
      }
    }

    // the farm grows with the herd: the bigger tank and the feed store,
    // the caravan before the first shepherd, and pens when it is nearly full
    final farm = v.me.farm;
    void build(Facility f, {required bool when}) {
      if (when && v.cannotBuild(f) == null && v.me.cash.value > f.price * 2) {
        _do(BuildFacility(me, f));
      }
    }

    build(Facility.tank, when: v.herd.length >= 5);
    build(Facility.store, when: v.herd.length >= 8);
    final needed = v.shepherdsNeeded;
    build(Facility.caravan, when: needed > 0);
    if (farm.shepherds != needed &&
        (needed == 0 || farm.has(Facility.caravan) > 0)) {
      _do(SetShepherds(me, needed));
    }
    build(Facility.pen, when: v.herd.length >= farm.capacity - 1);

    // Breeding season: put eligible females to the best affordable stud.
    if (v.breedingSeason) {
      final studs = v.studs.toList()
        ..sort((a, b) => b.bull.quality.compareTo(a.bull.quality));
      for (final f in v.herd.where((c) => c.sex == Sex.female)) {
        if (v.canBreed(f.id) != null) continue;
        // (a quarter of the money at most, the trucking counted: since
        // 13 Nov 2026 the game starts with SAR 20,000, not 600,000)
        final stud = studs
            .where(
              (s) =>
                  s.stud.fee.value + s.transport.value <
                  view.me.cash.value * 0.25,
            )
            .firstOrNull;
        if (stud != null) _do(MateWithStud(me, f.id, stud.stud.id));
      }
    }

    // Enter camels that fit open rounds (its one فردي camel among them),
    // when the trucking to the festivals is affordable; a bull with his
    // offspring in الفحل وإنتاجه. A cheating bot ([cheats]) now and then has
    // its فردي camel secretly treated first (GDD 7.1).
    final festivals = v.me.cash.value > 15000
        ? v.festivals.where((f) => f.registrationOpen(v.today))
        : const <FestivalView>[];
    for (final f in festivals) {
      // (the better camels only: the preliminary judging cuts half the
      // field, and the trucking is paid either way)
      for (final c in view.herd.where((c) => c.quality >= 60)) {
        for (final r in f.rounds) {
          if (!r.kind.single) continue;
          if (view.canEnter(f.id, r.id, [c.id]) != null) continue;
          if (r.kind.roundClass == RoundClass.fardi &&
              cheats &&
              commands % 4 == 0 &&
              view.canTamper(c.id, TamperKind.dye, 1) == null) {
            _do(Tamper(me, c.id, TamperKind.dye, 1));
          }
          _do(EnterRound(me, f.id, r.id, [c.id]));
          break;
        }
      }
      final fahal = f.rounds.where((r) => r.kind == RoundKind.fahal);
      for (final r in fahal) {
        for (final bull in view.herd.where((c) => c.sex == Sex.male)) {
          final kids = [
            for (final c in view.herd)
              if (c.sire?.id == bull.id) c.id,
          ];
          if (kids.length < r.size - 1) continue;
          final group = [bull.id, ...kids.take(r.size - 1)];
          if (view.canEnter(f.id, r.id, group) == null) {
            _do(EnterRound(me, f.id, r.id, group));
            break;
          }
        }
      }
    }

    // Buy a promising young female when rich (the long runs' farm, given the
    // old start's money).
    if (v.me.cash.value > 400000 && v.herd.length < v.me.farm.capacity) {
      final pick =
          v.market
              .where(
                (l) =>
                    l.camel.sex == Sex.female &&
                    l.camel.ageDays < 5 * 365 &&
                    l.askPrice.value + l.transport.value <
                        v.me.cash.value * 0.3,
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
    if (view.me.cash < const Riyal(3000) && view.herd.length > 2) {
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
