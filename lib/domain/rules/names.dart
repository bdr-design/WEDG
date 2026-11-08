import '../../core/rng.dart';

/// Camel names in common Gulf usage. Owners name camels after beauty,
/// gazelles, rain and pride; famous mazayen camels carry names like these.
const femaleNames = [
  'ظبية', 'غزيّل', 'مزنة', 'شاهة', 'ريم', 'هيلة', 'نورة', 'دانة', 'جوهرة',
  'مزيونة', 'صيته', 'شيخة', 'عنود', 'غلا', 'بشاير', 'هدلا', 'شمعة', 'ملحة',
  'سمحة', 'فتنة', 'نجمة', 'الغرّا', 'الهيلا', 'وضحى', 'مرية', 'زينة', 'حمدة',
  'ضيّة', 'سارة', 'نوف', 'مها', 'وعد', 'غيمة', 'صبحة', 'العذبة', 'شعاع',
  'منيرة', 'دلال', 'غالية', 'الفريدة', 'لطيفة', 'طيبة', 'الحرّة', 'رشا',
];

const maleNames = [
  'شاهين', 'مدهش', 'شبل', 'صقر', 'سلطان', 'فارس', 'ريّان', 'نمر', 'بركان',
  'هزّاع', 'مطلق', 'زعيم', 'شامخ', 'قايد', 'سيف', 'ذيب', 'مشعان', 'غازي',
  'ضاري', 'منصور', 'نايف', 'راشد', 'فهّاد', 'ماجد', 'شاهر', 'معزّي', 'حمدان',
  'عقاب', 'هادي', 'الوافي', 'الكاسر', 'نوّاف', 'مهاب', 'رعد', 'المرزوق', 'جسّار',
];

/// Owner nicknames used for other camel owners in the world (kunya only,
/// no family names, so no real family is implied).
const ownerNames = [
  'أبو فهد', 'أبو سعد', 'أبو ناصر', 'أبو تركي', 'أبو مشعل', 'أبو عبدالله',
  'أبو خالد', 'أبو سلطان', 'أبو ماجد', 'أبو فيصل', 'أبو بندر', 'أبو نايف',
  'أبو راشد', 'أبو عبدالعزيز', 'أبو محمد', 'أبو سلمان', 'أبو هزّاع',
  'أبو مطلق', 'أبو حمد', 'أبو عيد', 'أبو صالح', 'أبو منصور', 'أبو زياد',
  'أبو مساعد',
];

String randomCamelName(Rng rng, {required bool female}) =>
    rng.pick(female ? femaleNames : maleNames);

/// Microchip numbers follow the 15-digit ISO 11784 shape (country 682 = KSA).
String randomChipNumber(Rng rng) {
  final buf = StringBuffer('682');
  for (var i = 0; i < 12; i++) {
    buf.write(rng.nextInt(10));
  }
  return buf.toString();
}
