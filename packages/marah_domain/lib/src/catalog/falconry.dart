// The hunting season's catalog (task T18, part A): the falcons, the routes to
// one, the permits, the trapping gear and the grounds, with every Arabic word
// a screen will say about them. The sources are docs/research-realism.md
// section 8 by number ("[n]"); "(game choice)" marks ours. The approved
// design: docs/proposals/hunting_season_design.md, design/ui/phone_falcon.cjs.
import 'dart:math' as math;

import '../catalog/region.dart';
import '../common/time.dart';

/// The falcons of the season. Only two are ever the player's own: the saker
/// (bought: farm-bred or imported) and the passage peregrine of the year
/// (bought at the trapping auction, or trapped). The resident two come only
/// to the net, and go free (they are banned [194]).
enum FalconSpecies {
  /// الحر: farm-bred at the breeders' auction [158], imported at the
  /// exhibition [184]; passes the north in autumn [198]. Never accepted at
  /// the trapping auction [184][185].
  saker('حر'),

  /// الشاهين البحري: the passage peregrine; its فرخ is the only bird the
  /// trapping auction takes [184][189][185].
  passagePeregrine('شاهين بحري'),

  /// الشاهين الجبلي: the resident mountain peregrine; trapping it is banned
  /// [194].
  mountainPeregrine('شاهين جبلي'),

  /// الوكري: the resident lanner; trapping it is banned [194].
  lanner('وكري');

  const FalconSpecies(this.label);
  final String label;
}

/// A falcon's age class as the club and the auction use it [169][188]: فرخ in
/// its first year and first plumage, قرناس once it has moulted [208].
enum FalconAge {
  farkh('فرخ'),
  qarnas('قرناس');

  const FalconAge(this.label);
  final String label;

  /// A bird hatched in the spring of [hatched] is a فرخ through the season
  /// that opens that autumn, and a قرناس from 1 September of the next year,
  /// its first moult behind it (game choice: the moult's months are not
  /// sourced; the season's design marks it a gap).
  static FalconAge on(GameDay day, int hatched) {
    final d = day.date;
    final seasonYear = d.month >= 9 ? d.year : d.year - 1;
    return seasonYear <= hatched ? farkh : qarnas;
  }
}

/// The three routes to his own falcon, each in its month (the proxy's batch
/// 3 item 5, approved with the design on 14 Nov 2026).
enum FalconRoute {
  /// مزاد صقور المزارع at Malham: 5 to 25 August 2026 [158]; farm-bred sakers
  /// about SAR 19,000 [158].
  breeders('مزاد صقور المزارع', 8, 5, 8, 25),

  /// معرض الصقور: 1 to 10 October 2026 [157]; imported sakers, two sold at
  /// 700,000 and 100,000 [184].
  exhibition('معرض الصقور', 10, 1, 10, 10),

  /// مزاد الطرح at Malham: 1 October to 30 November, nightly
  /// [184][185][186]; only the passage peregrine of the year trapped in the
  /// Kingdom [184][189].
  trapping('مزاد الطرح', 10, 1, 11, 30);

  const FalconRoute(
    this.label,
    this.fromMonth,
    this.fromDay,
    this.toMonth,
    this.toDay,
  );
  final String label;
  final int fromMonth;
  final int fromDay;
  final int toMonth;
  final int toDay;

  /// Open on [day] (the dates are the same every year: game choice on the
  /// 2026 dates).
  bool openOn(GameDay day) => inSpan(day, fromMonth, fromDay, toMonth, toDay);
}

/// [day] falls between [fromMonth]/[fromDay] and [toMonth]/[toDay] of one
/// year, both ends in (a span that does not cross the new year).
bool inSpan(GameDay day, int fromMonth, int fromDay, int toMonth, int toDay) {
  final d = day.date;
  final k = d.month * 100 + d.day;
  return k >= fromMonth * 100 + fromDay && k <= toMonth * 100 + toDay;
}

/// The two permits in «تصريح الصيد» (the owner's generic name, decision 6).
enum PermitKind {
  /// تصريح صقار: the season 1 September to 31 January [127][128], by day only
  /// [135]; for falconers registered with the club, tied to a falcon's
  /// passport [128][131]. Its fee is not found from an official source: SAR
  /// 100 a season (game choice on a weak source [160]).
  hunting('تصريح صقار', 100),

  /// تصريح الطرح: 1 October to 30 November [184][185][186], on a trapping
  /// ground only. That a separate trapping permit exists, its issuer and
  /// terms were not found: the permit and its SAR 500 are game choices (the
  /// proxy's batch 3 item 9, approved with the design).
  trapping('تصريح الطرح', 500);

  const PermitKind(this.label, this.fee);
  final String label;
  final int fee;

  /// The season [day] is in for this permit (the year its autumn falls in),
  /// or null when it is closed.
  int? seasonOn(GameDay day) {
    final d = day.date;
    return switch (this) {
      hunting => d.month >= 9 ? d.year : (d.month == 1 ? d.year - 1 : null),
      trapping => d.month == 10 || d.month == 11 ? d.year : null,
    };
  }

  /// The season a permit bought on [day] is for: the one open, else the
  /// next to open.
  int seasonFor(GameDay day) {
    final open = seasonOn(day);
    if (open != null) return open;
    final d = day.date;
    return switch (this) {
      // February to August: the autumn to come
      hunting => d.year,
      // December and January: next autumn's; September and before: this
      trapping => d.month == 12 ? d.year + 1 : d.year,
    };
  }

  /// The season's first and last days.
  GameDay opens(int season) => switch (this) {
    hunting => GameDay.ofDate(DateTime.utc(season, 9)),
    trapping => GameDay.ofDate(DateTime.utc(season, 10)),
  };
  GameDay closes(int season) => switch (this) {
    hunting => GameDay.ofDate(DateTime.utc(season + 1, 1, 31)),
    trapping => GameDay.ofDate(DateTime.utc(season, 11, 30)),
  };
}

/// The trapping gear (عدة الطاروح) bought in «نادي الصقور» → «الطرح» and
/// delivered to the farm like feed (the owner's answer of 14 Nov 2026). What
/// each does is from the sources [198][204][222][223]; every price is a game
/// choice (no source prices any of it; the design's view 4); what each
/// moves in the odds is a game choice too (TrapOdds). [most]: how many he
/// may hold (game choices).
enum Gear {
  /// الحمام: the lure pigeons, the main method [198][204]; used up as they
  /// are released (game choice), so they are counted. SAR 50 each (the
  /// design's view 4).
  pigeon('الحمام', 50, most: 20),

  /// شبك الحمام: the net on the pigeon's back [198][204]. SAR 300 (game
  /// choice of ours: the design's view shows it held, with no price).
  pigeonNet('شبك الحمام', 300),

  /// شبك الطيور والجربوع: for a falcon that will not take the pigeon [204].
  /// SAR 1,200 (the design's view 4).
  birdNet('شبك الطيور والجربوع', 1200),

  /// الدربيل: watching and following falcons from far off [223]. SAR 900
  /// (the design's view 4).
  binoculars('الدربيل', 900),

  /// الخيمة المتنقلة (the owner's own idea): follow the falcons to another
  /// ground in the season; that the camp moves is not in the sources. SAR
  /// 6,500 (the design's view 4).
  mobileTent('الخيمة المتنقلة', 6500),

  /// مؤونة المخيم: water, food and fuel for the stay [204], by the day: SAR
  /// 150 a day (the design's view 4), up to the 60 days of the season.
  supplies('مؤونة المخيم', 150, most: 60),

  /// جهاز التتبع: fitted to his trained falcon [155] (the owner's decision 6:
  /// it lowers the risk of losing her); one for each falcon, each bird wears
  /// its own (the answers' Q-27), so as many as the room holds. SAR 2,500
  /// (game choice of ours: no source prices it).
  tracker('جهاز التتبع', 2500, most: 4);

  const Gear(this.label, this.price, {this.most = 1});
  final String label;
  final int price;
  final int most;

  /// The trapping gear proper (the tracker is the falcon's).
  static const trapping = [
    pigeon,
    pigeonNet,
    birdNet,
    binoculars,
    mobileTent,
    supplies,
  ];
}

/// What a falcon takes, by the rules: the stone-curlew in open land with
/// falcons only [140]; the houbara only in a licensed fenced estate
/// (المحازة) [142] (in open land its status was not confirmed: the game
/// keeps it to the estate, game choice).
///
/// Strictly by its source's dates (the answers' Q-10): the stone-curlew on
/// the autumn list, 1 September to 30 November [140]; the houbara 1
/// November to 31 January, as the club opened it [143]. A date no source
/// lists is closed.
enum Quarry {
  stoneCurlew('كروان', 9, 1, 11, 30),
  houbara('حبارى', 11, 1, 1, 31);

  const Quarry(
    this.label,
    this.fromMonth,
    this.fromDay,
    this.toMonth,
    this.toDay,
  );
  final String label;
  final int fromMonth;
  final int fromDay;
  final int toMonth;
  final int toDay;

  bool openOn(GameDay day) => fromMonth <= toMonth
      ? inSpan(day, fromMonth, fromDay, toMonth, toDay)
      : inSpan(day, fromMonth, fromDay, 12, 31) ||
            inSpan(day, 1, 1, toMonth, toDay);
}

/// What a ground is for.
enum GroundUse { hunting, trapping }

/// The real places of the season (each a pin on the map). The trapping
/// grounds are the research's [197][198][200][202][204][216][217]; their
/// coordinates are approximate town or desert centres, for the road's
/// length only (as Region's are). The hunting grounds are near the farm:
/// the open land at the Nafud's edge 14 km west of the yard, and a licensed
/// estate (their places and distances are the design's game choices,
/// design/hunt/trip.cjs).
enum Ground {
  nafudEdge(
    'طرف النفود',
    GroundUse.hunting,
    km: 14,
    quarry: [Quarry.stoneCurlew],
  ),
  estate(
    'المحازة',
    GroundUse.hunting,
    km: 17,
    quarry: [Quarry.houbara, Quarry.stoneCurlew],
  ),

  /// الحماد: north-west of Arar, toward Turaif (the director's own
  /// knowledge, not opened on this machine: the answers' Q-8); the research
  /// has it 100 km west of Arar in 2020 [198] and east of it in 2024 [203].
  /// Its distance from the farm is an estimate.
  hamad('الحماد', GroundUse.trapping, lat: 31.3, lon: 40.0, north: true),
  ummKhunsur('أم خنصر', GroundUse.trapping, lat: 30.9, lon: 41.6, north: true),
  uwayqilah(
    'العويقيلة',
    GroundUse.trapping,
    lat: 30.34,
    lon: 42.25,
    north: true,
  ),
  rafha('رفحاء', GroundUse.trapping, lat: 29.63, lon: 43.49, north: true),
  hail('حائل', GroundUse.trapping, lat: 27.52, lon: 41.69, north: true),
  dibdibah('الدبدبة', GroundUse.trapping, lat: 28.2, lon: 46.3, north: true),
  khafji(
    'الخفجي',
    GroundUse.trapping,
    lat: 28.44,
    lon: 48.49,
    coast: true,
    north: true,
  ),
  jubail('الجبيل', GroundUse.trapping, lat: 27.01, lon: 49.66, coast: true),
  sulayyil('السليل', GroundUse.trapping, lat: 20.46, lon: 45.57),
  sharurah('شرورة', GroundUse.trapping, lat: 17.47, lon: 47.11),
  lith('الليث', GroundUse.trapping, lat: 20.15, lon: 40.27, coast: true),
  qunfudhah('القنفذة', GroundUse.trapping, lat: 19.13, lon: 41.08, coast: true),
  mujayrimah('المجيرمة', GroundUse.trapping, lat: 20.6, lon: 39.9, coast: true),
  jazan('جازان', GroundUse.trapping, lat: 16.89, lon: 42.57, coast: true),
  yanbu('ينبع', GroundUse.trapping, lat: 24.09, lon: 38.06, coast: true),
  wajh('الوجه', GroundUse.trapping, lat: 26.23, lon: 36.47, coast: true);

  const Ground(
    this.label,
    this.use, {
    this.km,
    this.lat = 0,
    this.lon = 0,
    this.quarry = const [],
    this.coast = false,
    this.north = false,
  });
  final String label;
  final GroundUse use;

  /// A hunting ground's distance from the farm (game choice), or null: a
  /// trapping ground's is its road from the farm's region.
  final int? km;
  final double lat;
  final double lon;
  final List<Quarry> quarry;

  /// On the coast: the best trapping ground «بلا منازع» [204]; closed to
  /// hunting to 20 km inland [195], open to trapping in its season by the
  /// game's own choice (the design: «إلا أرض طرح بموسمها»).
  final bool coast;

  /// In the north, where the passage comes first [198][202][203].
  final bool north;

  bool get trapping => use == GroundUse.trapping;
  bool get hunting => use == GroundUse.hunting;

  /// The road from a farm in [farm] (great-circle × 1.25, as
  /// Region.roadKmTo; at least 25 km, the farm to the town's edge: game
  /// choice).
  int kmFrom(Region farm) {
    if (km != null) return km!;
    const r = 6371.0;
    double rad(double d) => d * math.pi / 180;
    final dLat = rad(lat - farm.lat);
    final dLon = rad(lon - farm.lon);
    final a =
        math.pow(math.sin(dLat / 2), 2) +
        math.cos(rad(farm.lat)) *
            math.cos(rad(lat)) *
            math.pow(math.sin(dLon / 2), 2);
    final c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a));
    final road = (r * c * 1.25).round();
    return road < 25 ? 25 : road;
  }

  /// Near enough for a one-day outing, back the same evening (the owner's
  /// answer of 14 Nov 2026): within [oneDayKm] by road (game choice).
  bool oneDayFrom(Region farm) => kmFrom(farm) <= oneDayKm;

  /// The road a one-day outing may take each way (game choice: under two
  /// hours' drive).
  static const oneDayKm = 150;

  /// The drive's hours at [kmPerHour] (game choice: the design's 600 km in
  /// about 7 hours).
  double hoursFrom(Region farm) => kmFrom(farm) / kmPerHour;
  static const kmPerHour = 85;
}

/// The sun by month (the answers' Q-1): civil dawn, sunrise and sunset in
/// minutes of the day (Arabia's time, UTC+3), on the 15th of each month at
/// Buraidah (26.33 N, 43.97 E), computed by the standard formula (NOAA's
/// declination and equation of time; the sun's centre 0.833° below the
/// horizon, civil dawn at 6°). One table for every farm: the latitudes of
/// the farms' regions differ by minutes (game choice).
class HuntSun {
  const HuntSun._();

  static const _dawn = [
    388,
    377,
    352,
    318,
    293,
    285,
    295,
    312,
    326,
    339,
    358,
    379,
  ];
  static const _rise = [
    413,
    401,
    375,
    342,
    318,
    311,
    320,
    336,
    349,
    362,
    383,
    404,
  ];
  static const _set = [
    1052,
    1076,
    1093,
    1107,
    1123,
    1137,
    1139,
    1122,
    1090,
    1057,
    1035,
    1034,
  ];

  static int dawn(GameDay d) => _dawn[d.month - 1];
  static int sunrise(GameDay d) => _rise[d.month - 1];
  static int sunset(GameDay d) => _set[d.month - 1];

  /// Hunting by day only: from an hour after sunrise to an hour before
  /// sunset [135].
  static bool huntingHours(GameDay d, int minute) =>
      minute >= sunrise(d) + 60 && minute <= sunset(d) - 60;

  /// Trapping in daylight, first light to sunset (the answers' Q-2: night
  /// and lights refused, the hunting rules' ban [135][136] taken to bind
  /// trapping; unconfirmed).
  static bool trappingHours(GameDay d, int minute) =>
      minute >= dawn(d) && minute <= sunset(d);

  /// The trappers' windows [204]: dawn to 10:00, the evening hour before
  /// sunset, and the hours between.
  static TrapWindow? window(GameDay d, int minute) {
    if (!trappingHours(d, minute)) return null;
    if (minute < 600) return TrapWindow.dawn;
    if (minute >= sunset(d) - 60) return TrapWindow.evening;
    return TrapWindow.midday;
  }
}

/// A trapping day's three windows (the hour, one of the odds' weights).
enum TrapWindow { dawn, midday, evening }

/// Where the map says he is when a hunting or trapping button is pressed:
/// on one of the grounds, or off them (the farm and around it, the coast
/// strip, a reserve, any other open land).
enum HuntOff {
  /// The farm and around it: cities, villages, farms and rest houses are
  /// closed to hunting [127][134][135].
  farm,

  /// The coast to 20 km inland [195].
  coast,

  /// The protected areas, royal reserves and giga-projects [127][134].
  reserve,

  /// Open land that is none of the grounds.
  open,
}

/// The lure he releases at a falcon he has seen.
enum Lure {
  /// A pigeon with the net on its back [198][204] (one pigeon used).
  pigeon,

  /// The bird and jerboa net, for a falcon that will not take the pigeon
  /// [204].
  birdNet,
}

/// What a stretch away is for.
enum TripKind { falconry, trapping }
