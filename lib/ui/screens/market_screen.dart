import 'package:flutter/material.dart';

import '../../core/format.dart';
import '../../domain/models/camel.dart';
import '../../domain/models/catalog.dart';
import '../../domain/models/region.dart';
import '../../domain/rules/judging.dart';
import '../controller.dart';
import '../widgets/camel_card.dart';
import '../widgets/common.dart';
import 'camel_screen.dart';

enum MarketSort {
  newest('الأحدث'),
  cheap('الأرخص'),
  quality('الأجمل');

  const MarketSort(this.label);
  final String label;
}

class MarketScreen extends StatefulWidget {
  const MarketScreen({super.key});

  @override
  State<MarketScreen> createState() => _MarketScreenState();
}

class _MarketScreenState extends State<MarketScreen> {
  ColorCategory? _category;
  Sex? _sex;
  Region? _region;
  MarketSort _sort = MarketSort.newest;

  @override
  Widget build(BuildContext context) {
    final ctl = GameScope.of(context);
    final s = ctl.state;
    final myListings = s.listings.where((l) => l.sellerId == playerOwnerId).toList();

    return DefaultTabController(
      length: 3,
      child: Column(
        children: [
          TabBar(
            tabs: [
              const Tab(text: 'المعروض'),
              const Tab(text: 'فحول التلقيح'),
              Tab(text: myListings.isEmpty ? 'عروضي' : 'عروضي (${myListings.length})'),
            ],
          ),
          Expanded(
            child: TabBarView(
              children: [
                _forSale(context),
                _studs(context),
                _mine(context),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _forSale(BuildContext context) {
    final ctl = GameScope.of(context);
    final s = ctl.state;
    final e = ctl.engine;
    final today = s.day;
    var list = s.listings.where((l) => l.sellerId != playerOwnerId).toList();
    list = list.where((l) {
      final c = s.camels[l.camelId];
      if (c == null) return false;
      if (_category != null && c.category != _category) return false;
      if (_sex != null && c.sex != _sex) return false;
      if (_region != null && l.region != _region) return false;
      return true;
    }).toList();
    switch (_sort) {
      case MarketSort.newest:
        list.sort((a, b) => b.listedDay.compareTo(a.listedDay));
      case MarketSort.cheap:
        list.sort((a, b) => a.askPrice.compareTo(b.askPrice));
      case MarketSort.quality:
        list.sort((a, b) => Judging.quality(s.camels[b.camelId]!, today)
            .compareTo(Judging.quality(s.camels[a.camelId]!, today)));
    }

    return Column(
      children: [
        SizedBox(
          height: 52,
          child: ListView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            children: [
              _menuChip<ColorCategory?>(
                label: _category?.label ?? 'كل الفئات',
                active: _category != null,
                values: [null, ...ColorCategory.values],
                labelOf: (v) => v?.label ?? 'كل الفئات',
                onPick: (v) => setState(() => _category = v),
              ),
              _menuChip<Sex?>(
                label: _sex == null ? 'نوق وجمال' : (_sex == Sex.female ? 'نوق' : 'جمال'),
                active: _sex != null,
                values: const [null, Sex.female, Sex.male],
                labelOf: (v) => v == null ? 'نوق وجمال' : (v == Sex.female ? 'نوق' : 'جمال'),
                onPick: (v) => setState(() => _sex = v),
              ),
              _menuChip<Region?>(
                label: _region?.label ?? 'كل الأسواق',
                active: _region != null,
                values: [null, ...Region.values],
                labelOf: (v) => v?.marketName ?? 'كل الأسواق',
                onPick: (v) => setState(() => _region = v),
              ),
              _menuChip<MarketSort>(
                label: 'الترتيب: ${_sort.label}',
                active: false,
                values: MarketSort.values,
                labelOf: (v) => v.label,
                onPick: (v) => setState(() => _sort = v),
              ),
            ],
          ),
        ),
        Expanded(
          child: list.isEmpty
              ? const EmptyNote(icon: Icons.storefront, title: 'ما فيه معروض بهالتصفية')
              : ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
                  itemCount: list.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 10),
                  itemBuilder: (context, i) {
                    final l = list[i];
                    final c = s.camels[l.camelId]!;
                    return CamelCard(
                      camel: c,
                      engine: e,
                      priceLine: riyal(l.askPrice),
                      subLine: '${l.region.marketName} · ${l.sellerName}${l.listedDay == today ? ' · جديد' : ''}',
                      onTap: () => openCamel(context, c.id),
                    );
                  },
                ),
        ),
      ],
    );
  }

  Widget _menuChip<T>({
    required String label,
    required bool active,
    required List<T> values,
    required String Function(T) labelOf,
    required ValueChanged<T> onPick,
  }) {
    return Padding(
      padding: const EdgeInsetsDirectional.only(end: 8),
      child: PopupMenuButton<int>(
        onSelected: (i) => onPick(values[i]),
        itemBuilder: (_) => [
          for (var i = 0; i < values.length; i++) PopupMenuItem(value: i, child: Text(labelOf(values[i]))),
        ],
        child: Chip(
          label: Text(label),
          avatar: const Icon(Icons.expand_more, size: 18),
          backgroundColor: active ? Theme.of(context).colorScheme.primary.withValues(alpha: 0.12) : null,
        ),
      ),
    );
  }

  Widget _studs(BuildContext context) {
    final ctl = GameScope.of(context);
    final s = ctl.state;
    final e = ctl.engine;
    final list = s.studs.where((st) => s.camels[st.camelId] != null).toList()
      ..sort((a, b) => Judging.quality(s.camels[b.camelId]!, s.day).compareTo(Judging.quality(s.camels[a.camelId]!, s.day)));
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
      children: [
        Text(
          e.isBreedingSeason()
              ? 'موسم التلقيح شغّال. اختر فحل وودّ له ناقتك. فحص الحمل بعد ٢١ يوم.'
              : 'الحين مو موسم تلقيح. الموسم من نوفمبر إلى أبريل، والفحول المعروضة أقل.',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        const SizedBox(height: 10),
        if (list.isEmpty) const EmptyNote(icon: Icons.pets, title: 'ما فيه فحول معروضة الحين'),
        for (final st in list) ...[
          CamelCard(
            camel: s.camels[st.camelId]!,
            engine: e,
            priceLine: 'أجرة الضراب ${riyal(st.fee)}',
            subLine: '${st.ownerName} · ${st.region.label}',
            onTap: () => openCamel(context, st.camelId),
          ),
          const SizedBox(height: 10),
        ],
      ],
    );
  }

  Widget _mine(BuildContext context) {
    final ctl = GameScope.of(context);
    final s = ctl.state;
    final e = ctl.engine;
    final mine = s.listings.where((l) => l.sellerId == playerOwnerId).toList();
    if (mine.isEmpty) {
      return const EmptyNote(
        icon: Icons.sell_outlined,
        title: 'ما عندك شي معروض',
        body: 'افتح أي راس من حلالك واختر "اعرض للبيع"، والسوّام بيجونك مع الأيام.',
      );
    }
    return ListView.separated(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
      itemCount: mine.length,
      separatorBuilder: (_, _) => const SizedBox(height: 10),
      itemBuilder: (context, i) {
        final l = mine[i];
        final c = s.camels[l.camelId]!;
        final offers = s.buyerOffers.where((o) => o.listingId == l.id).toList();
        final best = offers.isEmpty ? null : offers.map((o) => o.amount).reduce((a, b) => a > b ? a : b);
        return CamelCard(
          camel: c,
          engine: e,
          priceLine: 'مطلوب ${riyal(l.askPrice)}',
          subLine: offers.isEmpty
              ? 'ما فيه سوم · باقي ${formatDays(l.expiresDay - s.day)}'
              : '${offers.length} سوم · أعلى سوم ${riyal(best!)}',
          onTap: () => openCamel(context, c.id),
        );
      },
    );
  }
}
