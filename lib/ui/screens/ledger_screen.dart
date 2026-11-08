import 'package:flutter/material.dart';

import '../../core/format.dart';
import '../../domain/models/game_state.dart';
import '../../domain/models/ledger.dart';
import '../controller.dart';
import '../theme.dart';
import '../widgets/common.dart';

/// The farm's books: month by month, income and spending by category.
class LedgerScreen extends StatelessWidget {
  const LedgerScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final s = GameScope.of(context).state;
    final t = Theme.of(context).textTheme;

    // Group by month, newest first.
    final months = <String, List<LedgerEntry>>{};
    for (final l in s.ledger.reversed) {
      final d = dateOfDay(l.day);
      months.putIfAbsent('${monthName(d.month)} ${d.year}', () => []).add(l);
    }

    return Scaffold(
      appBar: AppBar(title: const Text('الحسابات')),
      body: months.isEmpty
          ? const EmptyNote(icon: Icons.receipt_long, title: 'ما فيه حركات للحين')
          : ListView(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
              children: [
                for (final m in months.entries) ...[
                  SectionTitle(m.key, trailing: _net(context, m.value)),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(14),
                      child: Column(
                        children: [
                          for (final cat in _byCategory(m.value).entries)
                            Padding(
                              padding: const EdgeInsets.symmetric(vertical: 4),
                              child: Row(
                                children: [
                                  Expanded(child: Text(cat.key.label)),
                                  Text(
                                    riyal(cat.value),
                                    style: TextStyle(
                                      fontWeight: FontWeight.w600,
                                      color: cat.value >= 0 ? Palette.tamarisk : null,
                                      fontFeatures: const [FontFeature.tabularFigures()],
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ExpansionTile(
                            tilePadding: EdgeInsets.zero,
                            title: Text('التفاصيل (${m.value.where((l) => l.category != LedgerCategory.feed).length} حركة)', style: t.bodyMedium),
                            children: [
                              for (final l in m.value.where((l) => l.category != LedgerCategory.feed))
                                ListTile(
                                  dense: true,
                                  contentPadding: EdgeInsets.zero,
                                  title: Text(l.note),
                                  subtitle: Text(formatDate(dateOfDay(l.day))),
                                  trailing: Text(riyal(l.amount),
                                      style: TextStyle(
                                          color: l.amount >= 0 ? Palette.tamarisk : null,
                                          fontFeatures: const [FontFeature.tabularFigures()])),
                                ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                ],
              ],
            ),
    );
  }

  Map<LedgerCategory, int> _byCategory(List<LedgerEntry> list) {
    final m = <LedgerCategory, int>{};
    for (final l in list) {
      m[l.category] = (m[l.category] ?? 0) + l.amount;
    }
    final sorted = m.entries.toList()..sort((a, b) => a.value.compareTo(b.value));
    return {for (final e in sorted) e.key: e.value};
  }

  Widget _net(BuildContext context, List<LedgerEntry> list) {
    final net = list.fold<int>(0, (a, l) => a + l.amount);
    return Text(
      'الصافي ${riyal(net)}',
      style: TextStyle(fontWeight: FontWeight.w700, color: net >= 0 ? Palette.tamarisk : Palette.henna),
    );
  }
}
