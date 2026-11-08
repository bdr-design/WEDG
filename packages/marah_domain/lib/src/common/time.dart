/// Game time.
///
/// The world advances in whole game days. Day 0 is 1 January of the game's
/// base year; dates use the Gregorian calendar so seasons (breeding in the
/// cool months, contests from October to March, summer heat) fall where
/// they do in Saudi Arabia.
library;

extension type const GameDay(int value) implements Object {
  static final DateTime epoch = DateTime.utc(2026);

  factory GameDay.ofDate(DateTime d) =>
      GameDay(DateTime.utc(d.year, d.month, d.day).difference(epoch).inDays);

  DateTime get date => epoch.add(Duration(days: value));
  int get month => date.month;
  int get year => date.year;

  GameDay operator +(int days) => GameDay(value + days);
  GameDay operator -(int days) => GameDay(value - days);
  int daysSince(GameDay other) => value - other.value;
  bool operator <(GameDay o) => value < o.value;
  bool operator <=(GameDay o) => value <= o.value;
  bool operator >(GameDay o) => value > o.value;
  bool operator >=(GameDay o) => value >= o.value;
}

/// Where "today" comes from.
///
/// Offline the device clock drives the world: one real day is one game week
/// (see docs/adr/0001-time-model.md). Online the server owns the clock.
abstract interface class WorldClock {
  GameDay today();
}

/// Real-time clock at a fixed speed: [gameDaysPerRealDay] game days pass for
/// every real day, counted from [anchorReal] when the game day was
/// [anchorDay].
class RealTimeClock implements WorldClock {
  RealTimeClock({
    required this.anchorReal,
    required this.anchorDay,
    this.gameDaysPerRealDay = 7,
    DateTime Function()? now,
  }) : _now = now ?? DateTime.now;

  final DateTime anchorReal;
  final GameDay anchorDay;
  final int gameDaysPerRealDay;
  final DateTime Function() _now;

  /// Real time one game day takes.
  Duration get gameDayLength =>
      Duration(microseconds: Duration.microsecondsPerDay ~/ gameDaysPerRealDay);

  @override
  GameDay today() {
    final elapsed = _now().toUtc().difference(anchorReal.toUtc());
    if (elapsed.isNegative) return anchorDay; // device clock moved back
    return anchorDay + elapsed.inMicroseconds ~/ gameDayLength.inMicroseconds;
  }

  /// Real time left until the next game day starts.
  Duration untilNextDay() {
    final elapsed = _now().toUtc().difference(anchorReal.toUtc());
    if (elapsed.isNegative) return gameDayLength;
    final into = elapsed.inMicroseconds % gameDayLength.inMicroseconds;
    return Duration(microseconds: gameDayLength.inMicroseconds - into);
  }
}

/// A clock set by hand (tests, simulations, tools).
class ManualClock implements WorldClock {
  ManualClock(this.day);
  GameDay day;

  @override
  GameDay today() => day;
}
