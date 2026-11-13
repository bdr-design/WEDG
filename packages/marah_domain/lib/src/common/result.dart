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

  /// An order would overfill the feed store or the water tank ({'room'}: units
  /// that still fit).
  storeFull,

  /// A facility the farm has all it can of, or is building
  /// (Facility.most).
  alreadyBuilt,

  /// The farm needs a facility first ({'facility'}: its name; a shepherd
  /// needs the caravan).
  needsFacility,

  /// The engine hit a bug; the game was restored from the last save.
  internalError,
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
