/// Sex of a camel. Arabic usage: ناقة (female), جمل / فحل (male).
enum Sex {
  female('ناقة'),
  male('جمل');

  const Sex(this.label);
  final String label;
}

/// Colour families (الفئات) that mazayen contests are split by.
///
/// [baseDemand] scales market prices for the family.
enum ColorCategory {
  majaheem('مجاهيم', 'سود داكنة اللون، أكبرها حجمًا، وهي إبل الجنوب والوسط',
      baseDemand: 1.15),
  maghateer('مغاتير', 'بيض ناصعة، الوبر أبيض والجلد فاتح',
      baseDemand: 1.10),
  wodh('وضح', 'بيض اللون مع سواد في الجلد والعين وأطراف الخشم',
      baseDemand: 1.05),
  sofr('صفر', 'صفرة ذهبية فاتحة في الوبر',
      baseDemand: 1.00),
  homr('حمر', 'حمرة بنية مائلة للبرتقالي',
      baseDemand: 0.95),
  shoal('شعل', 'بني محمرّ داكن، أطراف الوبر أغمق',
      baseDemand: 0.95),
  shoqh('شقح', 'لون فاتح بين البياض والحمرة، رمادي محمرّ',
      baseDemand: 0.90);

  const ColorCategory(this.label, this.description,
      {required this.baseDemand});

  final String label;
  final String description;
  final double baseDemand;
}

/// Age classes by completed years, with the Gulf names used in contest
/// rounds (أشواط). [minYears] is inclusive, [maxYears] exclusive.
enum AgeClass {
  hwar('حوار', 'حوار', 0, 1),
  mafrood('مفرود', 'مفرودة', 1, 2),
  laqi('لقي', 'لقية', 2, 3),
  haq('حق', 'حقة', 3, 4),
  jatha('جذع', 'جذعة', 4, 5),
  thani('ثني', 'ثنية', 5, 6),
  rubaa('رباع', 'رباعية', 6, 7),
  sedees('سديس', 'سديسة', 7, 8),
  mature('فاطر', 'فاطر', 8, 99);

  const AgeClass(this.male, this.female, this.minYears, this.maxYears);

  final String male;
  final String female;
  final int minYears;
  final int maxYears;

  String labelFor(Sex sex) => sex == Sex.female ? female : male;

  static AgeClass fromDays(int ageDays) {
    final years = ageDays ~/ 365;
    return AgeClass.values.firstWhere(
      (a) => years >= a.minYears && years < a.maxYears,
      orElse: () => AgeClass.mature,
    );
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
