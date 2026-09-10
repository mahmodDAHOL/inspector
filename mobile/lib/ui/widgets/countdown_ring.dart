/// The ring that drains as the current 30-second step runs out — the same
/// affordance the web authenticator uses, so the two look like siblings.
library;

import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../theme.dart';

class CountdownRing extends StatelessWidget {
  const CountdownRing({
    super.key,
    required this.fractionRemaining,
    required this.secondsRemaining,
    required this.label,
    this.size = 52,
    this.strokeWidth = 4,
    this.warnAtSeconds = 5,
  });

  /// 1.0 at the start of the step, 0.0 as it expires.
  final double fractionRemaining;
  final int secondsRemaining;

  /// Localized text for screen readers, e.g. "8 s".
  final String label;
  final double size;
  final double strokeWidth;
  final int warnAtSeconds;

  @override
  Widget build(BuildContext context) {
    final AppPalette palette = AppPalette.of(context);
    final bool warning = secondsRemaining <= warnAtSeconds;
    final Color color = warning ? palette.danger : palette.teal;

    return Semantics(
      label: label,
      excludeSemantics: true,
      child: SizedBox(
        width: size,
        height: size,
        child: CustomPaint(
          painter: _RingPainter(
            fraction: fractionRemaining.clamp(0.0, 1.0),
            color: color,
            trackColor: palette.ringTrack,
            strokeWidth: strokeWidth,
          ),
          child: Center(
            child: Text(
              '$secondsRemaining',
              style: TextStyle(
                fontSize: size * 0.34,
                fontWeight: FontWeight.w600,
                fontFeatures: const <FontFeature>[FontFeature.tabularFigures()],
                color: color,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _RingPainter extends CustomPainter {
  const _RingPainter({
    required this.fraction,
    required this.color,
    required this.trackColor,
    required this.strokeWidth,
  });

  final double fraction;
  final Color color;
  final Color trackColor;
  final double strokeWidth;

  @override
  void paint(Canvas canvas, Size size) {
    final Offset center = size.center(Offset.zero);
    final double radius = (math.min(size.width, size.height) - strokeWidth) / 2;

    final Paint track = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..color = trackColor;
    canvas.drawCircle(center, radius, track);

    if (fraction <= 0) return;

    final Paint arc = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round
      ..color = color;
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      -math.pi / 2,
      -2 * math.pi * fraction,
      false,
      arc,
    );
  }

  @override
  bool shouldRepaint(_RingPainter old) =>
      old.fraction != fraction ||
      old.color != color ||
      old.trackColor != trackColor ||
      old.strokeWidth != strokeWidth;
}
