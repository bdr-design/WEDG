// A save for design/ui/phone_haraj_vet.cjs (part B of T10, a design awaiting the owner): the two states of الحراج's vet
// check and declared sale that one sitting of the real page does not reach (the market's 3% of treated listings, the
// vet's 60% a look), played into a new game on seed 4242 by the engine's own commands, so every figure on the views is
// the engine's:
//  - two of the cheapest listings carry a treatment put on by their sellers, as the market's 3% does (Balance
//    .marketTamperChance); on the first the player's vet looks (CheckListing, SAR 500 each) until he finds it;
//  - the second the player buys unchecked (BuyListing), the next day the daily look finds it (TamperingSystem
//    .foundOutside): he did not know, so he is told and not fined, and may sell her declared (decision 15);
//  - نورة treated by her owner (Tamper): the engine refuses her a declared sale (ownTreatment).
// Run `dart run bin/vet_design_save.dart <out.json>` in tool/proto_engine; the page opens it from localStorage.
import 'dart:io';

import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/marah_domain.dart';
// ignore: implementation_imports
import 'package:marah_domain/src/sim.dart';
// ignore: implementation_imports
import 'package:marah_domain/src/systems/systems.dart';

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
  final list = w.listings.values.toList()
    ..sort((a, b) => a.askPrice.value.compareTo(b.askPrice.value));
  // the market's treated listings: a light dye and a light botox, the sellers'
  for (final (l, k) in [
    (list[0], TamperKind.dye),
    (list[1], TamperKind.botox),
  ]) {
    w.camels[l.camelId]!.treatments.add(
      Tampering(
        kind: k,
        strength: 1,
        on: g.today - 10,
        until: g.today - 10 + (k.lastsDays - 1),
        by: l.sellerId,
      ),
    );
  }
  // the vet looks at the first until he finds it (a look a day)
  var looks = 0;
  for (; looks < 8; looks++) {
    g.dispatch(CheckListing(me, list[0].id));
    final c = w.camels[list[0].camelId]!;
    if (c.treatments.any((t) => t.knownBy.contains(me))) break;
    g.advanceDays(1);
  }
  // the second bought unchecked, then found by the daily look
  final bought = list[1].camelId;
  final r = g.dispatch(BuyListing(me, list[1].id));
  if (!r.ok) throw StateError('not bought: $r');
  g.advanceDays(1);
  final c = w.camels[bought]!;
  final sim = Sim(g.state);
  TamperingSystem.foundOutside(sim, g.me, c, c.treatments.single);
  g.state.record(sim.drain());
  // نورة treated by her owner
  final noura = w.aliveOwnedBy(me).firstWhere((x) => x.name == 'نورة');
  g.dispatch(Tamper(me, noura.id, TamperKind.dye, 1));
  g.state.lastSeenUtcMs = now.millisecondsSinceEpoch;
  File(args.first).writeAsStringSync(const SaveCodec().encode(g.state));
  stdout.writeln(
    'looks $looks, found ${w.camels[list[0].camelId]!.treatments.first.knownBy.contains(me)}, '
    'bought ${c.name} declared ${GameView(g.state, me).cannotDeclare(bought)}, '
    'noura ${GameView(g.state, me).cannotDeclare(noura.id)?.code}, cash ${g.me.cash.value}, '
    'invariants ${checkInvariants(g.state)}',
  );
}
