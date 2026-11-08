// Process memory and GPU backend, from dart:io and Flutter GPU on native.
// The web stub exists only so the same app can be smoke-tested in a browser.
export 'platform_probe_web.dart' if (dart.library.io) 'platform_probe_io.dart';
