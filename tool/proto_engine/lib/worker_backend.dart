import 'dart:async';
import 'dart:convert';

import 'package:marah_data/marah_data.dart';

/// The save's keys and values held in the worker, read from where the save is
/// kept ([SaveIo]) at start. Every change goes there, and the write completes
/// only when it has been kept: a write that could not be fails here, so the
/// engine reports it and tries again.
class WorkerBackend implements SaveBackend {
  WorkerBackend(Map<String, String> seed, this.io) : _data = {...seed};

  final Map<String, String> _data;
  final SaveIo io;

  @override
  Future<String?> read(String key) async => _data[key];

  @override
  Future<void> write(String key, String value) {
    _data[key] = value;
    return io.keep(key, value);
  }

  @override
  Future<void> delete(String key) {
    _data.remove(key);
    return io.keep(key, null);
  }

  @override
  Future<void> copy(String from, String to) async {
    final v = _data[from];
    if (v == null) return; // as SaveBackend says: nothing to copy, nothing done
    return write(to, v);
  }
}

/// Where the save is kept, seen from the worker.
abstract interface class SaveIo {
  /// Every key and its text, at start.
  Future<Map<String, String>> load();

  /// Keeps a key's text (null deletes it); throws [SaveWriteFailed] when it
  /// could not.
  Future<void> keep(String key, String? value);
}

/// The page keeps the save (the browser tests: localStorage): each write is
/// posted to it, numbered, and done when it answers.
class PageSaveIo implements SaveIo {
  PageSaveIo(
    this.seed,
    this.send, {
    required this.nextSeq,
    this.timeout = const Duration(seconds: 30),
  });

  final Map<String, String> seed;

  /// Hands a write (a null value deletes the key) to the page.
  final void Function(int seq, String key, String? value) send;

  /// Numbers the writes; shared by every engine the worker makes, so a late
  /// answer to an earlier engine's write never settles a later one's.
  final int Function() nextSeq;

  /// A write the page has not answered by then counts as failed.
  final Duration timeout;

  final Map<int, Completer<void>> _pending = {};

  @override
  Future<Map<String, String>> load() async => seed;

  /// The page's answer for write [seq].
  void stored(int seq, {required bool ok, String? error}) {
    final c = _pending.remove(seq);
    if (c == null) return; // already timed out, or another engine's
    if (ok) {
      c.complete();
    } else {
      c.completeError(SaveWriteFailed(error ?? 'not written'));
    }
  }

  @override
  Future<void> keep(String key, String? value) {
    final seq = nextSeq();
    final c = Completer<void>();
    _pending[seq] = c;
    send(seq, key, value);
    return c.future.timeout(
      timeout,
      onTimeout: () {
        _pending.remove(seq);
        throw SaveWriteFailed('the page did not answer write $seq');
      },
    );
  }
}

/// An HTTP request from the worker: the status and the body's text, or a
/// throw when it failed or took longer than [timeout] (it is then cancelled).
typedef HttpCall = Future<(int status, String body)> Function(
  String method,
  String url,
  Map<String, String> headers,
  String? body,
  Duration timeout,
);

/// The iPhone app keeps the save as files behind its own server
/// (tool/proto_app, SaveFiles): the worker reads and writes them itself, so
/// the page's thread never holds the save's text (6.7 MB at 10,000 head).
class ServerSaveIo implements SaveIo {
  ServerSaveIo(
    this.http, {
    required this.base,
    required this.token,
    this.timeout = const Duration(seconds: 15),
  });

  final HttpCall http;

  /// The page's origin (the app's server).
  final String base;

  /// The launch's key to the save (`x-marah-save`).
  final String token;

  /// A request that has not answered by then is cancelled and fails: one
  /// that never answers must not hold up every later write.
  final Duration timeout;

  Map<String, String> get _headers => {'x-marah-save': token};

  @override
  Future<Map<String, String>> load() async {
    final (status, body) = await http(
      'GET',
      '$base/save',
      _headers,
      null,
      timeout,
    );
    if (status != 200)
      throw SaveWriteFailed('the save could not be read ($status)');
    final all = jsonDecode(body);
    if (all is! Map)
      throw const SaveWriteFailed('the save is not a list of keys');
    return {
      for (final e in all.entries)
        if (e.key is String && e.value is String)
          e.key as String: e.value as String,
    };
  }

  @override
  Future<void> keep(String key, String? value) async {
    final (int, String) r;
    try {
      r = await http(
        value == null ? 'DELETE' : 'PUT',
        '$base/save/${Uri.encodeComponent(key)}',
        _headers,
        value,
        timeout,
      );
    } on Object catch (e) {
      throw SaveWriteFailed('$key: $e');
    }
    if (r.$1 != 204 && r.$1 != 200) throw SaveWriteFailed('$key: ${r.$1}');
  }
}

/// A write that could not be kept.
class SaveWriteFailed implements Exception {
  const SaveWriteFailed(this.reason);
  final String reason;

  @override
  String toString() => 'save not written: $reason';
}
