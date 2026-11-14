// What the phone reads of the hunting season through the snapshot (task T18
// part B, "engine view for the phone"): the falcons' room among the farm's
// facilities, for its row in العزبة's build list, with its price, its
// building and its refusal as the others have them; and the news in
// falconFacts carried by the snapshot.
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:marah_runtime/marah_runtime.dart';
import 'package:marah_runtime/src/presenter.dart';
import 'package:test/test.dart';

void main() {
  Game game() => Game.create(
    seed: 4242,
    playerName: 'p',
    farmName: 'f',
    region: Region.qassim,
    favourite: ColorCategory.wodh,
    startDay: GameDay.ofDate(DateTime.utc(2026, 10, 1)),
    startedAt: DateTime.utc(2026, 11, 14),
  );
  FacilitySummary room(Game g) => Presenter(g.state, g.me.id)
      .snapshot(1)
      .farm
      .facilities
      .singleWhere((f) => f.facility == Facility.falconRoom);

  test('the falcons\' room is a row of the farm: price, refusal, building, '
      'built', () {
    final g = game();
    var r = room(g);
    expect(r.price, 18000);
    expect(r.most, 1);
    expect(r.has, 0);
    expect(r.cannot, isNull, reason: 'a new game has 20,000');
    Sim(g.state).pay(g.me, const Riyal(-15000), LedgerCategory.opening);
    expect(room(g).cannot, ErrorCode.insufficientFunds);
    Sim(g.state).pay(g.me, const Riyal(15000), LedgerCategory.opening);
    expect(g.dispatch(BuildFacility(g.me.id, Facility.falconRoom)).ok, isTrue);
    r = room(g);
    expect(r.building, 1);
    expect(r.doneOn, g.today + Balance.buildDays);
    g.advanceDays(Balance.buildDays);
    r = room(g);
    expect(r.has, 1);
    expect(r.building, 0);
    expect(r.cannot, isNotNull, reason: 'one room at most');
  });

  test('the snapshot carries the news list', () {
    final g = game();
    final s = Presenter(g.state, g.me.id).snapshot(1);
    expect(s.falcons['news'], isEmpty);
  });
}
