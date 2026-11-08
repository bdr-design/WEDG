/// Typed identifiers. Each is a plain string at runtime, but the compiler
/// stops a camel id being passed where a listing id is expected.
///
/// Offline, ids come from [IdGenerator] (world seed + counter, deterministic).
/// Online, the server assigns them; the format is opaque to the rules.
library;

extension type const CamelId(String value) {}

extension type const OwnerId(String value) {}

extension type const ListingId(String value) {}

extension type const OfferId(String value) {}

extension type const StudId(String value) {}

extension type const FestivalId(String value) {}

extension type const RoundId(String value) {}

/// Issues unique ids for one world. Ids embed the world seed so two offline
/// worlds never produce the same id, and the counter keeps them ordered.
class IdGenerator {
  IdGenerator({required this.worldSeed, this.counter = 0});

  final int worldSeed;
  int counter;

  String _next(String prefix) {
    counter++;
    final seed = worldSeed.toRadixString(36).padLeft(7, '0');
    return '$prefix-$seed-${counter.toRadixString(36)}';
  }

  CamelId camel() => CamelId(_next('c'));
  ListingId listing() => ListingId(_next('l'));
  OfferId offer() => OfferId(_next('o'));
  StudId stud() => StudId(_next('s'));
  FestivalId festival() => FestivalId(_next('f'));
  RoundId round() => RoundId(_next('r'));
  OwnerId owner() => OwnerId(_next('w'));
}
