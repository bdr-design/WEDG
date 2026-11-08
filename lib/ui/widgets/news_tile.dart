import 'package:flutter/material.dart';

import '../../core/format.dart';
import '../../domain/models/game_state.dart';
import '../../domain/models/ledger.dart';
import '../theme.dart';

class NewsTile extends StatelessWidget {
  const NewsTile({super.key, required this.item, this.showDate = false});
  final NewsItem item;
  final bool showDate;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final (icon, color) = switch (item.kind) {
      NewsKind.good => (Icons.check_circle, Palette.tamarisk),
      NewsKind.warning => (Icons.warning_amber_rounded, Palette.saffron),
      NewsKind.bad => (Icons.error, Palette.henna),
      NewsKind.market => (Icons.storefront, scheme.primary),
      NewsKind.contest => (Icons.emoji_events, Palette.saffron),
      NewsKind.birth => (Icons.child_friendly, Palette.tamarisk),
      NewsKind.info => (Icons.info_outline, scheme.onSurface.withValues(alpha: 0.6)),
    };
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18, color: color),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item.text, style: const TextStyle(height: 1.45)),
                if (showDate)
                  Text(formatDate(dateOfDay(item.day)),
                      style: TextStyle(fontSize: 11, color: scheme.onSurface.withValues(alpha: 0.55))),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
