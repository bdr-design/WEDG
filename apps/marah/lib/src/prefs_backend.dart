import 'package:marah_data/marah_data.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Stores saves in the platform key-value store (NSUserDefaults on iOS,
/// SharedPreferences on Android, localStorage on the web).
class PrefsBackend implements SaveBackend {
  Future<SharedPreferences> get _prefs => SharedPreferences.getInstance();

  @override
  Future<String?> read(String key) async => (await _prefs).getString(key);

  @override
  Future<void> write(String key, String value) async {
    final ok = await (await _prefs).setString(key, value);
    if (!ok) throw StateError('could not write $key');
  }

  @override
  Future<void> delete(String key) async => (await _prefs).remove(key);

  @override
  Future<void> copy(String from, String to) async {
    final prefs = await _prefs;
    final v = prefs.getString(from);
    if (v != null) await prefs.setString(to, v);
  }
}
