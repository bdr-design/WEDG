import 'model/camel.dart';
import 'model/game_state.dart';

/// Rules that must hold after every command and every day. Tests and the
/// long-run simulation check them; a violation is always a bug.
List<String> checkInvariants(GameState s) {
  final problems = <String>[];
  final w = s.world;

  for (final p in s.players.values) {
    final sum = p.ledger.fold<int>(0, (a, l) => a + l.amount.value);
    if (sum != p.cash.value) {
      problems.add('cash ${p.cash.value} != ledger sum $sum for ${p.id.value}');
    }
    // the merchant's account: never below zero, never more than the money
    // is below zero (it is part of that debt, and clears with it)
    final debt = p.cash.isNegative ? -p.cash.value : 0;
    if (p.onAccount < 0 || p.onAccount > debt) {
      problems.add('account ${p.onAccount} outside 0..$debt for ${p.id.value}');
    }
  }
  for (final l in w.listings.values) {
    final c = w.camels[l.camelId];
    if (c == null || !c.isAlive) {
      problems.add('listing ${l.id.value} for missing or dead camel');
    } else if (c.ownerId != l.sellerId) {
      problems.add('listing ${l.id.value} seller does not own the camel');
    }
  }
  for (final o in w.offers.values) {
    if (!w.listings.containsKey(o.listingId)) {
      problems.add('offer ${o.id.value} on missing listing');
    }
  }
  for (final st in w.studs.values) {
    final c = w.camels[st.camelId];
    if (c == null || !c.isAlive) {
      problems.add('stud ${st.id.value} bull missing or dead');
    }
  }
  for (final f in w.festivals.values) {
    if (f.done) continue;
    for (final r in f.rounds) {
      if (r.judged) continue;
      for (final e in r.entries) {
        for (final id in e.camels) {
          final c = w.camels[id];
          if (c == null || !c.isAlive || c.ownerId != e.ownerId) {
            problems.add('entry ${id.value} in ${r.id.value} is stale');
          }
        }
        if (e.camels.isEmpty) problems.add('empty entry in ${r.id.value}');
      }
    }
  }
  for (final c in w.camels.values) {
    if (c.status == CamelStatus.alive && c.endedOn != null) {
      problems.add('alive camel ${c.id.value} has an end date');
    }
    if (c.condition.isNaN || c.condition < 0 || c.condition > 100) {
      problems.add('camel ${c.id.value} condition out of range');
    }
    if (s.players.containsKey(c.ownerId) &&
        c.isAlive &&
        c.pregnancy != null &&
        c.sex.name != 'female') {
      problems.add('male camel ${c.id.value} is pregnant');
    }
  }
  return problems;
}
