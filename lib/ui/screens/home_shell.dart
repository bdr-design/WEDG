import 'package:flutter/material.dart';

import '../../core/format.dart';
import '../../domain/models/camel.dart';
import '../../domain/models/ledger.dart';
import '../controller.dart';
import '../theme.dart';
import '../widgets/news_tile.dart';
import 'contests_screen.dart';
import 'farm_screen.dart';
import 'herd_screen.dart';
import 'market_screen.dart';

class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _tab = 0;

  static const _titles = ['العزبة', 'الحلال', 'السوق', 'المشاركات'];

  void _advance(int days) {
    final news = GameScope.read(context).advance(days);
    final important = news.where((n) => n.kind != NewsKind.market).toList();
    if (important.isEmpty && news.isEmpty) return;
    showModalBottomSheet(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      builder: (c) => _DaySummary(days: days, news: news),
    );
  }

  @override
  Widget build(BuildContext context) {
    final ctl = GameScope.of(context);
    final s = ctl.state;
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: Text(_titles[_tab]),
        actions: [
          _TimeButton(label: 'يوم', icon: Icons.chevron_left, onTap: () => _advance(1)),
          const SizedBox(width: 6),
          _TimeButton(label: 'أسبوع', icon: Icons.keyboard_double_arrow_left, onTap: () => _advance(7)),
          const SizedBox(width: 12),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(34),
          child: Container(
            height: 34,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            color: scheme.surfaceContainerLow,
            child: Row(
              children: [
                Icon(Icons.calendar_today_outlined, size: 15, color: scheme.onSurface.withValues(alpha: 0.7)),
                const SizedBox(width: 6),
                Text(formatDate(s.date), style: const TextStyle(fontWeight: FontWeight.w600)),
                const Spacer(),
                Icon(Icons.account_balance_wallet_outlined, size: 15, color: scheme.onSurface.withValues(alpha: 0.7)),
                const SizedBox(width: 6),
                Text(
                  riyal(s.cash),
                  style: TextStyle(
                    fontWeight: FontWeight.w700,
                    color: s.cash < 0 ? Palette.henna : null,
                    fontFeatures: const [FontFeature.tabularFigures()],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
      body: IndexedStack(
        index: _tab,
        children: const [FarmScreen(), HerdScreen(), MarketScreen(), ContestsScreen()],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (i) => setState(() => _tab = i),
        destinations: [
          const NavigationDestination(icon: Icon(Icons.cottage_outlined), selectedIcon: Icon(Icons.cottage), label: 'العزبة'),
          NavigationDestination(
            icon: Badge.count(
              count: s.herd.where((c) => c.health == HealthStatus.sick).length,
              isLabelVisible: s.herd.any((c) => c.health == HealthStatus.sick),
              child: const Icon(Icons.pets_outlined),
            ),
            selectedIcon: const Icon(Icons.pets),
            label: 'الحلال',
          ),
          NavigationDestination(
            icon: Badge.count(
              count: s.buyerOffers.length,
              isLabelVisible: s.buyerOffers.isNotEmpty,
              child: const Icon(Icons.storefront_outlined),
            ),
            selectedIcon: const Icon(Icons.storefront),
            label: 'السوق',
          ),
          const NavigationDestination(icon: Icon(Icons.emoji_events_outlined), selectedIcon: Icon(Icons.emoji_events), label: 'المشاركات'),
        ],
      ),
    );
  }
}

class _TimeButton extends StatelessWidget {
  const _TimeButton({required this.label, required this.icon, required this.onTap});
  final String label;
  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return FilledButton.tonal(
      onPressed: onTap,
      style: FilledButton.styleFrom(
        minimumSize: const Size(44, 40),
        padding: const EdgeInsets.symmetric(horizontal: 12),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [Text(label), const SizedBox(width: 2), Icon(icon, size: 18)],
      ),
    );
  }
}

class _DaySummary extends StatelessWidget {
  const _DaySummary({required this.days, required this.news});
  final int days;
  final List<NewsItem> news;

  @override
  Widget build(BuildContext context) {
    final s = GameScope.of(context).state;
    final spent = s.ledger
        .where((l) => l.day > s.day - days && l.amount < 0)
        .fold<int>(0, (a, l) => a + l.amount);
    final earned = s.ledger
        .where((l) => l.day > s.day - days && l.amount > 0)
        .fold<int>(0, (a, l) => a + l.amount);
    return SafeArea(
      child: ConstrainedBox(
        constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.75),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(days == 1 ? 'مرّ يوم' : 'مرّ $days أيام', style: display(context, 20)),
              const SizedBox(height: 4),
              Text(
                'المصاريف ${riyal(-spent)}${earned > 0 ? ' · الدخل ${riyal(earned)}' : ''}',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 12),
              Flexible(
                child: ListView(
                  shrinkWrap: true,
                  children: [
                    for (final n in news.reversed) NewsTile(item: n),
                    if (news.isEmpty)
                      const Padding(
                        padding: EdgeInsets.all(12),
                        child: Text('ما صار شي جديد. الحلال بخير.'),
                      ),
                  ],
                ),
              ),
              const SizedBox(height: 8),
              FilledButton(onPressed: () => Navigator.pop(context), child: const Text('تمام')),
            ],
          ),
        ),
      ),
    );
  }
}
