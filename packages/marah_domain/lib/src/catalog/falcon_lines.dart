// Every line of the hunting season a player can read that the engine owns
// (task T18): the warnings of a refused command (the owner's decision 4: the
// button warns, says why, and does not act), the lines of a bird released,
// the bank's kinds. Taken word for word from the approved design where it
// has them (design/ui/phone_falcon.cjs, design/hunt/trip.cjs, docs/agents/
// proxy_decisions.md batch 3); the others are ours, listed in the task's
// report for the owner's eye.
import '../common/result.dart';
import 'falconry.dart';

/// Why the hunting season refused a command: DomainError(huntRefused,
/// {'reason': name, ...}).
enum HuntRefusal {
  /// The auction is not open today ({'route'}).
  routeClosed,

  /// The lot is sold (to him or to another).
  lotGone,

  /// No lot of today's by that key (a stale or a malformed one).
  notALot,

  /// No falcons' room on the farm yet.
  noRoom,

  /// The falcons' room is full (HuntBalance.roomHolds).
  roomFull,

  /// The permit is held for that season already ({'kind'}).
  permitHeld,

  /// The hunting permit wants a falcon with its passport in his name.
  needsFalcon,

  /// More gear than he can hold ({'room'}: what still fits).
  gearFull,

  /// On a trip already; or not on one (nor at that ground).
  onTrip,
  notOnTrip,

  /// A day's outing to a ground too far to be back the same evening.
  tooFar,

  /// A trip of days with no camp supplies.
  noSupplies,

  /// Moving the camp needs the mobile tent.
  noTent,

  /// The net off a trapping ground (decision 4; trip_20).
  offGround,

  /// Hunting by the farm and around it (trip_21), on the coast strip, in a
  /// reserve; a falcon cast on a trapping ground (not a hunting ground).
  nearFarm,
  coast,
  reserve,
  notHuntingGround,

  /// Out of the season ({'kind'}: hunting or trapping), or without its
  /// permit ({'kind'}).
  outOfSeason,
  noPermit,

  /// Trapping at night; hunting outside its hours.
  night,
  notByDay,

  /// No quarry lawful there today (Q-10).
  noQuarry,

  /// A cast from a moving car (Q-26).
  movingCar,

  /// The falcon is not ready (its الدعو not done), is lost, has flown its
  /// flights today, or is not his.
  notReady,
  falconAway,
  flownOut,

  /// The lure he has not got ({'lure'}).
  noLure,

  /// Not a bird held for sale; the trapping auction closed; not a kept
  /// peregrine; not in the months to set it free; not lost.
  notHeld,
  auctionClosed,
  notKept,
  releaseMonths,
  notLost,

  /// No الدعو in the moult.
  moult,

  /// Still driving to the ground ({'day', 'minute'}: when he is there).
  driving,

  /// A day's outing whose drive there and back does not fit the day.
  noTime,

  /// Another trapping ground worked today (one a day).
  oneGroundADay,

  /// الدعو from away from the farm (a camp, a drive).
  awayFromFarm,

  /// No falcons at all.
  noFalcons,

  /// A kept bird offered for sale (the owner's decision 8).
  keptNotForSale,

  /// The falcon wears a tracker already, or one is on its way for it.
  hasTracker,

  /// He has looked for the lost falcon today already.
  searchedToday,
}

class FalconLines {
  const FalconLines._();

  /// The words of a refusal [e] of the hunting season, or null for an error
  /// of another kind (money, debt: the phone's own words).
  static String? refusal(DomainError e) {
    if (e.code != ErrorCode.huntRefused) return null;
    final why = HuntRefusal.values.byName(e.params['reason']! as String);
    return switch (why) {
      HuntRefusal.routeClosed => closed(
        FalconRoute.values.byName(e.params['route']! as String),
      ),
      HuntRefusal.lotGone => 'هالطير انباع، شوف طيور اليوم',
      HuntRefusal.notALot => 'هالطير مو من طيور اليوم',
      HuntRefusal.noRoom => 'ابنِ غرفة الصقور أول: الصقر يبي مكانه بالعزبة',
      HuntRefusal.roomFull => 'غرفة الصقور مليانة: تاخذ 4 صقور بس',
      HuntRefusal.permitHeld => 'عندك هالتصريح لهالموسم',
      HuntRefusal.needsFalcon => 'تصريح الصقار يبي صقر جوازه باسمك',
      HuntRefusal.gearFull => _room(
        e.params['room'] as int? ?? 0,
        e.params['gear'] as String?,
      ),
      HuntRefusal.onTrip => 'انت طالع الحين: ارجع أول',
      HuntRefusal.notOnTrip => 'مخيمك مو هنا',
      HuntRefusal.tooFar => 'بعيدة على طلعة يوم: ما ترجع نفس اليوم',
      HuntRefusal.noSupplies => 'ما عندك مؤونة للمخيم',
      HuntRefusal.noTent => 'تنقل المخيم بالخيمة المتنقلة بس',
      // the design's words (design/hunt/trip.cjs, trip_20 and trip_21)
      HuntRefusal.offGround =>
        'الطرح بأرض طرح بس وبموسمه، والشبك برا أرض الطرح غرامته 100,000 ريال.',
      HuntRefusal.nearFarm => 'الصيد بالمزارع وحولها ممنوع، وغرامته 5,000 ريال لو انمسكت. ابعد عن العزب والقرى وأرسله.',
      HuntRefusal.coast => 'الساحل ممنوع الصيد فيه لين 20 كيلو داخل البر',
      HuntRefusal.reserve => 'المحميات ممنوع الصيد فيها',
      HuntRefusal.notHuntingGround => 'هذي أرض طرح، مو أرض مقناص',
      HuntRefusal.outOfSeason =>
        e.params['kind'] == 'trapping'
            ? 'الطرح من 1 أكتوبر لين 30 نوفمبر بس'
            : 'المقناص من 1 سبتمبر لين 31 يناير بس',
      HuntRefusal.noPermit =>
        e.params['kind'] == 'trapping'
            ? 'ما عندك تصريح طرح لهالموسم'
            : 'ما عندك تصريح صقار لهالموسم',
      // the permit's line (phone_falcon.cjs, view 13)
      HuntRefusal.night => 'بالليل وبالضو ما فيه طرح',
      HuntRefusal.notByDay =>
        'الصيد بالنهار بس، من بعد الشروق بساعة لين قبل الغروب بساعة',
      HuntRefusal.noQuarry => 'ما فيه طريدة مسموحة هنا بهالوقت',
      HuntRefusal.movingCar => 'الصيد من سيارة تمشي ممنوع: وقّف أول',
      HuntRefusal.notReady => 'صقرك ما خلص الدعو',
      HuntRefusal.falconAway => 'صقرك مو معك',
      HuntRefusal.flownOut => 'صقرك طار كفايته اليوم',
      HuntRefusal.noLure =>
        e.params['lure'] == 'birdNet'
            ? 'ما عندك شبك الطيور والجربوع'
            : 'ما عندك حمام وشبك الحمام',
      HuntRefusal.notHeld => 'هالطير مو للبيع',
      HuntRefusal.auctionClosed => 'مزاد الطرح من 1 أكتوبر لين 30 نوفمبر بس',
      HuntRefusal.notKept => 'تطلق بس الشاهين اللي طرحته وخليته لك',
      HuntRefusal.releaseMonths => 'تطلقه من أول فبراير لين آخر أبريل',
      HuntRefusal.notLost => 'صقرك مو ضايع',
      HuntRefusal.moult => 'بالمقيض ما فيه دعو',
      HuntRefusal.driving => 'لسا بالطريق، ما وصلت',
      HuntRefusal.noTime => 'ما يمديك تروح وترجع اليوم',
      HuntRefusal.oneGroundADay => 'اشتغلت اليوم بأرض ثانية: أرض وحدة باليوم',
      HuntRefusal.awayFromFarm => 'الدعو بغرفة الصقور، وانت برا العزبة',
      HuntRefusal.noFalcons => 'ما عندك صقور',
      HuntRefusal.keptNotForSale => 'الطير اللي تخليه لك ما ينعرض للبيع',
      HuntRefusal.hasTracker => 'عليه جهاز تتبع',
      HuntRefusal.searchedToday => 'دوّرته اليوم: دوّره بكرة',
    };
  }

  /// What still fits of a gear, its counting noun in its four forms (1, 2,
  /// 3 to 10, 11 and up); none: «عندك كفايتك منها».
  static String _room(int n, String? gear) {
    if (n <= 0) return 'عندك كفايتك منها';
    final (one, two, few, many) = switch (gear) {
      'pigeon' => ('حمامة وحدة', 'حمامتين', 'حمامات', 'حمامة'),
      'supplies' => (
        'يوم مؤونة واحد',
        'يومين مؤونة',
        'أيام مؤونة',
        'يوم مؤونة',
      ),
      _ => ('وحدة', 'ثنتين', '', ''),
    };
    final what = switch (n) {
      1 => one,
      2 => two,
      <= 10 => '$n $few',
      _ => '$n $many',
    };
    return 'تقدر تطلب ${what.trim()} بس';
  }

  /// The line of a bird in the net set free at once: the proxy's lines
  /// word for word (batch 3, items 3 and 4; approved with the design), the
  /// saker's before the قرناس's (the answers' Q-12). Null for a sellable
  /// bird.
  static String? release(FalconSpecies s, bool farkh) => switch (s) {
    FalconSpecies.mountainPeregrine =>
      'طلقته: الشاهين الجبلي طير مقيم، وطرحه ممنوع',
    FalconSpecies.lanner => 'طلقته: الوكري طير مقيم، وطرحه ممنوع',
    FalconSpecies.saker =>
      'طلقته: الحر مهدد، والمزاد ما يقبل إلا فرخ الشاهين البحري',
    FalconSpecies.passagePeregrine =>
      farkh ? null : 'طلقته: المزاد ما يقبل إلا الفرخ',
  };

  /// A bird neither sold nor kept when the trapping auction closed (ours).
  static const freedAtClose = 'طلقته: خلص مزاد الطرح وما بعته ولا خليته لك';

  /// The trip's lines in the summary (the design's words, view 18: «طرحت
  /// فرخ شاهين بحري»، «طلقت حر»، «المؤونة والبنزين»; the others ours).
  static const summary = {
    'caught': 'طرحت فرخ شاهين بحري',
    'released': 'طلقت',
    'stooped': 'نزل على الطعم وما علق',
    'flights': 'طلعات الصقر',
    'taken': 'صاد',
    'suppliesUsed': 'المؤونة والبنزين',
    'nights': 'ليالي',
  };

  /// The trip's outcomes in words (ours, for the camp's answers).
  static const trap = {
    'inSight': 'فيه صقر',
    'nothingInSight': 'ما فيه شي',
    'nothingCame': 'ما جا شي',
    'refused': 'ما بغى الطعم',
    'refusedAndWent': 'ما بغى الطعم وراح',
    'stooped': 'نزل على الطعم وما علق',
    'netted': 'طاح بالشبك',
  };

  /// An auction closed: when it opens.
  static String closed(FalconRoute r) => switch (r) {
    FalconRoute.breeders => 'مزاد صقور المزارع بأغسطس بس، من 5 لين 25',
    FalconRoute.exhibition => 'معرض الصقور من 1 لين 10 أكتوبر بس',
    FalconRoute.trapping => 'مزاد الطرح من 1 أكتوبر لين 30 نوفمبر بس',
  };

  /// The bank's names for the hunting season's kinds of money.
  static const moneyKinds = {
    'falcons': 'الصقور وأجهزة التتبع',
    'falconSale': 'بيع الطرح',
    'permits': 'التصاريح',
    'gear': 'عدة الطرح',
    'falconUpkeep': 'أكل الصقور',
  };
}
