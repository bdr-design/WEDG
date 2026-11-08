# Design brief: engine and persistence off the UI isolate

**How this was sourced.** docs.flutter.dev, dart.dev and api.flutter.dev failed DNS lookup (ENOTFOUND) here, so claims about them come from search extracts of those pages or their mirrors. [unverified] marks a claim from memory. To check them, allow those hosts in the session's network settings.

## 1. Native: use one long-lived worker isolate
- Spawn one isolate with `Isolate.spawn` and let it own `Game`/`GameState` for the whole session. Flutter's docs recommend long-lived isolates for work that repeats over the app's lifetime or returns values over time [1].
- `Isolate.run`/`compute` per call is the wrong fit. Spawning is cheap since Dart 2.15 (over 100x faster, 10–100x less memory [6]) but not free [1]. Worse, the state must cross the boundary on every call. `SendPort.send` copies the message's whole object graph in linear time, at the moment of sending [4]. If a closure captures `GameState`, the UI isolate is the sender and pays that copy. The result comes back through `Isolate.exit` without a copy [5][7], but the VM still walks the graph (a third-party measurement found about 10 ns per object [37]).
- What can be sent: with `spawn` (shared code), almost anything except objects holding native resources (Socket, ReceivePort…). Strings and other immutables are shared, not copied [4].

## 2. Message protocol
- **Handshake:** the worker sends back its `SendPort`. The UI keeps a map of `id → Completer` for pending requests (the "robust ports" pattern [2]).
- **UI → worker:** `Init(saveDirPath, nowUtcMs)`, `Dispatch(id, Command)`, `CatchUp(id, nowUtcMs)`, `View(id, playerId)`, `Flush(id)`, `Shutdown(id)`.
- **Worker → UI:** `Reply(id, result)`, `Failure(id, message, stackString)`, `Snapshot(revision, PlayerViewModel)`, `Progress(done, total)`, `Saved(revision)`. Make all of these small, immutable, sealed classes.
- **Never send `GameState`.** Send view models already shaped for the UI. The worker pays the copy cost, because it is the sender [4]. The UI still allocates and garbage-collects what it receives, so keep it small. During a 200-day catch-up, send a throttled `Progress` and one final `Snapshot`. Use `revision` to drop stale snapshots.
- **Large blobs** (export, debugging): send a JSON `String`, which is shared rather than copied [4], or `TransferableTypedData`, which sends in constant time and can be materialized once [8]. Never decode either on the UI isolate.
- **JSON:** all encoding and decoding happens in the worker. On load: read → `jsonDecode` → `fromJson`. On save: `toJson` → `jsonEncode` → write.
- **Errors:** wrap every request handler in try/catch and answer with `Failure`. Spawn with `onError`/`onExit` ports [9]. If the worker exits, fail all pending completers and respawn it from the last save.
- **Shutdown:** on `Shutdown`, the worker flushes, replies, closes its port, then calls `Isolate.exit()`. Hot restart kills background isolates (Flutter has a test asserting this [31]), so spawn the worker during startup and never keep ports in statics. Atomic writes keep a write that is cut off from corrupting the save.
- **Long catch-ups:** in the worker, yield every K days so queued requests can run.

## 3. Persistence
- **Plugins in the worker:** this works since Flutter 3.7. Pass `RootIsolateToken.instance` (it is null off the root isolate [14]) and call `BackgroundIsolateBinaryMessenger.ensureInitialized(token)` [11][12]. Background isolates can call the host and get replies, but cannot receive messages the host starts: `setMessageHandler` throws [13][1]. Plugins implemented in Dart may also need `DartPluginRegistrant.ensureInitialized()` [38]. shared_preferences warns that each isolate gets its own singleton and cache; `SharedPreferencesAsync` has no cache [15].
- **Simpler:** call `getApplicationSupportDirectory()` once on the UI isolate and pass the path in `Init`. The worker then uses plain `dart:io` and needs no plugin channel. (On iOS/macOS, path_provider_foundation now uses FFI [16].)
- **iOS/Android: use a file, not preferences.** Write `save.json.tmp` with `flush: true`, which flushes before the future completes [17], then `rename` it over `save.json`, which replaces the existing file [18]. Same-directory rename is atomic on POSIX; that is OS behaviour, and the Dart docs don't promise it. Keep the previous file as `save.bak`, and store `schemaVersion` plus a checksum.
- **Why not preferences:** NSUserDefaults has a documented hard cap (1 MB) only on tvOS [19], but Android points large datasets to Room, not DataStore [20].
- **Web:** shared_preferences_web writes to `window.localStorage` [24]. localStorage is synchronous and blocks the main thread [22], and quotas are around 5 MiB per origin [21]. Use IndexedDB instead: it is asynchronous and available in workers [23]. Call `navigator.storage.persist()` to make eviction less likely [21].

## 4. Web
- Dart web, including Flutter web, has no isolates [1]. `compute` runs its callback on the current event loop [10]. `Isolate.run` throws on web, Wasm included [25].
- **Official guidance:** use `compute` so the code still compiles [1]. dart.dev says web apps can use Web Workers instead, which need a separately compiled entrypoint and copy data between threads [3, unverified].
- **Option A, a real background thread:** compile `engine_worker.dart` with `dart compile js` (or `wasm`) and start it as a `Worker`. The squadron and isolate_manager packages wrap this [26]. The worker must not import Flutter or `dart:ui`, which a pure-Dart engine already satisfies. Send only strings, primitives and maps or lists of them [26], and persist to IndexedDB from inside the worker. This needs an extra build step.
- **Option B, the fallback:** run the engine on the main thread in time slices of about 1 ms or less, then yield. `SchedulerBinding.scheduleTask` runs tasks between frames and asks each task to stay around 1 ms [28]. Show a progress screen while catching up.
- Wasm multi-threading (needs COOP/COEP headers) speeds up rendering, not your Dart code [27].
- Put all three paths behind one `EngineClient` interface, picked with conditional imports.

## 5. App lifecycle
- **`AppLifecycleListener` [29]:** on `onHide`/`onPause`, send `Flush`. On `onShow`/`onResume`, send `CatchUp(now)`. iOS and Android synthesize `hidden` before `paused`, and `paused` mostly happens only there; on web, `hidden` means the tab isn't visible [30]. So handle `hide`.
- **Don't rely on pause alone:** autosave about 1–2 s after each state-changing command (debounced), because the OS can kill the process while it is in the background.
- **Game-day timer:** set a one-shot `Timer` for the next day boundary (epoch + n × 3h26m, computed from the wall clock). Cancel it on hide and recompute it on resume. Don't use periodic timers. Persist the last-seen UTC time to catch the device clock moving backwards.

## 6. UI-thread checklist
- **Frame budget:** about 16 ms at 60 Hz. Flutter also targets 120 fps on devices that support it, which is about 8.3 ms. The UI thread and the raster thread must each fit [33].
- **Profiling:** measure in profile mode on a physical device, with the performance overlay and the DevTools Performance view [33].
- **Widgets:** keep `build()` cheap, keep `setState` local, use `const` widgets and builder-based lists, and avoid needless `saveLayer`, `Opacity` and `ShaderMask` [32].
- **Images:** decode at display size with `cacheWidth`/`cacheHeight` or `ResizeImage` (`Image.network` ignores these on web) [34]. Call `precacheImage` before a scene appears, but it raises out-of-memory risk on low-memory devices [35].
- **RepaintBoundary:** use it only where a child repaints at a different rate from its parent, and check with `debugDumpRenderTree` [36].
- **Never on the UI isolate:** JSON work or computing `GameView`. Rebuild only widgets whose slice changed.

## Sources
1. https://docs.flutter.dev/perf/isolates (mirror: https://docs.flutter.cn/perf/isolates)
2. https://dart.dev/language/isolates ; https://github.com/dart-lang/site-www/blob/main/examples/concurrency/lib/robust_ports_example/spawn_2.dart
3. https://dart.dev/language/concurrency
4. https://api.dart.dev/dart-isolate/SendPort/send.html
5. https://api.dart.dev/dart-isolate/Isolate/exit.html
6. https://dart.cn/blog/announcing-dart-2-15
7. https://dart.cn/blog/better-isolate-management-with-isolate-run
8. https://api.dart.dev/stable/dart-isolate/TransferableTypedData/materialize.html
9. https://api.dart.dev/dart-isolate/Isolate/spawn.html
10. https://api.flutter.dev/flutter/foundation/compute.html
11. https://flutter.dev/blog/introducing-background-isolate-channels
12. https://api.flutter.dev/flutter/services/BackgroundIsolateBinaryMessenger-class.html
13. https://api.flutter.dev/flutter/services/BackgroundIsolateBinaryMessenger/setMessageHandler.html
14. https://api.flutter.dev/flutter/services/ServicesBinding/rootIsolateToken.html
15. https://pub.dev/packages/shared_preferences
16. https://pub.dev/packages/path_provider_foundation/changelog
17. https://api.dart.dev/dart-io/File/writeAsString.html
18. https://api.flutter.dev/flutter/dart-io/File/renameSync.html
19. https://developer.apple.com/documentation/foundation/userdefaults/sizelimitexceededmessage
20. https://developer.android.com/codelabs/android-preferences-datastore
21. https://developer.mozilla.org/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria
22. https://developer.mozilla.org/en/dom/storage (Web Storage API)
23. https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Functions_and_classes_available_to_workers
24. https://flutter.googlesource.com/mirrors/plugins/+/2cbb314d99d800cb4e1229ce6b304755303bbd64/packages/shared_preferences/shared_preferences_web/lib/shared_preferences_web.dart
25. https://nikoro.github.io/many_lints/docs/rules/testing-rules/prefer-compute-over-isolate-run ; https://github.com/flutter/flutter/issues/145132
26. https://pub.dev/packages/squadron ; https://pub.dev/packages/isolate_manager
27. https://docs.flutter.dev/platform-integration/web/wasm
28. https://api.flutter.dev/flutter/scheduler/SchedulerBinding/scheduleTask.html
29. https://api.flutter.dev/flutter/widgets/AppLifecycleListener-class.html
30. https://api.flutter.dev/flutter/dart-ui/AppLifecycleState.html
31. https://flutter.googlesource.com/mirrors/flutter/+/HEAD/packages/flutter_tools/test/integration.shard/background_isolate_test.dart
32. https://docs.flutter.dev/perf/best-practices
33. https://docs.flutter.dev/perf/ui-performance
34. https://api.flutter.dev/flutter/widgets/Image/Image.network.html
35. https://api.flutter.dev/flutter/widgets/precacheImage.html
36. https://api.flutter.dev/flutter/rendering/RenderRepaintBoundary-class.html
37. https://danreynolds.github.io/resqlite/blog/stories/2026-04-06-zero-copy.html (third-party benchmark)
38. https://dart.googlesource.com/flute/+/a0858fce56849727df72811c33803d48bfaa7552/framework/lib/src/dart_plugin_registrant.dart (copy of Flutter framework source)
