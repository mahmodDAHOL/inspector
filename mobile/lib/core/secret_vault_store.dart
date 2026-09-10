/// Persistence for the one thing in this app that actually matters: the TOTP
/// secrets. They live in the platform keystore (Android Keystore-backed
/// storage, iOS Keychain) as a single JSON document, never in plain
/// preferences, never in a file we manage ourselves.
library;

import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../models/account.dart';

class VaultReadException implements Exception {
  const VaultReadException(this.message);

  final String message;

  @override
  String toString() => 'VaultReadException: $message';
}

class SecretVaultStore {
  SecretVaultStore({FlutterSecureStorage? storage})
    : _storage =
          storage ??
          const FlutterSecureStorage(
            // resetOnError defaults to true, which quietly wipes the store
            // when a value fails to decrypt. For an authenticator that means
            // silently losing every enrolled account, so we'd rather fail
            // loudly and let the user re-enroll deliberately.
            aOptions: AndroidOptions(resetOnError: false),
            // Readable after the first unlock following a reboot (so codes
            // work without babysitting), and never synced to iCloud —
            // a TOTP secret should not travel to another device.
            iOptions: IOSOptions(
              accessibility: KeychainAccessibility.first_unlock_this_device,
              synchronizable: false,
            ),
          );

  static const String _accountsKey = 'inspection_authenticator.accounts.v1';

  final FlutterSecureStorage _storage;

  /// Reads every enrolled account, oldest first.
  ///
  /// Throws [VaultReadException] if the stored document exists but cannot be
  /// parsed — better than reporting "no accounts" for a vault that has them.
  Future<List<TotpAccount>> loadAccounts() async {
    final String? raw = await _storage.read(key: _accountsKey);
    if (raw == null || raw.trim().isEmpty) return <TotpAccount>[];

    try {
      final dynamic decoded = jsonDecode(raw);
      if (decoded is! List) {
        throw const VaultReadException('Stored accounts are not a list.');
      }
      final List<TotpAccount> accounts = decoded
          .whereType<Map<String, dynamic>>()
          .map(TotpAccount.fromJson)
          .toList(growable: false);
      return accounts;
    } on FormatException catch (e) {
      throw VaultReadException('Stored accounts are corrupt: ${e.message}');
    } on TypeError catch (_) {
      throw const VaultReadException(
        'Stored accounts are missing required fields.',
      );
    }
  }

  Future<void> saveAccounts(List<TotpAccount> accounts) async {
    if (accounts.isEmpty) {
      await _storage.delete(key: _accountsKey);
      return;
    }
    await _storage.write(
      key: _accountsKey,
      value: jsonEncode(
        accounts.map((TotpAccount a) => a.toJson()).toList(growable: false),
      ),
    );
  }

  Future<void> wipe() => _storage.delete(key: _accountsKey);
}
