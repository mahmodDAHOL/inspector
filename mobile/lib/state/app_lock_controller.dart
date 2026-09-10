/// Optional device-credential gate in front of the codes.
///
/// The lock is a screen over the UI, not encryption of the vault — the
/// secrets are already protected by the platform keystore. It exists so a
/// briefly-borrowed unlocked phone doesn't hand someone a working second
/// factor for a ministry account.
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:local_auth/local_auth.dart';

import 'settings_controller.dart';

enum UnlockOutcome { success, canceled, unavailable, lockedOut, failed }

class AppLockController extends ChangeNotifier with WidgetsBindingObserver {
  AppLockController(this._settings, {LocalAuthentication? auth})
    : _auth = auth ?? LocalAuthentication() {
    _locked = _settings.appLockEnabled;
    _settings.addListener(_onSettingsChanged);
    WidgetsBinding.instance.addObserver(this);
  }

  /// How long the app may sit in the background before it re-locks. Short
  /// enough to matter, long enough that switching to the portal to paste a
  /// code and coming back doesn't demand a fingerprint every time.
  static const Duration _gracePeriod = Duration(seconds: 30);

  final SettingsController _settings;
  final LocalAuthentication _auth;

  bool _locked = false;
  bool _authInProgress = false;
  DateTime? _backgroundedAt;

  bool get isLocked => _locked && _settings.appLockEnabled;

  Future<bool> deviceSupportsLock() async {
    try {
      return await _auth.isDeviceSupported();
    } on LocalAuthException {
      return false;
    } on MissingPluginException {
      return false;
    }
  }

  void lock() {
    if (_locked) return;
    _locked = true;
    notifyListeners();
  }

  Future<UnlockOutcome> unlock(String reason) async {
    if (_authInProgress) return UnlockOutcome.failed;
    _authInProgress = true;
    try {
      final bool ok = await _auth.authenticate(
        localizedReason: reason,
        // Device credential (PIN/pattern) is an acceptable fallback: the point
        // is that whoever holds the phone proves they can unlock it.
        biometricOnly: false,
        // Don't treat the system's own biometric sheet as "app backgrounded".
        persistAcrossBackgrounding: true,
      );
      if (ok) {
        _locked = false;
        _backgroundedAt = null;
        notifyListeners();
        return UnlockOutcome.success;
      }
      return UnlockOutcome.failed;
    } on LocalAuthException catch (e) {
      return switch (e.code) {
        LocalAuthExceptionCode.userCanceled ||
        LocalAuthExceptionCode.systemCanceled ||
        LocalAuthExceptionCode.timeout => UnlockOutcome.canceled,
        LocalAuthExceptionCode.temporaryLockout ||
        LocalAuthExceptionCode.biometricLockout => UnlockOutcome.lockedOut,
        LocalAuthExceptionCode.noCredentialsSet ||
        LocalAuthExceptionCode.noBiometricsEnrolled ||
        LocalAuthExceptionCode.noBiometricHardware ||
        LocalAuthExceptionCode.uiUnavailable => UnlockOutcome.unavailable,
        _ => UnlockOutcome.failed,
      };
    } finally {
      _authInProgress = false;
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (!_settings.appLockEnabled) return;
    // While the biometric sheet is up the app itself reports paused/inactive;
    // re-locking on that would fight the very prompt asking to unlock.
    if (_authInProgress) return;

    switch (state) {
      case AppLifecycleState.paused:
      case AppLifecycleState.hidden:
        _backgroundedAt ??= DateTime.now();
      case AppLifecycleState.resumed:
        final DateTime? since = _backgroundedAt;
        _backgroundedAt = null;
        if (since != null && DateTime.now().difference(since) >= _gracePeriod) {
          lock();
        }
      case AppLifecycleState.inactive:
      case AppLifecycleState.detached:
        break;
    }
  }

  void _onSettingsChanged() {
    // Turning the lock on should take effect the next time the app is opened,
    // not strand the user who just flipped the switch behind a lock screen.
    if (!_settings.appLockEnabled && _locked) {
      _locked = false;
      notifyListeners();
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _settings.removeListener(_onSettingsChanged);
    super.dispose();
  }
}
