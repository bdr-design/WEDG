/// Native-only parts (dart:io, dart:isolate): the worker isolate client and
/// file storage. Not available on the web.
library;

export 'src/file_backend.dart';
export 'src/isolate_client.dart';
