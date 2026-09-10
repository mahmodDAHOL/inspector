import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../core/base32.dart';
import '../core/otpauth.dart';
import '../core/portal_api.dart';
import '../core/totp.dart';
import '../l10n/app_strings.dart';
import '../models/account.dart';
import '../state/settings_controller.dart';
import '../state/vault_controller.dart';
import '../theme.dart';
import 'app_scope.dart';
import 'widgets/portal_header.dart';

/// Two steps, in this order for a reason: prove the account is yours against
/// the portal first, then take the secret. Reversing them would let anyone
/// who finds a secret on a whiteboard enroll it silently.
enum _Step { identity, secret }

class AddAccountScreen extends StatefulWidget {
  const AddAccountScreen({super.key});

  @override
  State<AddAccountScreen> createState() => _AddAccountScreenState();
}

class _AddAccountScreenState extends State<AddAccountScreen> {
  final TextEditingController _username = TextEditingController();
  final TextEditingController _password = TextEditingController();
  final TextEditingController _secret = TextEditingController();
  final GlobalKey<FormState> _identityForm = GlobalKey<FormState>();

  _Step _step = _Step.identity;
  bool _busy = false;
  bool _obscurePassword = true;
  String? _error;
  String? _notice;

  /// Held only in memory, only until this screen closes.
  String? _tempToken;

  /// False when we could not get a temp token (offline enrollment, or the
  /// portal skipped MFA), i.e. the secret cannot be confirmed.
  bool _canConfirm = false;

  /// Set when confirmation failed for a reason that is not "wrong secret",
  /// so the screen can offer to save it unconfirmed instead.
  bool _offerUnverifiedSave = false;

  @override
  void dispose() {
    _username.dispose();
    _password.dispose();
    _secret.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final AppStrings s = AppStrings.of(context);
    final AppPalette palette = AppPalette.of(context);

    return Scaffold(
      body: Column(
        children: <Widget>[
          PortalHeader(
            title: s.addAccountTitle,
            subtitle: _step == _Step.identity ? s.stepIdentity : s.stepSecret,
            // The stock BackButton, so it carries the platform's own icon,
            // localized tooltip and semantics rather than a hand-rolled copy.
            leading: const BackButton(color: Color(0xFFF6F3EC)),
          ),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(20, 24, 20, 32),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  Text(
                    _step == _Step.identity
                        ? s.stepIdentityBody
                        : s.stepSecretBody,
                    style: TextStyle(
                      fontSize: 14,
                      height: 1.65,
                      color: palette.inkSoft,
                    ),
                  ),
                  const SizedBox(height: 22),
                  if (_step == _Step.identity)
                    _buildIdentityStep(s)
                  else
                    _buildSecretStep(s),
                  if (_notice != null) ...<Widget>[
                    const SizedBox(height: 18),
                    _Banner(text: _notice!, tone: _BannerTone.info),
                  ],
                  if (_error != null) ...<Widget>[
                    const SizedBox(height: 18),
                    _Banner(text: _error!, tone: _BannerTone.error),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildIdentityStep(AppStrings s) {
    return Form(
      key: _identityForm,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          TextFormField(
            controller: _username,
            enabled: !_busy,
            autocorrect: false,
            textInputAction: TextInputAction.next,
            decoration: InputDecoration(
              labelText: s.usernameLabel,
              prefixIcon: const Icon(Icons.person_outline),
            ),
            validator: (String? value) =>
                (value == null || value.trim().isEmpty)
                ? s.usernameRequired
                : null,
          ),
          const SizedBox(height: 14),
          TextFormField(
            controller: _password,
            enabled: !_busy,
            obscureText: _obscurePassword,
            autocorrect: false,
            enableSuggestions: false,
            textInputAction: TextInputAction.done,
            onFieldSubmitted: (_) => _submitIdentity(),
            decoration: InputDecoration(
              labelText: s.passwordLabel,
              prefixIcon: const Icon(Icons.lock_outline),
              suffixIcon: IconButton(
                onPressed: () =>
                    setState(() => _obscurePassword = !_obscurePassword),
                icon: Icon(
                  _obscurePassword
                      ? Icons.visibility_outlined
                      : Icons.visibility_off_outlined,
                ),
              ),
            ),
            validator: (String? value) => (value == null || value.isEmpty)
                ? s.passwordRequired
                : null,
          ),
          const SizedBox(height: 24),
          FilledButton(
            onPressed: _busy ? null : _submitIdentity,
            child: _busy
                ? _ButtonProgress(label: s.checkingCredentials)
                : Text(s.next),
          ),
          const SizedBox(height: 6),
          TextButton(
            onPressed: _busy ? null : _enrollOffline,
            child: Text(s.enrollOffline),
          ),
        ],
      ),
    );
  }

  Widget _buildSecretStep(AppStrings s) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        TextField(
          controller: _secret,
          enabled: !_busy,
          autocorrect: false,
          enableSuggestions: false,
          maxLines: 3,
          minLines: 1,
          textDirection: TextDirection.ltr,
          style: const TextStyle(letterSpacing: 1.2),
          decoration: InputDecoration(
            labelText: s.secretLabel,
            hintText: s.secretHint,
            hintTextDirection: TextDirection.ltr,
            alignLabelWithHint: true,
          ),
        ),
        const SizedBox(height: 10),
        Align(
          alignment: AlignmentDirectional.centerStart,
          child: TextButton.icon(
            onPressed: _busy ? null : _pasteSecret,
            icon: const Icon(Icons.content_paste_outlined, size: 18),
            label: Text(s.pasteFromClipboard),
          ),
        ),
        const SizedBox(height: 14),
        FilledButton(
          onPressed: _busy ? null : _submitSecret,
          child: _busy
              ? _ButtonProgress(
                  label: _canConfirm ? s.confirmingSecret : s.checkingCredentials,
                )
              : Text(s.save),
        ),
        if (_offerUnverifiedSave)
          TextButton(
            onPressed: _busy ? null : _saveUnverifiedAfterFailure,
            child: Text(s.enrollOffline),
          ),
      ],
    );
  }

  Future<void> _pasteSecret() async {
    final AppStrings s = AppStrings.of(context);
    final ClipboardData? data = await Clipboard.getData(Clipboard.kTextPlain);
    final String text = data?.text?.trim() ?? '';
    if (!mounted) return;
    if (text.isEmpty) {
      setState(() => _error = s.clipboardEmpty);
      return;
    }
    setState(() {
      _secret.text = text;
      _error = null;
    });
  }

  Future<void> _submitIdentity() async {
    final AppStrings s = AppStrings.of(context);
    final AppScope scope = AppScope.of(context);
    final SettingsController settings = scope.settings;
    final VaultController vault = scope.vault;

    if (!(_identityForm.currentState?.validate() ?? false)) return;

    final String username = _username.text.trim();
    if (vault.hasAccountNamed(username)) {
      setState(() => _error = s.accountExists(username));
      return;
    }
    if (!settings.hasServerUrl) {
      setState(() => _error = s.serverUrlMissing);
      return;
    }

    setState(() {
      _busy = true;
      _error = null;
      _notice = null;
    });

    try {
      final PasswordCheckResult result = await settings.buildApi().checkPassword(
        username: username,
        password: _password.text,
      );
      if (!mounted) return;
      setState(() {
        _tempToken = result.tempToken;
        _canConfirm = result.tempToken != null;
        _step = _Step.secret;
        _notice = result.tempToken == null ? s.mfaNotRequired : null;
        // The password has done its job; don't keep it in a live text field.
        _password.clear();
      });
    } on PortalApiException catch (e) {
      if (!mounted) return;
      setState(() => _error = s.portalError(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _enrollOffline() async {
    final AppStrings s = AppStrings.of(context);
    final VaultController vault = AppScope.of(context).vault;

    final String username = _username.text.trim();
    if (username.isEmpty) {
      setState(() => _error = s.usernameRequired);
      return;
    }
    if (vault.hasAccountNamed(username)) {
      setState(() => _error = s.accountExists(username));
      return;
    }

    if (!await _confirmUnverifiedEnrollment()) return;

    setState(() {
      _tempToken = null;
      _canConfirm = false;
      _step = _Step.secret;
      _error = null;
      _notice = null;
      _password.clear();
    });
  }

  /// Asks before saving a secret the portal has not vouched for. Shared by
  /// both routes into an unconfirmed enrollment.
  Future<bool> _confirmUnverifiedEnrollment() async {
    final AppStrings s = AppStrings.of(context);
    final bool? proceed = await showDialog<bool>(
      context: context,
      builder: (BuildContext context) => AlertDialog(
        title: Text(s.enrollOfflineTitle),
        content: Text(s.enrollOfflineBody),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(s.cancel),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(s.enrollOfflineConfirm),
          ),
        ],
      ),
    );
    return mounted && (proceed ?? false);
  }

  /// The portal could not be asked at the confirmation step. Rather than dead-
  /// ending someone who has already typed the secret, offer to save it
  /// unconfirmed from here.
  Future<void> _saveUnverifiedAfterFailure() async {
    if (!await _confirmUnverifiedEnrollment()) return;
    setState(() {
      _tempToken = null;
      _canConfirm = false;
      _offerUnverifiedSave = false;
      _error = null;
    });
    await _submitSecret();
  }

  Future<void> _submitSecret() async {
    final AppStrings s = AppStrings.of(context);
    final AppScope scope = AppScope.of(context);
    final SettingsController settings = scope.settings;
    final VaultController vault = scope.vault;
    final NavigatorState navigator = Navigator.of(context);
    final ScaffoldMessengerState messenger = ScaffoldMessenger.of(context);

    final String raw = _secret.text.trim();
    if (raw.isEmpty) {
      setState(() => _error = s.secretTooShort);
      return;
    }

    String secret;
    int digits = kDefaultDigits;
    int period = kDefaultPeriod;
    TotpAlgorithm algorithm = TotpAlgorithm.sha1;
    String? issuer;

    if (looksLikeOtpAuthUri(raw)) {
      try {
        final OtpAuthData data = parseOtpAuthUri(raw);
        secret = data.secret;
        digits = data.digits;
        period = data.period;
        algorithm = data.algorithm;
        issuer = data.issuer;
      } on OtpAuthParseException catch (e) {
        setState(() => _error = e.message);
        return;
      }
    } else {
      secret = normalizeBase32(raw);
      if (!isValidBase32(secret)) {
        setState(() => _error = s.secretInvalid);
        return;
      }
      // 16 Base32 characters is 80 bits — the shortest secret pyotp will
      // hand out, and short enough that a truncated paste is obvious.
      if (secret.length < 16) {
        setState(() => _error = s.secretTooShort);
        return;
      }
    }

    issuer ??= Uri.tryParse(settings.serverUrl)?.host;

    setState(() {
      _busy = true;
      _error = null;
      _offerUnverifiedSave = false;
    });

    bool verified = false;
    final String? tempToken = _tempToken;
    if (_canConfirm && tempToken != null) {
      try {
        final String code = generateTotp(
          secret: secret,
          digits: digits,
          period: period,
          algorithm: algorithm,
        );
        await settings.buildApi().confirmCode(
          tempToken: tempToken,
          code: code,
        );
        verified = true;
      } on PortalApiException catch (e) {
        if (!mounted) return;
        setState(() {
          _busy = false;
          _error = s.portalError(e);
          // A rejected code means this secret is wrong, and saving it would
          // only produce codes the portal keeps refusing. Any other failure
          // means we could not ask at all — that one is worth offering.
          _offerUnverifiedSave = e.kind != PortalErrorKind.invalidCode;
        });
        return;
      } on Base32DecodeException {
        if (!mounted) return;
        setState(() {
          _busy = false;
          _error = s.secretInvalid;
        });
        return;
      }
    }

    final TotpAccount account = TotpAccount(
      id: '${DateTime.now().microsecondsSinceEpoch}',
      username: _username.text.trim(),
      secret: secret,
      issuer: issuer,
      digits: digits,
      period: period,
      algorithm: algorithm,
      serverVerified: verified,
      serverUrl: settings.serverUrl.isEmpty ? null : settings.serverUrl,
      addedAt: DateTime.now(),
    );
    await vault.add(account);

    if (!mounted) return;
    navigator.pop();
    // The messenger lives above this route, so the confirmation survives the
    // pop and lands on the accounts screen the user is looking at.
    messenger
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(
            account.serverVerified
                ? s.enrolledVerifiedBody(account.username)
                : s.enrolledUnverifiedBody(account.username),
          ),
          duration: const Duration(seconds: 4),
        ),
      );
  }
}

enum _BannerTone { info, error }

class _Banner extends StatelessWidget {
  const _Banner({required this.text, required this.tone});

  final String text;
  final _BannerTone tone;

  @override
  Widget build(BuildContext context) {
    final AppPalette palette = AppPalette.of(context);
    final Color color = tone == _BannerTone.error
        ? palette.danger
        : palette.brass;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withValues(alpha: 0.35)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(
            tone == _BannerTone.error
                ? Icons.error_outline
                : Icons.info_outline,
            size: 19,
            color: color,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              text,
              style: TextStyle(fontSize: 13.5, height: 1.55, color: palette.ink),
            ),
          ),
        ],
      ),
    );
  }
}

class _ButtonProgress extends StatelessWidget {
  const _ButtonProgress({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: <Widget>[
        const SizedBox(
          width: 18,
          height: 18,
          child: CircularProgressIndicator(
            strokeWidth: 2,
            color: Color(0xFFF6F3EC),
          ),
        ),
        const SizedBox(width: 12),
        Text(label),
      ],
    );
  }
}
