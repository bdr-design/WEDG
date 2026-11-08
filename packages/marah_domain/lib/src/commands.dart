import 'common/ids.dart';
import 'model/player.dart';

/// Everything a player can ask the world to do. Commands carry ids and
/// amounts only, never prices or offers the server should look up itself,
/// so the same command can be sent to a server unchanged.
sealed class Command {
  const Command(this.actor);

  /// The player issuing the command.
  final OwnerId actor;
}

// ----------------------------------------------------------------- market

final class BuyListing extends Command {
  const BuyListing(super.actor, this.listing);
  final ListingId listing;
}

final class Bargain extends Command {
  const Bargain(super.actor, this.listing, this.amount);
  final ListingId listing;
  final int amount;
}

final class ListForSale extends Command {
  const ListForSale(super.actor, this.camel, this.askPrice);
  final CamelId camel;
  final int askPrice;
}

final class CancelListing extends Command {
  const CancelListing(super.actor, this.listing);
  final ListingId listing;
}

final class AcceptOffer extends Command {
  const AcceptOffer(super.actor, this.offer);
  final OfferId offer;
}

final class DeclineOffer extends Command {
  const DeclineOffer(super.actor, this.offer);
  final OfferId offer;
}

/// Sell straight to the broker for a quick, lower price.
final class QuickSale extends Command {
  const QuickSale(super.actor, this.camel);
  final CamelId camel;
}

// --------------------------------------------------------------- breeding

final class MateWithOwnBull extends Command {
  const MateWithOwnBull(super.actor, this.female, this.bull);
  final CamelId female;
  final CamelId bull;
}

final class MateWithStud extends Command {
  const MateWithStud(super.actor, this.female, this.stud);
  final CamelId female;
  final StudId stud;
}

// ----------------------------------------------------------------- farm

final class Treat extends Command {
  const Treat(super.actor, this.camel);
  final CamelId camel;
}

final class RenameCamel extends Command {
  const RenameCamel(super.actor, this.camel, this.name);
  final CamelId camel;
  final String name;
}

final class SetFeedPlan extends Command {
  const SetFeedPlan(super.actor, this.plan);
  final FeedPlan plan;
}

final class SetShepherds extends Command {
  const SetShepherds(super.actor, this.count);
  final int count;
}

final class ExpandFarm extends Command {
  const ExpandFarm(super.actor);
}

// --------------------------------------------------------------- contests

final class EnterRound extends Command {
  const EnterRound(super.actor, this.festival, this.round, this.camel);
  final FestivalId festival;
  final RoundId round;
  final CamelId camel;
}

final class WithdrawEntry extends Command {
  const WithdrawEntry(super.actor, this.festival, this.round, this.camel);
  final FestivalId festival;
  final RoundId round;
  final CamelId camel;
}
