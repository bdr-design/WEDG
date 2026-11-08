import 'dart:convert';
import 'dart:io';

import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/persistence.dart';
import 'package:sqlite3/sqlite3.dart';

/// Keeps the game in a SQLite file (ADR 0004, "Decision at 10,000").
///
/// * **Incremental:** a save writes only the camels whose changeable fields
///   differ from what was last written, and only the small documents
///   (listings, festivals, inboxes...) whose JSON changed. Committing a
///   command touches a handful of rows instead of rewriting megabytes.
/// * **Atomic:** each save is one transaction; a failed write rolls back
///   and the in-memory caches are only updated after a commit.
/// * **Ordered:** rows carry the insertion sequence of the in-memory maps,
///   so a reloaded game iterates in the same order and replays identically.
/// * **Safe:** a file that cannot be opened, fails `quick_check` or cannot
///   be decoded is copied to `.broken` and saving is locked. After a good
///   open the file is copied to `.prev` (`VACUUM INTO`), the fallback that
///   is proven readable.
class SqliteGameStore implements GameStore {
  SqliteGameStore(this.path);

  /// Path of the database file, e.g. `<app support>/marah.db`.
  final String path;

  /// Version of the table layout (PRAGMA user_version).
  static const schemaVersion = 1;

  String get _prev => '$path.prev';
  String get _broken => '$path.broken';

  Database? _db;
  bool _locked = false;
  Future<void> _queue = Future.value();

  // What was last written, to find what changed.
  final Map<String, List<Object?>> _camelFields = {};
  final Map<String, int> _camelSeq = {};
  final Map<String, String> _docs = {};
  final Map<String, int> _docSeq = {};
  int _nextSeq = 1;

  /// Set by [startOver]: the next save may create a new file. Without it,
  /// a save never replaces a file it has not opened.
  bool _mayCreate = false;

  /// Rows written by the last save (camels, documents), for tests and
  /// budgets.
  ({int camels, int docs}) lastWrite = (camels: 0, docs: 0);

  @override
  bool get locked => _locked;

  // ------------------------------------------------------------- opening

  @override
  Future<OpenResult> open() async {
    if (!File(path).existsSync()) return const NoSave();
    final OpenResult result;
    try {
      result = _load();
    } on Object catch (e) {
      return _fail(LoadProblem.corrupt, 'open failed: $e');
    }
    if (result is Opened) _backupToPrev();
    if (result is OpenFailed) return _fail(result.problem, result.detail);
    return result;
  }

  OpenResult _load() {
    _close();
    final db = sqlite3.open(path);
    _db = db;
    final check = db.select('PRAGMA quick_check').first.values.first;
    if (check != 'ok') {
      return OpenFailed(LoadProblem.corrupt, 'quick_check: $check');
    }
    final layout = db.select('PRAGMA user_version').first.values.first! as int;
    if (layout > schemaVersion) {
      return OpenFailed(LoadProblem.tooNew, 'layout $layout');
    }
    final meta = {
      for (final r in db.select('SELECT key, value FROM meta'))
        r['key'] as String: r['value'] as String,
    };
    if (meta['format'] != 'marah-db') {
      return const OpenFailed(LoadProblem.notASave, 'missing format marker');
    }
    final version = int.parse(meta['version']!);
    if (version > SaveCodec.currentVersion) {
      return OpenFailed(LoadProblem.tooNew, 'data version $version');
    }

    _resetCaches();
    List<Map<String, Object?>> docs(String kind) => [
      for (final r in db.select(
        'SELECT id, seq, data FROM doc WHERE kind = ? ORDER BY seq',
        [kind],
      ))
        _rememberDoc(
          kind,
          r['id'] as String,
          r['seq'] as int,
          r['data'] as String,
        ),
    ];
    final camels = [
      for (final r in db.select('SELECT id, seq, data FROM camel ORDER BY seq'))
        _rememberCamelRow(
          r['id'] as String,
          r['seq'] as int,
          r['data'] as String,
        ),
    ];
    final inboxes = <String, Object?>{
      for (final r in db.select(
        "SELECT id, seq, data FROM doc WHERE kind = 'inbox' ORDER BY seq",
      ))
        r['id'] as String: _rememberDocRaw(
          'inbox',
          r['id'] as String,
          r['seq'] as int,
          r['data'] as String,
        ),
    };
    final state = jsonDecode(meta['state']!) as Map<String, Object?>;
    final world = jsonDecode(meta['world']!) as Map<String, Object?>;
    _docs['meta:state'] = meta['state']!;
    _docs['meta:world'] = meta['world']!;
    _docs['meta:version'] = meta['version']!;

    var data = <String, Object?>{
      ...state,
      'world': {
        ...world,
        'owners': docs('owner'),
        'camels': camels,
        'listings': docs('listing'),
        'offers': docs('offer'),
        'studs': docs('stud'),
        'festivals': docs('festival'),
      },
      'players': docs('player'),
      'inboxes': inboxes,
    };
    final upgraded = version < SaveCodec.currentVersion;
    for (var v = version; v < SaveCodec.currentVersion; v++) {
      final step = SaveCodec.migrations[v];
      if (step == null) {
        return OpenFailed(LoadProblem.noMigration, 'no step from $v');
      }
      data = step(data);
    }
    final GameState game;
    try {
      game = GameState.fromJson(data);
    } on Object catch (e) {
      return OpenFailed(LoadProblem.corrupt, e.toString());
    }
    if (upgraded) {
      // Rewrite everything in the new shape.
      _resetCaches();
      _write(game);
    } else {
      // Camels are cached as decoded rows; record their changeable fields.
      for (final c in game.world.camels.values) {
        _camelFields[c.id.value] = c.mutableFields();
      }
    }
    return Opened(game, migratedFrom: version);
  }

  Map<String, Object?> _rememberDoc(
    String kind,
    String id,
    int seq,
    String data,
  ) {
    final key = '$kind:$id';
    _docs[key] = data;
    _docSeq[key] = seq;
    if (seq >= _nextSeq) _nextSeq = seq + 1;
    return jsonDecode(data) as Map<String, Object?>;
  }

  Object? _rememberDocRaw(String kind, String id, int seq, String data) {
    final key = '$kind:$id';
    _docs[key] = data;
    _docSeq[key] = seq;
    if (seq >= _nextSeq) _nextSeq = seq + 1;
    return jsonDecode(data);
  }

  Map<String, Object?> _rememberCamelRow(String id, int seq, String data) {
    _camelSeq[id] = seq;
    if (seq >= _nextSeq) _nextSeq = seq + 1;
    return jsonDecode(data) as Map<String, Object?>;
  }

  void _resetCaches() {
    _camelFields.clear();
    _camelSeq.clear();
    _docs.clear();
    _docSeq.clear();
    _nextSeq = 1;
  }

  Database _create() {
    _close();
    _deleteFiles(path);
    final db = sqlite3.open(path);
    db.execute('''
      PRAGMA journal_mode = WAL;
      PRAGMA synchronous = NORMAL;
      CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL) WITHOUT ROWID;
      CREATE TABLE doc(
        kind TEXT NOT NULL, id TEXT NOT NULL, seq INTEGER NOT NULL,
        data TEXT NOT NULL, PRIMARY KEY (kind, id)) WITHOUT ROWID;
      CREATE TABLE camel(
        id TEXT PRIMARY KEY, seq INTEGER NOT NULL, owner TEXT NOT NULL,
        status INTEGER NOT NULL, data TEXT NOT NULL) WITHOUT ROWID;
      CREATE INDEX camel_owner ON camel(owner, status);
      PRAGMA user_version = $schemaVersion;
    ''');
    db.execute(
      "INSERT INTO meta VALUES ('format', 'marah-db'), ('version', ?)",
      ['${SaveCodec.currentVersion}'],
    );
    _db = db;
    _resetCaches();
    return db;
  }

  Future<OpenFailed> _fail(LoadProblem problem, String detail) async {
    _locked = true;
    _close();
    try {
      for (final suffix in ['', '-wal']) {
        _copyFile('$path$suffix', '$_broken$suffix');
      }
    } on Object {
      // Even the backup failed; saving stays locked so nothing is lost.
    }
    return OpenFailed(problem, detail);
  }

  @override
  Future<OpenFailed> reject(String detail) =>
      _fail(LoadProblem.corrupt, detail);

  void _backupToPrev() {
    final db = _db;
    if (db == null) return;
    _deleteFiles(_prev);
    db.execute('VACUUM INTO ?', [_prev]);
  }

  // ------------------------------------------------------------- saving

  @override
  Future<void> save(GameState state) {
    if (_locked) return Future.value();
    final job = _queue.catchError((Object _) {}).then((_) {
      if (_db == null) {
        if (File(path).existsSync() && !_mayCreate) {
          throw StateError('save store not opened; refusing to replace $path');
        }
        _create();
        _mayCreate = false;
      }
      _write(state);
    });
    _queue = job.catchError((Object _) {});
    return job;
  }

  /// Writes what changed in one transaction; caches update after commit.
  void _write(GameState s) {
    final db = _db!;
    final w = s.world;
    final camelUpserts = <(String, int, String, int, String, List<Object?>)>[];
    final seen = <String>{};
    var seq = _nextSeq;
    for (final c in w.camels.values) {
      final id = c.id.value;
      seen.add(id);
      final fields = c.mutableFields();
      final old = _camelFields[id];
      if (old != null && _sameFields(old, fields)) continue;
      final rowSeq = _camelSeq[id] ?? seq++;
      camelUpserts.add((
        id,
        rowSeq,
        c.ownerId.value,
        c.status.index,
        jsonEncode(c.toJson()),
        fields,
      ));
    }
    final camelDeletes = [
      for (final id in _camelFields.keys)
        if (!seen.contains(id)) id,
    ];

    final docs = <String, (String, String, String)>{};
    void doc(String kind, String id, Object? json) =>
        docs['$kind:$id'] = (kind, id, jsonEncode(json));
    for (final o in w.owners.values) {
      doc('owner', o.id.value, o.toJson());
    }
    for (final l in w.listings.values) {
      doc('listing', l.id.value, l.toJson());
    }
    for (final o in w.offers.values) {
      doc('offer', o.id.value, o.toJson());
    }
    for (final st in w.studs.values) {
      doc('stud', st.id.value, st.toJson());
    }
    for (final f in w.festivals.values) {
      doc('festival', f.id.value, f.toJson());
    }
    for (final p in s.players.values) {
      doc('player', p.id.value, p.toJson());
    }
    for (final e in s.inboxes.entries) {
      doc('inbox', e.key, [for (final ev in e.value) ev.toJson()]);
    }
    final docUpserts = [
      for (final e in docs.entries)
        if (_docs[e.key] != e.value.$3) (e.key, e.value),
    ];
    final docDeletes = [
      for (final k in _docSeq.keys)
        if (!docs.containsKey(k)) k,
    ];
    final metaState = jsonEncode({
      'startedOn': s.startedOn.value,
      'startedAtUtcMs': s.startedAtUtcMs,
      'clockShiftMs': s.clockShiftMs,
      'lastSeenUtcMs': s.lastSeenUtcMs,
    });
    const metaVersion = '${SaveCodec.currentVersion}';
    final metaWorld = jsonEncode({
      'seed': w.seed,
      'day': w.day.value,
      'idCounter': w.ids.counter,
      'plannedUntil': w.plannedUntil.value,
    });

    final newDocSeq = <String, int>{};
    db.execute('BEGIN IMMEDIATE');
    try {
      final upCamel = db.prepare(
        'INSERT INTO camel(id, seq, owner, status, data) VALUES (?, ?, ?, ?, ?) '
        'ON CONFLICT(id) DO UPDATE SET owner = excluded.owner, '
        'status = excluded.status, data = excluded.data',
      );
      for (final (id, rowSeq, owner, status, data, _) in camelUpserts) {
        upCamel.execute([id, rowSeq, owner, status, data]);
      }
      upCamel.close();
      final delCamel = db.prepare('DELETE FROM camel WHERE id = ?');
      for (final id in camelDeletes) {
        delCamel.execute([id]);
      }
      delCamel.close();

      final upDoc = db.prepare(
        'INSERT INTO doc(kind, id, seq, data) VALUES (?, ?, ?, ?) '
        'ON CONFLICT(kind, id) DO UPDATE SET data = excluded.data',
      );
      for (final (key, (kind, id, data)) in docUpserts) {
        final rowSeq = _docSeq[key] ?? seq++;
        newDocSeq[key] = rowSeq;
        upDoc.execute([kind, id, rowSeq, data]);
      }
      upDoc.close();
      final delDoc = db.prepare('DELETE FROM doc WHERE kind = ? AND id = ?');
      for (final key in docDeletes) {
        final i = key.indexOf(':');
        delDoc.execute([key.substring(0, i), key.substring(i + 1)]);
      }
      delDoc.close();

      final upMeta = db.prepare(
        'INSERT INTO meta(key, value) VALUES (?, ?) '
        'ON CONFLICT(key) DO UPDATE SET value = excluded.value',
      );
      if (_docs['meta:state'] != metaState) {
        upMeta.execute(['state', metaState]);
      }
      if (_docs['meta:world'] != metaWorld) {
        upMeta.execute(['world', metaWorld]);
      }
      if (_docs['meta:version'] != metaVersion) {
        upMeta.execute(['version', metaVersion]);
      }
      upMeta.close();
      db.execute('COMMIT');
    } on Object {
      if (db.autocommit == false) db.execute('ROLLBACK');
      rethrow;
    }

    // Committed: remember what is on disk.
    for (final (id, rowSeq, _, _, _, fields) in camelUpserts) {
      _camelFields[id] = fields;
      _camelSeq[id] = rowSeq;
    }
    for (final id in camelDeletes) {
      _camelFields.remove(id);
      _camelSeq.remove(id);
    }
    for (final (key, (_, _, data)) in docUpserts) {
      _docs[key] = data;
      _docSeq[key] = newDocSeq[key]!;
    }
    for (final key in docDeletes) {
      _docs.remove(key);
      _docSeq.remove(key);
    }
    _docs['meta:state'] = metaState;
    _docs['meta:world'] = metaWorld;
    _docs['meta:version'] = metaVersion;
    _nextSeq = seq;
    lastWrite = (camels: camelUpserts.length, docs: docUpserts.length);
  }

  static bool _sameFields(List<Object?> a, List<Object?> b) {
    if (a.length != b.length) return false;
    for (var i = 0; i < a.length; i++) {
      if (a[i] != b[i]) return false;
    }
    return true;
  }

  // ------------------------------------------------------------- recovery

  @override
  Future<OpenResult> openPrevious() async {
    if (!File(_prev).existsSync()) return const NoSave();
    _close();
    _deleteFiles(path);
    _copyFile(_prev, path);
    _locked = false;
    try {
      final r = _load();
      if (r is OpenFailed) _locked = true;
      return r;
    } on Object catch (e) {
      _locked = true;
      return OpenFailed(LoadProblem.corrupt, 'open failed: $e');
    }
  }

  @override
  Future<void> startOver() async {
    _locked = false;
    _close();
    _deleteFiles(path);
    _resetCaches();
    _mayCreate = true;
  }

  @override
  Future<void> flush() => _queue;

  @override
  Future<void> close() async {
    await _queue;
    _close();
  }

  void _close() {
    _db?.close();
    _db = null;
  }

  static void _deleteFiles(String p) {
    for (final suffix in ['', '-wal', '-shm']) {
      final f = File('$p$suffix');
      if (f.existsSync()) f.deleteSync();
    }
  }

  static void _copyFile(String from, String to) {
    final src = File(from);
    if (!src.existsSync()) return;
    final tmp = File('$to.tmp');
    src.copySync(tmp.path);
    tmp.renameSync(to);
  }
}
