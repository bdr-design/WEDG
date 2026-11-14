// T18B reviewer: saves holding each state the hunting screens can be in (review only, staged with the engine's own
// commands where it has them; a trapped bird is put in the net by hand: the camp is part C and the odds are low).
// Copy into <checkout>/tool/proto_engine/tool_rv/ and run there: dart run tool_rv/falcon_states.dart <out folder>
// Each save is <name>.json, played to its day with lastSeenUtcMs = now (no catch-up when the page opens it).
import 'dart:convert';
import 'dart:io';
import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/testing.dart';
import 'package:marah_domain/src/model/falconry.dart';
import 'package:marah_domain/src/rules/falcon_market.dart';

final now = DateTime.now().toUtc();
GameDay d(int y, int m, int dd) => GameDay.ofDate(DateTime.utc(y, m, dd));

Game fresh(GameDay start, {int cash = 1000000}) {
  final g = Game.create(seed: 4242, playerName: 'اللاعب', farmName: 'العزبة', region: Region.qassim, favourite: ColorCategory.wodh, startDay: start, startedAt: now);
  if (cash > 0) grant(g, cash);
  g.me.farm..storeKg = 1 << 20..tankL = 1 << 20..barleyKg = 1e5..alfalfaKg = 1e5..waterL = 1e6;
  return g;
}

/// A passage peregrine of the year put in his net on [ground] today, held for sale (worth and skill hidden).
Falcon netted(Game g, Ground ground, {int value = 112000}) {
  final f = Falcon(id: g.state.world.ids.falcon(), name: 'براق', species: FalconSpecies.passagePeregrine, female: true, hatched: g.today.date.month >= 9 ? g.today.date.year : g.today.date.year - 1, how: FalconHow.trapped, on: g.today, ground: ground, lengthQ: 60, widthQ: 62, weightG: 1010, skill: 0.61, value: value);
  g.me.hunt.held.add(f);
  return f;
}

void room(Game g) { g.dispatch(BuildFacility(g.me.id, Facility.falconRoom)); }

/// [n] falcons bought from the day's lots (any route open; a day further on if none).
void buy(Game g, int n) {
  for (var i = 0; i < 40 && n > 0; i++) {
    for (final r in FalconRoute.values) {
      if (n == 0) break;
      for (final l in FalconMarket.lots(g.state.world.seed, r, g.today)) {
        if (n == 0) break;
        if (g.dispatch(BuyFalcon(g.me.id, l.key, g.me.cash.value)).ok) n--;
      }
    }
    if (n > 0) g.advanceDays(1);
  }
}

void save(Game g, String dir, String name, [Map<String, Object?> note = const {}]) {
  g.state.lastSeenUtcMs = now.millisecondsSinceEpoch;
  File('$dir/$name.json').writeAsStringSync(const SaveCodec().encode(g.state));
  final h = g.me.falconry;
  print('$name: ${g.today.date.toIso8601String().substring(0, 10)} cash ${g.me.cash.value} room ${g.me.farm.has(Facility.falconRoom)} falcons ${h?.falcons.map((f) => '${f.name}/${f.how.name}/dau${f.dauDays}').toList()} held ${h?.held.map((f) => f.id.value).toList()} entered ${h?.entered.length} ${jsonEncode(note)} inv ${checkInvariants(g.state)}');
}

void main(List<String> a) {
  final dir = a.first;
  Directory(dir).createSync(recursive: true);
  // 1 October: nothing bought (the game's first day): every permit and gear unheld, no room
  save(fresh(d(2026, 10, 1)), dir, 'oct1_none');
  // 1 October, ready: room built, the trapping permit, part of the gear, one order still on its way
  { final g = fresh(d(2026, 9, 25)); room(g); g.dispatch(BuyPermit(g.me.id, PermitKind.trapping));
    for (final (x, n) in [(Gear.pigeon, 6), (Gear.pigeonNet, 1), (Gear.supplies, 10)]) { g.dispatch(OrderGear(g.me.id, x, n)); }
    g.advanceTo(d(2026, 10, 1)); g.dispatch(OrderGear(g.me.id, Gear.binoculars, 1));
    save(g, dir, 'oct1_ready'); }
  // a held bird, three ways: no room; a room with places; a full room (4)
  { final g = fresh(d(2026, 10, 12)); g.dispatch(BuyPermit(g.me.id, PermitKind.trapping)); netted(g, Ground.hamad); save(g, dir, 'held_noroom'); }
  { final g = fresh(d(2026, 10, 6)); room(g); g.advanceTo(d(2026, 10, 10)); buy(g, 1); netted(g, Ground.hamad); save(g, dir, 'held_room'); }
  { final g = fresh(d(2026, 10, 6)); room(g); g.advanceTo(d(2026, 10, 10)); buy(g, 4); netted(g, Ground.hamad); save(g, dir, 'held_full'); }
  // entered tonight; and the morning after (sold at the hammer)
  { final g = fresh(d(2026, 10, 12)); final f = netted(g, Ground.hamad); g.dispatch(EnterTrapAuction(g.me.id, f.id)); save(g, dir, 'entered');
    g.advanceDays(1); save(g, dir, 'sold'); }
  // the auction's last day with a bird neither sold nor kept; and the day after (set free at the close)
  { final g = fresh(d(2026, 11, 30)); netted(g, Ground.hamad); save(g, dir, 'close_last');
    g.advanceDays(1); save(g, dir, 'close_after'); }
  // his falcons: one bought (الدعو part done, cared 10 days ago: steps back in 4), one trapped and kept, a tracker each
  { final g = fresh(d(2026, 10, 6)); room(g); g.advanceTo(d(2026, 10, 10)); buy(g, 1);
    final f = netted(g, Ground.hamad); g.dispatch(KeepBird(g.me.id, f.id));
    g.dispatch(OrderGear(g.me.id, Gear.tracker, 1));
    for (var i = 0; i < 9; i++) { g.dispatch(CareFalcons(g.me.id)); g.advanceDays(1); }
    g.advanceDays(10); save(g, dir, 'mine_mid');
    g.dispatch(BuyPermit(g.me.id, PermitKind.hunting)); save(g, dir, 'mine_permit');
    // February: the kept peregrine may be set free; June: the moult (no الدعو)
    g.advanceTo(d(2027, 2, 3)); save(g, dir, 'feb_kept');
    g.advanceTo(d(2027, 6, 10)); save(g, dir, 'moult'); }
  // in debt with nothing bought (every purchase refused for cash)
  { final g = fresh(d(2026, 10, 1), cash: 0); grant(g, -(g.me.cash.value + 500)); save(g, dir, 'debt'); }
}
