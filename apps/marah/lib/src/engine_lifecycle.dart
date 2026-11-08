import 'dart:async';

import 'package:flutter/widgets.dart';
import 'package:marah_runtime/marah_runtime.dart';

/// Saves when the app is hidden and catches up with the clock when it comes
/// back. `hide` is used rather than `pause` because iOS and Android always
/// pass through `hidden` first, and on the web it means the tab is hidden.
class EngineLifecycle {
  EngineLifecycle(this.engine) {
    _listener = AppLifecycleListener(
      onHide: () => unawaited(engine.pause()),
      onShow: () => unawaited(engine.resume()),
    );
  }

  final EngineClient engine;
  late final AppLifecycleListener _listener;

  void dispose() => _listener.dispose();
}
