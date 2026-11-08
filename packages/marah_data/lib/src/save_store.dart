import 'package:marah_domain/marah_domain.dart';

import 'save_codec.dart';

/// Raw text storage for one save slot (device key-value store, a file, or a
/// server later). Implementations live in the app.
abstract interface class SaveBackend {
  Future<String?> read(String key);
  Future<void> write(String key, String value);
  Future<void> delete(String key);
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

/// The save exists but could not be read. It has been copied to a backup
/// key and is left untouched; the app must ask the player what to do.
final class OpenFailed extends OpenResult {
  const OpenFailed(this.problem, this.detail);
  final LoadProblem problem;
  final String detail;
}

/// Loads and saves one game safely:
///
/// * a save that fails to load is copied to a backup and never overwritten
///   unless the player explicitly starts over;
/// * every write keeps the previous good save as `.prev`;
/// * writes are serialised so two saves never interleave.
class SaveStore {
  SaveStore(this.backend, {this.slot = 'marah.save', SaveCodec? codec})
    : codec = codec ?? const SaveCodec();

  final SaveBackend backend;
  final String slot;
  final SaveCodec codec;

  String get _prev => '$slot.prev';
  String get _broken => '$slot.broken';

  bool _locked = false;
  Future<void> _queue = Future.value();

  Future<OpenResult> open() async {
    final raw = await backend.read(slot);
    if (raw == null) return const NoSave();
    final result = codec.decode(raw);
    switch (result) {
      case Loaded(:final state, :final migratedFrom):
        return Opened(state, migratedFrom: migratedFrom);
      case LoadFailed(:final problem, :final detail):
        await backend.write(_broken, raw);
        _locked = true;
        return OpenFailed(problem, detail);
    }
  }

  /// Saves the game. Ignored while a broken save is waiting for the
  /// player's decision, so it can never be overwritten by accident.
  Future<void> save(GameState state) {
    if (_locked) return Future.value();
    final text = codec.encode(state);
    return _queue = _queue.then((_) async {
      final current = await backend.read(slot);
      if (current != null) await backend.write(_prev, current);
      await backend.write(slot, text);
    });
  }

  /// Tries the previous good save after a failed open.
  Future<OpenResult> openPrevious() async {
    final raw = await backend.read(_prev);
    if (raw == null) return const NoSave();
    final result = codec.decode(raw);
    return switch (result) {
      Loaded(:final state, :final migratedFrom) => Opened(
        state,
        migratedFrom: migratedFrom,
      ),
      LoadFailed(:final problem, :final detail) => OpenFailed(problem, detail),
    };
  }

  /// The player chose to start over. The broken save stays in its backup.
  Future<void> startOver() async {
    _locked = false;
    await backend.delete(slot);
    await backend.delete(_prev);
  }

  /// Waits for pending writes (call when the app goes to the background).
  Future<void> flush() => _queue;
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
}
