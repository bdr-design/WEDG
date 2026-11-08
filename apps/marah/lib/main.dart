import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

/// Placeholder shell. The game screens are built after the owner approves
/// the visual design (see docs/GDD.md); the rules and saving live in
/// packages/marah_domain and packages/marah_data.
void main() => runApp(const MarahApp());

class MarahApp extends StatelessWidget {
  const MarahApp({super.key});

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
