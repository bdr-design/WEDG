import 'package:flutter/material.dart';

import '../../core/format.dart';
import '../../domain/models/catalog.dart';
import '../../domain/models/contest.dart';
import '../../domain/models/game_state.dart';
import '../../domain/rules/constants.dart';
import '../../domain/rules/judging.dart';
import '../controller.dart';
import '../theme.dart';
import '../widgets/common.dart';
import 'camel_screen.dart';

/// One festival: its rounds by colour family, entries and results.
class FestivalScreen extends StatefulWidget {
  const FestivalScreen({super.key, required this.festivalId});
  final String festivalId;

  @override
  State<FestivalScreen> createState() => _FestivalScreenState();
}

class _FestivalScreenState extends State<FestivalScreen> {
  ColorCategory? _category;

  @override
  Widget build(BuildContext context) {
    final ctl = GameScope.of(context);
    final s = ctl.state;
    final e = ctl.engine;
    final f = s.festivals.where((x) => x.id == widget.festivalId).firstOrNull;
    if (f == null) {
      return Scaffold(appBar: AppBar(), body: const EmptyNote(icon: Icons.event_busy, title: 'المهرجان غير موجود'));
    }
    final categories = {for (final r in f.rounds) r.category}.toList();
    final cat = _category ?? (categories.contains(_favourite(s)) ? _favourite(s) : categories.first);
    final rounds = f.rounds.where((r) => r.category == cat).toList();
    final km = s.farm.region.roadKmTo(f.region);
    final t = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(title: Text(f.name)),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(children: [
                    Expanded(child: Text(f.tier.label, style: t.titleSmall)),
                    Text(f.region.label, style: t.titleSmall),
                  ]),
                  const SizedBox(height: 8),
                  _row(context, 'التسجيل', '${formatDate(dateOfDay(f.registrationOpens))} إلى ${formatDate(dateOfDay(f.registrationCloses))}'),
                  _row(context, 'التحكيم', formatDate(dateOfDay(f.judgingDay))),
                  _row(context, 'المسافة من العزبة', '$km كم · النقل ذهاب وعودة ${riyal(transportCost(km, 1) * 2)} لراس واحد'),
                  const SizedBox(height: 8),
                  Text(
                    'شروط الدخول: شريحة إلكترونية، الملكية باسمك قبل التحكيم بشهر على الأقل (إلا مواليد عزبتك)، والناقة سليمة يوم الفحص البيطري. العمر يُحسب يوم التحكيم.',
                    style: t.bodySmall,
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          SizedBox(
            height: 44,
            child: ListView(
              scrollDirection: Axis.horizontal,
              children: [
                for (final c in categories)
                  Padding(
                    padding: const EdgeInsetsDirectional.only(end: 8),
                    child: ChoiceChip(
                      avatar: ColorSwatchDot(c, size: 14),
                      label: Text(c.label),
                      selected: c == cat,
                      onSelected: (_) => setState(() => _category = c),
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          for (final r in rounds) ...[
            _RoundCard(festival: f, round: r),
            const SizedBox(height: 10),
          ],
          if (!f.done && !f.isRegistrationOpen(s.day) && s.day < f.registrationOpens)
            Text('التسجيل يفتح بعد ${formatDays(f.registrationOpens - s.day)}.', style: t.bodySmall),
          if (e.s.herd.isEmpty) const EmptyNote(icon: Icons.pets, title: 'ما عندك حلال تسجله'),
        ],
      ),
    );
  }

  ColorCategory _favourite(GameState s) {
    final counts = <ColorCategory, int>{};
    for (final c in s.herd) {
      counts[c.category] = (counts[c.category] ?? 0) + 1;
    }
    if (counts.isEmpty) return ColorCategory.majaheem;
    return counts.entries.reduce((a, b) => a.value >= b.value ? a : b).key;
  }

  Widget _row(BuildContext context, String k, String v) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 3),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(width: 120, child: Text(k, style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.65)))),
            Expanded(child: Text(v, style: const TextStyle(fontWeight: FontWeight.w600))),
          ],
        ),
      );
}

class _RoundCard extends StatelessWidget {
  const _RoundCard({required this.festival, required this.round});
  final Festival festival;
  final ContestRound round;

  @override
  Widget build(BuildContext context) {
    final ctl = GameScope.of(context);
    final s = ctl.state;
    final e = ctl.engine;
    final f = festival;
    final r = round;
    final t = Theme.of(context).textTheme;
    final scheme = Theme.of(context).colorScheme;
    final open = f.isRegistrationOpen(s.day);
    final eligible = s.herd.where((c) => e.entryProblem(c, f, r) == null).toList()
      ..sort((a, b) => Judging.quality(b, s.day).compareTo(Judging.quality(a, s.day)));

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(child: Text(r.title, style: t.titleMedium?.copyWith(fontWeight: FontWeight.w700))),
                Text('${r.fieldSize + r.entries.length} مشارك', style: t.labelMedium),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              'الجوائز: الأول ${riyal(r.prizes[0])} · الثاني ${riyal(r.prizes[1])} · الثالث ${riyal(r.prizes[2])} · لين العاشر ${riyal(r.prizes.last)}',
              style: t.bodySmall,
            ),
            if (r.entries.isNotEmpty) ...[
              const SizedBox(height: 8),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: [
                  for (final id in r.entries)
                    if (s.camels[id] != null)
                      InputChip(
                        label: Text(s.camels[id]!.name),
                        onPressed: () => openCamel(context, id),
                        onDeleted: f.done ? null : () => showResult(context, ctl.run((e) => e.withdraw(f.id, r.id, id))),
                      ),
                ],
              ),
            ],
            if (open) ...[
              const SizedBox(height: 8),
              Align(
                alignment: AlignmentDirectional.centerStart,
                child: OutlinedButton.icon(
                  onPressed: eligible.isEmpty
                      ? null
                      : () async {
                          final picked = await showModalBottomSheet<String>(
                            context: context,
                            showDragHandle: true,
                            builder: (c) => SafeArea(
                              child: ListView(
                                shrinkWrap: true,
                                children: [
                                  Padding(
                                    padding: const EdgeInsets.symmetric(horizontal: 16),
                                    child: Text('سجّل في ${r.title}', style: display(c, 18)),
                                  ),
                                  for (final cm in eligible)
                                    ListTile(
                                      leading: SizedBox(width: 56, child: CamelImage(camel: cm, today: s.day, height: 42, backdrop: false)),
                                      title: Text(cm.name),
                                      subtitle: Text(
                                          '${Judging.quality(cm, s.day).toStringAsFixed(1)} · ${Judging.grade(Judging.quality(cm, s.day))} · الحالة ${cm.condition.round()}'),
                                      onTap: () => Navigator.pop(c, cm.id),
                                    ),
                                ],
                              ),
                            ),
                          );
                          if (picked != null && context.mounted) {
                            showResult(context, ctl.run((e) => e.enter(f.id, r.id, picked)));
                          }
                        },
                  icon: const Icon(Icons.add),
                  label: Text(eligible.isEmpty ? 'ما عندك حلال يناسب هالشوط' : 'سجّل من حلالك (${eligible.length})'),
                ),
              ),
            ],
            if (r.results != null) ...[
              const Divider(height: 22),
              for (final row in r.results!)
                Container(
                  margin: const EdgeInsets.only(bottom: 4),
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                  decoration: row.isPlayer
                      ? BoxDecoration(color: Palette.saffron.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(8))
                      : null,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          SizedBox(
                            width: 30,
                            child: Text('${row.rank}',
                                style: TextStyle(fontWeight: FontWeight.w700, color: row.rank <= 3 ? Palette.saffron : null)),
                          ),
                          Expanded(
                            child: Text('${row.camelName} · ${row.ownerName}',
                                style: TextStyle(fontWeight: row.isPlayer ? FontWeight.w700 : FontWeight.w400)),
                          ),
                          Text(row.score.toStringAsFixed(2),
                              style: const TextStyle(fontFeatures: [FontFeature.tabularFigures()])),
                          const SizedBox(width: 10),
                          SizedBox(
                            width: 70,
                            child: Text(row.prize > 0 ? riyalShort(row.prize) : '—',
                                textAlign: TextAlign.end, style: t.bodySmall),
                          ),
                        ],
                      ),
                      if (row.isPlayer && row.breakdown != null)
                        Padding(
                          padding: const EdgeInsetsDirectional.only(start: 30, top: 4),
                          child: Wrap(
                            spacing: 10,
                            runSpacing: 2,
                            children: [
                              for (final e in row.breakdown!.entries)
                                Text('${e.key.label} ${e.value.toStringAsFixed(1)}',
                                    style: t.bodySmall?.copyWith(color: scheme.onSurface.withValues(alpha: 0.75))),
                            ],
                          ),
                        ),
                    ],
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }
}
