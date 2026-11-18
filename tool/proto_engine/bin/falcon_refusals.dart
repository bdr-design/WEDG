// Every refusal line of the hunting season as the engine words it (FalconLines.refusal), each variant it gives, and
// where the phone or the map shows it; with the phone's own words for money. For the owner, beside the design sheet
// (design/ui/phone_falcon_engine.jpg): reviewer A's F4, the refusals with their screens.
//
//   dart run bin/falcon_refusals.dart > ../../design/ui/phone_falcon_refusals.txt      (in tool/proto_engine)
import 'dart:io';

import 'package:marah_domain/marah_domain.dart';

/// Where each refusal is shown (part C's map screens are named as the design has them: design/hunt/trip.cjs).
const where = <HuntRefusal, String>{
  HuntRefusal.routeClosed: 'نادي الصقور · المزاد: صف المزاد المسكّر',
  HuntRefusal.lotGone: 'مزاد الليلة · صفحة الطير',
  HuntRefusal.notALot: 'مزاد الليلة · صفحة الطير',
  HuntRefusal.noRoom: 'صفحة الطير بالمزاد، وطيرك المطروح («خله لك»)',
  HuntRefusal.roomFull: 'صفحة الطير بالمزاد، وطيرك المطروح («خله لك»)',
  HuntRefusal.permitHeld: 'تصريح الصيد',
  HuntRefusal.needsFalcon: 'تصريح الصيد · تصريح صقار',
  HuntRefusal.gearFull: 'نادي الصقور · الطرح: طلب العدة، وجهاز التتبع',
  HuntRefusal.onTrip: 'بطاقة «قبل ما تمشي»',
  HuntRefusal.notOnTrip: 'الخريطة · المخيم (الجزء C)',
  HuntRefusal.tooFar: 'بطاقة «قبل ما تمشي» · طلعة يوم',
  HuntRefusal.noSupplies: 'بطاقة «قبل ما تمشي»',
  HuntRefusal.noTent: 'الخريطة · نقل المخيم (الجزء C)',
  HuntRefusal.offGround: 'الخريطة · الطرح (الجزء C)',
  HuntRefusal.nearFarm: 'الخريطة · المقناص (الجزء C)',
  HuntRefusal.coast: 'الخريطة · المقناص (الجزء C)',
  HuntRefusal.reserve: 'الخريطة · المقناص (الجزء C)',
  HuntRefusal.notHuntingGround: 'الخريطة · المقناص (الجزء C)',
  HuntRefusal.outOfSeason: 'بطاقة «قبل ما تمشي»، والخريطة',
  HuntRefusal.noPermit: 'بطاقة «قبل ما تمشي»، والخريطة',
  HuntRefusal.night: 'الخريطة · الطرح (الجزء C)',
  HuntRefusal.notByDay: 'الخريطة · المقناص (الجزء C)',
  HuntRefusal.noQuarry: 'الخريطة · المقناص (الجزء C)',
  HuntRefusal.movingCar: 'الخريطة · المقناص من السيارة (الجزء C)',
  HuntRefusal.notReady: 'الخريطة · المقناص (الجزء C)',
  HuntRefusal.falconAway: 'الخريطة · المقناص (الجزء C)',
  HuntRefusal.flownOut: 'الخريطة · المقناص (الجزء C)',
  HuntRefusal.noLure: 'الخريطة · الطرح (الجزء C)',
  HuntRefusal.notHeld: 'طيرك المطروح',
  HuntRefusal.notKept: 'الدعو · تطلقه للبر',
  HuntRefusal.releaseMonths: 'الدعو · تطلقه للبر',
  HuntRefusal.notLost: 'الدعو · صقرك الضايع («دوّره»)',
  HuntRefusal.moult: 'الدعو · «ادعهم اليوم»',
  HuntRefusal.driving: 'التقويم · «نام لين الفجر» (الجزء C)',
  HuntRefusal.noTime: 'بطاقة «قبل ما تمشي» · طلعة يوم',
  HuntRefusal.oneGroundADay: 'الخريطة · الطرح والمقناص (الجزء C)',
  HuntRefusal.awayFromFarm: 'الدعو · «ادعهم اليوم»',
  HuntRefusal.noFalcons: 'الدعو · «ادعهم اليوم»',
  HuntRefusal.keptNotForSale: 'طيرك المطروح',
  HuntRefusal.hasTracker: 'الدعو · جهاز التتبع',
  HuntRefusal.searchedToday: 'الدعو · صقرك الضايع («دوّره»)',
  HuntRefusal.trackerComing: 'الدعو · جهاز التتبع',
  HuntRefusal.noTrip: 'التقويم · «نام لين الفجر» (الجزء C)',
  HuntRefusal.searchThere: 'الدعو · صقرك الضايع («دوّره»)',
  HuntRefusal.homeward: 'الخريطة · المخيم (الجزء C)',
  HuntRefusal.dayOuting: 'التقويم · «نام لين الفجر» (الجزء C)',
};

/// The variants a refusal's words change with.
List<Map<String, Object?>> variants(HuntRefusal r) => switch (r) {
  HuntRefusal.routeClosed => [
    for (final x in FalconRoute.values) {'route': x.name},
  ],
  HuntRefusal.outOfSeason || HuntRefusal.noPermit => [
    for (final k in PermitKind.values) {'kind': k.name},
  ],
  HuntRefusal.noLure => [
    for (final m in ['pigeon', 'pigeonNet', 'birdNet', null]) {'missing': m},
  ],
  // (only the room each can reach: the nets and the tent are one at most)
  HuntRefusal.gearFull => [
    for (final g in [
      Gear.pigeon,
      Gear.supplies,
      Gear.pigeonNet,
      Gear.mobileTent,
    ])
      for (final n in [0, 1, 2, 5, 14])
        if (n <= g.most) {'gear': g.name, 'room': n},
  ],
  _ => [const {}],
};

void main() {
  final out = StringBuffer()
    ..writeln(
      '# كلام الرفض بموسم الصيد، من المحرك (FalconLines.refusal)، ووين يطلع',
    )
    ..writeln('# السبب\tالمتغيّر\tالكلام\tوين يطلع');
  for (final r in HuntRefusal.values) {
    for (final v in variants(r)) {
      final line = FalconLines.refusal(
        DomainError(ErrorCode.huntRefused, {
          'reason': r.name,
          for (final e in v.entries)
            if (e.value case final x?) e.key: x,
        }),
      );
      final tag = v.entries
          .where((e) => e.value != null)
          .map((e) => '${e.key}=${e.value}')
          .join(',');
      out.writeln('${r.name}\t$tag\t$line\t${where[r] ?? '?'}');
    }
  }
  out
    ..writeln()
    ..writeln('# كلام الجوال للفلوس (phone.js fcRefusal، والتصريح بصفحته)')
    ..writeln(
      'inDebt\tbuyPermit\tعليك دين N ريال: التصريح نقد من رصيدك بس.\t'
      'تصريح الصيد',
    )
    ..writeln(
      'inDebt\torderGear\tعليك دين N ريال: العدة نقد من رصيدك بس.\t'
      'نادي الصقور · الطرح',
    )
    ..writeln(
      'inDebt\tbuyFalcon\tعليك دين N ريال: الصقر نقد من رصيدك بس.\t'
      'مزاد الليلة · صفحة الطير',
    )
    ..writeln(
      'insufficientFunds\t\tرصيدك ما يكفي: تبي N ريال من رصيدك.\t'
      'كل صفحة فيها دفع',
    )
    ..writeln(
      'insufficientFunds\tbuyPermit\tرصيدك ما يكفي: التصريح بـ N ريال\t'
      'تصريح الصيد',
    );
  // a refusal with no screen named fails the run: a new one must be placed
  final missing = HuntRefusal.values.where((r) => !where.containsKey(r));
  if (missing.isNotEmpty) throw StateError('no screen for $missing');
  stdout.writeln(out.toString().trimRight());
}
