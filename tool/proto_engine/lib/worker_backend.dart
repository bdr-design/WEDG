import 'package:marah_data/marah_data.dart';

/// The save's keys and values held in the worker, seeded by the page at start;
/// every change is handed to [persist] for the page to keep (the iPhone app's
/// files through its local server, or the browser's storage in tests).
class WorkerBackend implements SaveBackend {
  WorkerBackend(Map<String, String> seed, this.persist) : _data = {...seed};

  final Map<String, String> _data;
  final void Function(String key, String? value) persist;

  @override
  Future<String?> read(String key) async => _data[key];

  @override
  Future<void> write(String key, String value) async {
    _data[key] = value;
    persist(key, value);
  }

  @override
  Future<void> delete(String key) async {
    _data.remove(key);
    persist(key, null);
  }

  @override
  Future<void> copy(String from, String to) async {
    final v = _data[from];
    if (v == null) return; // as SaveBackend says: nothing to copy, nothing done
    return write(to, v);
  }
}
