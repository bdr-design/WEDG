import 'dart:async';

import 'package:marah_data/marah_data.dart';

/// The save's keys and values held in the worker, seeded by the page at start.
/// Every change is sent to the page ([send]) to keep (the iPhone app's files
/// through its local server, or the browser's storage in tests), and the write
/// completes only when the page says it landed ([stored]): a write the page
/// could not keep fails here, so the engine reports it and tries again.
class WorkerBackend implements SaveBackend {
  WorkerBackend(
    Map<String, String> seed,
    this.send, {
    this.timeout = const Duration(seconds: 30),
    int Function()? nextSeq,
  }) : _data = {...seed},
       _nextSeq = nextSeq;

  final Map<String, String> _data;

  /// Hands a write (a null value deletes the key) to the page, numbered.
  final void Function(int seq, String key, String? value) send;

  /// A write the page has not answered by then counts as failed.
  final Duration timeout;

  final Map<int, Completer<void>> _pending = {};
  int _seq = 0;

  /// Numbers the writes; shared by every backend the worker makes, so a late
  /// answer to an earlier engine's write never settles a later one's.
  final int Function()? _nextSeq;

  /// The page's answer for write [seq].
  void stored(int seq, {required bool ok, String? error}) {
    final c = _pending.remove(seq);
    if (c == null) return; // already timed out
    if (ok) {
      c.complete();
    } else {
      c.completeError(SaveWriteFailed(error ?? 'not written'));
    }
  }

  Future<void> _persist(String key, String? value) {
    final seq = _nextSeq?.call() ?? ++_seq;
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

  @override
  Future<String?> read(String key) async => _data[key];

  @override
  Future<void> write(String key, String value) {
    _data[key] = value;
    return _persist(key, value);
  }

  @override
  Future<void> delete(String key) {
    _data.remove(key);
    return _persist(key, null);
  }

  @override
  Future<void> copy(String from, String to) async {
    final v = _data[from];
    if (v == null) return; // as SaveBackend says: nothing to copy, nothing done
    return write(to, v);
  }
}

/// The page could not keep a write.
class SaveWriteFailed implements Exception {
  const SaveWriteFailed(this.reason);
  final String reason;

  @override
  String toString() => 'save not written: $reason';
}
