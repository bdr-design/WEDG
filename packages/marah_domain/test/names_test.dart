// Whatever has a name the player names, and renames (the owner's word of 18
// Nov): his farm, himself, his camels, his falcons; one rule for every name.
import 'package:marah_domain/marah_domain.dart';
import 'package:test/test.dart';

import 'falcon_phone_view_test.dart' show gameOn, d, netBird;

void main() {
  test('the farm and the player: renamed, trimmed, told', () {
    final g = gameOn(d(2026, 10, 1));
    final r = g.dispatch(RenameFarm(g.me.id, '  عزبة الرفيعة  '));
    expect(r.ok, isTrue);
    expect(g.me.farm.name, 'عزبة الرفيعة');
    expect(r.events.whereType<FarmRenamed>().single.to, 'عزبة الرفيعة');
    expect(g.dispatch(RenamePlayer(g.me.id, 'أبو فهد')).ok, isTrue);
    expect(g.me.name, 'أبو فهد');
  });

  test('a falcon: renamed; one not his is not found', () {
    final g = gameOn(d(2026, 10, 1));
    final f = netBird(g)..keep = true;
    g.me.hunt.held.remove(f);
    g.me.hunt.falcons.add(f);
    expect(g.dispatch(RenameFalcon(g.me.id, f.id, 'غيث')).ok, isTrue);
    expect(f.name, 'غيث');
    final no = g.dispatch(RenameFalcon(g.me.id, const FalconId('nope'), 'x'));
    expect(no.ok, isFalse);
  });

  test('one rule for every name: empty, blanks or over 24 refused; repeats '
      'allowed', () {
    final g = gameOn(d(2026, 10, 1));
    for (final bad in ['', '   ', 'ا' * 25]) {
      final r = g.dispatch(RenameFarm(g.me.id, bad));
      expect((r as Err).error.code, ErrorCode.invalidName, reason: bad);
    }
    expect(g.dispatch(RenameFarm(g.me.id, 'ا' * 24)).ok, isTrue);
    final camels = g.state.world.camels.values
        .where((c) => c.ownerId == g.me.id)
        .toList();
    for (final c in camels) {
      expect(g.dispatch(RenameCamel(g.me.id, c.id, 'وضحى')).ok, isTrue);
    }
  });
}
