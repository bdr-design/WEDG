import 'package:flutter/material.dart';

import '../../core/format.dart';
import '../../domain/models/catalog.dart';
import '../../domain/models/region.dart';
import '../../domain/rules/constants.dart';
import '../controller.dart';
import '../theme.dart';
import '../widgets/camel_silhouette.dart';
import '../widgets/common.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final _name = TextEditingController();
  final _farm = TextEditingController();
  Region _region = Region.qassim;
  ColorCategory _favourite = ColorCategory.majaheem;
  bool _busy = false;

  @override
  void dispose() {
    _name.dispose();
    _farm.dispose();
    super.dispose();
  }

  Future<void> _start() async {
    final name = _name.text.trim().isEmpty ? 'أبو فلان' : _name.text.trim();
    final farm = _farm.text.trim().isEmpty ? 'عزبة $name' : _farm.text.trim();
    setState(() => _busy = true);
    await GameScope.read(context).startNewGame(
      playerName: name,
      farmName: farm,
      region: _region,
      favourite: _favourite,
    );
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final t = Theme.of(context).textTheme;
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 560),
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 24, 20, 32),
              children: [
                SizedBox(
                  height: 150,
                  child: CustomPaint(
                    painter: CamelSilhouettePainter(
                      coat: coatColor(_favourite),
                      shade: shadeColor(_favourite),
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                Text('مراح', style: display(context, 44), textAlign: TextAlign.center),
                Text(
                  'ابنِ حلالك من أول راس: اشترِ من الأسواق، لقّح من أطيب الفحول، وشارك في المزاين.',
                  textAlign: TextAlign.center,
                  style: t.bodyLarge?.copyWith(color: scheme.onSurface.withValues(alpha: 0.75)),
                ),
                const SizedBox(height: 28),
                TextField(
                  key: const ValueKey('name'),
                  controller: _name,
                  textInputAction: TextInputAction.next,
                  decoration: const InputDecoration(labelText: 'اسمك أو كنيتك', hintText: 'مثل: أبو سعود'),
                ),
                const SizedBox(height: 14),
                TextField(
                  key: const ValueKey('farm'),
                  controller: _farm,
                  decoration: const InputDecoration(labelText: 'اسم العزبة', hintText: 'مثل: عزبة الصفوة'),
                ),
                const SizedBox(height: 22),
                Text('مقر العزبة', style: t.titleMedium),
                const SizedBox(height: 4),
                Text(
                  'المنطقة تحدد أسعار العلف وتكلفة البناء والمسافة للمهرجانات والأسواق.',
                  style: t.bodySmall?.copyWith(color: scheme.onSurface.withValues(alpha: 0.65)),
                ),
                const SizedBox(height: 10),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    for (final r in Region.values)
                      ChoiceChip(
                        label: Text(r.label),
                        selected: _region == r,
                        onSelected: (_) => setState(() => _region = r),
                      ),
                  ],
                ),
                const SizedBox(height: 8),
                _RegionNote(region: _region),
                const SizedBox(height: 22),
                Text('فئتك', style: t.titleMedium),
                const SizedBox(height: 4),
                Text(
                  'تبدأ بثلاث نوق من هالفئة. تقدر تشتري من كل الفئات بعدين.',
                  style: t.bodySmall?.copyWith(color: scheme.onSurface.withValues(alpha: 0.65)),
                ),
                const SizedBox(height: 10),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    for (final c in ColorCategory.values)
                      ChoiceChip(
                        avatar: ColorSwatchDot(c, size: 14),
                        label: Text(c.label),
                        selected: _favourite == c,
                        onSelected: (_) => setState(() => _favourite = c),
                      ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(_favourite.description,
                    style: t.bodyMedium?.copyWith(color: scheme.onSurface.withValues(alpha: 0.8))),
                const SizedBox(height: 28),
                FilledButton.icon(
                  key: const ValueKey('start'),
                  onPressed: _busy ? null : _start,
                  icon: const Icon(Icons.play_arrow_rounded),
                  label: Text('ابدأ برأس مال ${riyalShort(startingCash)} ريال'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _RegionNote extends StatelessWidget {
  const _RegionNote({required this.region});
  final Region region;

  @override
  Widget build(BuildContext context) {
    String pct(double f) {
      final d = ((f - 1) * 100).round();
      if (d == 0) return 'متوسط';
      return d < 0 ? 'أرخص ${-d}٪' : 'أغلى $d٪';
    }

    return Text(
      '${region.marketName} · العلف ${pct(region.feed)} · البناء ${pct(region.land)}',
      style: Theme.of(context).textTheme.bodySmall,
    );
  }
}
