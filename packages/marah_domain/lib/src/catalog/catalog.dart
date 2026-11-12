/// Sex of a camel. Arabic usage: ناقة (female), جمل / فحل (male).
enum Sex {
  female('ناقة'),
  male('جمل');

  const Sex(this.label);
  final String label;
}

/// Colour families (الفئات): the festival's six (GDD 2 and 5.1, research-realism
/// section 1). مغاتير is the umbrella name for the five light ones, not a class
/// of its own (the owner, 12 Nov 2026): [isMaghateer].
///
/// [baseDemand] (balance) scales market prices for the family.
enum ColorCategory {
  majaheem(
    'مجاهيم',
    'سود بدرجات، والغرابي أفخرها. إطار كبير وعظم ثقيل',
    baseDemand: 1.15,
  ),
  wodh('وضح', 'أبيض ناصع، أرقى المغاتير', baseDemand: 1.05),
  shoqh('شقح', 'أبيض أقل من الوضح، بين الوضح والشعل', baseDemand: 0.90),
  shoal('شعل', 'خليط أحمر وأشقر', baseDemand: 0.95),
  sofr('صفر', 'لون الرمل أو الدبس، وبر كثيف', baseDemand: 1.00),
  homr('حمر', 'محمرّة، متوسطة الحجم', baseDemand: 0.95);

  const ColorCategory(this.label, this.description, {required this.baseDemand});

  final String label;
  final String description;
  final double baseDemand;

  /// One of the five light colours the name مغاتير covers.
  bool get isMaghateer => this != majaheem;
}

/// Age classes (الأسنان) with their Gulf names (GDD 5.2, research-realism
/// section 2; the owner chose حق before لقي, 12 Nov 2026). [minMonths] is
/// inclusive, [maxMonths] exclusive. Names the sources give for one sex only
/// are used for both (game choice): مخلول, فاطر, and ناب for a female past 20.
enum AgeClass {
  hwar('حوار', 'حوارة', 0, 6),
  makhlool('مخلول', 'مخلول', 6, 12),
  mafrood('مفرود', 'مفرودة', 12, 24),
  haq('حق', 'حقة', 24, 36),
  laqi('لقي', 'لقية', 36, 48),
  jatha('جذع', 'جذعة', 48, 60),
  thani('ثني', 'ثنية', 60, 72),
  rubaa('رباع', 'رباعية', 72, 84),
  sedees('سديس', 'سديسة', 84, 96),
  fater('فاطر', 'فاطر', 96, 120),
  naab('عود', 'ناب', 120, 240),
  harish('هرش', 'ناب', 240, 1 << 20);

  const AgeClass(this.male, this.female, this.minMonths, this.maxMonths);

  final String male;
  final String female;
  final int minMonths;
  final int maxMonths;

  /// The first day of the class (days are counted as 365 a year).
  int get minDays => (minMonths * 365 + 11) ~/ 12;

  String labelFor(Sex sex) => sex == Sex.female ? female : male;

  static AgeClass fromDays(int ageDays) {
    for (var i = values.length - 1; i > 0; i--) {
      if (ageDays >= values[i].minDays) return values[i];
    }
    return hwar;
  }
}

/// Body features the judges score (معايير المزاين). [weight] is the share of
/// the total score; [matureAtYears] is when the feature is fully developed.
enum Trait {
  head('الرأس', 'كِبر الرأس وعرضه وتناسقه مع الجسم', 0.16, 5),
  nose('الخشم', 'ارتفاع الخشم وانحناؤه (الخشم المرتفع)', 0.12, 5),
  lips('الشفايف', 'تدلي الشفة السفلى (الهدل) وطول المشفر', 0.10, 5),
  ears('الأذان', 'صغر الأذنين وانتصابهما وتقاربهما', 0.08, 3),
  neck('الرقبة', 'طول الرقبة وغلظها عند الكتف', 0.14, 6),
  hump('السنام', 'موضع السنام للخلف وارتفاعه وتناسقه', 0.12, 6),
  back('الظهر', 'استواء الظهر وطوله', 0.07, 6),
  legs('القوائم', 'طول القوائم واستقامتها وغلظ الركب', 0.09, 5),
  stance('الوقفة', 'الهيبة والشموخ وطريقة الوقوف', 0.06, 5),
  coat('اللون', 'صفاء اللون ونقاوته داخل الفئة', 0.06, 2);

  const Trait(this.label, this.description, this.weight, this.matureAtYears);

  final String label;
  final String description;
  final double weight;
  final int matureAtYears;
}

/// Common camel illnesses in the Arabian Peninsula. [contagious] spreads to
/// pen-mates when untreated; [youngOnly] / [femaleOnly] restrict who gets it.
enum Illness {
  mange('جرب', contagious: true, treatMin: 300, treatMax: 900, recoverDays: 21),
  pneumonia('التهاب رئوي', treatMin: 600, treatMax: 1800, recoverDays: 10),
  calfDiarrhea(
    'إسهال الحيران',
    youngOnly: true,
    treatMin: 250,
    treatMax: 700,
    recoverDays: 6,
  ),
  lameness('عرج', treatMin: 300, treatMax: 1200, recoverDays: 14),
  mastitis(
    'التهاب الضرع',
    femaleOnly: true,
    treatMin: 400,
    treatMax: 1200,
    recoverDays: 9,
  ),
  trypanosomiasis(
    'الدباب (المثقبيات)',
    treatMin: 700,
    treatMax: 2000,
    recoverDays: 18,
  );

  const Illness(
    this.label, {
    this.contagious = false,
    this.youngOnly = false,
    this.femaleOnly = false,
    required this.treatMin,
    required this.treatMax,
    required this.recoverDays,
  });

  final String label;
  final bool contagious;
  final bool youngOnly;
  final bool femaleOnly;
  final int treatMin;
  final int treatMax;
  final int recoverDays;
}
