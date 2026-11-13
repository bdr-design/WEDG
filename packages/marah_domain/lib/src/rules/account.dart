import 'dart:math' as math;

import '../common/result.dart';
import '../common/time.dart';
import '../model/camel.dart';
import '../model/player.dart';
import 'balance.dart';
import 'provisions.dart';

/// The herd's necessities on account (the owner's decisions of 13 Nov
/// 2026): feed, water and the vet's treatment of a sick camel are bought on
/// account whenever the money does not cover them, as a merchant books a
/// breeder, up to a limit; past it the player must sell. The account counts
/// only what was bought on it, never a fine: a fined player's herd is still
/// fed, and the income that comes in pays the merchant first.
class Account {
  const Account._();

  /// (balance) The limit: a month of the herd's feed and water at today's
  /// ration ([Balance.creditDays]), at least [Balance.minCreditLimit]: a
  /// merchant gives a breeder about a month, and a bigger herd a bigger
  /// account.
  static int limit(Iterable<Camel> herd, PlayerState p, GameDay today) =>
      limitFor(Provisions.needs(herd, p.farm.feedPlan, today), p);

  /// [limit] from the herd's daily [n]eeds, worked out already.
  static int limitFor(
    ({double barley, double alfalfa, double water}) n,
    PlayerState p,
  ) {
    final daily =
        Provisions.feedCost(n, p.farm.region) +
        n.water / Balance.waterLoadL * Balance.waterLoadPrice;
    return math.max(
      Balance.minCreditLimit,
      (daily * Balance.creditDays).round(),
    );
  }

  /// What of [cost] the money does not cover, to go on account.
  static int shortfall(PlayerState p, int cost) =>
      cost - math.max(0, math.min(p.cash.value, cost));

  /// Why [cost] cannot be paid, from the money and then on account, or null.
  static DomainError? canPay(PlayerState p, int cost, int limit) {
    final rest = shortfall(p, cost);
    if (rest == 0 || p.onAccount + rest <= limit) return null;
    return DomainError(ErrorCode.accountFull, {
      'needed': cost,
      'limit': limit,
      'owed': p.onAccount,
    });
  }

  /// Books [cost]'s shortfall on account (before the money is paid out).
  static void book(PlayerState p, int cost) =>
      p.onAccount += shortfall(p, cost);
}
