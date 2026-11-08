import 'camel.dart';
import 'contest.dart';
import 'farm.dart';
import 'ledger.dart';
import 'market.dart';

/// Day 0 of the game calendar. Game days are counted from here.
final gameEpoch = DateTime.utc(2026, 1, 1);

DateTime dateOfDay(int day) => gameEpoch.add(Duration(days: day));
int dayOfDate(DateTime d) =>
    DateTime.utc(d.year, d.month, d.day).difference(gameEpoch).inDays;

/// The whole save file: everything needed to resume the game exactly.
class GameState {
  GameState({
    required this.rngState,
    required this.day,
    required this.startDay,
    required this.playerName,
    required this.cash,
    required this.farm,
    required this.camels,
    required this.owners,
    required this.listings,
    required this.buyerOffers,
    required this.studs,
    required this.festivals,
    required this.ledger,
    required this.news,
    required this.nextId,
    this.festivalsPlannedUntil = 0,
  });

  static const schemaVersion = 1;

  int rngState;
  int day;
  final int startDay;
  String playerName;
  int cash;
  final Farm farm;

  /// Every camel the world tracks: the player's herd, camels on the market
  /// and studs at service. Rival contest entries are generated on the day.
  final Map<String, Camel> camels;
  final List<Owner> owners;
  final List<Listing> listings;
  final List<BuyerOffer> buyerOffers;
  final List<StudOffer> studs;
  final List<Festival> festivals;
  final List<LedgerEntry> ledger;
  final List<NewsItem> news;
  int nextId;

  /// Festivals are scheduled season by season; this is the last day covered.
  int festivalsPlannedUntil;

  DateTime get date => dateOfDay(day);

  String newId(String prefix) => '$prefix${nextId++}';

  Iterable<Camel> get herd => camels.values.where((c) => c.isPlayers);
  int get herdSize => herd.length;

  Owner? ownerById(String id) {
    for (final o in owners) {
      if (o.id == id) return o;
    }
    return null;
  }

  Map<String, dynamic> toJson() => {
        'v': schemaVersion,
        'rng': rngState,
        'day': day,
        'start': startDay,
        'player': playerName,
        'cash': cash,
        'farm': farm.toJson(),
        'camels': camels.values.map((c) => c.toJson()).toList(),
        'owners': owners.map((o) => o.toJson()).toList(),
        'listings': listings.map((l) => l.toJson()).toList(),
        'offers': buyerOffers.map((o) => o.toJson()).toList(),
        'studs': studs.map((s) => s.toJson()).toList(),
        'festivals': festivals.map((f) => f.toJson()).toList(),
        'ledger': ledger.map((l) => l.toJson()).toList(),
        'news': news.map((n) => n.toJson()).toList(),
        'nextId': nextId,
        'fpu': festivalsPlannedUntil,
      };

  factory GameState.fromJson(Map<String, dynamic> j) {
    final camels = (j['camels'] as List)
        .map((e) => Camel.fromJson(e as Map<String, dynamic>));
    return GameState(
      rngState: j['rng'] as int,
      day: j['day'] as int,
      startDay: j['start'] as int,
      playerName: j['player'] as String,
      cash: j['cash'] as int,
      farm: Farm.fromJson(j['farm'] as Map<String, dynamic>),
      camels: {for (final c in camels) c.id: c},
      owners: (j['owners'] as List)
          .map((e) => Owner.fromJson(e as Map<String, dynamic>))
          .toList(),
      listings: (j['listings'] as List)
          .map((e) => Listing.fromJson(e as Map<String, dynamic>))
          .toList(),
      buyerOffers: (j['offers'] as List)
          .map((e) => BuyerOffer.fromJson(e as Map<String, dynamic>))
          .toList(),
      studs: (j['studs'] as List)
          .map((e) => StudOffer.fromJson(e as Map<String, dynamic>))
          .toList(),
      festivals: (j['festivals'] as List)
          .map((e) => Festival.fromJson(e as Map<String, dynamic>))
          .toList(),
      ledger: (j['ledger'] as List)
          .map((e) => LedgerEntry.fromJson(e as Map<String, dynamic>))
          .toList(),
      news: (j['news'] as List)
          .map((e) => NewsItem.fromJson(e as Map<String, dynamic>))
          .toList(),
      nextId: j['nextId'] as int,
      festivalsPlannedUntil: (j['fpu'] as int?) ?? 0,
    );
  }
}
