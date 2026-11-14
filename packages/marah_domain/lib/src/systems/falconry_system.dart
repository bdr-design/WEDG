// The hunting season's day (task T18): a step of the daily pipeline, keyed
// by the player's state (rush_and_calendar.md section 5, the rule N3: a
// played day and a day away run the same code). It does nothing for a
// player who has never touched falcons, and draws nothing then.
part of 'systems.dart';

class FalconrySystem implements DailySystem {
  const FalconrySystem();

  @override
  void run(Sim sim) {
    for (final p in sim.state.players.values) {
      final h = p.falconry;
      if (h == null) continue;
      _deliver(sim, p, h);
      _keep(sim, p, h);
      _trip(sim, p, h);
      _auction(sim, p, h);
      _neglect(sim, p, h);
    }
  }

  /// Each falcon's keep for the day, on one row a month.
  static void _keep(Sim sim, PlayerState p, Falconry h) {
    final n = h.falcons.length + h.held.length;
    if (n == 0) return;
    sim.bill(
      p,
      Riyal(-n * HuntBalance.upkeepPerDay),
      LedgerCategory.falconUpkeep,
    );
  }

  /// The gear on its way arrives, as feed does.
  static void _deliver(Sim sim, PlayerState p, Falconry h) {
    if (h.coming.isEmpty) return;
    for (final d in h.coming.where((d) => d.arrivesOn <= sim.today)) {
      h.gear[d.gear] = h.has(d.gear) + d.units;
      sim.emit(
        GearDelivered(sim.today, owner: p.id, gear: d.gear, units: d.units),
      );
    }
    h.coming.removeWhere((d) => d.arrivesOn <= sim.today);
  }

  /// A night out: a day of the camp's supplies used; a day's outing not
  /// ended by the evening ends with the day (back the same evening).
  static void _trip(Sim sim, PlayerState p, Falconry h) {
    final t = h.trip;
    if (t == null) return;
    if (t.oneDay) {
      endTripNow(sim, p);
      return;
    }
    final left = h.has(Gear.supplies);
    if (left > 0) {
      h.gear[Gear.supplies] = left - 1;
      t.suppliesUsed++;
    }
  }

  /// The trapping auction: the birds entered yesterday sold at the hammer
  /// that night, the price in full with no fee [191][190]; when it has
  /// closed, every bird neither sold nor kept set free (the owner's word on
  /// Q-13/15).
  static void _auction(Sim sim, PlayerState p, Falconry h) {
    if (h.held.isEmpty) return;
    for (final f in [...h.held]) {
      if (!h.entered.contains(f.id)) continue;
      final price = f.value!;
      h
        ..held.remove(f)
        ..entered.remove(f.id);
      sim.pay(p, Riyal(price), LedgerCategory.falconSale, ref: f.id.value);
      sim.emit(
        FalconFate(
          sim.today,
          owner: p.id,
          falcon: f.id.value,
          name: f.name,
          fate: Fate.sold,
          price: price,
        ),
      );
    }
    if (!FalconRoute.trapping.openOn(sim.today)) {
      for (final f in [...h.held]) {
        h.held.remove(f);
        sim.emit(
          FalconFate(
            sim.today,
            owner: p.id,
            falcon: f.id.value,
            name: f.name,
            fate: Fate.freedAtClose,
          ),
        );
      }
    }
  }

  /// Two weeks without الدعو (or a flight), outside the moult: a week back.
  static void _neglect(Sim sim, PlayerState p, Falconry h) {
    if (HuntBalance.moultMonths.contains(sim.today.month)) return;
    for (final f in h.falcons) {
      final c = f.caredOn;
      if (c == null || f.where != FalconWhere.home) continue;
      final gap = sim.today.daysSince(c);
      if (gap > 0 && gap % HuntBalance.stepBackDays == 0) {
        final before = f.dauDays;
        f.dauDays = before > HuntBalance.stepBack
            ? before - HuntBalance.stepBack
            : 0;
        if (before > 0) {
          sim.emit(
            FalconFate(
              sim.today,
              owner: p.id,
              falcon: f.id.value,
              name: f.name,
              fate: Fate.steppedBack,
            ),
          );
        }
      }
    }
  }
}
