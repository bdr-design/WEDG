import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'ui/controller.dart';
import 'ui/screens/home_shell.dart';
import 'ui/screens/onboarding_screen.dart';
import 'ui/theme.dart';

class MarahApp extends StatelessWidget {
  const MarahApp({super.key, required this.controller});

  final GameController controller;

  @override
  Widget build(BuildContext context) {
    return GameScope(
      controller: controller,
      child: MaterialApp(
        title: 'مراح',
        debugShowCheckedModeBanner: false,
        locale: const Locale('ar', 'SA'),
        supportedLocales: const [Locale('ar', 'SA')],
        localizationsDelegates: const [
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        theme: buildTheme(Brightness.light),
        darkTheme: buildTheme(Brightness.dark),
        home: ListenableBuilder(
          listenable: controller,
          builder: (context, _) => controller.hasGame
              ? const HomeShell()
              : const OnboardingScreen(),
        ),
      ),
    );
  }
}
