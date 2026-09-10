/// Non-secret preferences: which portal to talk to, language, theme, whether
/// the app asks for a fingerprint before showing codes.
///
/// Deliberately not in the keystore — none of this is a secret, and keeping
/// the secure store to exactly one purpose (the TOTP secrets) makes it much
/// easier to reason about what an attacker with the device would get.
library;

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../core/portal_api.dart';
import '../l10n/app_strings.dart';

class SettingsController extends ChangeNotifier {
  SettingsController._(this._prefs)
    : _serverUrl = _prefs.getString(_kServerUrl) ?? defaultServerUrl,
      _allowSelfSigned = _prefs.getBool(_kAllowSelfSigned) ?? false,
      _language = AppLanguage.fromCode(_prefs.getString(_kLanguage)),
      _themeMode = _themeModeFromName(_prefs.getString(_kThemeMode)),
      _appLockEnabled = _prefs.getBool(_kAppLock) ?? false;

  /// The ministry's portal, so a fresh install can enroll without anyone
  /// having to type an address. Only used until the user saves one — an
  /// address they saved (including an empty one) always wins.
  static const String defaultServerUrl = 'https://inspector.momc.sy';

  static const String _kServerUrl = 'server_url';
  static const String _kAllowSelfSigned = 'allow_self_signed';
  static const String _kLanguage = 'language';
  static const String _kThemeMode = 'theme_mode';
  static const String _kAppLock = 'app_lock_enabled';

  static Future<SettingsController> load() async =>
      SettingsController._(await SharedPreferences.getInstance());

  final SharedPreferences _prefs;

  String _serverUrl;
  bool _allowSelfSigned;
  AppLanguage _language;
  ThemeMode _themeMode;
  bool _appLockEnabled;

  String get serverUrl => _serverUrl;
  bool get hasServerUrl => PortalApi.isPlausibleBaseUrl(_serverUrl);
  bool get allowSelfSigned => _allowSelfSigned;
  AppLanguage get language => _language;
  ThemeMode get themeMode => _themeMode;
  bool get appLockEnabled => _appLockEnabled;

  /// A client pointed at the currently configured portal.
  PortalApi buildApi() => PortalApi(
    baseUrl: _serverUrl,
    allowSelfSignedCertificate: _allowSelfSigned,
  );

  Future<void> setServerUrl(String value) async {
    final String normalized = PortalApi.normalizeBaseUrl(value);
    if (normalized != _serverUrl) {
      _serverUrl = normalized;
      notifyListeners();
    }
    // Written even when it matches what is already in effect: on a fresh
    // install that value is only [defaultServerUrl], and an address the user
    // deliberately confirmed must not move if a later release ships a
    // different default.
    await _prefs.setString(_kServerUrl, normalized);
  }

  Future<void> setAllowSelfSigned(bool value) async {
    if (value == _allowSelfSigned) return;
    _allowSelfSigned = value;
    notifyListeners();
    await _prefs.setBool(_kAllowSelfSigned, value);
  }

  Future<void> setLanguage(AppLanguage value) async {
    if (value == _language) return;
    _language = value;
    notifyListeners();
    await _prefs.setString(_kLanguage, value.code);
  }

  Future<void> setThemeMode(ThemeMode value) async {
    if (value == _themeMode) return;
    _themeMode = value;
    notifyListeners();
    await _prefs.setString(_kThemeMode, value.name);
  }

  Future<void> setAppLockEnabled(bool value) async {
    if (value == _appLockEnabled) return;
    _appLockEnabled = value;
    notifyListeners();
    await _prefs.setBool(_kAppLock, value);
  }

  static ThemeMode _themeModeFromName(String? name) => ThemeMode.values
      .where((ThemeMode m) => m.name == name)
      .firstOrNull ??
      ThemeMode.system;
}
