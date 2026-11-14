/// Rules and simulation for Marah.
///
/// Apps use [Game] to create and advance a world, [Command]s to act, and
/// [GameView] to read what a player may see. Internal models are exported
/// for the save format and tools; screens should not read them directly.
library;

export 'src/away.dart';
export 'src/catalog/catalog.dart';
export 'src/catalog/region.dart';
export 'src/commands.dart';
export 'src/common/ids.dart';
export 'src/common/money.dart';
export 'src/common/result.dart';
export 'src/common/rng.dart' show Rng;
export 'src/common/time.dart';
export 'src/events.dart';
export 'src/game.dart';
export 'src/invariants.dart';
export 'src/model/camel.dart'
    show CamelStatus, HealthStatus, ParentRef, Placing;
export 'src/model/contest.dart';
export 'src/model/game_state.dart' show GameState;
export 'src/model/market.dart' show Offer;
export 'src/model/player.dart';
export 'src/model/tampering.dart';
export 'src/rules/balance.dart';
export 'src/rules/contest_rules.dart';
export 'src/rules/pasture.dart';
export 'src/rules/provisions.dart';
export 'src/rules/test_money.dart' show TestMoney;
export 'src/views/money.dart';
export 'src/views/views.dart';
