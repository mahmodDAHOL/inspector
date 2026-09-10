/// In-memory view of the enrolled accounts, backed by the keystore.
library;

import 'package:flutter/foundation.dart';

import '../core/secret_vault_store.dart';
import '../models/account.dart';

class VaultController extends ChangeNotifier {
  VaultController({SecretVaultStore? store})
    : _store = store ?? SecretVaultStore();

  final SecretVaultStore _store;

  List<TotpAccount> _accounts = <TotpAccount>[];
  bool _loading = true;
  String? _error;

  List<TotpAccount> get accounts => List<TotpAccount>.unmodifiable(_accounts);
  bool get isLoading => _loading;
  bool get isEmpty => !_loading && _accounts.isEmpty;

  /// Set when the stored vault could not be read. The accounts are *not*
  /// cleared in that case — the user decides whether to wipe.
  String? get error => _error;

  Future<void> load() async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      _accounts = await _store.loadAccounts();
    } on VaultReadException catch (e) {
      _error = e.message;
      _accounts = <TotpAccount>[];
    } catch (e) {
      _error = e.toString();
      _accounts = <TotpAccount>[];
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  bool hasAccountNamed(String username) => _accounts.any(
    (TotpAccount a) =>
        a.username.toLowerCase().trim() == username.toLowerCase().trim(),
  );

  Future<void> add(TotpAccount account) async {
    _accounts = <TotpAccount>[..._accounts, account];
    notifyListeners();
    await _store.saveAccounts(_accounts);
  }

  Future<void> remove(String id) async {
    _accounts = _accounts
        .where((TotpAccount a) => a.id != id)
        .toList(growable: false);
    notifyListeners();
    await _store.saveAccounts(_accounts);
  }

  Future<void> removeAll() async {
    _accounts = <TotpAccount>[];
    _error = null;
    notifyListeners();
    await _store.wipe();
  }
}
