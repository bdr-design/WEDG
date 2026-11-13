// Plays a world for many game-years with a scripted player and checks the
// invariants every week. Used by CI:  dart run marah_domain:simulate 10
import 'dart:io';

import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/testing.dart';

void main(List<String> args) {
  final years = args.isEmpty ? 10 : int.parse(args.first);
  final seeds = args.length > 1 ? int.parse(args[1]) : 3;
  var failed = false;
  for (var seed = 1; seed <= seeds; seed++) {
    final game = Game.create(
      seed: seed * 7919,
      playerName: 'bot',
      farmName: 'bot farm',
      region: Region.values[seed % Region.values.length],
      favourite: ColorCategory.values[seed % ColorCategory.values.length],
    );
    // the old start's money (SAR 600,000; a game starts with 20,000 since
    // 13 Nov 2026), so the run grows a herd and enters festivals as before
    grant(game, 580000);
    // an honest bot (one caught is barred six seasons, and the run would
    // stop testing the festivals); the cheating is tested in festival_test
    final bot = Bot(game);
    final watch = Stopwatch()..start();
    String? problem;
    var caught = 0;
    for (var w = 0; w < years * 52 && problem == null; w++) {
      for (final e in bot.week()) {
        if (e is TamperingFound) caught++;
      }
      final p = checkInvariants(game.state);
      if (p.isNotEmpty) problem = 'week $w: ${p.first}';
    }
    watch.stop();
    final me = game.me;
    final herd = game.state.world.aliveOwnedBy(me.id).length;
    final placings = game.state.world.camels.values
        .where((c) => c.ownerId == me.id)
        .expand((c) => c.placings)
        .length;
    stdout.writeln(
      'seed $seed: ${problem ?? 'ok'} | cash ${me.cash.value} | '
      'herd $herd | placings $placings | commands ${bot.commands} '
      '(${bot.refused} refused) | registry ${game.state.world.camels.length} '
      '| entries ${bot.entriesBySeason.values.fold(0, (a, b) => a + b)} in '
      '${bot.entriesBySeason.length} seasons, caught $caught '
      '| ${watch.elapsedMilliseconds} ms',
    );
    if (problem != null) failed = true;
  }
  if (failed) exitCode = 1;
}
