import 'dart:async';

import 'package:flutter/services.dart';
import 'package:flutter/widgets.dart';

import '../data/game_repository.dart';
import '../domain/engine/game_engine.dart';
import '../domain/models/catalog.dart';
import '../domain/models/game_state.dart';
import '../domain/models/ledger.dart';
import '../domain/models/region.dart';

/// Holds the running game for the UI: runs engine actions, saves, and
/// notifies the screens.
class GameController extends ChangeNotifier {
  GameController(this.repo);

  final GameRepository repo;
  GameState? _state;
  GameEngine? _engine;
  Timer? _saveTimer;

  /// Camel photo assets bundled with the app (filled at start-up).
  Set<String> assets = const {};

  bool get hasGame => _state != null;
  GameState get state => _state!;
  GameEngine get engine => _engine!;

  Future<void> init() async {
    _state = await repo.load();
    if (_state != null) _engine = GameEngine(_state!);
    try {
      final manifest = await AssetManifest.loadFromAssetBundle(rootBundle);
      assets = manifest.listAssets().toSet();
    } catch (_) {
      assets = const {};
    }
  }

  Future<void> startNewGame({
    required String playerName,
    required String farmName,
    required Region region,
    required ColorCategory favourite,
  }) async {
    _state = GameEngine.newGame(
      playerName: playerName,
      farmName: farmName,
      region: region,
      favourite: favourite,
      seed: DateTime.now().microsecondsSinceEpoch & 0x7FFFFFFF,
    );
    _engine = GameEngine(_state!);
    await repo.save(_state!);
    notifyListeners();
  }

  Future<void> endGame() async {
    _saveTimer?.cancel();
    await repo.clear();
    _state = null;
    _engine = null;
    notifyListeners();
  }

  /// Runs a player action, then saves and refreshes the screens.
  ActionResult run(ActionResult Function(GameEngine e) action) {
    final r = action(engine);
    _commit();
    return r;
  }

  void apply(void Function(GameEngine e) action) {
    action(engine);
    _commit();
  }

  List<NewsItem> advance(int days) {
    final news = engine.advance(days);
    _commit();
    return news;
  }

  void _commit() {
    notifyListeners();
    _saveTimer?.cancel();
    _saveTimer = Timer(const Duration(milliseconds: 250), () {
      if (_state != null) repo.save(_state!);
    });
  }

  @override
  void dispose() {
    _saveTimer?.cancel();
    super.dispose();
  }
}

/// Gives every screen access to the controller and rebuilds on changes.
class GameScope extends InheritedNotifier<GameController> {
  const GameScope({
    super.key,
    required GameController controller,
    required super.child,
  }) : super(notifier: controller);

  static GameController of(BuildContext context) =>
      context.dependOnInheritedWidgetOfExactType<GameScope>()!.notifier!;

  /// Access without subscribing to rebuilds (for callbacks).
  static GameController read(BuildContext context) =>
      context.getInheritedWidgetOfExactType<GameScope>()!.notifier!;
}
