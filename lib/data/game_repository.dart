import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../domain/models/game_state.dart';

/// Where the game is saved. Phase 1 saves on the device; phase 2 adds a
/// server-backed implementation (shared market, auctions, real players)
/// behind this same interface.
abstract class GameRepository {
  Future<GameState?> load();
  Future<void> save(GameState state);
  Future<void> clear();
}

class LocalGameRepository implements GameRepository {
  static const _key = 'marah.save.v1';

  @override
  Future<GameState?> load() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_key);
    if (raw == null) return null;
    try {
      return GameState.fromJson(jsonDecode(raw) as Map<String, dynamic>);
    } catch (_) {
      // A corrupt or incompatible save must never brick the app.
      return null;
    }
  }

  @override
  Future<void> save(GameState state) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_key, jsonEncode(state.toJson()));
  }

  @override
  Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_key);
  }
}

/// In-memory store for tests.
class MemoryGameRepository implements GameRepository {
  String? _raw;

  @override
  Future<GameState?> load() async => _raw == null
      ? null
      : GameState.fromJson(jsonDecode(_raw!) as Map<String, dynamic>);

  @override
  Future<void> save(GameState state) async =>
      _raw = jsonEncode(state.toJson());

  @override
  Future<void> clear() async => _raw = null;
}
