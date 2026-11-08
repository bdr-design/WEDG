/// Money movements of the player's farm, so every riyal is traceable.
enum LedgerCategory {
  purchase('شراء حلال'),
  sale('بيع حلال'),
  feed('أعلاف'),
  wages('رواتب الرعاة'),
  vet('بيطري'),
  transport('نقل'),
  prize('جوائز'),
  studFee('أجرة فحل'),
  studIncome('دخل الفحل'),
  commission('سعي الدلال'),
  construction('إنشاءات'),
  other('أخرى');

  const LedgerCategory(this.label);
  final String label;

  bool get isIncome =>
      this == sale || this == prize || this == studIncome;
}

class LedgerEntry {
  LedgerEntry({
    required this.day,
    required this.amount,
    required this.category,
    required this.note,
  });

  final int day;

  /// Positive = income, negative = expense.
  final int amount;
  final LedgerCategory category;
  final String note;

  Map<String, dynamic> toJson() => {
        'd': day,
        'a': amount,
        'c': category.name,
        'n': note,
      };

  factory LedgerEntry.fromJson(Map<String, dynamic> j) => LedgerEntry(
        day: j['d'] as int,
        amount: j['a'] as int,
        category: LedgerCategory.values.byName(j['c'] as String),
        note: j['n'] as String,
      );
}

enum NewsKind { info, good, warning, bad, market, contest, birth }

/// One line in the farm's activity log (what happened on which day).
class NewsItem {
  NewsItem({
    required this.day,
    required this.kind,
    required this.text,
    this.camelId,
  });

  final int day;
  final NewsKind kind;
  final String text;
  final String? camelId;

  Map<String, dynamic> toJson() => {
        'd': day,
        'k': kind.name,
        't': text,
        if (camelId != null) 'c': camelId,
      };

  factory NewsItem.fromJson(Map<String, dynamic> j) => NewsItem(
        day: j['d'] as int,
        kind: NewsKind.values.byName(j['k'] as String),
        text: j['t'] as String,
        camelId: j['c'] as String?,
      );
}
