// ignore_for_file: avoid_print
// Finds seeds whose same-seed hunting run (lib/same_seed.dart huntLines)
// covers every path in huntPaths; prints what each seed misses.
//   dart run tool/hunt_seed.dart [from] [to]
import 'package:marah_proto_engine/same_seed.dart';

void main(List<String> args) {
  final from = args.isEmpty ? 1 : int.parse(args[0]);
  final to = args.length < 2 ? from + 30 : int.parse(args[1]);
  for (var seed = from; seed <= to; seed++) {
    final covered = <String>{};
    huntLines(seed: seed, covered: covered).toList();
    final missing = huntPaths.difference(covered);
    print('seed $seed missing ${missing.length}: ${missing.join(' ')}');
  }
}
