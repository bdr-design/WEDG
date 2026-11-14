// An old game is unchanged (the review of task T15's part B): the session branch's own scripted game (bin/same_seed's
// two years, before the rush and the calendar existed), played on this build without the new paths, must give the
// lines the session branch gave at 7b5b481 (test/data/same_seed_7b5b.txt), week for week, the whole state hashed:
//  - exactly, with the vet's price keyed by the day as it was (runWithVetKeyedByDay, a zone no running game enters) and the farm's day record
//    (new: every day writes it) left out of the hash;
//  - and on the build as it is, identical to week 28; from week 32 the money differs, by the one change an old game
//    shows: the vet's price is keyed by the illness's first day, not by the day she is treated (the second review's
//    N5, so a player cannot wait for a cheaper day). The scripted farm treats some camels days after they fell ill,
//    and those treatments cost what the vet asked on the first day.
@TestOn('vm')
library;

import 'dart:io';

import 'package:marah_domain/testing.dart';
import 'package:marah_proto_engine/same_seed.dart';
import 'package:test/test.dart';

void main() {
  final stored = File('test/data/same_seed_7b5b.txt')
      .readAsLinesSync()
      .where((l) => l.isNotEmpty)
      .toList();

  test('the old game, with the vet keyed by the day as before: identical', () {
    final lines = runWithVetKeyedByDay(
      () => sameSeedLines(rush: false, legacyState: true).toList(),
    );
    expect(lines, stored);
  });

  test(
    'the old game on the build: identical to week 28, then the vet\'s price',
    () {
      final lines = sameSeedLines(rush: false, legacyState: true).toList();
      final first = [
        for (var i = 0; i < stored.length; i++)
          if (lines[i] != stored[i]) i,
      ].first;
      expect(stored[first], startsWith('week 32 '));
      // the same day, commands and refusals; the money and so the state differ
      final a = stored[first].split(' '), b = lines[first].split(' ');
      expect(b.sublist(0, 4), a.sublist(0, 4));
      expect(b[5], isNot(a[5]));
      expect(b.sublist(6, 12), a.sublist(6, 12));
    },
  );
}
