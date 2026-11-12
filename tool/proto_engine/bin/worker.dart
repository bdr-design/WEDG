// The rules engine in the 3D design prototype's Web Worker (docs/plan-gameplay.md, G2): lib/worker_host.dart, which
// holds the protocol, connected to the worker's `self`, and to the iPhone app's server by fetch (the worker reads and
// writes the save itself; a request is cut off by an AbortController at the host's timeout).
import 'dart:async';
import 'dart:js_interop';
import 'dart:js_interop_unsafe';

import 'package:marah_proto_engine/worker_host.dart';

@JS('self')
external _Scope get _self;

extension type _Scope._(JSObject _) implements JSObject {
  external set onmessage(JSFunction f);
  external void postMessage(JSAny? message);
}

extension type _Message._(JSObject _) implements JSObject {
  external JSAny? get data;
}

@JS('fetch')
external JSPromise<_Response> _fetch(JSString url, JSObject init);

extension type _Response._(JSObject _) implements JSObject {
  external int get status;
  external JSPromise<JSString> text();
}

@JS('AbortController')
extension type _Abort._(JSObject _) implements JSObject {
  external factory _Abort();
  external JSObject get signal;
  external void abort();
}

Future<(int, String)> _http(
  String method,
  String url,
  Map<String, String> headers,
  String? body,
  Duration timeout,
) async {
  final abort = _Abort();
  // ignore: unnecessary_lambdas, a JS interop member cannot be torn off
  final timer = Timer(timeout, () => abort.abort());
  try {
    final init = JSObject()
      ..['method'] = method.toJS
      ..['headers'] = headers.jsify()
      ..['cache'] = 'no-store'.toJS
      ..['signal'] = abort.signal;
    if (body != null) init['body'] = body.toJS;
    final res = await _fetch(url.toJS, init).toDart;
    final text = (await res.text().toDart).toDart;
    return (res.status, text);
  } finally {
    timer.cancel();
  }
}

void main() {
  final host = WorkerHost(
    post: (json) => _self.postMessage(json.toJS),
    // an object, not JSON: the save's text goes as it is
    postStore: (seq, key, value) => _self.postMessage(
      {'type': 'store', 'seq': seq, 'key': key, 'value': value}.jsify(),
    ),
    http: _http,
  );
  _self.onmessage = ((_Message e) {
    final d = e.data;
    host.receive(d.isA<JSString>() ? (d! as JSString).toDart : null);
  }).toJS;
  host.ready();
}
