import 'dart:math' as math;

import '../common/money.dart';
import '../events.dart';
import '../model/player.dart';
import '../sim.dart';

/// Money without limit, for the owner's own testing (the owner, 14 Nov 2026:
/// «good mood للفلوس فقط»; the proxy's answers M-1 to M-4, batch 5). While a
/// player's [PlayerState.testMoney] is on, the money never runs short:
/// before every order and after every day it is brought up to [floor] if it
/// is under it, and an order that costs more than the money is topped up by
/// what it lacks and tried once more ([Game.dispatch]). Nothing else
/// changes: prices, fines, the cheating risk, reputation, bans and the
/// account all run as before (the account is simply never needed).
///
/// Every top-up is money in, a ledger row of its own kind
/// ([LedgerCategory.testMoney], «فلوس تجربة» in the bank), rolled up into one
/// row a month, so the ledger still adds up to the money and stays small.
/// The game is marked for good ([PlayerState.testedFrom]). Turned off, the
/// money and the mark stay (M-4; taking the unspent money back is the
/// owner's option for later).
///
/// No screen of the game reaches it: only the prototype's test meter (#fps)
/// sends [SetTestMoney], through the prototype worker's JSON commands.
class TestMoney {
  const TestMoney._();

  /// (game choice) The money it keeps at the least, in riyals: above the
  /// biggest prize (5,000,000, a جزيرة round's) and any camel the market
  /// usually lists; a dearer order is topped up by what it lacks.
  static const floor = 10000000;

  /// Brings [p]'s money up to [floor] plus [need] (what an order costs beyond
  /// it) when it is under that. Returns the riyals added.
  static int topUp(Sim sim, PlayerState p, {int need = 0}) {
    if (!p.testMoney) return 0;
    final add = math.max(0, floor + need - p.cash.value);
    if (add == 0) return 0;
    sim.bill(p, Riyal(add), LedgerCategory.testMoney);
    sim.emit(TestMoneyAdded(sim.today, owner: p.id, amount: add));
    return add;
  }
}
