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
  static const currentVersion = 5;

  /// `migrations[n]` upgrades data from version n to n + 1. Each step works
  /// on plain JSON so it never depends on today's classes.
  static final Map<int, Map<String, Object?> Function(Map<String, Object?>)>
  migrations = {1: _v1ToV2, 2: _v2ToV3, 3: _v3ToV4, 4: _v4ToV5};

  /// v1 to v2 (the owner's decisions of 12 Nov 2026):
  /// - the colour family مغاتير is gone (it is only the umbrella name of the
  ///   light colours): its pure-white camels, rounds and a player's favourite
  ///   become وضح. A round not yet judged that would now duplicate a وضح round
  ///   of the same sex and age is merged into it (its entries moved over and
  ///   every reference to it pointed at the وضح one), or the festival would
  ///   pay the وضح prizes twice; judged rounds stay as they were run, and so
  ///   do two whose entries together would give an owner more than 3;
  /// - a calf marked crossbred whose parents are now both وضح is not;
  /// - the age classes حق and لقي swap places (حق is now 2 to 3 years, لقي 3
  ///   to 4), so a round or an event for the old 2-to-3 class keeps its ages
  ///   under its new name; the open-ended "mature" (8 years and up) becomes
  ///   فاطر, and a death recorded as "mature" takes the class of the camel's
  ///   age that day (فاطر to 10 years, ناب or عود to 20, هرش past that), as
  ///   does one recorded as حوار at 6 to 12 months (مخلول).
  static Map<String, Object?> _v1ToV2(Map<String, Object?> input) {
    // worked on a copy: the caller's JSON is left as it was
    final data = jsonDecode(jsonEncode(input)) as Map<String, Object?>;
    final world = data['world'] as Map<String, Object?>?;
    final rename = <String, String>{};
    for (final f in (world?['festivals'] as List<Object?>?) ?? const []) {
      final rounds = (f! as Map<String, Object?>)['rounds']! as List<Object?>;
      for (final r in [...rounds]) {
        final m = r! as Map<String, Object?>;
        if (m['cat'] != 'maghateer' || m['results'] != null) continue;
        final twin = rounds.cast<Map<String, Object?>>().where(
          (t) =>
              t['cat'] == 'wodh' &&
              t['sex'] == m['sex'] &&
              t['age'] == m['age'] &&
              t['results'] == null,
        );
        if (twin.isEmpty) continue;
        final into = twin.first;
        final have = {
          for (final e in into['entries']! as List<Object?>)
            (e! as Map<String, Object?>)['camel'],
        };
        final merged = [
          ...into['entries']! as List<Object?>,
          for (final e in m['entries']! as List<Object?>)
            if (!have.contains((e! as Map<String, Object?>)['camel'])) e,
        ];
        // not if an owner would then have more camels in the round than v2
        // allows (3, Balance.maxEntriesPerOwnerInRound): the two stay apart
        // rather than an entry be dropped
        final perOwner = <Object?, int>{};
        for (final e in merged) {
          final o = (e! as Map<String, Object?>)['owner'];
          perOwner[o] = (perOwner[o] ?? 0) + 1;
        }
        if (perOwner.values.any((n) => n > 3)) continue;
        into['entries'] = merged;
        rename[m['id']! as String] = into['id']! as String;
        rounds.remove(m);
      }
    }
    final camels = <Object?, Map<String, Object?>>{
      for (final c in (world?['camels'] as List<Object?>?) ?? const <Object?>[])
        if (c case final Map<String, Object?> m) m['id']: m,
    };
    final born = <Object?, int>{
      for (final MapEntry(:key, :value) in camels.entries)
        if (value['born'] case final int b) key: b,
    };
    // crossbred is the sire's family differing from the dam's, or the dam
    // crossbred herself (systems.dart); with مغاتير now وضح, worked out again
    // from the parents' families recorded at birth
    String? fam(Object? ref) {
      final cat = (ref as Map<String, Object?>?)?['cat'];
      return cat == 'maghateer' ? 'wodh' : cat as String?;
    }

    final crossed = <Object?, bool>{};
    bool crossbred(Map<String, Object?> c, [int depth = 0]) {
      final id = c['id'];
      if (crossed[id] case final known?) return known;
      var v = c['crossbred'] == true;
      final dam = c['dam'] as Map<String, Object?>?;
      if (v && c['sire'] != null && dam != null && depth < 64) {
        final mother = camels[dam['id']];
        v =
            fam(c['sire']) != fam(dam) ||
            (mother == null ? true : crossbred(mother, depth + 1));
      }
      return crossed[id] = v;
    }

    final notCrossed = {
      for (final c in camels.values)
        if (c['crossbred'] == true && !crossbred(c)) c['id'],
    };
    const ages = {'laqi': 'haq', 'haq': 'laqi', 'mature': 'fater'};
    String oldAge(Map<String, Object?> m, String a) {
      final b = born[m['camel']], day = m['day'];
      if ((a != 'mature' && a != 'hwar') ||
          m['type'] != 'died' ||
          b == null ||
          day is! int) {
        return ages[a] ?? a;
      }
      final days = day - b;
      if (a == 'hwar') return days >= 183 ? 'makhlool' : 'hwar';
      final years = days ~/ 365;
      return years >= 20 ? 'harish' : (years >= 10 ? 'naab' : 'fater');
    }

    Object? walk(Object? v) => switch (v) {
      final Map<String, Object?> m => {
        for (final MapEntry(:key, :value) in m.entries)
          key: switch ((key, value)) {
            ('cat' || 'favourite', 'maghateer') => 'wodh',
            ('age', final String a) => oldAge(m, a),
            ('crossbred', true) when notCrossed.contains(m['id']) => false,
            (_, final String id) when rename.containsKey(id) => rename[id],
            _ => walk(value),
          },
      },
      final List<Object?> l => [for (final x in l) walk(x)],
      final String id when rename.containsKey(id) => rename[id],
      _ => v,
    };
    return walk(data)! as Map<String, Object?>;
  }

  /// v2 to v3 (the judging weights the owner approved, 12 Nov 2026): the
  /// legs feature is judged as two, the forehand and the hindquarters. Every
  /// camel's breeding values and environment, and a pregnancy's sire values,
  /// stored as lists in feature order, get the hindquarters straight after
  /// the forehand with the legs' value for both; a round's marks by feature
  /// name do the same.
  static Map<String, Object?> _v2ToV3(Map<String, Object?> data) {
    Object? walk(Object? v) => switch (v) {
      final Map<String, Object?> m => {
        for (final MapEntry(:key, :value) in m.entries)
          ...switch ((key, value)) {
            ('genes' || 'env' || 'sireGenes', final List<Object?> l)
                when l.length == 10 =>
              {
                key: [...l.take(8), l[7], ...l.skip(8)],
              },
            ('marks', final Map<String, Object?> marks) => {
              key: {
                for (final MapEntry(:key, :value) in marks.entries)
                  ...key == 'legs'
                      ? {'fore': value, 'hind': value}
                      : {key: value},
              },
            },
            _ => {key: walk(value)},
          },
      },
      final List<Object?> l => [for (final x in l) walk(x)],
      _ => v,
    };
    return walk(data)! as Map<String, Object?>;
  }

  /// v3 to v4: brucellosis is left out until the vet's tests come (plan G5;
  /// modelled as an ordinary illness it was cured, never spread and caused no
  /// abortion). A camel down with it is well again, and its illness's events
  /// (fell sick, treated) are dropped.
  static Map<String, Object?> _v3ToV4(Map<String, Object?> data) {
    Object? walk(Object? v) => switch (v) {
      final Map<String, Object?> m when m['illness'] == 'brucellosis' =>
        m.containsKey('type')
            ? null
            : {
                for (final MapEntry(:key, :value) in m.entries)
                  key: switch (key) {
                    'health' => 'healthy',
                    'illness' || 'sickSince' || 'recoversOn' => null,
                    _ => walk(value),
                  },
              },
      final Map<String, Object?> m => {
        for (final MapEntry(:key, :value) in m.entries) key: walk(value),
      },
      final List<Object?> l => [
        for (final x in l)
          if (!(x is Map<String, Object?> &&
              x.containsKey('type') &&
              x['illness'] == 'brucellosis'))
            walk(x),
      ],
      _ => v,
    };
    return walk(data)! as Map<String, Object?>;
  }

  /// v4 to v5 (the owner's decision of 12 Nov 2026: feed and water run out
  /// and are ordered): every farm gets a feed store and a water tank, sized
  /// as a new farm's of its capacity or a month of its herd's needs if more,
  /// and filled with a
  /// month of them (an adult on the standard ration: 3.3 kg barley, 7.7 kg
  /// alfalfa and 30 L of water a day; v5's numbers, written here so the step
  /// never depends on today's classes).
  static Map<String, Object?> _v4ToV5(Map<String, Object?> input) {
    final data = jsonDecode(jsonEncode(input)) as Map<String, Object?>;
    final camels =
        ((data['world'] as Map<String, Object?>?)?['camels']
            as List<Object?>?) ??
        const [];
    for (final pl in (data['players'] as List<Object?>?) ?? const []) {
      final player = pl! as Map<String, Object?>;
      final farm = player['farm']! as Map<String, Object?>;
      final head = camels
          .cast<Map<String, Object?>>()
          .where((c) => c['owner'] == player['id'] && c['status'] == 'alive')
          .length;
      final barley = head * 3.3 * 30, alfalfa = head * 7.7 * 30;
      final water = head * 30.0 * 30;
      // a new farm's store and tank for the farm's capacity (20,000 kg and
      // 40,000 L at 20 head, 330 kg and 900 L more a head), or a month of the
      // herd's needs if more
      final room = (farm['capacity']! as int) - 20;
      final store = 20000 + (room > 0 ? room * 330 : 0);
      final tank = 40000 + (room > 0 ? room * 900 : 0);
      final month = (barley + alfalfa).ceil();
      farm
        ..['storeKg'] = month > store ? month : store
        ..['tankL'] = water.ceil() > tank ? water.ceil() : tank
        ..['barleyKg'] = barley
        ..['alfalfaKg'] = alfalfa
        ..['waterL'] = water
        ..['dryDays'] = 0
        ..['fedShare'] = 1.0
        ..['short'] = <Object?>[]
        ..['deliveries'] = <Object?>[];
    }
    return data;
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
