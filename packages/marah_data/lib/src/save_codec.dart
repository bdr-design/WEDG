import 'dart:convert';

import 'package:marah_domain/marah_domain.dart';

/// Save file format:
///
/// ```json
/// {"format": "marah-save", "version": 1, "savedAt": "...", "data": {...}}
/// ```
///
/// [data] is the game state at [version]. Older saves are upgraded step by
/// step through [migrations] before decoding. A save from a newer app, or
/// one that fails to decode, is reported, never silently replaced.
class SaveCodec {
  const SaveCodec();

  static const format = 'marah-save';

  /// The version this build writes. Bump it with every change to the shape
  /// of the state, and add the step from the previous version to
  /// [migrations] in the same change.
  static const currentVersion = 2;

  /// `migrations[n]` upgrades data from version n to n + 1. Each step works
  /// on plain JSON so it never depends on today's classes.
  static final Map<int, Map<String, Object?> Function(Map<String, Object?>)>
  migrations = {1: _v1ToV2};

  /// v1 to v2 (the owner's decisions of 12 Nov 2026):
  /// - the colour family مغاتير is gone (it is only the umbrella name of the
  ///   light colours): its pure-white camels, rounds and a player's favourite
  ///   become وضح;
  /// - the age classes حق and لقي swap places (حق is now 2 to 3 years, لقي 3
  ///   to 4), so a round or an event for the old 2-to-3 class keeps its ages
  ///   under its new name; the open-ended "mature" (8 years and up) becomes
  ///   فاطر.
  static Map<String, Object?> _v1ToV2(Map<String, Object?> data) {
    const ages = {'laqi': 'haq', 'haq': 'laqi', 'mature': 'fater'};
    Object? walk(Object? v) => switch (v) {
      final Map<String, Object?> m => {
        for (final MapEntry(:key, :value) in m.entries)
          key: switch ((key, value)) {
            ('cat' || 'favourite', 'maghateer') => 'wodh',
            ('age', final String a) => ages[a] ?? a,
            _ => walk(value),
          },
      },
      final List<Object?> l => [for (final x in l) walk(x)],
      _ => v,
    };
    return walk(data)! as Map<String, Object?>;
  }

  String encode(GameState state, {DateTime? savedAt}) => jsonEncode({
    'format': format,
    'version': currentVersion,
    'savedAt': (savedAt ?? DateTime.now()).toUtc().toIso8601String(),
    'data': state.toJson(),
  });

  LoadResult decode(String raw) {
    final Object? json;
    try {
      json = jsonDecode(raw);
    } on FormatException catch (e) {
      return LoadFailed(LoadProblem.corrupt, e.message);
    }
    if (json is! Map<String, Object?> || json['format'] != format) {
      return const LoadFailed(LoadProblem.notASave, 'missing format marker');
    }
    final version = json['version'];
    if (version is! int || version < 1) {
      return const LoadFailed(LoadProblem.corrupt, 'bad version');
    }
    if (version > currentVersion) {
      return LoadFailed(
        LoadProblem.tooNew,
        'save version $version, app supports $currentVersion',
      );
    }
    final payload = json['data'];
    if (payload is! Map<String, Object?>) {
      return const LoadFailed(LoadProblem.corrupt, 'missing data');
    }
    var data = payload;
    for (var v = version; v < currentVersion; v++) {
      final step = migrations[v];
      if (step == null) {
        return LoadFailed(LoadProblem.noMigration, 'no step from $v');
      }
      data = step(data);
    }
    try {
      return Loaded(GameState.fromJson(data), migratedFrom: version);
    } on Object catch (e) {
      // Any shape error in the data: keep the raw save, report it.
      return LoadFailed(LoadProblem.corrupt, e.toString());
    }
  }
}

enum LoadProblem {
  corrupt,
  notASave,
  tooNew,
  noMigration,

  /// The save is fine but this version of the game failed to resume it (a
  /// bug). Nothing was changed or locked; an update can fix it.
  engineError,
}

sealed class LoadResult {
  const LoadResult();
}

final class Loaded extends LoadResult {
  const Loaded(this.state, {required this.migratedFrom});
  final GameState state;

  /// The version the save was written in (equal to current if no upgrade).
  final int migratedFrom;
}

final class LoadFailed extends LoadResult {
  const LoadFailed(this.problem, this.detail);
  final LoadProblem problem;
  final String detail;
}
