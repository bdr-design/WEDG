import 'dart:convert';
import 'dart:io';

import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/persistence.dart';
import 'package:sqlite3/sqlite3.dart';

/// Keeps the game in a SQLite file (ADR 0004, "Decision at 10,000").
///
/// Files, in the save folder:
/// * `marah.db` (+ `-wal`, `-shm`): the live save.
/// * `backups/prev.db`, `backups/prev2.db`: the last two saves proven good
///   (opened, brought up to date and saved by the engine; see [markGood]).
/// * `backups/broken-<time>.db`: a byte-for-byte copy (with its `-wal`) of
///   every save that failed to open or was replaced by a restore.
/// * `backups/replaced-<time>.db`: the save before the player started over.
/// * `backups/v<N>-<time>.db`: the original before an upgrade.
///
/// Rules:
/// * **Incremental:** a save writes only camels whose changeable fields
///   differ from what was last written, and documents whose JSON changed.
/// * **Atomic:** each save is one transaction; caches update only after a
///   commit.
/// * **Ordered:** rows carry the in-memory insertion order, so a reloaded
///   game iterates the same way and replays identically.
/// * **Never destroys evidence:** nothing replaces or deletes the live save
///   without first keeping a dated copy of it.
class SqliteGameStore implements GameStore {
  SqliteGameStore(this.path, {DateTime Function()? now})
    : _now = now ?? DateTime.now;

  /// Path of the live database file, e.g. `<app support>/marah.db`.
  final String path;
  final DateTime Function() _now;

  /// Version of the table layout (PRAGMA user_version).
  static const schemaVersion = 1;

  /// Table-layout upgrades: `layoutMigrations[n]` moves layout n to n + 1.
  static final Map<int, void Function(Database)> layoutMigrations = {};

  String get _dir => File(path).parent.path;
  String get backupDir => '$_dir${Platform.pathSeparator}backups';
  String get _prev => '$backupDir${Platform.pathSeparator}prev.db';
  String get _prev2 => '$backupDir${Platform.pathSeparator}prev2.db';

  Database? _db;
  bool _locked = false;
  Future<void> _queue = Future.value();
  int _copies = 0;

  final Map<String, List<Object?>> _camelFields = {};
  final Map<String, int> _camelSeq = {};
  final Map<String, String> _docs = {};
  final Map<String, int> _docSeq = {};
  int _nextSeq = 1;

  /// Set by [startOver]: the next save may create a new file. Without it,
  /// a save never replaces a file it has not opened.
  bool _mayCreate = false;

  /// Rows written by the last save (camels, documents), for tests.
  ({int camels, int docs}) lastWrite = (camels: 0, docs: 0);

  @override
  bool get locked => _locked;

  // ------------------------------------------------------------- opening

  @override
  Future<OpenResult> open() async {
    await _queue;
    if (!File(path).existsSync()) return const NoSave();
    try {
      final r = _loadFrom(path);
      if (r is OpenFailed) return await _failOpen(r.problem, r.detail);
      return r;
    } on Object catch (e) {
      return _failOpen(LoadProblem.corrupt, 'open failed: $e');
    }
  }

  /// Opens [file] as the live connection and decodes it. On an older data
  /// version, keeps the original and rebuilds the file in the new shape.
  OpenResult _loadFrom(String file) {
    _close();
    final db = sqlite3.open(file);
    _db = db;
    final check = db.select('PRAGMA quick_check').first.values.first;
    if (check != 'ok') {
      return OpenFailed(LoadProblem.corrupt, 'quick_check: $check');
    }
    var layout = db.select('PRAGMA user_version').first.values.first! as int;
    if (layout > schemaVersion) {
      return OpenFailed(LoadProblem.tooNew, 'layout $layout');
    }
    final meta = _readMeta(db);
    if (meta['format'] != 'marah-db') {
      return const OpenFailed(LoadProblem.notASave, 'missing format marker');
    }
    final version = int.parse(meta['version']!);
    if (version > SaveCodec.currentVersion) {
      return OpenFailed(LoadProblem.tooNew, 'data version $version');
    }
    final upgrade =
        version < SaveCodec.currentVersion || layout < schemaVersion;
    if (upgrade) _keepCopy(file, 'v$version');
    while (layout < schemaVersion) {
      final step = layoutMigrations[layout];
      if (step == null) {
        return OpenFailed(LoadProblem.noMigration, 'no layout step $layout');
      }
      step(db);
      layout++;
      db.execute('PRAGMA user_version = $layout');
    }
    _applyPragmas(db);

    _resetCaches();
    var data = _readData(db, meta);
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
    if (version < SaveCodec.currentVersion) {
      _rebuild(game);
    } else {
      for (final c in game.world.camels.values) {
        _camelFields[c.id.value] = c.mutableFields();
      }
    }
    return Opened(game, migratedFrom: version);
  }

  static Map<String, String> _readMeta(Database db) => {
    for (final r in db.select('SELECT key, value FROM meta'))
      r['key'] as String: r['value'] as String,
  };

  /// Reads all rows back into the JSON shape of [GameState.toJson]. When
  /// [remember] is set, records what is on disk for incremental saves.
  Map<String, Object?> _readData(
    Database db,
    Map<String, String> meta, {
    bool remember = true,
  }) {
    Object? keep(String kind, String id, int seq, String data) {
      if (remember) {
        final key = '$kind:$id';
        _docs[key] = data;
        _docSeq[key] = seq;
        if (seq >= _nextSeq) _nextSeq = seq + 1;
      }
      return jsonDecode(data);
    }

    List<Object?> docs(String kind) => [
      for (final r in db.select(
        'SELECT id, seq, data FROM doc WHERE kind = ? ORDER BY seq',
        [kind],
      ))
        keep(kind, r['id'] as String, r['seq'] as int, r['data'] as String),
    ];
    final camels = <Object?>[];
    for (final r in db.select('SELECT id, seq, data FROM camel ORDER BY seq')) {
      final seq = r['seq'] as int;
      if (remember) {
        _camelSeq[r['id'] as String] = seq;
        if (seq >= _nextSeq) _nextSeq = seq + 1;
      }
      camels.add(jsonDecode(r['data'] as String));
    }
    final inboxes = <String, Object?>{
      for (final r in db.select(
        "SELECT id, seq, data FROM doc WHERE kind = 'inbox' ORDER BY seq",
      ))
        r['id'] as String: keep(
          'inbox',
          r['id'] as String,
          r['seq'] as int,
          r['data'] as String,
        ),
    };
    if (remember) {
      for (final k in ['state', 'world', 'version']) {
        _docs['meta:$k'] = meta[k]!;
      }
    }
    final state = jsonDecode(meta['state']!) as Map<String, Object?>;
    final world = jsonDecode(meta['world']!) as Map<String, Object?>;
    return {
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
  }

  void _resetCaches() {
    _camelFields.clear();
    _camelSeq.clear();
    _docs.clear();
    _docSeq.clear();
    _nextSeq = 1;
  }

  static void _applyPragmas(Database db) {
    db.execute('''
      PRAGMA journal_mode = WAL;
      PRAGMA synchronous = NORMAL;
      PRAGMA journal_size_limit = 4194304;
    ''');
  }

  static void _createTables(Database db) {
    _applyPragmas(db);
    db.execute('''
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
    db.execute("INSERT INTO meta VALUES ('format', 'marah-db')");
  }

  /// Writes [game] in full into a new file (fresh order) and swaps it in.
  void _rebuild(GameState game) {
    final fresh = '$path.new';
    _deleteDb(fresh);
    final db = sqlite3.open(fresh);
    try {
      _createTables(db);
      _close();
      _db = db;
      _resetCaches();
      _write(game);
      db.execute('PRAGMA wal_checkpoint(TRUNCATE)');
    } finally {
      db.close();
      _db = null;
    }
    _deleteDb(path);
    File(fresh).renameSync(path);
    _deleteDb(fresh);
    final live = sqlite3.open(path);
    _applyPragmas(live);
    _db = live;
  }

  /// A save could not be opened: keep a dated copy (with its WAL, before
  /// any connection closes and merges it), lock saving, report.
  Future<OpenFailed> _failOpen(LoadProblem problem, String detail) async {
    _locked = true;
    try {
      _keepCopy(path, 'broken');
    } on Object {
      // Even the copy failed; saving stays locked so nothing is lost.
    }
    _close();
    return OpenFailed(problem, detail);
  }

  /// Copies [file] and its `-wal`/`-shm` to `backups/<label>-<time>.db`.
  void _keepCopy(String file, String label) {
    if (!File(file).existsSync()) return;
    Directory(backupDir).createSync(recursive: true);
    final stamp = _now().toUtc().toIso8601String().replaceAll(':', '-');
    final target =
        '$backupDir${Platform.pathSeparator}$label-$stamp-${_copies++}.db';
    for (final suffix in ['', '-wal', '-shm']) {
      final src = File('$file$suffix');
      if (src.existsSync()) src.copySync('$target$suffix');
    }
  }

  // ------------------------------------------------------------- backups

  @override
  Future<bool> markGood() async {
    await _queue;
    final db = _db;
    if (db == null || _locked) return false;
    final tmp = '$_prev.tmp';
    try {
      Directory(backupDir).createSync(recursive: true);
      _deleteDb(tmp);
      db.execute('VACUUM INTO ?', [tmp]);
      if (!_isGood(tmp)) {
        _deleteDb(tmp);
        return false;
      }
      if (File(_prev).existsSync()) File(_prev).renameSync(_prev2);
      File(tmp).renameSync(_prev);
      return true;
    } on Object {
      _deleteDb(tmp);
      return false;
    }
  }

  @override
  Future<OpenResult> openPrevious() async {
    await _queue;
    for (final candidate in [_prev, _prev2]) {
      if (!File(candidate).existsSync() || !_isGood(candidate)) continue;
      // The fallback loads: keep the current save, then swap.
      _keepCopy(path, 'broken');
      _close();
      final tmp = '$path.restore';
      _deleteDb(tmp);
      File(candidate).copySync(tmp);
      _deleteDb(path);
      File(tmp).renameSync(path);
      _locked = false;
      try {
        final r = _loadFrom(path);
        if (r is OpenFailed) _locked = true;
        return r;
      } on Object catch (e) {
        _locked = true;
        return OpenFailed(LoadProblem.corrupt, 'restore failed: $e');
      }
    }
    return const NoSave();
  }

  /// Whether [file] opens, passes quick_check and decodes. Read-only.
  bool _isGood(String file) {
    Database? db;
    try {
      db = sqlite3.open(file, mode: OpenMode.readOnly);
      if (db.select('PRAGMA quick_check').first.values.first != 'ok') {
        return false;
      }
      final meta = _readMeta(db);
      if (meta['format'] != 'marah-db') return false;
      final version = int.parse(meta['version']!);
      if (version > SaveCodec.currentVersion) return false;
      if (version < SaveCodec.currentVersion) return true; // upgraded on load
      GameState.fromJson(_readData(db, meta, remember: false));
      return true;
    } on Object {
      return false;
    } finally {
      db?.close();
    }
  }

  @override
  Future<void> startOver() async {
    await _queue;
    _close();
    _keepCopy(path, 'replaced');
    _locked = false;
    _deleteDb(path);
    _resetCaches();
    _mayCreate = true;
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
        _deleteDb(path);
        final db = sqlite3.open(path);
        _createTables(db);
        _db = db;
        _resetCaches();
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
      for (final id in _camelSeq.keys)
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
    final meta = {
      'state': jsonEncode(s.scalarsToJson()),
      'world': jsonEncode(w.scalarsToJson()),
      'version': '${SaveCodec.currentVersion}',
    };
    final metaChanged = [
      for (final e in meta.entries)
        if (_docs['meta:${e.key}'] != e.value) e,
    ];

    final newDocSeq = <String, int>{};
    db.execute('BEGIN IMMEDIATE');
    try {
      final upCamel = db.prepare(
        'INSERT INTO camel(id, seq, owner, status, data) VALUES (?, ?, ?, ?, ?) '
        'ON CONFLICT(id) DO UPDATE SET seq = excluded.seq, '
        'owner = excluded.owner, status = excluded.status, '
        'data = excluded.data',
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
        'ON CONFLICT(kind, id) DO UPDATE SET seq = excluded.seq, '
        'data = excluded.data',
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
      for (final e in metaChanged) {
        upMeta.execute([e.key, e.value]);
      }
      upMeta.close();
      db.execute('COMMIT');
    } on Object {
      if (!db.autocommit) db.execute('ROLLBACK');
      rethrow;
    }

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
    for (final e in metaChanged) {
      _docs['meta:${e.key}'] = e.value;
    }
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

  // ------------------------------------------------------------- lifecycle

  /// Waits for pending writes and folds the WAL back into the main file, so
  /// the file is complete on its own (copies, OS backups) and stays small.
  @override
  Future<void> flush() async {
    await _queue;
    try {
      _db?.execute('PRAGMA wal_checkpoint(TRUNCATE)');
    } on SqliteException {
      // A busy checkpoint is retried next time; data is safe in the WAL.
    }
  }

  @override
  Future<void> close() async {
    await flush();
    _close();
  }

  void _close() {
    _db?.close();
    _db = null;
  }

  static void _deleteDb(String p) {
    for (final suffix in ['', '-wal', '-shm', '-journal']) {
      final f = File('$p$suffix');
      if (f.existsSync()) f.deleteSync();
    }
  }
}
