import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'app.dart';
import 'state/settings_controller.dart';
import 'state/vault_controller.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // A code generator is a one-hand, portrait tool; letting it rotate only
  // makes the digits smaller.
  await SystemChrome.setPreferredOrientations(<DeviceOrientation>[
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  final SettingsController settings = await SettingsController.load();
  final VaultController vault = VaultController();
  await vault.load();

  runApp(AuthenticatorApp(settings: settings, vault: vault));
}
