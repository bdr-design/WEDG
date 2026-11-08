import 'package:flutter/material.dart';

import '../../core/format.dart';
import '../../domain/engine/game_engine.dart';
import '../../domain/models/camel.dart';
import '../../domain/rules/judging.dart';
import '../../domain/rules/valuation.dart';
import 'common.dart';

/// One camel in a list: photo, name, family, age, score and status.
class CamelCard extends StatelessWidget {
  const CamelCard({
    super.key,
    required this.camel,
    required this.engine,
    required this.onTap,
    this.priceLine,
    this.subLine,
  });

  final Camel camel;
  final GameEngine engine;
  final VoidCallback onTap;

  /// Overrides the value estimate line (e.g. a market asking price).
  final String? priceLine;
  final String? subLine;

  @override
  Widget build(BuildContext context) {
    final s = engine.s;
    final t = Theme.of(context).textTheme;
    final scheme = Theme.of(context).colorScheme;
    final q = Judging.quality(camel, s.day);
    final (lo, hi) = Valuation.estimateRange(camel, s.day);
    final pills = camelPills(context, camel, engine);

    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(10),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(
                width: 104,
                child: CamelImage(camel: camel, today: s.day, height: 80),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(camel.name,
                              style: t.titleMedium?.copyWith(fontWeight: FontWeight.w700),
                              overflow: TextOverflow.ellipsis),
                        ),
                        QualityBadge(quality: q),
                      ],
                    ),
                    const SizedBox(height: 2),
                    Row(
                      children: [
                        ColorSwatchDot(camel.category),
                        const SizedBox(width: 6),
                        Flexible(
                          child: Text(
                            '${camel.category.label} · ${camel.sex.label} · ${camel.ageLabel(s.day)} (${formatAgeDays(camel.ageDays(s.day))})',
                            style: t.bodySmall,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      priceLine ?? 'تقدير السوق: ${riyalShort(lo)} – ${riyalShort(hi)}',
                      style: t.bodyMedium?.copyWith(fontWeight: FontWeight.w600, color: scheme.primary),
                    ),
                    if (subLine != null)
                      Text(subLine!, style: t.bodySmall?.copyWith(color: scheme.onSurface.withValues(alpha: 0.65))),
                    if (pills.isNotEmpty) ...[
                      const SizedBox(height: 6),
                      Wrap(spacing: 6, runSpacing: 6, children: pills),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
