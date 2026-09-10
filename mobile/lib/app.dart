import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'l10n/app_strings.dart';
import 'state/app_lock_controller.dart';
import 'state/settings_controller.dart';
import 'state/totp_clock.dart';
import 'state/vault_controller.dart';
import 'theme.dart';
import 'ui/accounts_screen.dart';
import 'ui/app_scope.dart';
import 'ui/lock_screen.dart';

class AuthenticatorApp extends StatefulWidget {
  const AuthenticatorApp({
    super.key,
    required this.settings,
    required this.vault,
  });

  final SettingsController settings;
  final VaultController vault;

  @override
  State<AuthenticatorApp> createState() => _AuthenticatorAppState();
}

class _AuthenticatorAppState extends State<AuthenticatorApp> {
  late final AppLockController _lock = AppLockController(widget.settings);
  late final TotpClock _clock = TotpClock();

  @override
  void dispose() {
    _clock.dispose();
    _lock.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AppScope(
      settings: widget.settings,
      vault: widget.vault,
      lock: _lock,
      clock: _clock,
      child: ListenableBuilder(
        listenable: widget.settings,
        builder: (BuildContext context, _) {
          return MaterialApp(
            onGenerateTitle: (BuildContext context) =>
                AppStrings.of(context).appTitle,
            debugShowCheckedModeBanner: false,
            theme: buildAppTheme(AppPalette.light, Brightness.light),
            darkTheme: buildAppTheme(AppPalette.dark, Brightness.dark),
            themeMode: widget.settings.themeMode,
            locale: widget.settings.language.locale,
            supportedLocales: AppLanguage.values
                .map((AppLanguage l) => l.locale)
                .toList(growable: false),
            localizationsDelegates: const <LocalizationsDelegate<dynamic>>[
              GlobalMaterialLocalizations.delegate,
              GlobalWidgetsLocalizations.delegate,
              GlobalCupertinoLocalizations.delegate,
            ],
            home: const _Home(),
          );
        },
      ),
    );
  }
}

/// Shows the lock screen or the accounts, and keeps them as one persistent
/// subtree so unlocking doesn't rebuild the vault from scratch.
class _Home extends StatelessWidget {
  const _Home();

  @override
  Widget build(BuildContext context) {
    final AppLockController lock = AppScope.of(context).lock;
    return ListenableBuilder(
      listenable: lock,
      builder: (BuildContext context, Widget? child) {
        return Stack(
          children: <Widget>[
            // Kept alive under the lock so codes are on screen the instant it
            // lifts — but hidden from both the eye and the semantics tree.
            ExcludeSemantics(
              excluding: lock.isLocked,
              child: TickerMode(
                enabled: !lock.isLocked,
                child: Visibility(
                  visible: !lock.isLocked,
                  maintainState: true,
                  child: child!,
                ),
              ),
            ),
            if (lock.isLocked) const LockScreen(),
          ],
        );
      },
      child: const AccountsScreen(),
    );
  }
}
