/// Formatting helpers for Arabic UI text (Saudi riyal, dates, durations).
library;

const _arabicMonths = [
  'يناير',
  'فبراير',
  'مارس',
  'أبريل',
  'مايو',
  'يونيو',
  'يوليو',
  'أغسطس',
  'سبتمبر',
  'أكتوبر',
  'نوفمبر',
  'ديسمبر',
];

String monthName(int month) => _arabicMonths[month - 1];

/// Groups digits in thousands: 1250000 -> 1,250,000
String groupDigits(int value) {
  final negative = value < 0;
  final s = value.abs().toString();
  final buf = StringBuffer();
  for (var i = 0; i < s.length; i++) {
    if (i > 0 && (s.length - i) % 3 == 0) buf.write(',');
    buf.write(s[i]);
  }
  return negative ? '-${buf.toString()}' : buf.toString();
}

/// 1250000 -> "1,250,000 ريال"
String riyal(int amount) => '${groupDigits(amount)} ريال';

/// Short form for big amounts: 1250000 -> "1.25 مليون"
String riyalShort(int amount) {
  final a = amount.abs();
  final sign = amount < 0 ? '-' : '';
  if (a >= 1000000) {
    final m = a / 1000000;
    return '$sign${_trim(m)} مليون';
  }
  if (a >= 1000) {
    final k = a / 1000;
    return '$sign${_trim(k)} ألف';
  }
  return '$sign$a ريال';
}

String _trim(double v) {
  final s = v.toStringAsFixed(v >= 100 ? 0 : (v >= 10 ? 1 : 2));
  if (!s.contains('.')) return s;
  return s.replaceFirst(RegExp(r'\.?0+$'), '');
}

String formatDate(DateTime d) => '${d.day} ${monthName(d.month)} ${d.year}';

/// Human duration for ages / waits, e.g. "سنتين و3 شهور".
String formatAgeDays(int days) {
  if (days < 30) return days <= 1 ? 'يوم' : '$days يوم';
  final years = days ~/ 365;
  final months = (days % 365) ~/ 30;
  final parts = <String>[];
  if (years > 0) parts.add(_years(years));
  if (months > 0) parts.add(_months(months));
  return parts.join(' و');
}

String _years(int y) {
  if (y == 1) return 'سنة';
  if (y == 2) return 'سنتين';
  if (y <= 10) return '$y سنوات';
  return '$y سنة';
}

String _months(int m) {
  if (m == 1) return 'شهر';
  if (m == 2) return 'شهرين';
  if (m <= 10) return '$m شهور';
  return '$m شهر';
}

String formatDays(int days) {
  if (days == 1) return 'يوم';
  if (days == 2) return 'يومين';
  if (days <= 10) return '$days أيام';
  return '$days يوم';
}
