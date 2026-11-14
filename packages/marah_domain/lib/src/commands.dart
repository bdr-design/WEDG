import 'catalog/falconry.dart';
import 'common/ids.dart';
import 'model/player.dart';
import 'model/tampering.dart';

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
  const BuyListing(super.actor, this.listing, {this.now = false, this.hour});
  final ListingId listing;

  /// Bought and brought now by a rushed truck (RushTruck), priced by [hour].
  final bool now;

  /// The game's hour of the day the rush is priced by: stamped by the
  /// engine from its own clock, never trusted from the page (RushTruck).
  final int? hour;
}

final class Bargain extends Command {
  const Bargain(super.actor, this.listing, this.amount);
  final ListingId listing;
  final int amount;
}

/// Lists a camel in الحراج. [declared]: offered as treated, the treatment
/// shown to every buyer, at her natural price, with no examination and no
/// fine (the owner's decision 15): only for an owner who bought her treated
/// without knowing and was told, never the one who had her treated.
final class ListForSale extends Command {
  const ListForSale(
    super.actor,
    this.camel,
    this.askPrice, {
    this.declared = false,
  });
  final CamelId camel;
  final int askPrice;
  final bool declared;
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
  const QuickSale(super.actor, this.camel, {this.declared = false});
  final CamelId camel;

  /// Sold as treated, declared (ListForSale.declared).
  final bool declared;
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

/// Orders [units] of a supply: bags of barley, bales of alfalfa or tanker
/// loads of water. It is paid on ordering and arrives a day later.
final class OrderSupply extends Command {
  const OrderSupply(
    super.actor,
    this.supply,
    this.units, {
    this.tanker = Tanker.large,
    this.now = false,
  });
  final Supply supply;
  final int units;

  /// Which tanker brings water (ignored for feed).
  final Tanker tanker;

  /// Brought now, on a day the herd went short (RushDelivery).
  final bool now;
}

final class SetShepherds extends Command {
  const SetShepherds(super.actor, this.count);
  final int count;
}

/// Builds a facility on the farm (paid now, done in Balance.buildDays).
final class BuildFacility extends Command {
  const BuildFacility(super.actor, this.facility, {this.now = false});
  final Facility facility;

  /// Finished now, for more (RushBuild).
  final bool now;
}

// ------------------------------------------------------------------ rush
// Finishing now, for more, what money can hurry in the real world (task T15,
// docs/proposals/rush_and_calendar.md section 2). Cash only, never on the
// merchant's account; refused below zero.

/// Finishes the earliest [facility] being built, now.
final class RushBuild extends Command {
  const RushBuild(super.actor, this.facility);
  final Facility facility;
}

/// Brings the water or the feed on its way now, on a day the herd went short
/// of it, and makes up what the day lacked (the note's 2.2).
final class RushDelivery extends Command {
  const RushDelivery(super.actor, this.kind);
  final StandingOrder kind;
}

/// Brings a camel bought today now, with a second driver, priced by the part
/// of the game's day left at [hour] (0 to 23). The hour is stamped by the
/// engine (EngineCore) from its own clock.
final class RushTruck extends Command {
  const RushTruck(super.actor, this.camel, {this.hour});
  final CamelId camel;
  final int? hour;
}

/// Turns a standing order on or off.
final class SetStandingOrder extends Command {
  const SetStandingOrder(super.actor, this.kind, {required this.on});
  final StandingOrder kind;
  final bool on;
}

/// Signs the vet's contract (the proxy's batch 4c): billed now for the rest
/// of the month, from cash only; every camel sick now treated.
final class SignVetContract extends Command {
  const SignVetContract(super.actor);
}

/// Treats every camel of his that is sick, each at the vet's own price, on
/// account as the vet is, till the account's limit (a large herd: one tap
/// for a thousand rows).
final class TreatAll extends Command {
  const TreatAll(super.actor);
}

/// Cancels it: it runs to the month's end, nothing refunded.
final class CancelVetContract extends Command {
  const CancelVetContract(super.actor);
}

/// How much of the nursing camels' milk their calves keep; the rest is
/// milked and sold each day.
final class SetCalfShare extends Command {
  const SetCalfShare(super.actor, this.share);
  final CalfShare share;
}

// --------------------------------------------------------------- contests

/// Registers [camels] in a round: one for a single round, the bull then
/// his offspring for الفحل وإنتاجه. After the festival's closing it is a
/// late entry, with its fee, until 72 hours before the round.
final class EnterRound extends Command {
  const EnterRound(super.actor, this.festival, this.round, this.camels);
  final FestivalId festival;
  final RoundId round;
  final List<CamelId> camels;
}

/// Withdraws the entry [camel] is in (until the day before its round).
/// After the closing its camels cannot be entered again at that festival.
final class WithdrawEntry extends Command {
  const WithdrawEntry(super.actor, this.festival, this.round, this.camel);
  final FestivalId festival;
  final RoundId round;
  final CamelId camel;
}

// --------------------------------------------------------------- cheating

/// Has a vet look at a camel for sale before buying: each treatment in her
/// may be found (GDD 7.1).
final class CheckListing extends Command {
  const CheckListing(super.actor, this.listing);
  final ListingId listing;
}

/// Has [camel] secretly treated ([strength] 1 light to 3 heavy): it looks
/// better on judging day, and may be found (GDD 7.1).
final class Tamper extends Command {
  const Tamper(super.actor, this.camel, this.kind, this.strength);
  final CamelId camel;
  final TamperKind kind;
  final int strength;
}

/// The secret treatment man's messages read (the phone's «المحادثات»
/// opened on his chat).
final class ReadMessages extends Command {
  const ReadMessages(super.actor);
}

/// The oldest [count] of the player's untold findings told (the phone has
/// said them).
final class MarkFindingsTold extends Command {
  const MarkFindingsTold(super.actor, this.count);
  final int count;
}

/// Money without limit for the owner's testing turned on or off (TestMoney):
/// sent only by the prototype's test meter, never by a screen of the game.
final class SetTestMoney extends Command {
  const SetTestMoney(super.actor, {required this.on});
  final bool on;
}

// --------------------------------------------------------------- falconry
// The hunting season (task T18, part A: docs/agents/T18_hunting_build.md).
// The falcons' room is a facility: BuildFacility(Facility.falconRoom).

/// Buys [kind] for the season open now, or the next to open (cash only:
/// the merchant's account is for the herd's feed, water and vet).
final class BuyPermit extends Command {
  const BuyPermit(super.actor, this.kind);
  final PermitKind kind;
}

/// Orders [units] of [gear] from «نادي الصقور» → «الطرح» (pigeons by the
/// bird, the camp's supplies by the day, the rest one each): paid now, cash
/// only, delivered to the farm as feed is (Balance.deliveryDays).
///
/// A tracker is ordered for one named [falcon] of his (each bird wears its
/// own, the answers' Q-27) and fitted to it when it comes.
final class OrderGear extends Command {
  const OrderGear(super.actor, this.gear, this.units, {this.falcon});
  final Gear gear;
  final int units;
  final FalconId? falcon;
}

/// Buys today's lot [lot] (FalconLot.key) at one of the three auctions, up
/// to his own ceiling [upTo] (the answers' Q-17 revised: no bidding game;
/// the price is not known before the hammer, as the design says «قيمته ما
/// تنعرف إلا بالمزاد»). If [upTo] reaches the hammer he pays the hammer;
/// else the lot goes to another bidder, its price told, gone for good. Cash
/// only (Q-18): a ceiling above his money is refused.
final class BuyFalcon extends Command {
  const BuyFalcon(super.actor, this.lot, this.upTo);
  final String lot;
  final int upTo;
}

/// Where a button was pressed, as the map says: on [ground], or off the
/// grounds ([off]); exactly one of the two.
final class HuntAt {
  const HuntAt.ground(Ground this.ground) : off = null;
  const HuntAt.off(HuntOff this.off) : ground = null;
  final Ground? ground;
  final HuntOff? off;
}

/// Goes out for falcons: [kind] to [ground] for [nights] (0: a day's
/// outing to a near ground, there and back inside the day), leaving at the
/// game's [minute] (stamped by the engine). The drive is game time: he is
/// at the ground at its working hour on the day the drive reaches it
/// (Trips.leg: the away call carries the days of a long drive). The farm
/// runs as on any day meanwhile.
final class StartTrip extends Command {
  const StartTrip(
    super.actor,
    this.kind,
    this.ground,
    this.nights, {
    this.minute,
  });
  final TripKind kind;
  final Ground ground;
  final int nights;
  final int? minute;
}

/// Breaks camp and drives home («فك المخيم وارجع»), at any time: the drive
/// home is game time as the drive out is.
final class EndTrip extends Command {
  const EndTrip(super.actor, {this.minute});
  final int? minute;
}

/// Moves the trapping camp to another trapping ground with the mobile tent.
final class MoveCamp extends Command {
  const MoveCamp(super.actor, this.ground);
  final Ground ground;
}

/// Looks for a falcon (with the binoculars if he has them) where he stands,
/// at the game's [minute] (stamped by the engine from its own clock).
final class SpotFalcon extends Command {
  const SpotFalcon(super.actor, this.at, {this.minute});
  final HuntAt at;
  final int? minute;
}

/// Releases [lure] at the falcon he has seen.
final class ReleaseLure extends Command {
  const ReleaseLure(super.actor, this.at, this.lure, {this.minute});
  final HuntAt at;
  final Lure lure;
  final int? minute;
}

/// Enters a trapped bird for tonight's trapping auction (the club checks it
/// and documents the trapping; the hammer falls tonight; no fee).
final class EnterTrapAuction extends Command {
  const EnterTrapAuction(super.actor, this.falcon);
  final FalconId falcon;
}

/// Keeps a trapped bird as his own (the club's check, the registration and
/// the passport; a free place in the room). Never offered for sale again.
final class KeepBird extends Command {
  const KeepBird(super.actor, this.falcon);
  final FalconId falcon;
}

/// Sets free a trapped peregrine he kept (the owner's item 19: from
/// February, or he keeps it; the window HuntBalance.releaseFrom/To).
final class ReleaseFalcon extends Command {
  const ReleaseFalcon(super.actor, this.falcon);
  final FalconId falcon;
}

/// Unhoods and casts [falcon] where he stands: on foot, or from the car
/// ([inCar], [moving]: a cast from a moving car is refused).
final class CastFalcon extends Command {
  const CastFalcon(
    super.actor,
    this.falcon,
    this.at, {
    this.inCar = false,
    this.moving = false,
    this.minute,
  });
  final FalconId falcon;
  final HuntAt at;
  final bool inCar;
  final bool moving;
  final int? minute;
}

/// Looks for a lost falcon (by the tracker's signal if it wears one).
final class SearchFalcon extends Command {
  const SearchFalcon(super.actor, this.falcon);
  final FalconId falcon;
}

/// الدعو: today's care for every falcon in the room (one tap).
final class CareFalcons extends Command {
  const CareFalcons(super.actor, {this.minute});
  final int? minute;
}
