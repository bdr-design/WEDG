import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/testing.dart';

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
  final bot = Bot(game);
  for (var w = 0; ; w++) {
    if (w % every == 0 || w == weeks) {
      yield 'week $w day ${game.today.value} cash ${game.me.cash.value} '
          'commands ${bot.commands} refused ${bot.refused} '
          '${stateLine(game.state)}';
    }
    if (w == weeks) {
      end?.call(game);
      return;
    }
    bot.week();
  }
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
