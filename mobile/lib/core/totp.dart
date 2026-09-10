/// RFC 6238 (TOTP) on top of RFC 4226 (HOTP), in pure Dart.
///
/// This mirrors what the portal's backend checks with `pyotp.TOTP(secret)`:
/// HMAC-SHA1, 6 digits, a 30-second step counted from the Unix epoch. The
/// other algorithms and digit counts exist so an `otpauth://` URI from any
/// other issuer still enrolls correctly.
library;

import 'dart:typed_data';

import 'package:crypto/crypto.dart' as crypto;

import 'base32.dart';

enum TotpAlgorithm {
  sha1('SHA1'),
  sha256('SHA256'),
  sha512('SHA512');

  const TotpAlgorithm(this.label);

  final String label;

  crypto.Hash get _hash => switch (this) {
    TotpAlgorithm.sha1 => crypto.sha1,
    TotpAlgorithm.sha256 => crypto.sha256,
    TotpAlgorithm.sha512 => crypto.sha512,
  };

  /// Parses the `algorithm=` parameter of an `otpauth://` URI.
  /// Returns null for anything unrecognized, so the caller can decide
  /// between "fall back to SHA1" and "reject this URI".
  static TotpAlgorithm? tryParse(String? value) {
    if (value == null) return null;
    final String v = value.trim().toUpperCase().replaceAll('-', '');
    return TotpAlgorithm.values
        .where((TotpAlgorithm a) => a.label == v)
        .firstOrNull;
  }
}

const int kDefaultDigits = 6;
const int kDefaultPeriod = 30;

/// The HOTP value for an explicit [counter] and raw [key] bytes.
String hotpFromKey(
  Uint8List key, {
  required int counter,
  int digits = kDefaultDigits,
  TotpAlgorithm algorithm = TotpAlgorithm.sha1,
}) {
  if (key.isEmpty) {
    throw ArgumentError.value(key, 'key', 'must not be empty');
  }
  if (digits < 6 || digits > 10) {
    throw ArgumentError.value(digits, 'digits', 'must be between 6 and 10');
  }

  // 8-byte big-endian counter, written as two 32-bit halves so this stays
  // correct on the web target too (ByteData.setUint64 is unsupported there).
  final ByteData message = ByteData(8);
  message.setUint32(0, counter ~/ 0x100000000, Endian.big);
  message.setUint32(4, counter % 0x100000000, Endian.big);

  final crypto.Digest digest = crypto.Hmac(
    algorithm._hash,
    key,
  ).convert(message.buffer.asUint8List());
  final List<int> mac = digest.bytes;

  // Dynamic truncation (RFC 4226 §5.3).
  final int offset = mac[mac.length - 1] & 0x0F;
  final int binary =
      ((mac[offset] & 0x7F) << 24) |
      ((mac[offset + 1] & 0xFF) << 16) |
      ((mac[offset + 2] & 0xFF) << 8) |
      (mac[offset + 3] & 0xFF);

  final int modulus = _pow10(digits);
  return (binary % modulus).toString().padLeft(digits, '0');
}

/// The TOTP value for [secret] (Base32) at [time].
///
/// Throws [Base32DecodeException] if the secret is not valid Base32.
String generateTotp({
  required String secret,
  DateTime? time,
  int digits = kDefaultDigits,
  int period = kDefaultPeriod,
  TotpAlgorithm algorithm = TotpAlgorithm.sha1,
  int stepOffset = 0,
}) {
  if (period <= 0) {
    throw ArgumentError.value(period, 'period', 'must be positive');
  }
  final int epochSeconds =
      (time ?? DateTime.now()).toUtc().millisecondsSinceEpoch ~/ 1000;
  return hotpFromKey(
    base32Decode(secret),
    counter: (epochSeconds ~/ period) + stepOffset,
    digits: digits,
    algorithm: algorithm,
  );
}

/// Whole seconds until the current step expires — what the countdown ring shows.
/// Always in 1..period, so the ring never renders an empty track.
int secondsRemaining({DateTime? time, int period = kDefaultPeriod}) {
  final int epochSeconds =
      (time ?? DateTime.now()).toUtc().millisecondsSinceEpoch ~/ 1000;
  return period - (epochSeconds % period);
}

/// Fraction of the current step still to run, in 0..1, at millisecond
/// resolution so the ring sweeps smoothly rather than in one-second jumps.
double fractionRemaining({DateTime? time, int period = kDefaultPeriod}) {
  final int epochMillis =
      (time ?? DateTime.now()).toUtc().millisecondsSinceEpoch;
  final int periodMillis = period * 1000;
  return 1.0 - ((epochMillis % periodMillis) / periodMillis);
}

/// Groups a code for display: "123456" -> "123 456", "12345678" -> "1234 5678".
String formatCodeForDisplay(String code) {
  if (code.length < 6) return code;
  final int half = (code.length / 2).ceil();
  return '${code.substring(0, half)} ${code.substring(half)}';
}

int _pow10(int exponent) {
  int result = 1;
  for (int i = 0; i < exponent; i++) {
    result *= 10;
  }
  return result;
}
