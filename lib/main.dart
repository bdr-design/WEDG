import 'package:flutter/material.dart';

import 'app.dart';
import 'data/game_repository.dart';
import 'ui/controller.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final controller = GameController(LocalGameRepository());
  await controller.init();
  runApp(MarahApp(controller: controller));
}
