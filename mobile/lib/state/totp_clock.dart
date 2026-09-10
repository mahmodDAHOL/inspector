/// A single ticking clock for the whole screen.
///
/// One timer drives every code tile, and it stops while the app is in the
/// background — a phone in a pocket has no reason to recompute HMACs.
library;

import 'dart:async';

import 'package:flutter/widgets.dart';

class TotpClock extends ChangeNotifier with WidgetsBindingObserver {
  TotpClock({this.interval = const Duration(milliseconds: 200)}) {
    WidgetsBinding.instance.addObserver(this);
    start();
  }

  /// Fine enough for the countdown ring to sweep smoothly; the code itself
  /// only changes once per period regardless.
  final Duration interval;

  DateTime _now = DateTime.now();
  Timer? _timer;

  DateTime get now => _now;

  void start() {
    _timer?.cancel();
    _now = DateTime.now();
    _timer = Timer.periodic(interval, (_) {
      _now = DateTime.now();
      notifyListeners();
    });
    notifyListeners();
  }

  void stop() {
    _timer?.cancel();
    _timer = null;
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      start();
    } else {
      stop();
    }
  }

  @override
  void dispose() {
    stop();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }
}
