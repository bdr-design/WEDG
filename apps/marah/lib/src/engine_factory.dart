import 'package:marah_runtime/marah_runtime.dart';

import 'engine_factory_io.dart'
    if (dart.library.js_interop) 'engine_factory_web.dart'
    as platform;

/// Starts the engine for this platform: a worker isolate on iOS and Android,
/// time-sliced on the web's main thread (no isolates there). ADR 0002.
Future<EngineClient> startEngine() => platform.startEngine();
