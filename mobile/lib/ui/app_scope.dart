/// The app's four long-lived objects, handed down the tree.
///
/// Small enough not to need a state-management package: widgets read what
/// they need with `AppScope.of(context)` and rebuild by listening to the one
/// controller they actually care about.
library;

import 'package:flutter/widgets.dart';

import '../state/app_lock_controller.dart';
import '../state/settings_controller.dart';
import '../state/totp_clock.dart';
import '../state/vault_controller.dart';

class AppScope extends InheritedWidget {
  const AppScope({
    super.key,
    required this.settings,
    required this.vault,
    required this.lock,
    required this.clock,
    required super.child,
  });

  final SettingsController settings;
  final VaultController vault;
  final AppLockController lock;
  final TotpClock clock;

  static AppScope of(BuildContext context) {
    final AppScope? scope = context
        .dependOnInheritedWidgetOfExactType<AppScope>();
    assert(scope != null, 'No AppScope found above this widget.');
    return scope!;
  }

  @override
  bool updateShouldNotify(AppScope oldWidget) =>
      settings != oldWidget.settings ||
      vault != oldWidget.vault ||
      lock != oldWidget.lock ||
      clock != oldWidget.clock;
}
