import '../common/ids.dart';
import '../common/time.dart';
import '../model/game_state.dart';
import '../model/player.dart';

/// What the bank shows a ledger row as (the owner's approved design of 13 Nov
/// 2026, design/ui/phone_bank.jpg): each [LedgerCategory] but the opening
/// balance (not an income: said apart) and the broker's commission, which
/// goes with the sale it was taken from (the sale shows what reached the
/// player, as الحراج says «يوصلك … بعد السعي»).
enum MoneyKind {
  milk,
  sale,
  prize,
  purchase,
  transport,
  feed,
  water,
  wages,
  construction,
  vet,
  studFee,
}

/// Why a camel or a herd was trucked: the ledger keeps the transport row's
/// ref only (the camel, or the festival); the reason is read from the rows
/// written with it (a purchase of the same camel the same day, a stud's fee
/// the same day), else it is a festival's (there and back).
enum TripReason { purchase, mating, festival }

/// One kind of money in a month (or a day): its sum and what the screen
/// says under it.
class MoneyLine {
  const MoneyLine({
    required this.kind,
    required this.amount,
    required this.count,
    this.name,
    this.day,
    this.price,
    this.fee,
    this.trip,
    this.facilities = const [],
  });

  final MoneyKind kind;

  /// The net riyals (positive: money in); a sale less its commission.
  final int amount;

  /// How many: rows of the kind (sales for a sale, trips, orders, prizes,
  /// matings, treatments, buildings); 1 for the monthly milk and wages.
  final int count;

  /// One row's camel (bought, sold, trucked) or festival, by its name; null
  /// for several, or a festival the world has since forgotten.
  final String? name;

  /// One row's day.
  final GameDay? day;

  /// A sale: what the buyers paid, and the broker's commission (0 when the
  /// broker bought it himself).
  final int? price;
  final int? fee;

  /// One transport row's reason.
  final TripReason? trip;

  /// What was built (construction).
  final List<Facility> facilities;

  @override
  bool operator ==(Object other) =>
      other is MoneyLine &&
      other.kind == kind &&
      other.amount == amount &&
      other.count == count &&
      other.name == name &&
      other.day == day &&
      other.price == price &&
      other.fee == fee &&
      other.trip == trip &&
      _sameList(other.facilities, facilities);

  @override
  int get hashCode => Object.hash(
    kind,
    amount,
    count,
    name,
    day,
    price,
    fee,
    trip,
    Object.hashAll(facilities),
  );
}

/// One month of the bank: what came in, what went out, each kind, and the
/// biggest of them.
class MonthMoney {
  const MonthMoney({
    required this.month,
    required this.income,
    required this.spent,
    required this.lines,
  });

  /// 'YYYY-MM'.
  final String month;
  final int income;
  final int spent;

  /// Money in first (the biggest first), then money out (the biggest first).
  final List<MoneyLine> lines;

  int get net => income - spent;

  /// The kind that moved the most money, in or out (the main screen's line).
  MoneyLine get top {
    var best = lines.first;
    for (final l in lines) {
      if (l.amount.abs() > best.amount.abs()) best = l;
    }
    return best;
  }
}

/// The player's ledger read for the bank. Every figure is the ledger's own
/// sum: the opening balance plus every month's net is the cash.
class Money {
  const Money._();

  static String monthOf(GameDay d) {
    final t = d.date;
    return '${t.year}-${t.month.toString().padLeft(2, '0')}';
  }

  static MoneyKind? kindOf(LedgerCategory c) => switch (c) {
    LedgerCategory.opening => null,
    LedgerCategory.commission => MoneyKind.sale,
    LedgerCategory.milk => MoneyKind.milk,
    LedgerCategory.sale => MoneyKind.sale,
    LedgerCategory.prize => MoneyKind.prize,
    LedgerCategory.purchase => MoneyKind.purchase,
    LedgerCategory.transport => MoneyKind.transport,
    LedgerCategory.feed => MoneyKind.feed,
    LedgerCategory.water => MoneyKind.water,
    LedgerCategory.wages => MoneyKind.wages,
    LedgerCategory.construction => MoneyKind.construction,
    LedgerCategory.vet => MoneyKind.vet,
    LedgerCategory.studFee => MoneyKind.studFee,
  };

  /// The opening balance (every opening row: one in a game).
  static int opening(PlayerState p) => p.ledger
      .where((e) => e.category == LedgerCategory.opening)
      .fold(0, (n, e) => n + e.amount.value);

  /// Every month with money in or out, the newest first.
  ///
  /// Read for every snapshot, so the months before this one are kept once
  /// read (1.1 ms a snapshot at 1,128 rows otherwise, ten years of the long
  /// run): the ledger only ever grows at its end, by today's rows and this
  /// month's roll-up rows (Sim.pay, Sim.bill), so a past month never
  /// changes. Only this month's rows, at the end, are read again; a new
  /// month, or a ledger that did not grow from the one read (a game opened
  /// again), reads the whole ledger once.
  static List<MonthMoney> months(GameState s, OwnerId owner) {
    final p = s.players[owner]!;
    final ledger = p.ledger;
    final now = monthOf(s.world.day);
    var c = _past[ledger];
    if (c == null || c.month != now || ledger.length < c.rows) {
      final by = <String, List<LedgerEntry>>{};
      var rows = 0;
      for (final e in ledger) {
        final k = e.month ?? monthOf(e.day);
        if (k.compareTo(now) >= 0) break;
        rows++;
        if (e.category == LedgerCategory.opening) continue;
        (by[k] ??= []).add(e);
      }
      final keys = by.keys.toList()..sort((a, b) => b.compareTo(a));
      c = _Past(now, rows, [for (final k in keys) _month(s, p, k, by[k]!)]);
      _past[ledger] = c;
    }
    final current = [
      for (var i = c.rows; i < ledger.length; i++)
        if (ledger[i].category != LedgerCategory.opening) ledger[i],
    ];
    return [if (current.isNotEmpty) _month(s, p, now, current), ...c.list];
  }

  static final _past = Expando<_Past>('money months');

  /// One month, or null when it has no money in or out.
  static MonthMoney? month(GameState s, OwnerId owner, String month) {
    final p = s.players[owner]!;
    final rows = [
      for (final e in p.ledger)
        if (e.category != LedgerCategory.opening &&
            (e.month ?? monthOf(e.day)) == month)
          e,
    ];
    return rows.isEmpty ? null : _month(s, p, month, rows);
  }

  /// Today's money in and out by kind ([milkToday]: the day's milk, which
  /// the ledger keeps in its month's single row). Its net is
  /// GameView.todayNet.
  static ({int income, int spent}) today(
    PlayerState p,
    GameDay today,
    int milkToday,
  ) {
    final sums = <MoneyKind, int>{};
    // (from the end: the rows are in the order written, their days never
    // going back)
    for (final e in p.ledger.reversed) {
      if (e.day < today) break;
      if (e.day != today || e.category == LedgerCategory.milk) continue;
      final k = kindOf(e.category);
      if (k != null) sums[k] = (sums[k] ?? 0) + e.amount.value;
    }
    if (milkToday != 0) sums[MoneyKind.milk] = milkToday;
    var income = 0, spent = 0;
    for (final v in sums.values) {
      if (v > 0)
        income += v;
      else
        spent -= v;
    }
    return (income: income, spent: spent);
  }

  static MonthMoney _month(
    GameState s,
    PlayerState p,
    String month,
    List<LedgerEntry> rows,
  ) {
    final by = <MoneyKind, List<LedgerEntry>>{};
    for (final e in rows) {
      (by[kindOf(e.category)!] ??= []).add(e);
    }
    final lines = [
      for (final MapEntry(:key, :value) in by.entries) _line(s, p, key, value),
    ];
    final ins = lines.where((l) => l.amount > 0).toList()
      ..sort((a, b) => b.amount.compareTo(a.amount));
    final outs = lines.where((l) => l.amount <= 0).toList()
      ..sort((a, b) => a.amount.compareTo(b.amount));
    return MonthMoney(
      month: month,
      income: ins.fold(0, (n, l) => n + l.amount),
      spent: -outs.fold(0, (n, l) => n + l.amount),
      lines: [...ins, ...outs],
    );
  }

  static MoneyLine _line(
    GameState s,
    PlayerState p,
    MoneyKind kind,
    List<LedgerEntry> rows,
  ) {
    final amount = rows.fold(0, (n, e) => n + e.amount.value);
    // the rows that count (a sale's commission rides with its sale)
    final own = kind == MoneyKind.sale
        ? rows.where((e) => e.category == LedgerCategory.sale).toList()
        : rows;
    final one = own.length == 1 ? own.first : null;
    final w = s.world;
    String? camelName(String? ref) =>
        ref == null ? null : w.camels[CamelId(ref)]?.name;
    String? festivalName(String? ref) {
      if (ref == null) return null;
      return w.festivals[FestivalId(ref)]?.name;
    }

    TripReason? trip;
    String? name;
    switch (kind) {
      case MoneyKind.sale || MoneyKind.purchase:
        name = camelName(one?.ref);
      case MoneyKind.transport when one != null:
        trip = _trip(s, p, one);
        name = trip == TripReason.festival
            ? festivalName(one.ref)
            : camelName(one.ref);
      case MoneyKind.prize:
        name = festivalName(one?.ref);
      default:
        break;
    }
    final sale = kind == MoneyKind.sale;
    return MoneyLine(
      kind: kind,
      amount: amount,
      count: own.length,
      name: name,
      day: kind == MoneyKind.milk || kind == MoneyKind.wages ? null : one?.day,
      price: sale ? own.fold<int>(0, (n, e) => n + e.amount.value) : null,
      fee: sale
          ? -rows
                .where((e) => e.category == LedgerCategory.commission)
                .fold<int>(0, (n, e) => n + e.amount.value)
          : null,
      trip: trip,
      facilities: kind == MoneyKind.construction
          ? [
              for (final e in rows)
                if (Facility.values.where((f) => f.name == e.ref).firstOrNull
                    case final f?)
                  f,
            ]
          : const [],
    );
  }

  /// A transport row's reason, from the rows written with it: a purchase of
  /// the same camel that day (trucked home), else a camel of the player's
  /// (his female trucked to a stud: a camel a player has had is never
  /// forgotten by the world), else a festival's (there and back).
  static TripReason _trip(GameState s, PlayerState p, LedgerEntry t) {
    for (final e in p.ledger) {
      if (e.day == t.day &&
          e.category == LedgerCategory.purchase &&
          e.ref == t.ref) {
        return TripReason.purchase;
      }
    }
    final ref = t.ref;
    return ref != null && s.world.camels.containsKey(CamelId(ref))
        ? TripReason.mating
        : TripReason.festival;
  }
}

bool _sameList<T>(List<T> a, List<T> b) {
  if (a.length != b.length) return false;
  for (var i = 0; i < a.length; i++) {
    if (a[i] != b[i]) return false;
  }
  return true;
}

/// The months before [month] as read when the ledger had [rows] rows.
class _Past {
  _Past(this.month, this.rows, this.list);
  final String month;
  final int rows;
  final List<MonthMoney> list;
}
