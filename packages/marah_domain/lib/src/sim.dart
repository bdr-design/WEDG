import 'common/ids.dart';
import 'common/money.dart';
import 'common/rng.dart';
import 'common/time.dart';
import 'events.dart';
import 'model/camel.dart';
import 'model/game_state.dart';
import 'model/player.dart';

/// Working context shared by systems (daily tick) and command handlers:
/// state access, keyed randomness, money with a ledger, and event output.
class Sim {
  Sim(this.state);

  final GameState state;
  final List<DomainEvent> _out = [];

  WorldState get world => state.world;
  GameDay get today => world.day;

  /// An independent random stream for this day and [key]. Keys name the
  /// system and the thing being decided, e.g. ['health', camelId].
  Rng rng(List<Object> key) => Rng.keyed(world.seed, [today.value, ...key]);

  void emit(DomainEvent e) => _out.add(e);

  List<DomainEvent> drain() {
    final events = List<DomainEvent>.unmodifiable(_out);
    _out.clear();
    return events;
  }

  PlayerState? player(OwnerId id) => state.players[id];

  bool isPlayer(OwnerId id) => state.players.containsKey(id);

  /// Records a one-off money movement (positive = income).
  void pay(PlayerState p, Riyal amount, LedgerCategory cat, {String? ref}) {
    if (amount.value == 0) return;
    p.cash = p.cash + amount;
    _settle(p, amount);
    p.ledger.add(
      LedgerEntry(day: today, category: cat, amount: amount, ref: ref),
    );
  }

  /// Money in pays the merchant's account first; it is clear once the money
  /// is back above zero (Account).
  static void _settle(PlayerState p, Riyal amount) {
    if (p.onAccount == 0) return;
    if (amount.value > 0) {
      p.onAccount = p.onAccount > amount.value ? p.onAccount - amount.value : 0;
    }
    if (!p.cash.isNegative) p.onAccount = 0;
  }

  /// Records a recurring cost into this month's single row for [cat].
  void bill(PlayerState p, Riyal amount, LedgerCategory cat) {
    if (amount.value == 0) return;
    p.cash = p.cash + amount;
    _settle(p, amount);
    final d = today.date;
    final month = '${d.year}-${d.month.toString().padLeft(2, '0')}';
    for (var i = p.ledger.length - 1; i >= 0; i--) {
      final row = p.ledger[i];
      if (row.month == month && row.category == cat) {
        row.amount = row.amount + amount;
        return;
      }
      if (row.month != null && row.month!.compareTo(month) < 0) break;
    }
    p.ledger.add(
      LedgerEntry(day: today, category: cat, amount: amount, month: month),
    );
  }

  Iterable<Camel> herdOf(OwnerId owner) => world.aliveOwnedBy(owner);
}
