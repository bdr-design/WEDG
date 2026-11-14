// A save for design/ui/phone_haraj_vet.cjs (part B of T10, a design awaiting the owner), a new game on seed 4242:
//  - played: the days go by (66 on this seed, the farm's stores filled so the herd lives through them unattended) till
//    the market's own treated listings (its 3%) are two on offer, and the player's vet looks at the first
//    (CheckListing, SAR 500, a look a day) till he finds the seller's treatment;
//  - staged: the second treated listing bought unchecked (with money granted for it), and its finding by the daily look
//    called directly (TamperingSystem.foundOutside: its chance, 0.04% a day a level, is years of play): he did not
//    know, so he is told and not fined, and may sell her declared (decision 15);
//  - played: his eldest camel (نورة, the start's she-camel) treated by her owner (Tamper), and the engine's refusal
//    of her declared sale (ownTreatment).
// One state is staged (the finding outside the ring called directly); every figure shown is the engine's own.
// Run `dart run bin/vet_design_save.dart <out.json> [<before.json>]` in tool/proto_engine; the page opens it from
// localStorage. <before.json>: the same game before the vet's first look (the phone's look is played on it).
import 'dart:io';

import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/marah_domain.dart';
// ignore: implementation_imports
import 'package:marah_domain/src/model/market.dart';
// ignore: implementation_imports
import 'package:marah_domain/src/sim.dart';
// ignore: implementation_imports
import 'package:marah_domain/src/systems/systems.dart';
import 'package:marah_domain/testing.dart';

void main(List<String> args) {
  final now = DateTime.now().toUtc();
  final g = Game.create(
    seed: 4242,
    playerName: 'اللاعب',
    farmName: 'العزبة',
    region: Region.qassim,
    favourite: ColorCategory.wodh,
    startedAt: now,
  );
  final w = g.state.world, me = g.me.id;
  // played: the market's own treated listings (its 3%, Balance.marketTamperChance), day by day till two are on
  // offer at once; the vet looks at the first, a look a day, till he finds it
  List<Listing> treated() => [
    for (final l in w.listings.values)
      if (l.sellerId != me && w.camels[l.camelId]!.treatments.isNotEmpty) l,
  ]..sort((a, b) => a.askPrice.value.compareTo(b.askPrice.value));
  // (the farm's stores filled, so the herd lives through the wait unattended)
  g.me.farm
    ..storeKg = 100000
    ..tankL = 200000
    ..barleyKg = 40000
    ..alfalfaKg = 40000
    ..waterL = 190000;
  var days = 0;
  while (treated().length < 2 && days < 365) {
    g.advanceDays(1);
    days++;
  }
  final first = treated().first;
  // (a second file, when named: the game as it is now, before any look: the
  // phone's own look is played on it, T16's page checks)
  // the game's clock moved with the days played, so a page that opens the
  // save runs on from its day (not waiting for the clock to catch up)
  void clockToWorld() => g.state
    ..clockShiftMs = -g.today.daysSince(g.state.startedOn) * 86400000 ~/ 7
    ..lastSeenUtcMs = now.millisecondsSinceEpoch;
  if (args.length > 1) {
    clockToWorld();
    File(args[1]).writeAsStringSync(const SaveCodec().encode(g.state));
  }
  var looks = 0;
  bool found() =>
      w.camels[first.camelId]!.treatments.any((t) => t.knownBy.contains(me));
  for (; looks < 30 && !found() && w.listings.containsKey(first.id); looks++) {
    g.dispatch(CheckListing(me, first.id));
    if (!found()) g.advanceDays(1);
  }
  // staged: the second bought unchecked, and its finding by the daily look
  // (a chance of 0.04% a day a level: years of play) called directly
  Listing? other() => treated().where((l) => l.id != first.id).firstOrNull;
  for (var d = 0; other() == null && d < 365; d++) {
    g.advanceDays(1);
  }
  final second = other()!;
  final bought = second.camelId;
  grant(g, second.askPrice.value + 20000);
  final r = g.dispatch(BuyListing(me, second.id));
  if (!r.ok) throw StateError('not bought: $r');
  g.advanceDays(1);
  final c = w.camels[bought]!;
  final sim = Sim(g.state);
  TamperingSystem.foundOutside(sim, g.me, c, c.treatments.first);
  g.state.record(sim.drain());
  // his eldest camel treated by her owner
  final noura = w
      .aliveOwnedBy(me)
      .where((x) => x.id != bought)
      .reduce((a, b) => a.ageDays(g.today) >= b.ageDays(g.today) ? a : b);
  g.dispatch(Tamper(me, noura.id, TamperKind.dye, 1));
  clockToWorld();
  File(args.first).writeAsStringSync(const SaveCodec().encode(g.state));
  stdout.writeln(
    'played $days days, looks $looks, found ${found()}, '
    'bought ${c.name} declared ${GameView(g.state, me).cannotDeclare(bought)}, '
    'noura ${GameView(g.state, me).cannotDeclare(noura.id)?.code}, cash ${g.me.cash.value}, '
    'invariants ${checkInvariants(g.state)}',
  );
}
