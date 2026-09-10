/// The only network surface this app has: the portal's own auth endpoints,
/// used to prove that whoever is enrolling an account actually owns it, and
/// that the secret they pasted is the one the server expects.
///
/// What is never sent: the TOTP secret. Enrollment is confirmed by sending
/// the six-digit code the secret produces, which is exactly what the login
/// screen would send anyway. Nothing here is persisted — the temp token lives
/// in memory for the duration of the enrollment screen and is then dropped.
library;

import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;
import 'package:http/io_client.dart';

enum PortalErrorKind {
  badUrl,
  network,
  certificate,
  hostNotAllowed,
  invalidCredentials,
  accountDisabled,
  accountLocked,
  rateLimited,
  invalidCode,
  unexpectedResponse,
  serverError,
}

class PortalApiException implements Exception {
  const PortalApiException(this.kind, {this.detail, this.retryAfterSeconds});

  final PortalErrorKind kind;

  /// Server-supplied text, shown only as a secondary line — the UI always has
  /// its own localized message for [kind].
  final String? detail;
  final int? retryAfterSeconds;

  @override
  String toString() => 'PortalApiException($kind): $detail';
}

/// Result of step 1 of enrollment (username + password accepted).
class PasswordCheckResult {
  const PasswordCheckResult({
    required this.tempToken,
    required this.requiresMfa,
  });

  /// Present when the portal asked for MFA next, which is the normal path and
  /// the only one that lets us confirm a secret. Absent if this install was
  /// somehow treated as a trusted device.
  final String? tempToken;
  final bool requiresMfa;
}

class PortalApi {
  PortalApi({
    required String baseUrl,
    this.allowSelfSignedCertificate = false,
    this.timeout = const Duration(seconds: 15),
    http.Client? client,
  }) : baseUrl = normalizeBaseUrl(baseUrl),
       _injectedClient = client;

  final String baseUrl;
  final bool allowSelfSignedCertificate;
  final Duration timeout;
  final http.Client? _injectedClient;

  /// Accepts what a human types ("portal.example", "https://host/") and
  /// returns a scheme-qualified origin with no trailing slash.
  static String normalizeBaseUrl(String raw) {
    String url = raw.trim();
    if (url.isEmpty) return '';
    if (!url.contains('://')) url = 'https://$url';
    while (url.endsWith('/')) {
      url = url.substring(0, url.length - 1);
    }
    return url;
  }

  static bool isPlausibleBaseUrl(String raw) {
    final String url = normalizeBaseUrl(raw);
    if (url.isEmpty) return false;
    final Uri? parsed = Uri.tryParse(url);
    if (parsed == null || !parsed.hasScheme || parsed.host.isEmpty) {
      return false;
    }
    return parsed.scheme == 'http' || parsed.scheme == 'https';
  }

  Uri _endpoint(String path) {
    final Uri? uri = Uri.tryParse('$baseUrl$path');
    if (baseUrl.isEmpty || uri == null || uri.host.isEmpty) {
      throw const PortalApiException(PortalErrorKind.badUrl);
    }
    return uri;
  }

  http.Client _newClient() {
    final http.Client? injected = _injectedClient;
    if (injected != null) return injected;
    if (!allowSelfSignedCertificate) return http.Client();
    // Opt-in, and narrow: only the configured host's certificate is waved
    // through, so pointing the app at a self-signed lab server can't also
    // silently accept a bad certificate from anywhere else.
    final String expectedHost = Uri.parse(baseUrl).host;
    final HttpClient inner = HttpClient()
      ..badCertificateCallback =
          (X509Certificate cert, String host, int port) => host == expectedHost;
    return IOClient(inner);
  }

  Future<T> _withClient<T>(Future<T> Function(http.Client client) body) async {
    final http.Client client = _newClient();
    try {
      return await body(client);
    } on TimeoutException {
      throw const PortalApiException(PortalErrorKind.network, detail: 'timeout');
    } on HandshakeException catch (e) {
      throw PortalApiException(PortalErrorKind.certificate, detail: e.message);
    } on SocketException catch (e) {
      throw PortalApiException(PortalErrorKind.network, detail: e.message);
    } on http.ClientException catch (e) {
      throw PortalApiException(PortalErrorKind.network, detail: e.message);
    } finally {
      if (_injectedClient == null) client.close();
    }
  }

  Future<http.Response> _postJson(
    http.Client client,
    String path,
    Map<String, dynamic> body,
  ) => client
      .post(
        _endpoint(path),
        headers: const <String, String>{
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: jsonEncode(body),
      )
      .timeout(timeout);

  /// `GET /health` — used by the "test connection" button in settings, so a
  /// wrong address or an untrusted certificate surfaces before enrollment.
  Future<void> checkHealth() => _withClient((http.Client client) async {
    final http.Response response = await client
        .get(_endpoint('/health'))
        .timeout(timeout);
    if (response.statusCode >= 500) {
      throw PortalApiException(
        PortalErrorKind.serverError,
        detail: 'HTTP ${response.statusCode}',
      );
    }
    if (response.statusCode >= 400) {
      if (_isHostRejection(response)) {
        throw PortalApiException(
          PortalErrorKind.hostNotAllowed,
          detail: _bodyText(response),
        );
      }
      throw PortalApiException(
        PortalErrorKind.unexpectedResponse,
        detail: 'HTTP ${response.statusCode}',
      );
    }
  });

  /// Step 1: prove the enrolling user owns the account.
  ///
  /// The password is used for this one request and never stored.
  Future<PasswordCheckResult> checkPassword({
    required String username,
    required String password,
  }) => _withClient((http.Client client) async {
    final http.Response response = await _postJson(
      client,
      '/api/v1/auth/login',
      <String, dynamic>{'username': username, 'password': password},
    );

    if (response.statusCode == 200) {
      final Map<String, dynamic> body = _decodeObject(response);
      return PasswordCheckResult(
        tempToken: body['temp_token'] as String?,
        requiresMfa: body['requires_mfa'] as bool? ?? false,
      );
    }
    throw _mapAuthError(
      response,
      wrongSecretKind: PortalErrorKind.invalidCredentials,
    );
  });

  /// Step 2: confirm the pasted secret really is this account's secret, by
  /// completing the portal's own MFA step with a code generated from it.
  Future<void> confirmCode({
    required String tempToken,
    required String code,
  }) => _withClient((http.Client client) async {
    final http.Response response = await _postJson(
      client,
      '/api/v1/auth/verify-totp',
      <String, dynamic>{
        'temp_token': tempToken,
        'totp_code': code,
        'remember_device': false,
      },
    );
    if (response.statusCode == 200) return;
    throw _mapAuthError(response, wrongSecretKind: PortalErrorKind.invalidCode);
  });

  static String _bodyText(http.Response response) {
    try {
      return utf8.decode(response.bodyBytes).trim();
    } on FormatException {
      return '';
    }
  }

  /// The portal reached us, but its backend refused the Host header nginx
  /// forwarded — Starlette's TrustedHostMiddleware answering 400 with
  /// "Invalid host header". A server-side setting, not anything the phone
  /// can fix, so it deserves its own message rather than "unexpected reply".
  static bool _isHostRejection(http.Response response) =>
      response.statusCode == 400 &&
      _bodyText(response).toLowerCase().contains('invalid host header');

  Map<String, dynamic> _decodeObject(http.Response response) {
    try {
      final dynamic decoded = jsonDecode(utf8.decode(response.bodyBytes));
      if (decoded is Map<String, dynamic>) return decoded;
    } on FormatException {
      // Fall through to the shared "not what we expected" error below.
    }
    throw const PortalApiException(PortalErrorKind.unexpectedResponse);
  }

  PortalApiException _mapAuthError(
    http.Response response, {
    required PortalErrorKind wrongSecretKind,
  }) {
    String? detail;
    try {
      final dynamic decoded = jsonDecode(utf8.decode(response.bodyBytes));
      if (decoded is Map && decoded['detail'] != null) {
        detail = decoded['detail'].toString();
      }
    } on FormatException {
      detail = null;
    }

    final int status = response.statusCode;
    if (status == 400 && _isHostRejection(response)) {
      return PortalApiException(
        PortalErrorKind.hostNotAllowed,
        detail: _bodyText(response),
      );
    }
    if (status == 401) return PortalApiException(wrongSecretKind, detail: detail);
    if (status == 403) {
      return PortalApiException(
        PortalErrorKind.accountDisabled,
        detail: detail,
      );
    }
    if (status == 423) {
      return PortalApiException(PortalErrorKind.accountLocked, detail: detail);
    }
    if (status == 429) {
      return PortalApiException(
        PortalErrorKind.rateLimited,
        detail: detail,
        retryAfterSeconds: int.tryParse(response.headers['retry-after'] ?? ''),
      );
    }
    if (status >= 500) {
      return PortalApiException(
        PortalErrorKind.serverError,
        detail: detail ?? 'HTTP $status',
      );
    }
    return PortalApiException(
      PortalErrorKind.unexpectedResponse,
      detail: detail ?? 'HTTP $status',
    );
  }
}
