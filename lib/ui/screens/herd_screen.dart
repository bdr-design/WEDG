import 'package:flutter/material.dart';

import '../../domain/models/camel.dart';
import '../../domain/models/catalog.dart';
import '../../domain/rules/judging.dart';
import '../../domain/rules/valuation.dart';
import '../controller.dart';
import '../widgets/camel_card.dart';
import '../widgets/common.dart';
import 'camel_screen.dart';

enum HerdFilter {
  all('الكل'),
  females('النوق'),
  males('الجمال'),
  young('الحيران والمفاريد'),
  pregnant('العشار'),
  sick('المريضة');

  const HerdFilter(this.label);
  final String label;
}

enum HerdSort {
  quality('الأجمل'),
  value('الأغلى'),
  age('الأكبر');

  const HerdSort(this.label);
  final String label;
}

class HerdScreen extends StatefulWidget {
  const HerdScreen({super.key});

  @override
  State<HerdScreen> createState() => _HerdScreenState();
}

class _HerdScreenState extends State<HerdScreen> {
  HerdFilter _filter = HerdFilter.all;
  HerdSort _sort = HerdSort.quality;

  bool _matches(Camel c, int today) => switch (_filter) {
        HerdFilter.all => true,
        HerdFilter.females => c.sex == Sex.female && c.ageYears(today) >= 2,
        HerdFilter.males => c.sex == Sex.male && c.ageYears(today) >= 2,
        HerdFilter.young => c.ageYears(today) < 2,
        HerdFilter.pregnant => c.isPregnantConfirmed,
        HerdFilter.sick => c.health != HealthStatus.healthy,
      };

  @override
  Widget build(BuildContext context) {
    final ctl = GameScope.of(context);
    final s = ctl.state;
    final today = s.day;
    final list = s.herd.where((c) => _matches(c, today)).toList();
    switch (_sort) {
      case HerdSort.quality:
        list.sort((a, b) => Judging.quality(b, today).compareTo(Judging.quality(a, today)));
      case HerdSort.value:
        list.sort((a, b) => Valuation.value(b, today).compareTo(Valuation.value(a, today)));
      case HerdSort.age:
        list.sort((a, b) => a.birthDay.compareTo(b.birthDay));
    }

    return Column(
      children: [
        SizedBox(
          height: 52,
          child: ListView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            children: [
              for (final f in HerdFilter.values)
                Padding(
                  padding: const EdgeInsetsDirectional.only(end: 8),
                  child: FilterChip(
                    label: Text(f.label),
                    selected: _filter == f,
                    onSelected: (_) => setState(() => _filter = f),
                  ),
                ),
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            children: [
              Text('${list.length} راس', style: Theme.of(context).textTheme.labelLarge),
              const Spacer(),
              DropdownButton<HerdSort>(
                value: _sort,
                underline: const SizedBox(),
                items: [for (final o in HerdSort.values) DropdownMenuItem(value: o, child: Text(o.label))],
                onChanged: (v) => setState(() => _sort = v ?? _sort),
              ),
            ],
          ),
        ),
        Expanded(
          child: list.isEmpty
              ? const EmptyNote(
                  icon: Icons.pets,
                  title: 'ما فيه حلال بهالتصنيف',
                  body: 'اشترِ من السوق أو لقّح نوقك في موسم التلقيح.',
                )
              : ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
                  itemCount: list.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 10),
                  itemBuilder: (context, i) => CamelCard(
                    camel: list[i],
                    engine: ctl.engine,
                    onTap: () => openCamel(context, list[i].id),
                  ),
                ),
        ),
      ],
    );
  }
}
