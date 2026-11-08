import 'package:marah_domain/marah_domain.dart';

import 'save_codec.dart';

/// Raw text storage for one save slot (device files, the browser's storage,
/// or a server later). Implementations live in the runtime and the app.
abstract interface class SaveBackend {
  Future<String?> read(String key);
  Future<void> write(String key, String value);
  Future<void> delete(String key);

  /// Copies whatever is stored under [from] to [to], byte for byte, even if
  /// it is not valid text. Does nothing if [from] does not exist.
  Future<void> copy(String from, String to);
}

/// What the app gets when it opens the game.
sealed class OpenResult {
  const OpenResult();
}

final class NoSave extends OpenResult {
  const NoSave();
}

final class Opened extends OpenResult {
  const Opened(this.state, {required this.migratedFrom});
  final GameState state;
  final int migratedFrom;
}

/// The save exists but could not be read. A byte-for-byte copy is kept as
/// `<slot>.broken`, the slot is locked, and the player decides what to do.
final class OpenFailed extends OpenResult {
  const OpenFailed(this.problem, this.detail);
  final LoadProblem problem;
  final String detail;
}

/// Where a game is kept. The engine only talks to this interface: the
/// SQLite store on devices, the JSON store in tests and tools.
///
/// Every implementation must: never overwrite a save it could not read
/// (back it up, lock, report); keep a fallback that is proven readable;
/// and keep later writes working after one write fails.
abstract interface class GameStore {
  /// True while a broken save waits for the player's decision; saving is
  /// ignored until they restore or start over.
  bool get locked;

  Future<OpenResult> open();

  /// Persists the game. Completes with an error if this write fails.
  Future<void> save(GameState state);

  /// Restores the last save that was proven good. The current save is kept
  /// as a dated copy first, and nothing changes unless the fallback loads.
  Future<OpenResult> openPrevious();

  /// The game was opened, brought up to date and saved: the current save is
  /// proven good and becomes the fallback. Returns false if the backup
  /// could not be written (the old fallback is kept).
  Future<bool> markGood();

  /// The player chose to start over.
  Future<void> startOver();

  /// Waits for pending writes.
  Future<void> flush();

  /// Releases resources (database connections).
  Future<void> close();
}

/// Keeps the game as one JSON document (tests, tools).
///
/// Loads and saves one game safely.
///
/// * A save that cannot be read is copied to `.broken` and never
///   overwritten: saving is locked until the player restores or starts over.
/// * `.prev` holds the last save that was **proven readable** (rotated when
///   a save loads successfully), not simply the previous write.
/// * Each write is independent: one failed write (full disk) never stops
///   later ones, and the error reaches the caller.
class SaveStore implements GameStore {
  SaveStore(this.backend, {this.slot = 'marah.save', SaveCodec? codec})
    : codec = codec ?? const SaveCodec();

  final SaveBackend backend;
  final String slot;
  final SaveCodec codec;

  String get _prev => '$slot.prev';
  String get _broken => '$slot.broken';

  bool _locked = false;
  Future<void> _queue = Future.value();

  @override
  bool get locked => _locked;

  @override
  Future<OpenResult> open() async {
    final String? raw;
    try {
      raw = await backend.read(slot);
    } on Object catch (e) {
      // Unreadable bytes (bad encoding, I/O error): keep them, lock, report.
      return _fail(LoadProblem.corrupt, 'read failed: $e');
    }
    if (raw == null) return const NoSave();
    final result = codec.decode(raw);
    switch (result) {
      case Loaded(:final state, :final migratedFrom):
        return Opened(state, migratedFrom: migratedFrom);
      case LoadFailed(:final problem, :final detail):
        return _fail(problem, detail);
    }
  }

  @override
  Future<bool> markGood() async {
    try {
      await flush();
      await backend.copy(slot, _prev);
      return true;
    } on Object {
      return false;
    }
  }

  Future<OpenFailed> _fail(LoadProblem problem, String detail) async {
    _locked = true;
    try {
      await backend.copy(slot, _broken);
    } on Object {
      // Even the backup failed; saving stays locked so nothing is lost.
    }
    return OpenFailed(problem, detail);
  }

  /// Saves the game. Ignored while a broken save awaits the player's
  /// decision. Completes with an error if this write fails; later writes
  /// still run.
  @override
  Future<void> save(GameState state) {
    if (_locked) return Future.value();
    final text = codec.encode(state);
    final job = _queue
        .catchError((Object _) {})
        .then((_) => backend.write(slot, text));
    _queue = job.catchError((Object _) {});
    return job;
  }

  /// Restores the last save that was proven readable. The restored text is
  /// written to the slot before anything else changes.
  @override
  Future<OpenResult> openPrevious() async {
    final String? raw;
    try {
      raw = await backend.read(_prev);
    } on Object catch (e) {
      return OpenFailed(LoadProblem.corrupt, 'read failed: $e');
    }
    if (raw == null) return const NoSave();
    final result = codec.decode(raw);
    switch (result) {
      case Loaded(:final state, :final migratedFrom):
        await backend.write(slot, raw);
        _locked = false;
        return Opened(state, migratedFrom: migratedFrom);
      case LoadFailed(:final problem, :final detail):
        return OpenFailed(problem, detail);
    }
  }

  /// The player chose to start over. The broken copy and the last good
  /// save stay where they are.
  @override
  Future<void> startOver() async {
    _locked = false;
    await backend.delete(slot);
  }

  /// Waits for pending writes (call when the app goes to the background).
  @override
  Future<void> flush() => _queue;

  @override
  Future<void> close() => _queue;
}

/// In-memory backend for tests and tools.
class MemoryBackend implements SaveBackend {
  final Map<String, String> data = {};

  @override
  Future<String?> read(String key) async => data[key];

  @override
  Future<void> write(String key, String value) async => data[key] = value;

  @override
  Future<void> delete(String key) async => data.remove(key);

  @override
  Future<void> copy(String from, String to) async {
    final v = data[from];
    if (v != null) data[to] = v;
  }
}
