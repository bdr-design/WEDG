import 'package:flutter/material.dart';

import '../../core/format.dart';
import '../../domain/models/camel.dart';
import '../../domain/models/farm.dart';
import '../../domain/models/game_state.dart';
import '../../domain/rules/constants.dart';
import '../controller.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../widgets/news_tile.dart';
import 'camel_screen.dart';
import 'festival_screen.dart';
import 'ledger_screen.dart';

class FarmScreen extends StatelessWidget {
  const FarmScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final ctl = GameScope.of(context);
    final s = ctl.state;
    final e = ctl.engine;
    final scheme = Theme.of(context).colorScheme;
    final t = Theme.of(context).textTheme;

    final herd = s.herd.toList();
    final sick = herd.where((c) => c.health == HealthStatus.sick).toList();
    final dueSoon = herd
        .where((c) => c.isPregnantConfirmed && c.pregnancy!.dueDay - s.day <= 30)
        .toList();
    final needed = e.shepherdsNeeded();
    final upcoming = s.festivals.where((f) => !f.done).toList()
      ..sort((a, b) => a.judgingDay.compareTo(b.judgingDay));
    final herdValue = e.herdValue();

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
      children: [
        // Farm identity and headline numbers.
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(s.farm.name, style: display(context, 26)),
                Text('${s.playerName} · ${s.farm.region.label} · قريب من ${s.farm.region.marketName}',
                    style: t.bodyMedium?.copyWith(color: scheme.onSurface.withValues(alpha: 0.7))),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(child: Kpi(label: 'الرصيد', value: riyalShort(s.cash), valueColor: s.cash < 0 ? Palette.henna : null)),
                    Expanded(child: Kpi(label: 'قيمة الحلال التقديرية', value: riyalShort(herdValue))),
                    Expanded(child: Kpi(label: 'الحلال', value: '${herd.length} / ${s.farm.capacity}', sub: 'راس / السعة')),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),

        // What needs attention today.
        if (sick.isNotEmpty || dueSoon.isNotEmpty || s.buyerOffers.isNotEmpty || s.farm.shepherds < needed || herd.length > s.farm.capacity)
          Card(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Column(
                children: [
                  for (final c in sick)
                    _Alert(
                      icon: Icons.healing,
                      color: Palette.henna,
                      text: '${c.name} مريضة (${c.illness}) من ${formatDays(c.sickDays)}',
                      action: 'عالجها',
                      onTap: () => showResult(context, ctl.run((e) => e.treat(c.id))),
                    ),
                  if (s.farm.shepherds < needed)
                    _Alert(
                      icon: Icons.groups,
                      color: Palette.saffron,
                      text: 'الرعاة ما يكفون: عندك ${s.farm.shepherds} وتحتاج $needed. الحالة بتنزل.',
                    ),
                  if (herd.length > s.farm.capacity)
                    const _Alert(
                      icon: Icons.fence,
                      color: Palette.saffron,
                      text: 'العزبة مزحومة فوق سعتها. المرض يزيد والحالة تنزل.',
                    ),
                  for (final c in dueSoon)
                    _Alert(
                      icon: Icons.child_friendly,
                      color: Palette.tamarisk,
                      text: '${c.name} قريبة ولادة، بعد ${formatDays(c.pregnancy!.dueDay - s.day)}',
                      onTap: () => openCamel(context, c.id),
                    ),
                  if (s.buyerOffers.isNotEmpty)
                    _Alert(
                      icon: Icons.local_offer,
                      color: scheme.primary,
                      text: 'عندك ${s.buyerOffers.length} سوم من مشترين في السوق.',
                    ),
                ],
              ),
            ),
          ),
        if (sick.isNotEmpty || dueSoon.isNotEmpty || s.buyerOffers.isNotEmpty) const SizedBox(height: 12),

        // Running the farm.
        SectionTitle('تشغيل العزبة',
            trailing: TextButton.icon(
              onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const LedgerScreen())),
              icon: const Icon(Icons.receipt_long, size: 18),
              label: const Text('الحسابات'),
            )),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('العلف', style: t.titleSmall),
                const SizedBox(height: 8),
                SegmentedButton<FeedPlan>(
                  showSelectedIcon: false,
                  segments: [
                    for (final p in FeedPlan.values) ButtonSegment(value: p, label: Text(p.label)),
                  ],
                  selected: {s.farm.feedPlan},
                  onSelectionChanged: (v) => ctl.apply((e) => e.setFeedPlan(v.first)),
                ),
                const SizedBox(height: 6),
                Text('${s.farm.feedPlan.detail}. الحالة المتوقعة ${s.farm.feedPlan.conditionTarget} من 100.',
                    style: t.bodySmall),
                const SizedBox(height: 4),
                Text('تكلفة العلف اليوم: ${riyal(e.dailyFeedCost())} (حوالي ${riyal(e.dailyFeedCost() * 30)} بالشهر)',
                    style: t.bodyMedium?.copyWith(fontWeight: FontWeight.w600)),
                const Divider(height: 28),
                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('الرعاة', style: t.titleSmall),
                          Text('${s.farm.shepherds} راعي · تحتاج $needed لـ ${herd.length} راس · ${riyal(e.monthlyWages())} بالشهر',
                              style: t.bodySmall),
                        ],
                      ),
                    ),
                    IconButton.outlined(
                      tooltip: 'نقّص راعي',
                      onPressed: s.farm.shepherds > 1 ? () => ctl.apply((e) => e.setShepherds(s.farm.shepherds - 1)) : null,
                      icon: const Icon(Icons.remove),
                    ),
                    const SizedBox(width: 6),
                    IconButton.outlined(
                      tooltip: 'زد راعي',
                      onPressed: () => ctl.apply((e) => e.setShepherds(s.farm.shepherds + 1)),
                      icon: const Icon(Icons.add),
                    ),
                  ],
                ),
                const Divider(height: 28),
                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('السعة', style: t.titleSmall),
                          Text('${s.farm.capacity} راس. التوسعة +$expansionStep بـ ${riyal(e.expansionCost())}',
                              style: t.bodySmall),
                        ],
                      ),
                    ),
                    OutlinedButton(
                      onPressed: () async {
                        final ok = await confirmAction(context,
                            title: 'توسعة العزبة',
                            body: 'بناء شبوك ومظلات ومشارب لـ $expansionStep رؤوس إضافية بتكلفة ${riyal(e.expansionCost())}.',
                            confirm: 'ابنِ');
                        if (ok && context.mounted) showResult(context, ctl.run((e) => e.expand()));
                      },
                      child: const Text('وسّع'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),

        // Next contest.
        if (upcoming.isNotEmpty) ...[
          const SectionTitle('المهرجان الجاي'),
          Card(
            child: ListTile(
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
              leading: const Icon(Icons.emoji_events, color: Palette.saffron),
              title: Text(upcoming.first.name, style: const TextStyle(fontWeight: FontWeight.w700)),
              subtitle: Text(
                  '${upcoming.first.tier.label} · ${upcoming.first.region.label} · التحكيم ${formatDate(dateOfDay(upcoming.first.judgingDay))}'),
              trailing: const Icon(Icons.chevron_left),
              onTap: () => Navigator.push(context,
                  MaterialPageRoute(builder: (_) => FestivalScreen(festivalId: upcoming.first.id))),
            ),
          ),
          const SizedBox(height: 12),
        ],

        // Activity log.
        const SectionTitle('آخر الأخبار'),
        Card(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Column(
              children: [
                for (final n in s.news.reversed.take(25)) NewsTile(item: n, showDate: true),
              ],
            ),
          ),
        ),
        const SizedBox(height: 24),
        Center(
          child: TextButton(
            onPressed: () async {
              final ok = await confirmAction(context,
                  title: 'لعبة جديدة',
                  body: 'بتنمسح العزبة الحالية وكل الحلال والحسابات. ما تقدر ترجعها.',
                  confirm: 'امسح وابدأ من جديد',
                  danger: true);
              if (ok) await ctl.endGame();
            },
            child: Text('لعبة جديدة', style: TextStyle(color: scheme.onSurface.withValues(alpha: 0.6))),
          ),
        ),
      ],
    );
  }
}

class _Alert extends StatelessWidget {
  const _Alert({required this.icon, required this.color, required this.text, this.action, this.onTap});
  final IconData icon;
  final Color color;
  final String text;
  final String? action;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: action == null ? onTap : null,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Row(
          children: [
            Icon(icon, color: color, size: 20),
            const SizedBox(width: 10),
            Expanded(child: Text(text)),
            if (action != null) TextButton(onPressed: onTap, child: Text(action!)),
          ],
        ),
      ),
    );
  }
}
