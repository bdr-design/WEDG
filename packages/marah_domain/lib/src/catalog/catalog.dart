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

/// Body features the judges score (معايير المزاين, GDD 5.3), by the approved
/// weights (the owner, 12 Nov 2026): head and neck 25, hump and top line 20,
/// forehand 15, hindquarters 10 and overall look 30, out of 100. How a region's
/// share is split between its features is a game choice. [matureAtYears] is
/// when the feature is fully developed. Where the مجاهيم and مغاتير standards
/// differ (the ears, the bone and feet, the withers and back), [describe]
/// says what each family is judged against.
enum Trait {
  head(
    'الرأس',
    'كِبر الرأس وعرضه وتناسقه مع الجسم',
    0.07,
    5,
    JudgedRegion.headNeck,
  ),
  nose('الخشم', 'خشم كبير مرتفع', 0.05, 5, JudgedRegion.headNeck),
  lips('الشفايف', 'شفة طويلة متدلية', 0.05, 5, JudgedRegion.headNeck),
  ears('الأذن', 'طول الأذن ووقفتها حسب الفئة', 0.03, 3, JudgedRegion.headNeck),
  neck('الرقبة', 'رقبة طويلة جرداء', 0.05, 6, JudgedRegion.headNeck),
  hump('السنام', 'موضع السنام وارتفاعه وتناسقه', 0.12, 6, JudgedRegion.top),
  back('الغارب والظهر', 'الغارب والظهر حسب الفئة', 0.08, 6, JudgedRegion.top),
  fore(
    'المقدمة',
    'الصدر والكتف والقوائم الأمامية والخف',
    0.15,
    5,
    JudgedRegion.fore,
  ),
  hind('المؤخرة', 'الورك والقوائم الخلفية', 0.10, 5, JudgedRegion.hind),
  stance(
    'الوقفة',
    'الهيبة والشموخ وطريقة الوقوف',
    0.15,
    5,
    JudgedRegion.overall,
  ),
  coat(
    'اللون والوبر',
    'صفاء اللون ونقاوته داخل الفئة',
    0.15,
    2,
    JudgedRegion.overall,
  );

  const Trait(
    this.label,
    this.description,
    this.weight,
    this.matureAtYears,
    this.region,
  );

  final String label;
  final String description;
  final double weight;
  final int matureAtYears;
  final JudgedRegion region;

  /// What a camel of [family] is judged against for this feature (GDD 5.3).
  String describe(ColorCategory family) => switch ((this, family.isMaghateer)) {
    (ears, false) => 'أذن طويلة مرفوعة لقدام',
    (ears, true) => 'أذن قصيرة مرجوعة لورا',
    (back, true) => 'غارب بارز، وظهر ينحدر للورك، وطول',
    (fore || hind, false) => '$description، وعظم ثقيل وخف عريض مدور',
    _ => description,
  };
}

/// The regions the approved weights are given for (GDD 5.3), out of 100.
enum JudgedRegion {
  headNeck('الرأس والرقبة', 25),
  top('السنام وأعلى الجسم', 20),
  fore('المقدمة', 15),
  hind('المؤخرة', 10),
  overall('المظهر العام', 30);

  const JudgedRegion(this.label, this.points);
  final String label;
  final int points;
}

/// Common camel illnesses in the Kingdom (GDD 5.5, research-realism section 6).
/// [contagious] spreads to pen-mates when untreated; [youngOnly] / [femaleOnly]
/// restrict who gets it; [peakMonths] are when it is commonest (real: mange
/// and ringworm with the winter's crowding, camelpox from July to September).
/// Treatment costs and days are game choices (vet costs have no source).
enum Illness {
  mange(
    'جرب',
    contagious: true,
    treatMin: 300,
    treatMax: 900,
    recoverDays: 21,
    peakMonths: {11, 12, 1, 2, 3},
  ),
  ringworm(
    'القراع',
    contagious: true,
    treatMin: 200,
    treatMax: 600,
    recoverDays: 28,
    peakMonths: {11, 12, 1, 2, 3},
  ),
  camelpox(
    'الجدري',
    contagious: true,
    treatMin: 300,
    treatMax: 900,
    recoverDays: 21,
    peakMonths: {7, 8, 9},
  ),
  brucellosis(
    'البروسيلا',
    femaleOnly: true,
    treatMin: 1500,
    treatMax: 3000,
    recoverDays: 60,
  ),
  mineralDeficiency(
    'نقص السيلينيوم والنحاس',
    treatMin: 150,
    treatMax: 400,
    recoverDays: 30,
  ),
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
    this.peakMonths = const {},
  });

  final String label;
  final Set<int> peakMonths;
  final bool contagious;
  final bool youngOnly;
  final bool femaleOnly;
  final int treatMin;
  final int treatMax;
  final int recoverDays;
}
