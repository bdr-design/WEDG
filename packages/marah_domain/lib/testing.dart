/// Helpers for tests and long-run simulations. Not for the app.
library;

import 'dart:async';

import 'src/handlers/handlers.dart' show vetKeyedByDay;

export 'src/testing/bot.dart';

/// Runs [body] with the vet's price keyed by the day, as before the second
/// review's N5: only for the check that an old game is unchanged.
T runWithVetKeyedByDay<T>(T Function() body) =>
    runZoned(body, zoneValues: {vetKeyedByDay: true});
