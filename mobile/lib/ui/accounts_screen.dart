import 'package:flutter/material.dart';

import '../l10n/app_strings.dart';
import '../models/account.dart';
import '../state/settings_controller.dart';
import '../state/totp_clock.dart';
import '../state/vault_controller.dart';
import '../theme.dart';
import 'add_account_screen.dart';
import 'app_scope.dart';
import 'settings_screen.dart';
import 'widgets/account_card.dart';
import 'widgets/portal_header.dart';

class AccountsScreen extends StatelessWidget {
  const AccountsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final AppStrings s = AppStrings.of(context);
    final AppScope scope = AppScope.of(context);
    final VaultController vault = scope.vault;

    return Scaffold(
      body: Column(
        children: <Widget>[
          ListenableBuilder(
            listenable: vault,
            builder: (BuildContext context, _) => PortalHeader(
              title: s.appTitle,
              subtitle: vault.accounts.isEmpty
                  ? s.appSubtitle
                  : s.accountCount(vault.accounts.length),
              actions: <Widget>[
                IconButton(
                  onPressed: () => Navigator.of(context).push<void>(
                    MaterialPageRoute<void>(
                      builder: (_) => const SettingsScreen(),
                    ),
                  ),
                  icon: const Icon(Icons.settings_outlined),
                  color: const Color(0xFFF6F3EC),
                  tooltip: s.settingsTitle,
                ),
              ],
            ),
          ),
          Expanded(
            child: ListenableBuilder(
              listenable: vault,
              builder: (BuildContext context, _) {
                if (vault.isLoading) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (vault.error != null) {
                  return _VaultErrorState(vault: vault);
                }
                if (vault.accounts.isEmpty) {
                  return const _EmptyState();
                }
                return _AccountList(vault: vault, clock: scope.clock);
              },
            ),
          ),
        ],
      ),
      floatingActionButton: ListenableBuilder(
        listenable: vault,
        builder: (BuildContext context, _) => vault.accounts.isEmpty
            ? const SizedBox.shrink()
            : FloatingActionButton.extended(
                onPressed: () => openAddAccount(context),
                icon: const Icon(Icons.add),
                label: Text(s.addAccount),
                backgroundColor: AppPalette.of(context).teal,
                foregroundColor: const Color(0xFFF6F3EC),
              ),
      ),
    );
  }
}

Future<void> openAddAccount(BuildContext context) async {
  final SettingsController settings = AppScope.of(context).settings;
  final AppStrings s = AppStrings.of(context);
  final NavigatorState navigator = Navigator.of(context);
  final ScaffoldMessengerState messenger = ScaffoldMessenger.of(context);

  // Enrollment needs a portal to ask, so send a first-run user to settings
  // rather than into a form that cannot succeed.
  if (!settings.hasServerUrl) {
    messenger
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(s.serverUrlMissing),
          action: SnackBarAction(
            label: s.openSettings,
            textColor: const Color(0xFFF6F3EC),
            onPressed: () => navigator.push<void>(
              MaterialPageRoute<void>(builder: (_) => const SettingsScreen()),
            ),
          ),
        ),
      );
    return;
  }

  await navigator.push<void>(
    MaterialPageRoute<void>(builder: (_) => const AddAccountScreen()),
  );
}

class _AccountList extends StatelessWidget {
  const _AccountList({required this.vault, required this.clock});

  final VaultController vault;
  final TotpClock clock;

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: clock,
      builder: (BuildContext context, _) {
        final List<TotpAccount> accounts = vault.accounts;
        return ListView.separated(
          padding: const EdgeInsets.fromLTRB(16, 20, 16, 110),
          itemCount: accounts.length,
          separatorBuilder: (_, _) => const SizedBox(height: 12),
          itemBuilder: (BuildContext context, int index) {
            final TotpAccount account = accounts[index];
            return AccountCard(
              key: ValueKey<String>(account.id),
              account: account,
              now: clock.now,
              onDelete: () => _confirmDelete(context, vault, account),
            );
          },
        );
      },
    );
  }

  Future<void> _confirmDelete(
    BuildContext context,
    VaultController vault,
    TotpAccount account,
  ) async {
    final AppStrings s = AppStrings.of(context);
    final AppPalette palette = AppPalette.of(context);
    final bool? confirmed = await showDialog<bool>(
      context: context,
      builder: (BuildContext context) => AlertDialog(
        title: Text(s.removeAccountTitle),
        content: Text(s.removeAccountBody(account.username)),
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
      await vault.remove(account.id);
    }
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    final AppStrings s = AppStrings.of(context);
    final AppPalette palette = AppPalette.of(context);

    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(28, 24, 28, 40),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            Container(
              width: 84,
              height: 84,
              decoration: BoxDecoration(
                color: palette.surfaceAlt,
                shape: BoxShape.circle,
                border: Border.all(color: palette.line),
              ),
              child: Icon(
                Icons.shield_outlined,
                size: 38,
                color: palette.brass,
              ),
            ),
            const SizedBox(height: 22),
            Text(
              s.emptyTitle,
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w700,
                color: palette.ink,
              ),
            ),
            const SizedBox(height: 10),
            Text(
              s.emptyBody,
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 14, height: 1.6, color: palette.inkSoft),
            ),
            const SizedBox(height: 26),
            SizedBox(
              width: 260,
              child: FilledButton.icon(
                onPressed: () => openAddAccount(context),
                icon: const Icon(Icons.add),
                label: Text(s.addAccount),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _VaultErrorState extends StatelessWidget {
  const _VaultErrorState({required this.vault});

  final VaultController vault;

  @override
  Widget build(BuildContext context) {
    final AppStrings s = AppStrings.of(context);
    final AppPalette palette = AppPalette.of(context);

    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(28, 24, 28, 40),
        child: Column(
          children: <Widget>[
            Icon(Icons.error_outline, size: 42, color: palette.danger),
            const SizedBox(height: 18),
            Text(
              s.vaultCorruptTitle,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 19,
                fontWeight: FontWeight.w700,
                color: palette.ink,
              ),
            ),
            const SizedBox(height: 10),
            Text(
              s.vaultCorruptBody,
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 14, height: 1.6, color: palette.inkSoft),
            ),
            const SizedBox(height: 22),
            FilledButton(
              onPressed: vault.load,
              child: Text(s.retry),
            ),
            const SizedBox(height: 10),
            TextButton(
              onPressed: vault.removeAll,
              style: TextButton.styleFrom(foregroundColor: palette.danger),
              child: Text(s.removeAllTitle),
            ),
          ],
        ),
      ),
    );
  }
}
