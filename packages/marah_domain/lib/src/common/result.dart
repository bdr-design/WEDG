import '../events.dart';

/// Why a command was refused. The UI turns the code (and its params) into
/// words; the rules never produce display text.
enum ErrorCode {
  notFound,
  notYourCamel,
  notYourListing,
  ownListing,
  insufficientFunds,
  farmFull,
  invalidAmount,
  invalidName,
  sellerRefusesBargaining,
  bargainCountered,
  bargainRejected,
  alreadyListed,
  enteredInContest,
  notFemale,
  notMale,
  tooYoungToBreed,
  alreadyPregnant,
  awaitingPregnancyCheck,
  restingAfterCalving,
  sick,
  notBreedingSeason,
  bullResting,
  studUnavailable,
  notSick,
  registrationClosed,
  wrongCategory,
  wrongSex,
  wrongAgeClass,
  ownershipTooRecent,
  alreadyEnteredInFestival,
  listedForSale,
  roundOwnerLimit,
  notEntered,

  /// The owner is barred from festivals ({'through'}: the last season of
  /// the ban), or the camel is ([camelBanned]): GDD 7.1.
  banned,
  camelBanned,

  /// A crossbred camel: the festivals take pure ones only.
  crossbred,

  /// A group round's entry is not its size ({'size'}).
  wrongGroupSize,

  /// الفحل وإنتاجه: a camel that is not the bull's own offspring.
  notOffspring,

  /// جل takes a she-camel from her second calf ({'calvings'}).
  tooFewCalvings,

  /// The owner has his one فردي camel entered at the festival already (one
  /// camel in one فردي round, the owner's decision of 13 Nov 2026).
  oneFardiRound,

  /// A group round: not open to players yet (the owner, 13 Nov 2026).
  notYet,

  /// Withdrawn after the closing: its class was fixed then (GDD 7).
  scratched,

  /// The camel has that treatment already.
  alreadyTreated,

  /// The balance is below zero ({'debt'}): no camel bought and nothing
  /// built till it is paid; feed and water still come (the owner, 13 Nov
  /// 2026).
  inDebt,

  /// Feed, water or the vet's treatment past the account's limit with the
  /// merchant ({'needed', 'limit', 'owed'}): the player must sell (the
  /// owner, 13 Nov 2026).
  accountFull,

  /// The buyer or the broker found a treatment in her before paying: the
  /// sale is off and the seller fined ({'fine'}; the owner, 13 Nov 2026).
  saleRefused,

  /// Sold as declared treated, but she has no treatment her owner knows of
  /// (the owner's decision 15).
  nothingToDeclare,

  /// Sold as declared treated by the owner who had her treated himself:
  /// declaring it would be confessing it (decision 15; GDD 7.1).
  ownTreatment,

  /// An order would overfill the feed store or the water tank ({'room'}: units
  /// that still fit).
  storeFull,

  /// A facility the farm has all it can of, or is building
  /// (Facility.most).
  alreadyBuilt,

  /// The farm needs a facility first ({'facility'}: its name; a shepherd
  /// needs the caravan).
  needsFacility,

  /// A camel bought today, still on the truck to the farm (it comes
  /// tomorrow: Balance.camelTruckDays).
  onTheWay,

  /// A rush of water or feed on a day the herd was not short of it: the
  /// ordinary delivery comes before the herd drinks or eats tomorrow
  /// ({'supply'}).
  notShortToday,

  /// Nothing of that kind is on its way, or being built, to hurry.
  nothingToRush,

  /// A rushed truck's price was for an hour that has gone ({'hour'}): the
  /// price shown is the price paid, this hour or the one before.
  priceChanged,

  /// The vet's contract is signed already, or there is none to cancel.
  contractState,

  /// The calendar's jump cannot go: a day not ahead, more than a year, a
  /// camel sick and untreated without a vet's contract, or his round's day
  /// being told ({'reason'}).
  cannotJump,

  /// The hunting season refuses it ({'reason'}: a HuntRefusal's name, and
  /// what its words need): out of its season or hours, off its ground,
  /// without its permit, no room, a lot gone (task T18). The words are
  /// FalconLines.refusal's; nothing happens, and no fine follows (the
  /// owner's decision 4: the button warns and does not act).
  huntRefused,

  /// The engine hit a bug; the game was restored from the last save.
  internalError,

  /// The player's vet looked at this listing today already: the same day's
  /// looks agree (a fresh look is another day's).
  checkedToday,

  /// He bought her knowing of the treatment (his vet found it, or it was
  /// declared): the declared sale is only for one who did not know (the
  /// owner, 14 Nov 2026, item 12).
  knewWhenBought,
}

class DomainError {
  const DomainError(this.code, [this.params = const {}]);
  final ErrorCode code;

  /// Values the message needs, e.g. {'price': 150000} or {'days': 12}.
  final Map<String, Object> params;

  @override
  String toString() => 'DomainError(${code.name}, $params)';
}

/// Outcome of a command: the events it caused, or why it was refused.
/// A refusal can still carry events (a counter-offer is a refusal that
/// changes the asking price).
sealed class Result {
  const Result();
  bool get ok;
  List<DomainEvent> get events;
}

final class Ok extends Result {
  const Ok(this.events);
  @override
  final List<DomainEvent> events;
  @override
  bool get ok => true;
}

final class Err extends Result {
  const Err(this.error, [this.events = const []]);
  final DomainError error;
  @override
  final List<DomainEvent> events;
  @override
  bool get ok => false;
}
