// ignore_for_file: avoid_print
// Reads a save written by bin/same_seed.dart --save (on either platform) on
// the Dart VM and prints its state line, which must equal the end of the
// writer's last line: a save the prototype's worker writes is one the app
// reads the same.
import 'dart:io';

import 'package:marah_data/marah_data.dart';
import 'package:marah_proto_engine/same_seed.dart';

void main(List<String> args) {
  final text = File(args.single).readAsStringSync();
  final save = text.substring(text.indexOf('--save--\n') + 9).trim();
  switch (const SaveCodec().decode(save)) {
    case Loaded(:final state):
      print(stateLine(state));
    case LoadFailed(:final problem, :final detail):
      stderr.writeln('could not read: ${problem.name} $detail');
      exitCode = 1;
  }
}
