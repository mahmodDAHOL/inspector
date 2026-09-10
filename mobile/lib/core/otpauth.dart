/// Parsing of the `otpauth://totp/...` provisioning URI.
///
/// `scripts/reset_totp.py` prints exactly such a URI next to the raw Base32
/// secret, so a user enrolling on this app may paste either form. Both land
/// in the same [OtpAuthData].
library;

import 'base32.dart';
import 'totp.dart';

class OtpAuthParseException implements Exception {
  const OtpAuthParseException(this.message);

  final String message;

  @override
  String toString() => 'OtpAuthParseException: $message';
}

class OtpAuthData {
  const OtpAuthData({
    required this.secret,
    this.accountName,
    this.issuer,
    this.digits = kDefaultDigits,
    this.period = kDefaultPeriod,
    this.algorithm = TotpAlgorithm.sha1,
  });

  final String secret;
  final String? accountName;
  final String? issuer;
  final int digits;
  final int period;
  final TotpAlgorithm algorithm;
}

bool looksLikeOtpAuthUri(String input) =>
    input.trim().toLowerCase().startsWith('otpauth://');

/// Parses a provisioning URI. Throws [OtpAuthParseException] when the URI is
/// malformed, is for a counter-based (HOTP) credential this app cannot show,
/// or carries no usable secret.
OtpAuthData parseOtpAuthUri(String input) {
  final Uri uri;
  try {
    uri = Uri.parse(input.trim());
  } on FormatException {
    throw const OtpAuthParseException('This is not a valid otpauth:// link.');
  }

  if (uri.scheme.toLowerCase() != 'otpauth') {
    throw const OtpAuthParseException('The link must start with otpauth://.');
  }
  final String type = uri.host.toLowerCase();
  if (type == 'hotp') {
    throw const OtpAuthParseException(
      'This is a counter-based (HOTP) link. The portal issues time-based codes only.',
    );
  }
  if (type != 'totp') {
    throw OtpAuthParseException('Unsupported link type: ${uri.host}.');
  }

  final String? rawSecret = uri.queryParameters['secret'];
  if (rawSecret == null || rawSecret.trim().isEmpty) {
    throw const OtpAuthParseException('The link carries no secret= value.');
  }
  final String secret = normalizeBase32(rawSecret);
  if (!isValidBase32(secret)) {
    throw const OtpAuthParseException(
      'The secret in the link is not valid Base32.',
    );
  }

  // The label is "Issuer:account" or just "account", after the leading slash.
  String label = uri.path;
  if (label.startsWith('/')) label = label.substring(1);
  label = Uri.decodeComponent(label).trim();

  String? labelIssuer;
  String? accountName;
  if (label.isNotEmpty) {
    final int separator = label.indexOf(':');
    if (separator > 0) {
      labelIssuer = label.substring(0, separator).trim();
      accountName = label.substring(separator + 1).trim();
    } else {
      accountName = label;
    }
  }

  final String? queryIssuer = uri.queryParameters['issuer']?.trim();

  return OtpAuthData(
    secret: secret,
    // A query-string issuer wins over the label prefix (RFC-recommended).
    issuer: (queryIssuer != null && queryIssuer.isNotEmpty)
        ? queryIssuer
        : (labelIssuer != null && labelIssuer.isNotEmpty ? labelIssuer : null),
    accountName: (accountName != null && accountName.isNotEmpty)
        ? accountName
        : null,
    digits: _positiveIntOr(uri.queryParameters['digits'], kDefaultDigits, 6, 10),
    period: _positiveIntOr(uri.queryParameters['period'], kDefaultPeriod, 1, 300),
    algorithm:
        TotpAlgorithm.tryParse(uri.queryParameters['algorithm']) ??
        TotpAlgorithm.sha1,
  );
}

int _positiveIntOr(String? raw, int fallback, int min, int max) {
  final int? parsed = int.tryParse(raw?.trim() ?? '');
  if (parsed == null || parsed < min || parsed > max) return fallback;
  return parsed;
}
