import 'package:flutter/material.dart';

import '../../core/format.dart';
import '../../domain/engine/game_engine.dart';
import '../../domain/models/camel.dart';
import '../../domain/models/catalog.dart';
import '../../domain/rules/judging.dart';
import '../controller.dart';
import '../theme.dart';
import 'camel_silhouette.dart';

/// Coat colours per family, used for swatches and the stand-in drawing.
Color coatColor(ColorCategory c) => switch (c) {
      ColorCategory.majaheem => const Color(0xFF2A211C),
      ColorCategory.maghateer => const Color(0xFFF1ECE2),
      ColorCategory.wodh => const Color(0xFFE5DED0),
      ColorCategory.sofr => const Color(0xFFD3B07A),
      ColorCategory.homr => const Color(0xFFA9683D),
      ColorCategory.shoal => const Color(0xFF7A4A2C),
      ColorCategory.shoqh => const Color(0xFFC9AE95),
    };

Color shadeColor(ColorCategory c) => switch (c) {
      ColorCategory.majaheem => const Color(0xFF0F0B09),
      ColorCategory.maghateer => const Color(0xFFB8AE9E),
      ColorCategory.wodh => const Color(0xFF6F665A),
      ColorCategory.sofr => const Color(0xFF8D6A3A),
      ColorCategory.homr => const Color(0xFF5F3519),
      ColorCategory.shoal => const Color(0xFF3A2112),
      ColorCategory.shoqh => const Color(0xFF7D6450),
    };

/// Asset path for a camel photo: `assets/camels/{family}_{female|male|calf}.webp`
String camelAssetPath(ColorCategory c, Sex sex, bool calf) =>
    'assets/camels/${c.name}_${calf ? 'calf' : sex.name}.webp';

/// Shows the camel's photo when bundled, otherwise the drawn silhouette.
class CamelImage extends StatelessWidget {
  const CamelImage({
    super.key,
    required this.camel,
    required this.today,
    this.height = 120,
    this.backdrop = true,
  });

  final Camel camel;
  final int today;
  final double height;
  final bool backdrop;

  @override
  Widget build(BuildContext context) {
    final calf = camel.ageYears(today) < 2;
    final path = camelAssetPath(camel.category, camel.sex, calf);
    final assets = GameScope.read(context).assets;
    final scheme = Theme.of(context).colorScheme;
    final Widget image = assets.contains(path)
        ? Image.asset(path, fit: BoxFit.contain, height: height)
        : CustomPaint(
            size: Size(height * 4 / 3, height),
            painter: CamelSilhouettePainter(
              coat: coatColor(camel.category),
              shade: shadeColor(camel.category),
              calf: calf,
              male: camel.sex == Sex.male,
            ),
          );
    if (!backdrop) return SizedBox(height: height, child: image);
    return Container(
      height: height,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            scheme.surfaceContainerLow,
            Color.lerp(scheme.surfaceContainerLow, Palette.dune, 0.22)!,
          ],
        ),
      ),
      alignment: Alignment.center,
      child: image,
    );
  }
}

class ColorSwatchDot extends StatelessWidget {
  const ColorSwatchDot(this.category, {super.key, this.size = 12});
  final ColorCategory category;
  final double size;

  @override
  Widget build(BuildContext context) => Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          color: coatColor(category),
          shape: BoxShape.circle,
          border: Border.all(
              color: Theme.of(context).colorScheme.outline.withValues(alpha: 0.6)),
        ),
      );
}

enum PillTone { neutral, good, warn, bad, accent }

class Pill extends StatelessWidget {
  const Pill(this.text, {super.key, this.tone = PillTone.neutral, this.icon});
  final String text;
  final PillTone tone;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final color = switch (tone) {
      PillTone.neutral => scheme.onSurface.withValues(alpha: 0.75),
      PillTone.good => Palette.tamarisk,
      PillTone.warn => Palette.saffron,
      PillTone.bad => Palette.henna,
      PillTone.accent => scheme.primary,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 13, color: color),
            const SizedBox(width: 4),
          ],
          Text(text,
              style: TextStyle(
                  fontSize: 12, fontWeight: FontWeight.w600, color: color)),
        ],
      ),
    );
  }
}

/// Status pills for a camel (pregnant, sick, for sale, entered...).
List<Widget> camelPills(BuildContext context, Camel c, GameEngine e) {
  final s = e.s;
  final pills = <Widget>[];
  if (c.health == HealthStatus.sick) {
    pills.add(Pill('مريضة: ${c.illness}', tone: PillTone.bad, icon: Icons.healing));
  } else if (c.health == HealthStatus.treated) {
    pills.add(const Pill('تحت العلاج', tone: PillTone.warn, icon: Icons.medication));
  }
  if (c.isPregnantConfirmed) {
    final left = c.pregnancy!.dueDay - s.day;
    pills.add(Pill('عشراء · تولد بعد ${formatDays(left)}',
        tone: PillTone.good, icon: Icons.favorite));
  } else if (c.awaitingCheck) {
    pills.add(const Pill('ملقّحة · تنتظر الفحص', tone: PillTone.warn));
  }
  if (s.listings.any((l) => l.camelId == c.id)) {
    pills.add(const Pill('معروضة للبيع', tone: PillTone.accent, icon: Icons.sell));
  }
  if (s.festivals.any((f) => !f.done && f.rounds.any((r) => r.entries.contains(c.id)))) {
    pills.add(const Pill('مسجلة في مهرجان', tone: PillTone.accent, icon: Icons.emoji_events));
  }
  if (c.titles.isNotEmpty) {
    final best = c.titles.map((t) => t.rank).reduce((a, b) => a < b ? a : b);
    pills.add(Pill('أفضل مركز: $best', tone: PillTone.good, icon: Icons.military_tech));
  }
  if (c.crossbred) pills.add(const Pill('خلط'));
  return pills;
}

/// Horizontal bar for a 0–100 value.
class ScoreBar extends StatelessWidget {
  const ScoreBar({super.key, required this.value, this.color, this.height = 6});
  final double value;
  final Color? color;
  final double height;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return ClipRRect(
      borderRadius: BorderRadius.circular(height),
      child: LinearProgressIndicator(
        value: (value / 100).clamp(0, 1),
        minHeight: height,
        backgroundColor: scheme.surfaceContainerHigh,
        color: color ?? scoreColor(value),
      ),
    );
  }
}

Color scoreColor(double v) {
  if (v >= 78) return Palette.saffron;
  if (v >= 62) return Palette.tamarisk;
  if (v >= 48) return Palette.dune;
  return Palette.henna;
}

/// "86.4" + grade word, for the overall mazayen score.
class QualityBadge extends StatelessWidget {
  const QualityBadge({super.key, required this.quality, this.large = false});
  final double quality;
  final bool large;

  @override
  Widget build(BuildContext context) {
    final color = scoreColor(quality);
    return Container(
      padding: EdgeInsets.symmetric(horizontal: large ? 12 : 8, vertical: large ? 8 : 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withValues(alpha: 0.4)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            quality.toStringAsFixed(1),
            style: TextStyle(
              fontSize: large ? 26 : 16,
              fontWeight: FontWeight.w700,
              color: color,
              fontFeatures: const [FontFeature.tabularFigures()],
              height: 1.1,
            ),
          ),
          Text(Judging.grade(quality),
              style: TextStyle(fontSize: large ? 12 : 10, color: color, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}

class Kpi extends StatelessWidget {
  const Kpi({super.key, required this.label, required this.value, this.sub, this.valueColor});
  final String label;
  final String value;
  final String? sub;
  final Color? valueColor;

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context).textTheme;
    final scheme = Theme.of(context).colorScheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(label, style: t.labelMedium?.copyWith(color: scheme.onSurface.withValues(alpha: 0.65))),
        const SizedBox(height: 2),
        FittedBox(
          fit: BoxFit.scaleDown,
          alignment: AlignmentDirectional.centerStart,
          child: Text(value,
              style: t.titleLarge?.copyWith(
                fontWeight: FontWeight.w700,
                color: valueColor,
                fontFeatures: const [FontFeature.tabularFigures()],
              )),
        ),
        if (sub != null)
          Text(sub!, style: t.bodySmall?.copyWith(color: scheme.onSurface.withValues(alpha: 0.6))),
      ],
    );
  }
}

class SectionTitle extends StatelessWidget {
  const SectionTitle(this.text, {super.key, this.trailing});
  final String text;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 8, bottom: 8),
      child: Row(
        children: [
          Expanded(child: Text(text, style: display(context, 18))),
          ?trailing,
        ],
      ),
    );
  }
}

class EmptyNote extends StatelessWidget {
  const EmptyNote({super.key, required this.icon, required this.title, this.body});
  final IconData icon;
  final String title;
  final String? body;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 32, horizontal: 24),
      child: Column(
        children: [
          Icon(icon, size: 40, color: scheme.onSurface.withValues(alpha: 0.35)),
          const SizedBox(height: 10),
          Text(title, textAlign: TextAlign.center, style: Theme.of(context).textTheme.titleMedium),
          if (body != null) ...[
            const SizedBox(height: 6),
            Text(body!,
                textAlign: TextAlign.center,
                style: TextStyle(color: scheme.onSurface.withValues(alpha: 0.65))),
          ],
        ],
      ),
    );
  }
}

/// Shows an action's message at the bottom of the screen.
void showResult(BuildContext context, ActionResult r) {
  final messenger = ScaffoldMessenger.of(context);
  messenger.hideCurrentSnackBar();
  messenger.showSnackBar(SnackBar(
    content: Text(r.message),
    behavior: SnackBarBehavior.floating,
    backgroundColor: r.ok ? Palette.tamarisk : Palette.hair,
    duration: const Duration(seconds: 3),
  ));
}

/// Two-step confirmation inside a dialog, for costly or final actions.
Future<bool> confirmAction(BuildContext context,
    {required String title, required String body, required String confirm, bool danger = false}) async {
  final ok = await showDialog<bool>(
    context: context,
    builder: (c) => AlertDialog(
      title: Text(title),
      content: Text(body),
      actions: [
        TextButton(onPressed: () => Navigator.pop(c, false), child: const Text('إلغاء')),
        FilledButton(
          style: danger ? FilledButton.styleFrom(backgroundColor: Palette.henna) : null,
          onPressed: () => Navigator.pop(c, true),
          child: Text(confirm),
        ),
      ],
    ),
  );
  return ok == true;
}
