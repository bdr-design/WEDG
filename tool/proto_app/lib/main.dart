// The 3D prototype (design/prototype3d) inside an iPhone app, to try it on a
// phone: full screen, landscape only, everything bundled. A small HTTP server
// on the loopback address serves the bundled files to a WKWebView (module
// scripts do not load from file:// URLs).
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:webview_flutter/webview_flutter.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await SystemChrome.setPreferredOrientations(const [
    DeviceOrientation.landscapeLeft,
    DeviceOrientation.landscapeRight,
  ]);
  await SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
  final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
  server.listen(serveBundled);
  runApp(ProtoApp(port: server.port));
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
  final asset = assetFor(Uri.decodeComponent(req.uri.path));
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
  const ProtoApp({super.key, required this.port});

  final int port;

  @override
  State<ProtoApp> createState() => _ProtoAppState();
}

class _ProtoAppState extends State<ProtoApp> {
  late final WebViewController _web = WebViewController()
    ..setJavaScriptMode(JavaScriptMode.unrestricted)
    ..setBackgroundColor(Colors.black)
    // #fps shows the frame meter: frames a second, the slowest 1%, stutters.
    ..loadRequest(Uri.parse('http://127.0.0.1:${widget.port}/index.html#fps'));

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
