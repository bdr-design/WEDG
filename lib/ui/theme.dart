import 'package:flutter/material.dart';

/// Palette drawn from the Najdi desert at dusk: dune sand, dark camel-hair
/// brown, saffron for value and prizes, and a tamarisk green for good news.
class Palette {
  static const sand = Color(0xFFE9DCC4);
  static const sandDeep = Color(0xFFD8C3A0);
  static const dune = Color(0xFFB98B55);
  static const hair = Color(0xFF4A3426); // وبر داكن
  static const night = Color(0xFF1F1813);
  static const saffron = Color(0xFFC98A1B);
  static const tamarisk = Color(0xFF4F7A52);
  static const henna = Color(0xFFA6432F);
  static const ink = Color(0xFF2B211A);
}

/// Reem Kufi for names and headings (a Kufi with heritage character);
/// IBM Plex Sans Arabic for everything people read and compare.
const displayFont = 'ReemKufi';

TextStyle display(BuildContext context, double size, {Color? color}) =>
    TextStyle(
      fontFamily: displayFont,
      fontSize: size,
      fontWeight: FontWeight.w700,
      height: 1.25,
      color: color ?? Theme.of(context).colorScheme.onSurface,
    );

ThemeData buildTheme(Brightness brightness) {
  final dark = brightness == Brightness.dark;
  final scheme = ColorScheme.fromSeed(
    seedColor: Palette.dune,
    brightness: brightness,
  ).copyWith(
    primary: dark ? const Color(0xFFE2B57A) : Palette.hair,
    onPrimary: dark ? Palette.night : Colors.white,
    secondary: Palette.saffron,
    onSecondary: Colors.white,
    tertiary: Palette.tamarisk,
    error: Palette.henna,
    surface: dark ? const Color(0xFF221B16) : const Color(0xFFFBF7F0),
    onSurface: dark ? const Color(0xFFF1E6D6) : Palette.ink,
    surfaceContainerLowest: dark ? const Color(0xFF1A1410) : Colors.white,
    surfaceContainerLow: dark ? const Color(0xFF29211B) : const Color(0xFFF6EFE3),
    surfaceContainer: dark ? const Color(0xFF30271F) : const Color(0xFFF1E7D6),
    surfaceContainerHigh: dark ? const Color(0xFF3A2F26) : const Color(0xFFEADDC8),
    outlineVariant: dark ? const Color(0xFF4D4035) : const Color(0xFFDCCBB0),
  );

  final base = ThemeData(
    useMaterial3: true,
    colorScheme: scheme,
    brightness: brightness,
    fontFamily: 'Plex',
    scaffoldBackgroundColor: scheme.surface,
    visualDensity: VisualDensity.standard,
  );

  return base.copyWith(
    appBarTheme: AppBarTheme(
      backgroundColor: scheme.surface,
      foregroundColor: scheme.onSurface,
      elevation: 0,
      scrolledUnderElevation: 0.5,
      centerTitle: false,
      titleTextStyle: TextStyle(
        fontFamily: displayFont,
        fontSize: 22,
        fontWeight: FontWeight.w700,
        color: scheme.onSurface,
      ),
    ),
    cardTheme: CardThemeData(
      color: scheme.surfaceContainerLowest,
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(color: scheme.outlineVariant),
      ),
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: scheme.surfaceContainerLow,
      indicatorColor: scheme.primary.withValues(alpha: 0.14),
      labelTextStyle: WidgetStatePropertyAll(
        base.textTheme.labelMedium?.copyWith(fontWeight: FontWeight.w600),
      ),
      height: 66,
    ),
    chipTheme: base.chipTheme.copyWith(
      side: BorderSide(color: scheme.outlineVariant),
      labelStyle: base.textTheme.labelMedium,
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        minimumSize: const Size(48, 48),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        textStyle: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        minimumSize: const Size(48, 48),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: scheme.surfaceContainerLowest,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
    ),
    dividerTheme: DividerThemeData(color: scheme.outlineVariant, space: 1),
  );
}

/// Semantic colours for status pills (independent of the accent).
class StatusColors {
  static Color good(BuildContext c) => Palette.tamarisk;
  static Color warn(BuildContext c) => Palette.saffron;
  static Color bad(BuildContext c) => Palette.henna;
}
