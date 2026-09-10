/// RFC 4648 Base32 — the encoding every authenticator uses for TOTP secrets.
///
/// Decoding is deliberately lenient about what humans do to a secret on its
/// way from a terminal to a phone: lowercase, spaces, dashes and trailing
/// '=' padding are all accepted. Anything else is rejected loudly, because a
/// silently-dropped character produces codes that are wrong but plausible —
/// the single hardest TOTP failure to debug.
library;

import 'dart:typed_data';

const String _alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';

class Base32DecodeException implements Exception {
  const Base32DecodeException(this.message);

  final String message;

  @override
  String toString() => 'Base32DecodeException: $message';
}

/// Strips the cosmetic noise a pasted secret usually carries, and uppercases.
///
/// Does not validate: use [isValidBase32] or [base32Decode] for that.
String normalizeBase32(String input) =>
    input.replaceAll(RegExp(r'[\s\-_]'), '').replaceAll('=', '').toUpperCase();

bool isValidBase32(String input) {
  final String clean = normalizeBase32(input);
  if (clean.isEmpty) return false;
  return !clean.split('').any((String c) => !_alphabet.contains(c));
}

/// Decodes [input] to its raw key bytes.
///
/// Throws [Base32DecodeException] on any character outside the RFC 4648
/// alphabet, rather than skipping it.
Uint8List base32Decode(String input) {
  final String clean = normalizeBase32(input);
  if (clean.isEmpty) {
    throw const Base32DecodeException('The secret is empty.');
  }

  final List<int> bytes = <int>[];
  int buffer = 0;
  int bitsInBuffer = 0;

  for (int i = 0; i < clean.length; i++) {
    final int value = _alphabet.indexOf(clean[i]);
    if (value < 0) {
      throw Base32DecodeException(
        'Not a Base32 character: "${clean[i]}" at position ${i + 1}.',
      );
    }
    buffer = (buffer << 5) | value;
    bitsInBuffer += 5;
    if (bitsInBuffer >= 8) {
      bitsInBuffer -= 8;
      bytes.add((buffer >> bitsInBuffer) & 0xFF);
    }
  }

  if (bytes.isEmpty) {
    throw const Base32DecodeException(
      'The secret is too short to contain a single byte.',
    );
  }
  return Uint8List.fromList(bytes);
}

String base32Encode(List<int> bytes) {
  final StringBuffer out = StringBuffer();
  int buffer = 0;
  int bitsInBuffer = 0;
  for (final int byte in bytes) {
    buffer = (buffer << 8) | (byte & 0xFF);
    bitsInBuffer += 8;
    while (bitsInBuffer >= 5) {
      bitsInBuffer -= 5;
      out.write(_alphabet[(buffer >> bitsInBuffer) & 0x1F]);
    }
  }
  if (bitsInBuffer > 0) {
    out.write(_alphabet[(buffer << (5 - bitsInBuffer)) & 0x1F]);
  }
  return out.toString();
}
