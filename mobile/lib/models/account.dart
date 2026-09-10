/// One enrolled portal account: a username plus the TOTP secret that belongs
/// to it. The secret only ever lives inside the platform keystore (see
/// [SecretVaultStore]) and is never sent anywhere — enrollment verifies it by
/// sending the six-digit code it produces, never the secret itself.
library;

import '../core/totp.dart';

class TotpAccount {
  const TotpAccount({
    required this.id,
    required this.username,
    required this.secret,
    this.issuer,
    this.digits = kDefaultDigits,
    this.period = kDefaultPeriod,
    this.algorithm = TotpAlgorithm.sha1,
    this.serverVerified = false,
    this.serverUrl,
    required this.addedAt,
  });

  final String id;
  final String username;
  final String secret;
  final String? issuer;
  final int digits;
  final int period;
  final TotpAlgorithm algorithm;

  /// True when the portal itself accepted a code from this secret during
  /// enrollment — i.e. this account is known to work, not just plausible.
  final bool serverVerified;

  /// The portal this account was enrolled against, kept for display only.
  final String? serverUrl;

  final DateTime addedAt;

  String get displayIssuer =>
      (issuer != null && issuer!.trim().isNotEmpty) ? issuer!.trim() : '—';

  String codeAt(DateTime time) => generateTotp(
    secret: secret,
    time: time,
    digits: digits,
    period: period,
    algorithm: algorithm,
  );

  TotpAccount copyWith({
    String? username,
    String? secret,
    String? issuer,
    int? digits,
    int? period,
    TotpAlgorithm? algorithm,
    bool? serverVerified,
    String? serverUrl,
  }) => TotpAccount(
    id: id,
    username: username ?? this.username,
    secret: secret ?? this.secret,
    issuer: issuer ?? this.issuer,
    digits: digits ?? this.digits,
    period: period ?? this.period,
    algorithm: algorithm ?? this.algorithm,
    serverVerified: serverVerified ?? this.serverVerified,
    serverUrl: serverUrl ?? this.serverUrl,
    addedAt: addedAt,
  );

  Map<String, dynamic> toJson() => <String, dynamic>{
    'id': id,
    'username': username,
    'secret': secret,
    'issuer': issuer,
    'digits': digits,
    'period': period,
    'algorithm': algorithm.label,
    'server_verified': serverVerified,
    'server_url': serverUrl,
    'added_at': addedAt.toUtc().toIso8601String(),
  };

  static TotpAccount fromJson(Map<String, dynamic> json) => TotpAccount(
    id: json['id'] as String,
    username: json['username'] as String,
    secret: json['secret'] as String,
    issuer: json['issuer'] as String?,
    digits: (json['digits'] as num?)?.toInt() ?? kDefaultDigits,
    period: (json['period'] as num?)?.toInt() ?? kDefaultPeriod,
    algorithm:
        TotpAlgorithm.tryParse(json['algorithm'] as String?) ??
        TotpAlgorithm.sha1,
    serverVerified: json['server_verified'] as bool? ?? false,
    serverUrl: json['server_url'] as String?,
    addedAt:
        DateTime.tryParse(json['added_at'] as String? ?? '')?.toLocal() ??
        DateTime.now(),
  );
}
