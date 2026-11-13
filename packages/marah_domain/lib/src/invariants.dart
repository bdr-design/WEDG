import 'model/camel.dart';
import 'model/game_state.dart';
import 'views/money.dart';

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
    // the ledger is written in order: a row's day never before the last's,
    // and a month's roll-up row not before an earlier month's rows (the
    // bank reads it so: views/money.dart)
    for (var i = 1; i < p.ledger.length; i++) {
      final a = p.ledger[i - 1], b = p.ledger[i];
      final ka = a.month ?? Money.monthOf(a.day);
      final kb = b.month ?? Money.monthOf(b.day);
      if (b.day < a.day || kb.compareTo(ka) < 0) {
        problems.add('ledger goes back at row $i for ${p.id.value}');
        break;
      }
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
