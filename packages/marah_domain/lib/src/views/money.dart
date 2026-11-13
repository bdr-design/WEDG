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

  /// A late festival entry's fee (GDD 7).
  entryFee,

  /// The player's own spending on a secret treatment (GDD 7.1).
  tampering,

  /// A fine for a treatment found (GDD 7.1).
  fine,
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
    LedgerCategory.entryFee => MoneyKind.entryFee,
    LedgerCategory.tampering => MoneyKind.tampering,
    LedgerCategory.fine => MoneyKind.fine,
  };

  /// The opening balance (every opening row: one in a game).
  static int opening(PlayerState p) => p.ledger
      .where((e) => e.category == LedgerCategory.opening)
      .fold(0, (n, e) => n + e.amount.value);

  /// Every month with money in or out, the newest first.
  ///
  /// Read for every snapshot, so the months before this one are kept once
  /// read, by their sums, counts and refs (1.1 ms a snapshot at 1,128 rows
  /// otherwise, ten years of the long run): the ledger only ever grows at its
  /// end, by today's rows and this month's roll-up rows (Sim.pay, Sim.bill;
  /// checkInvariants holds every writer to it), so a past month's rows never
  /// change. Only this month's rows, at the end, are read again; a month
  /// that ends adds its rows to the kept ones, and a ledger that is not the
  /// one read grown at its end (a game opened again) is read whole once. The names (a camel's, a festival's) are looked up as the
  /// months are given, so a camel renamed or a festival the world has
  /// forgotten reads the same here and in the month opened.
  static List<MonthMoney> months(GameState s, OwnerId owner) {
    final p = s.players[owner]!;
    final c = _kept(s, p);
    final current = _currentRows(p, c);
    return [
      if (current.isNotEmpty) _named(s, _sums(s, c.month, current)),
      for (final m in c.list) _named(s, m),
    ];
  }

  /// One month, or null when it has no money in or out: a past month from
  /// the kept ones, this month from its rows at the ledger's end.
  static MonthMoney? month(GameState s, OwnerId owner, String month) {
    final p = s.players[owner]!;
    final c = _kept(s, p);
    if (month == c.month) {
      final current = _currentRows(p, c);
      return current.isEmpty ? null : _named(s, _sums(s, month, current));
    }
    final m = c.byMonth[month];
    return m == null ? null : _named(s, m);
  }

  static final _past = Expando<_Past>('money months');

  /// Ledger rows read into the kept months so far (for the tests: a read
  /// that keeps them reads none; a month that ends reads its own rows only).
  static int keptRowsRead = 0;

  /// The months before this one, read again when the month has turned or the
  /// ledger is not the one read grown at its end.
  static _Past _kept(GameState s, PlayerState p) {
    final ledger = p.ledger;
    final now = monthOf(s.world.day);
    var c = _past[ledger];
    // the ledger read before, grown at its end (the same row where the kept
    // part ended, nothing after it from before that month)
    final grown =
        c != null &&
        ledger.length >= c.rows &&
        (c.rows == 0 || identical(ledger[c.rows - 1], c.last)) &&
        (ledger.length == c.rows || _key(ledger.last).compareTo(c.month) >= 0);
    if (grown && c.month == now) return c;
    if (!grown || c.month.compareTo(now) > 0) {
      c = _Past('', 0, null, const [], const {});
    }
    // the months that have ended since: their rows added to the kept ones
    final by = <String, List<LedgerEntry>>{};
    var rows = c.rows;
    for (var i = c.rows; i < ledger.length; i++) {
      final e = ledger[i];
      final k = _key(e);
      if (k.compareTo(now) >= 0) break;
      rows++;
      keptRowsRead++;
      if (e.category == LedgerCategory.opening) continue;
      (by[k] ??= []).add(e);
    }
    final keys = by.keys.toList()..sort((a, b) => b.compareTo(a));
    final list = [for (final k in keys) _sums(s, k, by[k]!), ...c.list];
    final kept = _Past(now, rows, rows == 0 ? null : ledger[rows - 1], list, {
      for (final m in list) m.month: m,
    });
    _past[ledger] = kept;
    return kept;
  }

  static String _key(LedgerEntry e) => e.month ?? monthOf(e.day);

  static List<LedgerEntry> _currentRows(PlayerState p, _Past c) => [
    for (var i = c.rows; i < p.ledger.length; i++)
      if (p.ledger[i].category != LedgerCategory.opening) p.ledger[i],
  ];

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
    // going back: checkInvariants)
    for (final e in p.ledger.reversed) {
      if (e.day < today) break;
      if (e.day != today || e.category == LedgerCategory.milk) continue;
      final k = kindOf(e.category);
      if (k != null) sums[k] = (sums[k] ?? 0) + e.amount.value;
    }
    if (milkToday != 0) sums[MoneyKind.milk] = milkToday;
    var income = 0, spent = 0;
    for (final v in sums.values) {
      if (v > 0) {
        income += v;
      } else {
        spent -= v;
      }
    }
    return (income: income, spent: spent);
  }

  /// A month's rows as sums, counts and refs, its kinds in the screen's order
  /// (money in, the biggest first; then money out, the biggest first).
  static _MonthSums _sums(GameState s, String month, List<LedgerEntry> rows) {
    final by = <MoneyKind, List<LedgerEntry>>{};
    for (final e in rows) {
      (by[kindOf(e.category)!] ??= []).add(e);
    }
    final kinds = [
      for (final MapEntry(:key, :value) in by.entries)
        _kindSums(s, rows, key, value),
    ];
    final ins = kinds.where((k) => k.amount > 0).toList()
      ..sort((a, b) => b.amount.compareTo(a.amount));
    final outs = kinds.where((k) => k.amount <= 0).toList()
      ..sort((a, b) => a.amount.compareTo(b.amount));
    return _MonthSums(month, [...ins, ...outs]);
  }

  static _KindSums _kindSums(
    GameState s,
    List<LedgerEntry> month,
    MoneyKind kind,
    List<LedgerEntry> rows,
  ) {
    // the rows that count (a sale's commission rides with its sale)
    final own = kind == MoneyKind.sale
        ? rows.where((e) => e.category == LedgerCategory.sale).toList()
        : rows;
    final one = own.length == 1 ? own.first : null;
    final sale = kind == MoneyKind.sale;
    return _KindSums(
      kind: kind,
      amount: rows.fold(0, (n, e) => n + e.amount.value),
      count: own.length,
      ref: one?.ref,
      day: kind == MoneyKind.milk || kind == MoneyKind.wages ? null : one?.day,
      price: sale ? own.fold<int>(0, (n, e) => n + e.amount.value) : null,
      fee: sale
          ? -rows
                .where((e) => e.category == LedgerCategory.commission)
                .fold<int>(0, (n, e) => n + e.amount.value)
          : null,
      trip: kind == MoneyKind.transport && one != null
          ? _trip(s, month, one)
          : null,
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

  /// A month as the screens show it, its names looked up now.
  static MonthMoney _named(GameState s, _MonthSums m) {
    final w = s.world;
    String? camelName(String? ref) =>
        ref == null ? null : w.camels[CamelId(ref)]?.name;
    String? festivalName(String? ref) =>
        ref == null ? null : w.festivals[FestivalId(ref)]?.name;
    var income = 0, spent = 0;
    final lines = <MoneyLine>[];
    for (final k in m.kinds) {
      if (k.amount > 0) {
        income += k.amount;
      } else {
        spent -= k.amount;
      }
      lines.add(
        MoneyLine(
          kind: k.kind,
          amount: k.amount,
          count: k.count,
          name: switch (k.kind) {
            MoneyKind.sale || MoneyKind.purchase => camelName(k.ref),
            MoneyKind.transport =>
              k.trip == TripReason.festival
                  ? festivalName(k.ref)
                  : camelName(k.ref),
            MoneyKind.prize => festivalName(k.ref),
            _ => null,
          },
          day: k.day,
          price: k.price,
          fee: k.fee,
          trip: k.trip,
          facilities: k.facilities,
        ),
      );
    }
    return MonthMoney(
      month: m.month,
      income: income,
      spent: spent,
      lines: lines,
    );
  }

  /// A transport row's reason, from the rows of its month written with it: a
  /// purchase of the same camel that day (trucked home), else a camel of the
  /// player's (his female trucked to a stud: a camel a player has had is
  /// never forgotten by the world), else a festival's (there and back).
  static TripReason _trip(GameState s, List<LedgerEntry> month, LedgerEntry t) {
    for (final e in month) {
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

/// The months before [month] as read when the ledger had [rows] rows, the
/// last of them [last].
class _Past {
  _Past(this.month, this.rows, this.last, this.list, this.byMonth);
  final String month;
  final int rows;
  final LedgerEntry? last;
  final List<_MonthSums> list;
  final Map<String, _MonthSums> byMonth;
}

/// A month's kinds by their sums, counts and refs (no names: looked up as
/// the month is given).
class _MonthSums {
  _MonthSums(this.month, this.kinds);
  final String month;
  final List<_KindSums> kinds;
}

class _KindSums {
  const _KindSums({
    required this.kind,
    required this.amount,
    required this.count,
    required this.ref,
    required this.day,
    required this.price,
    required this.fee,
    required this.trip,
    required this.facilities,
  });

  final MoneyKind kind;
  final int amount;
  final int count;
  final String? ref;
  final GameDay? day;
  final int? price;
  final int? fee;
  final TripReason? trip;
  final List<Facility> facilities;
}
