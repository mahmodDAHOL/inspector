import 'package:flutter/material.dart';

import '../core/portal_api.dart';
import '../l10n/app_strings.dart';
import '../state/app_lock_controller.dart';
import '../state/settings_controller.dart';
import '../state/vault_controller.dart';
import '../theme.dart';
import 'app_scope.dart';
import 'widgets/portal_header.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final TextEditingController _serverUrl = TextEditingController();
  bool _testing = false;
  String? _serverError;
  bool _lockAvailable = true;
  bool _initialized = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_initialized) return;
    _initialized = true;
    _serverUrl.text = AppScope.of(context).settings.serverUrl;
    _checkLockAvailability();
  }

  @override
  void dispose() {
    _serverUrl.dispose();
    super.dispose();
  }

  Future<void> _checkLockAvailability() async {
    final AppLockController lock = AppScope.of(context).lock;
    final bool available = await lock.deviceSupportsLock();
    if (mounted) setState(() => _lockAvailable = available);
  }

  @override
  Widget build(BuildContext context) {
    final AppStrings s = AppStrings.of(context);
    final AppScope scope = AppScope.of(context);
    final SettingsController settings = scope.settings;

    return Scaffold(
      body: Column(
        children: <Widget>[
          PortalHeader(
            title: s.settingsTitle,
            // The stock BackButton, so it carries the platform's own icon,
            // localized tooltip and semantics rather than a hand-rolled copy.
            leading: const BackButton(color: Color(0xFFF6F3EC)),
          ),
          Expanded(
            child: ListenableBuilder(
              listenable: settings,
              builder: (BuildContext context, _) => ListView(
                padding: const EdgeInsets.fromLTRB(20, 22, 20, 40),
                children: <Widget>[
                  _SectionTitle(s.serverSection),
                  TextField(
                    controller: _serverUrl,
                    autocorrect: false,
                    keyboardType: TextInputType.url,
                    textDirection: TextDirection.ltr,
                    decoration: InputDecoration(
                      labelText: s.serverUrlLabel,
                      hintText: s.serverUrlHint,
                      hintTextDirection: TextDirection.ltr,
                      prefixIcon: const Icon(Icons.dns_outlined),
                      errorText: _serverError,
                      helperText: s.serverUrlHelp,
                      helperMaxLines: 2,
                    ),
                    onChanged: (_) {
                      if (_serverError != null) {
                        setState(() => _serverError = null);
                      }
                    },
                    onSubmitted: (_) => _saveServerUrl(settings),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: <Widget>[
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: _testing
                              ? null
                              : () => _testConnection(settings),
                          icon: _testing
                              ? const SizedBox(
                                  width: 16,
                                  height: 16,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                  ),
                                )
                              : const Icon(Icons.wifi_tethering, size: 18),
                          label: Text(
                            _testing ? s.testingConnection : s.testConnection,
                          ),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: FilledButton(
                          onPressed: () => _saveServerUrl(settings),
                          child: Text(s.save),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  _SwitchTile(
                    title: s.allowSelfSignedTitle,
                    subtitle: s.allowSelfSignedBody,
                    value: settings.allowSelfSigned,
                    onChanged: settings.setAllowSelfSigned,
                    warn: settings.allowSelfSigned,
                  ),

                  const SizedBox(height: 26),
                  _SectionTitle(s.securitySection),
                  _SwitchTile(
                    title: s.appLockTitle,
                    subtitle: _lockAvailable
                        ? s.appLockBody
                        : s.appLockUnavailable,
                    value: settings.appLockEnabled && _lockAvailable,
                    onChanged: _lockAvailable
                        ? settings.setAppLockEnabled
                        : null,
                  ),

                  const SizedBox(height: 26),
                  _SectionTitle(s.appearanceSection),
                  _ChoiceTile<AppLanguage>(
                    icon: Icons.translate,
                    label: s.languageLabel,
                    value: settings.language,
                    options: <_Choice<AppLanguage>>[
                      for (final AppLanguage language in AppLanguage.values)
                        _Choice<AppLanguage>(language, language.nativeName),
                    ],
                    onChanged: settings.setLanguage,
                  ),
                  const SizedBox(height: 10),
                  _ChoiceTile<ThemeMode>(
                    icon: Icons.brightness_6_outlined,
                    label: s.themeLabel,
                    value: settings.themeMode,
                    options: <_Choice<ThemeMode>>[
                      _Choice<ThemeMode>(ThemeMode.system, s.themeSystem),
                      _Choice<ThemeMode>(ThemeMode.light, s.themeLight),
                      _Choice<ThemeMode>(ThemeMode.dark, s.themeDark),
                    ],
                    onChanged: settings.setThemeMode,
                  ),

                  const SizedBox(height: 26),
                  _SectionTitle(s.dangerSection),
                  _DangerTile(
                    title: s.removeAllTitle,
                    subtitle: s.removeAllBody,
                    onTap: () => _confirmWipe(scope.vault),
                  ),

                  const SizedBox(height: 26),
                  _SectionTitle(s.aboutSection),
                  Text(
                    s.aboutBody,
                    style: TextStyle(
                      fontSize: 13.5,
                      height: 1.7,
                      color: AppPalette.of(context).inkSoft,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _saveServerUrl(SettingsController settings) async {
    final AppStrings s = AppStrings.of(context);
    final String value = _serverUrl.text.trim();
    if (value.isNotEmpty && !PortalApi.isPlausibleBaseUrl(value)) {
      setState(() => _serverError = s.serverUrlInvalid);
      return;
    }
    await settings.setServerUrl(value);
    if (!mounted) return;
    setState(() {
      _serverError = null;
      _serverUrl.text = settings.serverUrl;
    });
    FocusScope.of(context).unfocus();
  }

  Future<void> _testConnection(SettingsController settings) async {
    final AppStrings s = AppStrings.of(context);
    final ScaffoldMessengerState messenger = ScaffoldMessenger.of(context);
    final String value = _serverUrl.text.trim();
    if (!PortalApi.isPlausibleBaseUrl(value)) {
      setState(() => _serverError = s.serverUrlInvalid);
      return;
    }
    // Test what is in the field, not what was last saved.
    await settings.setServerUrl(value);

    setState(() {
      _testing = true;
      _serverError = null;
    });
    try {
      await settings.buildApi().checkHealth();
      messenger
        ..hideCurrentSnackBar()
        ..showSnackBar(SnackBar(content: Text(s.connectionOk)));
    } on PortalApiException catch (e) {
      messenger
        ..hideCurrentSnackBar()
        ..showSnackBar(SnackBar(content: Text(s.portalError(e))));
    } finally {
      if (mounted) setState(() => _testing = false);
    }
  }

  Future<void> _confirmWipe(VaultController vault) async {
    final AppStrings s = AppStrings.of(context);
    final AppPalette palette = AppPalette.of(context);
    final bool? confirmed = await showDialog<bool>(
      context: context,
      builder: (BuildContext context) => AlertDialog(
        title: Text(s.removeAllTitle),
        content: Text(s.removeAllBody),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(s.cancel),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            style: TextButton.styleFrom(foregroundColor: palette.danger),
            child: Text(s.remove),
          ),
        ],
      ),
    );
    if (confirmed ?? false) {
      await vault.removeAll();
    }
  }
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    final AppPalette palette = AppPalette.of(context);
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(
        text,
        style: TextStyle(
          fontSize: 12.5,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.6,
          color: palette.brass,
        ),
      ),
    );
  }
}

class _SwitchTile extends StatelessWidget {
  const _SwitchTile({
    required this.title,
    required this.subtitle,
    required this.value,
    required this.onChanged,
    this.warn = false,
  });

  final String title;
  final String subtitle;
  final bool value;
  final ValueChanged<bool>? onChanged;
  final bool warn;

  @override
  Widget build(BuildContext context) {
    final AppPalette palette = AppPalette.of(context);
    return Container(
      decoration: BoxDecoration(
        color: palette.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: warn ? palette.brass.withValues(alpha: 0.6) : palette.line,
        ),
      ),
      padding: const EdgeInsets.fromLTRB(16, 6, 8, 6),
      child: Row(
        children: <Widget>[
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                const SizedBox(height: 10),
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                    color: onChanged == null ? palette.inkFaint : palette.ink,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  subtitle,
                  style: TextStyle(
                    fontSize: 12.5,
                    height: 1.55,
                    color: palette.inkSoft,
                  ),
                ),
                const SizedBox(height: 10),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Switch(value: value, onChanged: onChanged),
        ],
      ),
    );
  }
}

class _Choice<T> {
  const _Choice(this.value, this.label);

  final T value;
  final String label;
}

class _ChoiceTile<T> extends StatelessWidget {
  const _ChoiceTile({
    required this.icon,
    required this.label,
    required this.value,
    required this.options,
    required this.onChanged,
  });

  final IconData icon;
  final String label;
  final T value;
  final List<_Choice<T>> options;
  final ValueChanged<T> onChanged;

  @override
  Widget build(BuildContext context) {
    final AppPalette palette = AppPalette.of(context);
    return Container(
      decoration: BoxDecoration(
        color: palette.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: palette.line),
      ),
      padding: const EdgeInsetsDirectional.fromSTEB(16, 14, 12, 14),
      child: Row(
        children: <Widget>[
          Icon(icon, size: 20, color: palette.inkSoft),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              label,
              style: TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w600,
                color: palette.ink,
              ),
            ),
          ),
          DropdownButtonHideUnderline(
            child: DropdownButton<T>(
              value: value,
              borderRadius: BorderRadius.circular(14),
              dropdownColor: palette.surface,
              style: TextStyle(fontSize: 14, color: palette.ink),
              items: <DropdownMenuItem<T>>[
                for (final _Choice<T> option in options)
                  DropdownMenuItem<T>(
                    value: option.value,
                    child: Text(option.label),
                  ),
              ],
              onChanged: (T? selected) {
                if (selected != null) onChanged(selected);
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _DangerTile extends StatelessWidget {
  const _DangerTile({
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final AppPalette palette = AppPalette.of(context);
    return InkWell(
      borderRadius: BorderRadius.circular(16),
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: palette.danger.withValues(alpha: 0.06),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: palette.danger.withValues(alpha: 0.35)),
        ),
        padding: const EdgeInsets.all(16),
        child: Row(
          children: <Widget>[
            Icon(Icons.delete_forever_outlined, color: palette.danger),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    title,
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                      color: palette.danger,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    subtitle,
                    style: TextStyle(
                      fontSize: 12.5,
                      height: 1.5,
                      color: palette.inkSoft,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
