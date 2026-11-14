// ignore_for_file: avoid_print
// Prints the same-seed lines (lib/same_seed.dart), then a line `--save--` and
// the final save's text. CI runs it on the Dart VM and compiled to JavaScript
// (node) and fails if the outputs differ; bin/read_save.dart then reads the
// JavaScript save on the VM. (No arguments: node does not pass them to a
// compiled main.)
import 'package:marah_data/marah_data.dart';
import 'package:marah_proto_engine/same_seed.dart';

void main() {
  String? save;
  for (final line in sameSeedLines(
    end: (g) => save = const SaveCodec().encode(
      g.state,
      savedAt: DateTime.utc(2026, 11, 1),
    ),
  )) {
    print(line);
  }
  for (final line in huntLines()) {
    print(line);
  }
  print('--save--');
  print(save);
}
