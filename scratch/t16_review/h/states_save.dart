// T16 reviewer: a save holding every vet-view state with a real male and a real female camel (review only, staged):
// market: a treated male and a treated female listing (looked at till found), a clean male and female looked at
// once (nothing found), a male and a female looked at today twice? (one look each: checkedToday), one never looked at;
// herd: a male and a female bought unknowing and told (declare), bought knowing (refused knewWhenBought), treated by
// himself (ownTreatment). Prints the ids. Run: dart run tool_rv/states_save.dart <out.json>
import 'dart:io';
import 'dart:convert';
import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/testing.dart';
import 'package:marah_domain/src/model/tampering.dart';
import 'package:marah_domain/src/model/market.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:marah_domain/src/systems/systems.dart';
void main(List<String> a) {
  final now = DateTime.now().toUtc();
  final g = Game.create(seed: 4242, playerName: 'اللاعب', farmName: 'العزبة', region: Region.qassim, favourite: ColorCategory.wodh, startedAt: now);
  grant(g, 600000);
  g.me.farm..storeKg = 1 << 20..tankL = 1 << 20..barleyKg = 1e5..alfalfaKg = 1e5..waterL = 1e6..capacity = 60;
  final w = g.state.world, me = g.me.id;
  List<Listing> of(Sex s) => (w.listings.values.where((l) => l.sellerId != me && w.camels[l.camelId]!.sex == s).toList()..sort((x, y) => x.askPrice.value.compareTo(y.askPrice.value)));
  void treat(Listing l, TamperKind k) => w.camels[l.camelId]!.treatments.add(Tampering(kind: k, strength: 1, on: g.today - 3, until: g.today + 300, by: l.sellerId));
  bool knows(Listing l) => w.camels[l.camelId]!.treatments.any((t) => t.knownBy.contains(me));
  final out = <String, String>{};
  final m = of(Sex.male), f = of(Sex.female);
  // herd states first (purchases), then the market's looks on the last day
  void buyKnowing(Listing l, String key) { treat(l, TamperKind.dye); w.camels[l.camelId]!.treatments.first.knownBy.add(me); g.dispatch(BuyListing(me, l.id)); out[key] = l.camelId.value; }
  void buyTold(Listing l, String key) { treat(l, TamperKind.botox); g.dispatch(BuyListing(me, l.id)); out[key] = l.camelId.value; }
  buyKnowing(m[0], 'herd_knew_m'); buyKnowing(f[0], 'herd_knew_f');
  buyTold(m[1], 'herd_told_m'); buyTold(f[1], 'herd_told_f');
  g.advanceDays(1);
  for (final k in ['herd_told_m', 'herd_told_f']) {
    final c = w.camels[CamelId(out[k]!)]!; final sim = Sim(g.state);
    TamperingSystem.foundOutside(sim, g.me, c, c.treatments.first); g.state.record(sim.drain());
  }
  // own treatment on a male and a female of his
  final mine = w.aliveOwnedBy(me).where((c) => !out.values.contains(c.id.value)).toList();
  for (final s in [Sex.male, Sex.female]) {
    final c = mine.where((x) => x.sex == s).firstOrNull;
    if (c != null) { g.dispatch(Tamper(me, c.id, TamperKind.dye, 1)); out['herd_own_${s == Sex.male ? 'm' : 'f'}'] = c.id.value; }
  }
  // the market: a treated male and female found by looks on earlier days (several looks); clean ones looked at once today
  final m2 = of(Sex.male), f2 = of(Sex.female);
  for (final (l, key) in [(m2[0], 'mk_found_m'), (f2[0], 'mk_found_f')]) { treat(l, TamperKind.tailCut); treat(l, TamperKind.dye); out[key] = l.id.value; }
  var d = 0;
  while ((!knows(m2[0]) || !knows(f2[0])) && d < 10) { for (final l in [m2[0], f2[0]]) { if (!knows(l)) g.dispatch(CheckListing(me, l.id)); } g.advanceDays(1); d++; }
  // clean ones: looked twice on earlier days, then today once (checkedToday), and never
  for (final (l, key) in [(m2[1], 'mk_clean_m'), (f2[1], 'mk_clean_f')]) { out[key] = l.id.value; }
  for (var i = 0; i < 2; i++) { g.dispatch(CheckListing(me, m2[1].id)); g.dispatch(CheckListing(me, f2[1].id)); g.advanceDays(1); }
  g.dispatch(CheckListing(me, m2[1].id)); g.dispatch(CheckListing(me, f2[1].id));
  out['mk_never_m'] = m2[2].id.value; out['mk_never_f'] = f2[2].id.value;
  for (final e in out.entries.where((e) => e.key.startsWith('mk_'))) { if (!w.listings.containsKey(ListingId(e.value))) print('GONE ${e.key}'); }
  g.state.lastSeenUtcMs = now.millisecondsSinceEpoch;
  File(a.first).writeAsStringSync(const SaveCodec().encode(g.state));
  File('${a.first}.ids.json').writeAsStringSync(jsonEncode(out));
  print('day ${g.today.value} cash ${g.me.cash.value} $out invariants ${checkInvariants(g.state)}');
}
