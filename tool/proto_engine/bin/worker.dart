// The rules engine in the 3D design prototype's Web Worker (docs/plan-gameplay.md, G2): lib/worker_host.dart, which
// holds the protocol, connected to the worker's `self`.
import 'dart:js_interop';

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

void main() {
  final host = WorkerHost(
    post: (json) => _self.postMessage(json.toJS),
    // an object, not JSON: the save's text goes as it is
    postStore: (seq, key, value) => _self.postMessage(
      {'type': 'store', 'seq': seq, 'key': key, 'value': value}.jsify(),
    ),
  );
  _self.onmessage = ((_Message e) {
    final d = e.data;
    host.receive(d.isA<JSString>() ? (d! as JSString).toDart : null);
  }).toJS;
  host.ready();
}
