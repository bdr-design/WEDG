/// Saudi riyals as whole numbers. Money is never a double.
extension type const Riyal(int value) implements Object {
  static const zero = Riyal(0);

  Riyal operator +(Riyal other) => Riyal(value + other.value);
  Riyal operator -(Riyal other) => Riyal(value - other.value);
  Riyal operator -() => Riyal(-value);
  Riyal times(num factor) => Riyal((value * factor).round());
  bool operator <(Riyal other) => value < other.value;
  bool operator <=(Riyal other) => value <= other.value;
  bool operator >(Riyal other) => value > other.value;
  bool operator >=(Riyal other) => value >= other.value;
  bool get isNegative => value < 0;
}

/// Rounds an amount to what people would quote at a camel market.
Riyal marketRound(double v) {
  if (v >= 1000000) return Riyal((v / 50000).round() * 50000);
  if (v >= 100000) return Riyal((v / 5000).round() * 5000);
  if (v >= 10000) return Riyal((v / 500).round() * 500);
  return Riyal((v / 100).round() * 100);
}
