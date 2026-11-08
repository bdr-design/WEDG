import 'package:flutter/material.dart';

import '../../core/format.dart';
import '../../domain/models/contest.dart';
import '../../domain/models/game_state.dart';
import '../controller.dart';
import '../theme.dart';
import '../widgets/common.dart';
import 'festival_screen.dart';

class ContestsScreen extends StatelessWidget {
  const ContestsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final ctl = GameScope.of(context);
    final s = ctl.state;
    final upcoming = s.festivals.where((f) => !f.done).toList()
      ..sort((a, b) => a.judgingDay.compareTo(b.judgingDay));
    final past = s.festivals.where((f) => f.done).toList()
      ..sort((a, b) => b.judgingDay.compareTo(a.judgingDay));

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
      children: [
        Text(
          'موسم المزاين في الشتاء من أكتوبر إلى مارس. سجّل حلالك قبل ما يقفل التسجيل بأسبوع من التحكيم، وكل شوط لفئة وعمر وجنس.',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        const SizedBox(height: 12),
        if (upcoming.isEmpty)
          const EmptyNote(
            icon: Icons.wb_sunny_outlined,
            title: 'ما فيه مهرجانات قريبة',
            body: 'الصيف ما فيه مزاين. مواعيد الموسم الجاي تنزل قبل الخريف.',
          ),
        for (final f in upcoming) ...[
          _FestivalCard(festival: f),
          const SizedBox(height: 10),
        ],
        if (past.isNotEmpty) ...[
          const SectionTitle('النتائج'),
          for (final f in past) ...[
            _FestivalCard(festival: f),
            const SizedBox(height: 10),
          ],
        ],
      ],
    );
  }
}

class _FestivalCard extends StatelessWidget {
  const _FestivalCard({required this.festival});
  final Festival festival;

  @override
  Widget build(BuildContext context) {
    final s = GameScope.of(context).state;
    final f = festival;
    final t = Theme.of(context).textTheme;
    final mine = f.rounds.fold<int>(0, (a, r) => a + r.entries.length);
    final open = f.isRegistrationOpen(s.day);
    final (status, tone) = f.done
        ? ('انتهى', PillTone.neutral)
        : open
            ? ('التسجيل مفتوح لين ${formatDate(dateOfDay(f.registrationCloses))}', PillTone.good)
            : s.day < f.registrationOpens
                ? ('يفتح التسجيل ${formatDate(dateOfDay(f.registrationOpens))}', PillTone.warn)
                : ('التسجيل مقفل · التحكيم قريب', PillTone.accent);

    int? bestRank;
    var won = 0;
    if (f.done) {
      for (final r in f.rounds) {
        for (final row in r.results ?? const <ResultRow>[]) {
          if (row.isPlayer) {
            won += row.prize;
            if (bestRank == null || row.rank < bestRank) bestRank = row.rank;
          }
        }
      }
    }

    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => FestivalScreen(festivalId: f.id))),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(child: Text(f.name, style: display(context, 20))),
                  Pill(f.tier.label, tone: f.tier == FestivalTier.grand ? PillTone.warn : PillTone.neutral),
                ],
              ),
              const SizedBox(height: 4),
              Text('${f.region.label} · التحكيم ${formatDate(dateOfDay(f.judgingDay))} · ${f.rounds.length} شوط',
                  style: t.bodySmall),
              const SizedBox(height: 8),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: [
                  Pill(status, tone: tone),
                  if (mine > 0) Pill('مسجّل لك $mine', tone: PillTone.accent, icon: Icons.how_to_reg),
                  if (bestRank != null)
                    Pill('أفضل مركز $bestRank${won > 0 ? ' · ${riyalShort(won)}' : ''}',
                        tone: bestRank <= 3 ? PillTone.good : PillTone.neutral, icon: Icons.military_tech),
                ],
              ),
              if (!f.done) ...[
                const SizedBox(height: 8),
                Text(
                  'جائزة المركز الأول تصل ${riyal(f.rounds.map((r) => r.prizes.first).reduce((a, b) => a > b ? a : b))}',
                  style: t.bodyMedium?.copyWith(fontWeight: FontWeight.w600, color: Palette.saffron),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
