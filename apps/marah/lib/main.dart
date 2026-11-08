import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:marah_runtime/marah_runtime.dart';

import 'src/engine_factory.dart';
import 'src/engine_lifecycle.dart';

/// Placeholder shell. The engine runs off the UI thread (ADR 0002); game
/// screens are built after the owner approves the visual design.
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final engine = await startEngine();
  EngineLifecycle(engine);
  final status = await engine.open();
  runApp(MarahApp(status: status));
}

class MarahApp extends StatelessWidget {
  const MarahApp({super.key, this.status = const NoGame()});

  final OpenStatus status;

  @override
  Widget build(BuildContext context) => const MaterialApp(
    title: 'مراح',
    debugShowCheckedModeBanner: false,
    locale: Locale('ar', 'SA'),
    supportedLocales: [Locale('ar', 'SA')],
    localizationsDelegates: [
      GlobalMaterialLocalizations.delegate,
      GlobalWidgetsLocalizations.delegate,
      GlobalCupertinoLocalizations.delegate,
    ],
    home: Scaffold(body: Center(child: Text('مراح · قيد البناء'))),
  );
}
