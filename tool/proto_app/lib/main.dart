// The 3D prototype (design/prototype3d) inside an iPhone app, to try it on a
// phone: full screen, landscape only, everything bundled. A small HTTP server
// on the loopback address serves the bundled files to a WKWebView (module
// scripts do not load from file:// URLs), and keeps the game's save in files
// (the page's own storage would be lost: its origin, with the port in it,
// changes every launch).
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:webview_flutter/webview_flutter.dart';

import 'save_files.dart';

export 'save_files.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await SystemChrome.setPreferredOrientations(const [
    DeviceOrientation.landscapeLeft,
    DeviceOrientation.landscapeRight,
  ]);
  await SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
  runApp(const ProtoApp());
}

/// The server for the bundled files and the save on the loopback address (an
/// error on its socket is dropped: the app checks the server when it comes
/// back to the front).
Future<HttpServer> bindServer(SaveFiles saves) async {
  final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
  server.listen((req) => serve(req, saves), onError: (Object _) {});
  return server;
}

Future<void> serve(HttpRequest req, SaveFiles saves) {
  final path = req.uri.path;
  if (path == '/save' || path.startsWith('/save/')) return saves.handle(req);
  return serveBundled(req);
}

/// The MIME type of a bundled file; module scripts need a JavaScript type.
ContentType contentTypeFor(String path) {
  final dot = path.lastIndexOf('.');
  final ext = dot < 0 ? '' : path.substring(dot + 1).toLowerCase();
  return switch (ext) {
    'html' => ContentType.html,
    'js' || 'mjs' => ContentType('text', 'javascript', charset: 'utf-8'),
    'json' => ContentType.json,
    'png' => ContentType('image', 'png'),
    'jpg' || 'jpeg' => ContentType('image', 'jpeg'),
    'wasm' => ContentType('application', 'wasm'),
    'woff2' => ContentType('font', 'woff2'),
    'txt' => ContentType('text', 'plain', charset: 'utf-8'),
    _ => ContentType.binary,
  };
}

/// The bundled asset for a request path, or null for one that may not be served.
String? assetFor(String requestPath) {
  final path = requestPath == '/' ? '/index.html' : requestPath;
  if (!path.startsWith('/') || path.split('/').contains('..')) return null;
  return 'assets/web$path';
}

Future<void> serveBundled(HttpRequest req) async {
  final res = req.response;
  String? asset;
  try {
    asset = assetFor(Uri.decodeComponent(req.uri.path));
  } catch (_) {
    // a malformed escape such as /%FF: answered, and the connection closed
    res.statusCode = HttpStatus.badRequest;
    await res.close();
    return;
  }
  try {
    if (asset == null) throw const FormatException('outside the bundle');
    final data = await rootBundle.load(asset);
    res.headers.contentType = contentTypeFor(asset);
    res.headers.set('Cache-Control', 'no-store');
    res.add(data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes));
  } catch (_) {
    res.statusCode = HttpStatus.notFound;
  }
  await res.close();
}

class ProtoApp extends StatefulWidget {
  const ProtoApp({super.key});

  @override
  State<ProtoApp> createState() => _ProtoAppState();
}

class _ProtoAppState extends State<ProtoApp> with WidgetsBindingObserver {
  final WebViewController _web = WebViewController()
    ..setJavaScriptMode(JavaScriptMode.unrestricted)
    ..setBackgroundColor(Colors.black);
  HttpServer? _server;
  // the save beside the app's other files: iOS gives the app its own HOME
  late final SaveFiles _saves = SaveFiles(
    Directory(
      '${Platform.environment['HOME'] ?? Directory.systemTemp.path}/Documents/marah',
    ),
  );

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _start();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _server?.close(force: true);
    super.dispose();
  }

  Future<void> _start() async {
    await _server?.close(force: true);
    final server = await bindServer(_saves);
    _server = server;
    // #fps shows the frame meter: frames a second and the slowest 1%; a tap
    // on it opens the stutters and the engine's costs. ?save= gives the page
    // the key to its save.
    await _web.loadRequest(
      Uri.parse(
        'http://127.0.0.1:${server.port}/index.html?save=${_saves.token}#fps',
      ),
    );
  }

  // Back in front: if iOS took the server's socket or ended the page's process
  // while the app was away, start again (the screen stayed black until the app
  // was closed and opened again).
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) _check();
  }

  Future<void> _check() async {
    final server = _server;
    var alive = server != null;
    if (server != null) {
      final client = HttpClient()
        ..connectionTimeout = const Duration(seconds: 2);
      try {
        final req = await client.get('127.0.0.1', server.port, '/index.html');
        final res = await req.close().timeout(const Duration(seconds: 2));
        await res.drain<void>();
        alive = res.statusCode == HttpStatus.ok;
      } catch (_) {
        alive = false;
      } finally {
        client.close(force: true);
      }
    }
    if (alive) {
      try {
        await _web
            .runJavaScriptReturningResult('document.readyState')
            .timeout(const Duration(seconds: 2));
      } catch (_) {
        alive = false;
      }
    }
    if (!alive && mounted) await _start();
  }

  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'مراح',
    debugShowCheckedModeBanner: false,
    home: Scaffold(
      backgroundColor: Colors.black,
      body: WebViewWidget(controller: _web),
    ),
  );
}
