import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/totp.dart';
import '../../l10n/app_strings.dart';
import '../../models/account.dart';
import '../../theme.dart';
import 'countdown_ring.dart';

class AccountCard extends StatelessWidget {
  const AccountCard({
    super.key,
    required this.account,
    required this.now,
    required this.onDelete,
  });

  final TotpAccount account;
  final DateTime now;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final AppStrings s = AppStrings.of(context);
    final AppPalette palette = AppPalette.of(context);

    String? code;
    try {
      code = account.codeAt(now);
    } catch (_) {
      // A stored secret that no longer decodes: show the account, not a crash,
      // so the user can delete it and re-enroll.
      code = null;
    }

    final int seconds = secondsRemaining(time: now, period: account.period);
    final double fraction = fractionRemaining(time: now, period: account.period);

    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: code == null ? null : () => _copy(context, code!),
        child: Padding(
          // Directional, so the delete button keeps its tighter gutter on the
          // trailing edge in both Arabic and English.
          padding: const EdgeInsetsDirectional.fromSTEB(18, 16, 10, 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Row(
                children: <Widget>[
                  Expanded(
                    child: Text(
                      account.username,
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: palette.ink,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  IconButton(
                    onPressed: onDelete,
                    icon: const Icon(Icons.delete_outline),
                    color: palette.inkFaint,
                    tooltip: s.remove,
                    visualDensity: VisualDensity.compact,
                  ),
                ],
              ),
              Row(
                children: <Widget>[
                  Flexible(
                    child: Text(
                      account.displayIssuer,
                      style: TextStyle(fontSize: 13, color: palette.inkSoft),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  const SizedBox(width: 8),
                  _VerificationBadge(verified: account.serverVerified),
                ],
              ),
              const SizedBox(height: 14),
              Row(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: <Widget>[
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          code == null
                              ? '—'
                              : formatCodeForDisplay(code),
                          textDirection: TextDirection.ltr,
                          style: TextStyle(
                            fontSize: 34,
                            height: 1.1,
                            fontWeight: FontWeight.w600,
                            letterSpacing: 3,
                            fontFamily: kCodeFontFallback.first,
                            fontFamilyFallback: kCodeFontFallback,
                            fontFeatures: const <FontFeature>[
                              FontFeature.tabularFigures(),
                            ],
                            color: seconds <= 5 ? palette.danger : palette.ink,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          code == null ? s.secretInvalid : s.tapToCopyHint,
                          style: TextStyle(
                            fontSize: 12,
                            color: code == null
                                ? palette.danger
                                : palette.inkFaint,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  CountdownRing(
                    fractionRemaining: fraction,
                    secondsRemaining: seconds,
                    label: s.secondsLeft(seconds),
                  ),
                  const SizedBox(width: 8),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _copy(BuildContext context, String code) async {
    final AppStrings s = AppStrings.of(context);
    final ScaffoldMessengerState messenger = ScaffoldMessenger.of(context);
    await HapticFeedback.selectionClick();
    try {
      await Clipboard.setData(ClipboardData(text: code));
      messenger
        ..hideCurrentSnackBar()
        ..showSnackBar(
          SnackBar(
            content: Text(s.copied),
            duration: const Duration(milliseconds: 1400),
          ),
        );
    } on PlatformException {
      messenger
        ..hideCurrentSnackBar()
        ..showSnackBar(SnackBar(content: Text(s.copyFailed)));
    }
  }
}

class _VerificationBadge extends StatelessWidget {
  const _VerificationBadge({required this.verified});

  final bool verified;

  @override
  Widget build(BuildContext context) {
    final AppStrings s = AppStrings.of(context);
    final AppPalette palette = AppPalette.of(context);
    final Color color = verified ? palette.success : palette.brass;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: color.withValues(alpha: 0.35)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(
            verified ? Icons.verified_outlined : Icons.help_outline,
            size: 13,
            color: color,
          ),
          const SizedBox(width: 4),
          Text(
            verified ? s.verifiedBadge : s.unverifiedBadge,
            style: TextStyle(
              fontSize: 11,
              color: color,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}
