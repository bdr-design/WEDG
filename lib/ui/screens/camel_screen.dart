import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/format.dart';
import '../../domain/engine/game_engine.dart';
import '../../domain/models/camel.dart';
import '../../domain/models/catalog.dart';
import '../../domain/models/contest.dart';
import '../../domain/models/game_state.dart';
import '../../domain/models/market.dart';
import '../../domain/rules/judging.dart';
import '../../domain/rules/valuation.dart';
import '../controller.dart';
import '../theme.dart';
import '../widgets/common.dart';

void openCamel(BuildContext context, String camelId) => Navigator.push(
    context, MaterialPageRoute(builder: (_) => CamelScreen(camelId: camelId)));

/// Full record of one camel: looks, judged features, pedigree, record, and
/// what the player can do with it (sell, mate, enter, buy, bargain).
class CamelScreen extends StatelessWidget {
  const CamelScreen({super.key, required this.camelId});
  final String camelId;

  @override
  Widget build(BuildContext context) {
    final ctl = GameScope.of(context);
    final s = ctl.state;
    final e = ctl.engine;
    final c = s.camels[camelId];
    if (c == null) {
      return Scaffold(
        appBar: AppBar(),
        body: const EmptyNote(icon: Icons.search_off, title: 'هالراس ما عاد موجود', body: 'انباع أو انتهى عرضه.'),
      );
    }
    final listing = s.listings.where((l) => l.camelId == c.id).firstOrNull;
    final stud = s.studs.where((st) => st.camelId == c.id).firstOrNull;
    final t = Theme.of(context).textTheme;
    final scheme = Theme.of(context).colorScheme;
    final q = Judging.quality(c, s.day);
    final phen = Judging.phenotypes(c, s.day);
    final (lo, hi) = Valuation.estimateRange(c, s.day);

    return Scaffold(
      appBar: AppBar(
        title: Text(c.name),
        actions: [
          if (c.isPlayers)
            IconButton(
              tooltip: 'غيّر الاسم',
              icon: const Icon(Icons.edit_outlined),
              onPressed: () => _rename(context, c),
            ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        children: [
          CamelImage(camel: c, today: s.day, height: 220),
          const SizedBox(height: 14),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(c.name, style: display(context, 30)),
                    const SizedBox(height: 4),
                    Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: [
                        Pill(c.category.label, icon: Icons.circle),
                        Pill(c.sex.label),
                        Pill('${c.ageLabel(s.day)} · ${formatAgeDays(c.ageDays(s.day))}'),
                      ],
                    ),
                  ],
                ),
              ),
              QualityBadge(quality: q, large: true),
            ],
          ),
          const SizedBox(height: 10),
          Wrap(spacing: 6, runSpacing: 6, children: camelPills(context, c, e)),
          const SizedBox(height: 14),

          // Ownership / sale context.
          if (!c.isPlayers && listing != null) _MarketBox(listing: listing, camel: c),
          if (!c.isPlayers && stud != null) _StudBox(stud: stud, camel: c),
          if (c.isPlayers) _OwnerActions(camel: c),
          const SizedBox(height: 14),

          // Judged features.
          SectionTitle('صفات المزاين', trailing: Text('من 10', style: t.labelMedium)),
          Card(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
              child: Column(
                children: [
                  for (final tr in Trait.values)
                    _TraitRow(trait: tr, value: phen[tr]!),
                ],
              ),
            ),
          ),
          const SizedBox(height: 14),

          // Body and health.
          const SectionTitle('الحالة والصحة'),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Expanded(child: Text('الحالة (السمنة)')),
                      Text('${c.condition.round()} من 100', style: const TextStyle(fontWeight: FontWeight.w700)),
                    ],
                  ),
                  const SizedBox(height: 6),
                  ScoreBar(value: c.condition),
                  const SizedBox(height: 6),
                  Text('الحالة تأثر على السنام والرقبة والوقفة يوم التحكيم. تتحسن مع العلف الجيد وكفاية الرعاة.',
                      style: t.bodySmall),
                  const Divider(height: 24),
                  Row(
                    children: [
                      const Expanded(child: Text('الصحة')),
                      Text(c.health == HealthStatus.sick ? 'مريضة: ${c.illness}' : c.health.label,
                          style: TextStyle(
                              fontWeight: FontWeight.w700,
                              color: c.health == HealthStatus.healthy ? Palette.tamarisk : Palette.henna)),
                    ],
                  ),
                  if (c.isPlayers && c.health == HealthStatus.sick) ...[
                    const SizedBox(height: 8),
                    FilledButton.icon(
                      onPressed: () => showResult(context, ctl.run((e) => e.treat(c.id))),
                      icon: const Icon(Icons.medical_services_outlined),
                      label: const Text('اطلب البيطري'),
                    ),
                  ],
                  const Divider(height: 24),
                  _kv(context, 'رقم الشريحة', c.chip, mono: true),
                  if (c.sex == Sex.female) ...[
                    _kv(context, 'عدد الولادات', '${c.calvings}'),
                    if (c.lastCalvingDay != null)
                      _kv(context, 'آخر ولادة', formatDate(dateOfDay(c.lastCalvingDay!))),
                    if (c.isPregnantConfirmed) ...[
                      _kv(context, 'عشراء من', c.pregnancy!.sire.name),
                      _kv(context, 'الولادة المتوقعة', formatDate(dateOfDay(c.pregnancy!.dueDay))),
                    ],
                  ],
                ],
              ),
            ),
          ),
          const SizedBox(height: 14),

          // Pedigree.
          const SectionTitle('النسب'),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  _kv(context, 'الأب (الفحل)', c.sire == null ? 'غير معروف' : '${c.sire!.name} · ${c.sire!.category.label}'),
                  _kv(context, 'الأم', c.dam == null ? 'غير معروفة' : '${c.dam!.name} · ${c.dam!.category.label}'),
                  if (c.crossbred) _kv(context, 'ملاحظة', 'خلط بين فئتين، اللون أقل صفاء'),
                ],
              ),
            ),
          ),
          const SizedBox(height: 14),

          // Contest record.
          const SectionTitle('سجل المشاركات'),
          Card(
            child: c.titles.isEmpty
                ? const Padding(
                    padding: EdgeInsets.all(16),
                    child: Text('ما شاركت في مهرجان للحين.'),
                  )
                : Column(
                    children: [
                      for (final ti in c.titles.reversed)
                        ListTile(
                          leading: CircleAvatar(
                            backgroundColor: (ti.rank <= 3 ? Palette.saffron : scheme.primary).withValues(alpha: 0.15),
                            child: Text('${ti.rank}', style: const TextStyle(fontWeight: FontWeight.w700)),
                          ),
                          title: Text(ti.round),
                          subtitle: Text('${ti.festival} · ${formatDate(dateOfDay(ti.day))}'),
                          trailing: Text(riyalShort(ti.prize), style: const TextStyle(fontWeight: FontWeight.w700)),
                        ),
                    ],
                  ),
          ),
          const SizedBox(height: 14),
          if (c.isPlayers)
            Text(
              'تقدير السوق ${riyal(lo)} – ${riyal(hi)}${c.purchasePrice > 0 ? ' · اشتريتها بـ ${riyal(c.purchasePrice)}' : ''}',
              style: t.bodySmall,
            ),
        ],
      ),
    );
  }

  Future<void> _rename(BuildContext context, Camel c) async {
    final ctl = GameScope.read(context);
    final text = TextEditingController(text: c.name);
    final name = await showDialog<String>(
      context: context,
      builder: (d) => AlertDialog(
        title: const Text('اسم جديد'),
        content: TextField(
          key: const ValueKey('rename'),
          controller: text,
          autofocus: true,
          maxLength: 24,
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(d), child: const Text('إلغاء')),
          FilledButton(onPressed: () => Navigator.pop(d, text.text), child: const Text('حفظ')),
        ],
      ),
    );
    if (name != null && context.mounted) {
      showResult(context, ctl.run((e) => e.rename(c.id, name)));
    }
  }
}

Widget _kv(BuildContext context, String k, String v, {bool mono = false}) {
  final scheme = Theme.of(context).colorScheme;
  return Padding(
    padding: const EdgeInsets.symmetric(vertical: 4),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 130,
          child: Text(k, style: TextStyle(color: scheme.onSurface.withValues(alpha: 0.65))),
        ),
        Expanded(
          child: Text(v,
              style: TextStyle(
                fontWeight: FontWeight.w600,
                fontFeatures: mono ? const [FontFeature.tabularFigures()] : null,
                letterSpacing: mono ? 0.6 : null,
              )),
        ),
      ],
    ),
  );
}

class _TraitRow extends StatelessWidget {
  const _TraitRow({required this.trait, required this.value});
  final Trait trait;
  final double value;

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(trait.label, style: const TextStyle(fontWeight: FontWeight.w700)),
              const SizedBox(width: 6),
              Text('${(trait.weight * 100).round()}٪ من الدرجة', style: t.labelSmall),
              const Spacer(),
              Text(
                (value / 10).toStringAsFixed(1),
                style: TextStyle(
                    fontWeight: FontWeight.w700,
                    color: scoreColor(value),
                    fontFeatures: const [FontFeature.tabularFigures()]),
              ),
            ],
          ),
          const SizedBox(height: 4),
          ScoreBar(value: value),
          const SizedBox(height: 2),
          Text(trait.description, style: t.bodySmall),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------- market

class _MarketBox extends StatelessWidget {
  const _MarketBox({required this.listing, required this.camel});
  final Listing listing;
  final Camel camel;

  @override
  Widget build(BuildContext context) {
    final ctl = GameScope.of(context);
    final e = ctl.engine;
    final s = ctl.state;
    final move = e.transportToFarm(listing.region);
    final km = listing.region.roadKmTo(s.farm.region);
    final t = Theme.of(context).textTheme;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('معروضة في ${listing.region.marketName}', style: t.titleSmall),
            Text('البايع: ${listing.sellerName} · باقي ${formatDays(listing.expiresDay - s.day)} على العرض', style: t.bodySmall),
            const SizedBox(height: 10),
            Text(riyal(listing.askPrice), style: display(context, 28, color: Theme.of(context).colorScheme.primary)),
            Text('+ نقل للعزبة ${riyal(move)} ($km كم)', style: t.bodySmall),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: FilledButton(
                    onPressed: () async {
                      final ok = await confirmAction(context,
                          title: 'شراء ${camel.name}',
                          body: 'بتدفع ${riyal(listing.askPrice)} للبايع و${riyal(move)} نقل. المجموع ${riyal(listing.askPrice + move)}.',
                          confirm: 'اشترِ');
                      if (!ok || !context.mounted) return;
                      final r = ctl.run((e) => e.buy(listing.id));
                      showResult(context, r);
                      if (r.ok) Navigator.pop(context);
                    },
                    child: const Text('اشترِ بالسعر'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: OutlinedButton(
                    onPressed: listing.bargains >= 3 ? null : () => _bargain(context, listing),
                    child: Text(listing.bargains >= 3 ? 'البايع رفض السوم' : 'سُم عليها'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _bargain(BuildContext context, Listing l) async {
    final ctl = GameScope.read(context);
    final amount = await askAmount(context,
        title: 'كم تسوم ${camel.name}؟',
        hint: 'السعر المطلوب ${riyal(l.askPrice)}. باقي لك ${3 - l.bargains} محاولات.',
        initial: Valuation.roundPrice(l.askPrice * 0.85),
        confirm: 'سُم');
    if (amount == null || !context.mounted) return;
    final r = ctl.run((e) => e.bargain(l.id, amount));
    showResult(context, r);
    if (r.ok && context.mounted) Navigator.pop(context);
  }
}

/// Asks for a riyal amount in a dialog.
Future<int?> askAmount(BuildContext context,
    {required String title, required String hint, required int initial, required String confirm}) {
  final text = TextEditingController(text: '$initial');
  return showDialog<int>(
    context: context,
    builder: (d) => AlertDialog(
      title: Text(title),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(hint),
          const SizedBox(height: 12),
          TextField(
            key: const ValueKey('amount'),
            controller: text,
            autofocus: true,
            keyboardType: TextInputType.number,
            inputFormatters: [FilteringTextInputFormatter.digitsOnly],
            decoration: const InputDecoration(suffixText: 'ريال'),
          ),
        ],
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(d), child: const Text('إلغاء')),
        FilledButton(
          onPressed: () => Navigator.pop(d, int.tryParse(text.text)),
          child: Text(confirm),
        ),
      ],
    ),
  );
}

class _StudBox extends StatelessWidget {
  const _StudBox({required this.stud, required this.camel});
  final StudOffer stud;
  final Camel camel;

  @override
  Widget build(BuildContext context) {
    final ctl = GameScope.of(context);
    final s = ctl.state;
    final e = ctl.engine;
    final t = Theme.of(context).textTheme;
    final move = e.transportToFarm(stud.region);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('فحل للتلقيح عند ${stud.ownerName}', style: t.titleSmall),
            Text('${stud.region.label} · متاح لين ${formatDate(dateOfDay(stud.untilDay))}', style: t.bodySmall),
            const SizedBox(height: 10),
            Text('أجرة الضراب ${riyal(stud.fee)}', style: display(context, 22, color: Theme.of(context).colorScheme.primary)),
            Text('+ نقل الناقة ${riyal(move)}', style: t.bodySmall),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: () => pickFemaleForStud(context, e, stud, camel),
              icon: const Icon(Icons.favorite_border),
              label: const Text('لقّح ناقة من حلالي'),
            ),
            if (!e.isBreedingSeason())
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text('موسم التلقيح من نوفمبر إلى أبريل. التاريخ الحين ${formatDate(s.date)}.', style: t.bodySmall),
              ),
          ],
        ),
      ),
    );
  }
}

Future<void> pickFemaleForStud(BuildContext context, GameEngine e, StudOffer stud, Camel bull) async {
  final ctl = GameScope.read(context);
  final females = e.s.herd.where((c) => c.sex == Sex.female).toList()
    ..sort((a, b) => (e.femaleProblem(a) == null ? 0 : 1).compareTo(e.femaleProblem(b) == null ? 0 : 1));
  final picked = await showModalBottomSheet<Camel>(
    context: context,
    showDragHandle: true,
    builder: (c) => _PickList(
      title: 'اختر الناقة للفحل ${bull.name}',
      camels: females,
      problem: e.femaleProblem,
      today: e.s.day,
    ),
  );
  if (picked == null || !context.mounted) return;
  final r = ctl.run((e) => e.mate(picked.id, bull.id, stud: stud));
  showResult(context, r);
}

class _PickList extends StatelessWidget {
  const _PickList({required this.title, required this.camels, required this.problem, required this.today});
  final String title;
  final List<Camel> camels;
  final String? Function(Camel) problem;
  final int today;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Text(title, style: display(context, 18)),
          ),
          const SizedBox(height: 8),
          if (camels.isEmpty)
            const Padding(padding: EdgeInsets.all(16), child: Text('ما عندك حلال يناسب.')),
          Flexible(
            child: ListView(
              shrinkWrap: true,
              children: [
                for (final c in camels)
                  Builder(builder: (context) {
                    final p = problem(c);
                    return ListTile(
                      enabled: p == null,
                      leading: SizedBox(width: 56, child: CamelImage(camel: c, today: today, height: 42, backdrop: false)),
                      title: Text(c.name),
                      subtitle: Text(p ?? '${c.category.label} · ${c.ageLabel(today)} · ${Judging.quality(c, today).toStringAsFixed(1)}'),
                      onTap: p == null ? () => Navigator.pop(context, c) : null,
                    );
                  }),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------- owner

class _OwnerActions extends StatelessWidget {
  const _OwnerActions({required this.camel});
  final Camel camel;

  @override
  Widget build(BuildContext context) {
    final ctl = GameScope.of(context);
    final s = ctl.state;
    final e = ctl.engine;
    final listing = s.listings.where((l) => l.camelId == camel.id).firstOrNull;
    final offers = listing == null ? <BuyerOffer>[] : s.buyerOffers.where((o) => o.listingId == listing.id).toList();
    final sellProblem = e.sellProblem(camel);
    final t = Theme.of(context).textTheme;

    final entries = <(Festival, ContestRound)>[];
    for (final f in s.festivals.where((f) => !f.done)) {
      for (final r in f.rounds) {
        if (r.entries.contains(camel.id)) entries.add((f, r));
      }
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (listing != null)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('معروضة في ${listing.region.marketName} بـ ${riyal(listing.askPrice)}', style: t.titleSmall),
                  Text('باقي ${formatDays(listing.expiresDay - s.day)} على العرض', style: t.bodySmall),
                  const SizedBox(height: 8),
                  if (offers.isEmpty) const Text('ما فيه سوم للحين. السوّام يجون مع الأيام.'),
                  for (final o in offers)
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      title: Text('${o.buyerName} سام بـ ${riyal(o.amount)}'),
                      subtitle: Text('من ${o.buyerRegion.label} · ينتهي بعد ${formatDays(o.expiresDay - s.day + 1)}'),
                      trailing: Wrap(spacing: 4, children: [
                        IconButton(
                          tooltip: 'ارفض',
                          onPressed: () => ctl.apply((e) => e.declineOffer(o.id)),
                          icon: const Icon(Icons.close),
                        ),
                        IconButton.filled(
                          tooltip: 'بِع',
                          onPressed: () async {
                            final ok = await confirmAction(context,
                                title: 'بيع ${camel.name}',
                                body: 'تبيع على ${o.buyerName} بـ ${riyal(o.amount)}؟ السعي ٢٫٥٪ على البايع.',
                                confirm: 'بِع');
                            if (!ok || !context.mounted) return;
                            showResult(context, ctl.run((e) => e.acceptOffer(o.id)));
                            Navigator.pop(context);
                          },
                          icon: const Icon(Icons.check),
                        ),
                      ]),
                    ),
                  const SizedBox(height: 4),
                  OutlinedButton(
                    onPressed: () => showResult(context, ctl.run((e) => e.cancelListing(listing.id))),
                    child: const Text('اسحب العرض'),
                  ),
                ],
              ),
            ),
          ),
        if (entries.isNotEmpty)
          Card(
            child: Column(
              children: [
                for (final (f, r) in entries)
                  ListTile(
                    leading: const Icon(Icons.emoji_events, color: Palette.saffron),
                    title: Text(r.title),
                    subtitle: Text('${f.name} · التحكيم ${formatDate(dateOfDay(f.judgingDay))}'),
                    trailing: TextButton(
                      onPressed: () => showResult(context, ctl.run((e) => e.withdraw(f.id, r.id, camel.id))),
                      child: const Text('انسحب'),
                    ),
                  ),
              ],
            ),
          ),
        if (listing == null) ...[
          const SizedBox(height: 4),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              FilledButton.icon(
                onPressed: sellProblem != null
                    ? null
                    : () async {
                        final (lo, hi) = Valuation.estimateRange(camel, s.day);
                        final ask = await askAmount(context,
                            title: 'اعرض ${camel.name} للبيع',
                            hint: 'تقدير السوق ${riyal(lo)} – ${riyal(hi)}. كل ما زاد السعر عن السوق قل السوّام.',
                            initial: Valuation.roundPrice(hi * 1.0),
                            confirm: 'اعرض');
                        if (ask != null && context.mounted) {
                          showResult(context, ctl.run((e) => e.listForSale(camel.id, ask)));
                        }
                      },
                icon: const Icon(Icons.sell_outlined),
                label: const Text('اعرض للبيع'),
              ),
              OutlinedButton.icon(
                onPressed: sellProblem != null
                    ? null
                    : () async {
                        final price = e.quickSalePrice(camel);
                        final ok = await confirmAction(context,
                            title: 'بيع على الدلال',
                            body: 'الدلال ياخذها الحين بـ ${riyal(price)} (أقل من السوق). عليك السعي ٢٫٥٪.',
                            confirm: 'بِع الحين',
                            danger: true);
                        if (!ok || !context.mounted) return;
                        showResult(context, ctl.run((e) => e.quickSale(camel.id)));
                        Navigator.pop(context);
                      },
                icon: const Icon(Icons.flash_on_outlined),
                label: const Text('بيع على الدلال'),
              ),
              if (camel.sex == Sex.female)
                OutlinedButton.icon(
                  onPressed: () => _mateOwn(context, e),
                  icon: const Icon(Icons.favorite_border),
                  label: const Text('لقّحها'),
                ),
              OutlinedButton.icon(
                onPressed: () => _enter(context, e),
                icon: const Icon(Icons.emoji_events_outlined),
                label: const Text('سجّل في مهرجان'),
              ),
            ],
          ),
          if (sellProblem != null)
            Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Text('ما تقدر تبيعها: $sellProblem', style: t.bodySmall),
            ),
        ],
      ],
    );
  }

  Future<void> _mateOwn(BuildContext context, GameEngine e) async {
    final ctl = GameScope.read(context);
    final fp = e.femaleProblem(camel);
    if (fp != null) {
      showResult(context, ActionResult.fail(fp));
      return;
    }
    final own = e.s.herd.where((c) => c.sex == Sex.male).toList();
    final studs = e.s.studs.map((st) => (st, e.s.camels[st.camelId])).where((p) => p.$2 != null).toList()
      ..sort((a, b) => Judging.quality(b.$2!, e.s.day).compareTo(Judging.quality(a.$2!, e.s.day)));
    final picked = await showModalBottomSheet<(Camel, StudOffer?)>(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      builder: (c) => SafeArea(
        child: ConstrainedBox(
          constraints: BoxConstraints(maxHeight: MediaQuery.of(c).size.height * 0.8),
          child: ListView(
            shrinkWrap: true,
            children: [
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Text('اختر الفحل لـ ${camel.name}', style: display(c, 18)),
              ),
              if (own.isNotEmpty) const ListTile(dense: true, title: Text('فحول حلالك')),
              for (final m in own)
                ListTile(
                  enabled: e.bullProblem(m) == null,
                  leading: SizedBox(width: 56, child: CamelImage(camel: m, today: e.s.day, height: 42, backdrop: false)),
                  title: Text(m.name),
                  subtitle: Text(e.bullProblem(m) ?? '${m.category.label} · ${Judging.quality(m, e.s.day).toStringAsFixed(1)} · بدون أجرة'),
                  onTap: e.bullProblem(m) == null ? () => Navigator.pop(c, (m, null)) : null,
                ),
              const ListTile(dense: true, title: Text('فحول للتلقيح عند الملاك')),
              for (final (st, m) in studs)
                ListTile(
                  leading: SizedBox(width: 56, child: CamelImage(camel: m!, today: e.s.day, height: 42, backdrop: false)),
                  title: Text('${m.name} · ${st.ownerName}'),
                  subtitle: Text(
                      '${m.category.label}${m.category != camel.category ? ' (خلط)' : ''} · ${Judging.quality(m, e.s.day).toStringAsFixed(1)} · ${st.region.label} · أجرة ${riyal(st.fee)}'),
                  onTap: () => Navigator.pop(c, (m, st)),
                ),
            ],
          ),
        ),
      ),
    );
    if (picked == null || !context.mounted) return;
    showResult(context, ctl.run((e) => e.mate(camel.id, picked.$1.id, stud: picked.$2)));
  }

  Future<void> _enter(BuildContext context, GameEngine e) async {
    final ctl = GameScope.read(context);
    final options = <(Festival, ContestRound)>[];
    for (final f in e.s.festivals.where((f) => f.isRegistrationOpen(e.s.day))) {
      for (final r in f.rounds) {
        if (e.entryProblem(camel, f, r) == null) options.add((f, r));
      }
    }
    if (options.isEmpty) {
      showResult(
          context,
          const ActionResult.fail(
              'ما فيه شوط مفتوح يناسب فئتها وعمرها الحين. شوف مواعيد المهرجانات في المشاركات.'));
      return;
    }
    final picked = await showModalBottomSheet<(Festival, ContestRound)>(
      context: context,
      showDragHandle: true,
      builder: (c) => SafeArea(
        child: ListView(
          shrinkWrap: true,
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Text('الأشواط المناسبة لـ ${camel.name}', style: display(c, 18)),
            ),
            for (final (f, r) in options)
              ListTile(
                leading: const Icon(Icons.emoji_events_outlined),
                title: Text(r.title),
                subtitle: Text(
                    '${f.name} · التحكيم ${formatDate(dateOfDay(f.judgingDay))} · الأول ${riyalShort(r.prizes.first)}'),
                onTap: () => Navigator.pop(c, (f, r)),
              ),
          ],
        ),
      ),
    );
    if (picked == null || !context.mounted) return;
    showResult(context, ctl.run((e) => e.enter(picked.$1.id, picked.$2.id, camel.id)));
  }
}
