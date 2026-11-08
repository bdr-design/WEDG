import 'package:flutter/scheduler.dart';
import 'package:marah_data/marah_data.dart';
import 'package:marah_runtime/marah_runtime.dart';

import 'prefs_backend.dart';

/// Web: no isolates, so the engine runs on the main thread in slices of
/// about 1 ms, each scheduled between frames.
Future<EngineClient> startEngine() async => InlineEngineClient(
  (emit) => EngineCore(
    store: SaveStore(PrefsBackend()),
    emit: emit,
    sliceBudget: const Duration(milliseconds: 1),
    yielder: () =>
        SchedulerBinding.instance.scheduleTask<void>(() {}, Priority.animation),
  ),
);
