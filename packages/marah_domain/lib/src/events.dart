import 'common/ids.dart';
import 'common/time.dart';

/// Everything that can happen in the world. Events carry values only; the
/// app turns each type into words. Notifications, the activity log and
/// (later) analytics and server sync all read the same events.
enum EventType {
  // money
  feedBilled,
  wagesPaid,
  cashNegative,
  // market
  camelBought,
  camelSold,
  bargainCountered,
  bargainRejected,
  listingCreated,
  listingCancelled,
  listingExpired,
  offerReceived,
  offerDeclined,
  // farm
  farmExpanded,
  shepherdsChanged,
  feedPlanChanged,
  camelRenamed,
  // health
  fellSick,
  treated,
  recovered,
  died,
  // breeding
  mated,
  pregnancyConfirmed,
  pregnancyFailed,
  calfBorn,
  calfLost,
  // contests
  seasonPlanned,
  registrationOpened,
  registrationClosingSoon,
  entered,
  withdrawn,
  disqualifiedSick,
  placed,
  festivalSummary,
}

class DomainEvent {
  const DomainEvent(
    this.type,
    this.day, {
    this.owner,
    this.camel,
    this.data = const {},
  });

  final EventType type;
  final GameDay day;

  /// Whose news this is; null for public world news.
  final OwnerId? owner;
  final CamelId? camel;

  /// Values for the message: names, amounts, ranks, ids. Primitives only.
  final Map<String, Object> data;

  Map<String, Object?> toJson() => {
    'type': type.name,
    'day': day.value,
    'owner': owner?.value,
    'camel': camel?.value,
    'data': data,
  };

  static DomainEvent fromJson(Map<String, Object?> j) => DomainEvent(
    EventType.values.byName(j['type']! as String),
    GameDay(j['day']! as int),
    owner: j['owner'] == null ? null : OwnerId(j['owner']! as String),
    camel: j['camel'] == null ? null : CamelId(j['camel']! as String),
    data: (j['data']! as Map<String, Object?>).map((k, v) => MapEntry(k, v!)),
  );

  @override
  String toString() => 'DomainEvent(${type.name}, day ${day.value}, $data)';
}
