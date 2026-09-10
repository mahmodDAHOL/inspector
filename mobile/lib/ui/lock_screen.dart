import 'package:flutter/material.dart';

import '../l10n/app_strings.dart';
import '../state/app_lock_controller.dart';
import '../theme.dart';
import 'app_scope.dart';

/// Covers the codes until the device says who is holding the phone.
class LockScreen extends StatefulWidget {
  const LockScreen({super.key});

  @override
  State<LockScreen> createState() => _LockScreenState();
}

class _LockScreenState extends State<LockScreen> {
  bool _prompting = false;
  String? _message;
  bool _promptedOnce = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_promptedOnce) return;
    _promptedOnce = true;
    // Ask immediately, so the common case is one glance at the fingerprint
    // sensor rather than a screen that has to be tapped first.
    WidgetsBinding.instance.addPostFrameCallback((_) => _authenticate());
  }

  Future<void> _authenticate() async {
    if (_prompting) return;
    final AppStrings s = AppStrings.of(context);
    final AppLockController lock = AppScope.of(context).lock;

    setState(() {
      _prompting = true;
      _message = null;
    });
    final UnlockOutcome outcome = await lock.unlock(s.unlockReason);
    if (!mounted) return;
    setState(() {
      _prompting = false;
      _message = switch (outcome) {
        UnlockOutcome.success || UnlockOutcome.canceled => null,
        UnlockOutcome.lockedOut => s.unlockLockedOut,
        UnlockOutcome.unavailable => s.appLockUnavailable,
        UnlockOutcome.failed => s.unlockFailed,
      };
    });
  }

  @override
  Widget build(BuildContext context) {
    final AppStrings s = AppStrings.of(context);
    final AppPalette palette = AppPalette.of(context);

    return Material(
      color: palette.ground,
      child: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 32),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                Container(
                  width: 96,
                  height: 96,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: <Color>[palette.teal, palette.tealDeep],
                    ),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.lock_outline,
                    size: 42,
                    color: Color(0xFFF6F3EC),
                  ),
                ),
                const SizedBox(height: 26),
                Text(
                  s.lockedTitle,
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w700,
                    color: palette.ink,
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  s.lockedBody,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 14,
                    height: 1.6,
                    color: palette.inkSoft,
                  ),
                ),
                if (_message != null) ...<Widget>[
                  const SizedBox(height: 16),
                  Text(
                    _message!,
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 13,
                      height: 1.55,
                      color: palette.danger,
                    ),
                  ),
                ],
                const SizedBox(height: 30),
                SizedBox(
                  width: 240,
                  child: FilledButton.icon(
                    onPressed: _prompting ? null : _authenticate,
                    icon: const Icon(Icons.fingerprint),
                    label: Text(s.unlock),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
