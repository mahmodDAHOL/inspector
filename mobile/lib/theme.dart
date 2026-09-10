/// The portal's own palette, carried over from the web authenticator so the
/// phone app and the browser page read as one product: teal and brass on a
/// warm paper ground, with a dark mode that keeps the same relationships.
library;

import 'package:flutter/material.dart';

@immutable
class AppPalette extends ThemeExtension<AppPalette> {
  const AppPalette({
    required this.ground,
    required this.surface,
    required this.surfaceAlt,
    required this.ink,
    required this.inkSoft,
    required this.inkFaint,
    required this.line,
    required this.teal,
    required this.tealDeep,
    required this.brass,
    required this.brassBright,
    required this.danger,
    required this.success,
    required this.ringTrack,
  });

  static const AppPalette light = AppPalette(
    ground: Color(0xFFF6F3EC),
    surface: Color(0xFFFFFFFF),
    surfaceAlt: Color(0xFFEFEAE0),
    ink: Color(0xFF12201F),
    inkSoft: Color(0xFF4B5B58),
    inkFaint: Color(0xFF8A9794),
    line: Color(0xFFDCD5C6),
    teal: Color(0xFF1B5E5E),
    tealDeep: Color(0xFF0E3636),
    brass: Color(0xFFA68B5B),
    brassBright: Color(0xFFB8944F),
    danger: Color(0xFFB85450),
    success: Color(0xFF4C8B5A),
    ringTrack: Color(0xFFE4DDCC),
  );

  static const AppPalette dark = AppPalette(
    ground: Color(0xFF0A1614),
    surface: Color(0xFF12211F),
    surfaceAlt: Color(0xFF182B28),
    ink: Color(0xFFEFEAE0),
    inkSoft: Color(0xFFA9B8B4),
    inkFaint: Color(0xFF6C7B77),
    line: Color(0xFF223634),
    teal: Color(0xFF4A9490),
    tealDeep: Color(0xFF2E6E6A),
    brass: Color(0xFFC9A96B),
    brassBright: Color(0xFFD9B770),
    danger: Color(0xFFD97C77),
    success: Color(0xFF7FBE8C),
    ringTrack: Color(0xFF1C2E2B),
  );

  final Color ground;
  final Color surface;
  final Color surfaceAlt;
  final Color ink;
  final Color inkSoft;
  final Color inkFaint;
  final Color line;
  final Color teal;
  final Color tealDeep;
  final Color brass;
  final Color brassBright;
  final Color danger;
  final Color success;
  final Color ringTrack;

  static AppPalette of(BuildContext context) =>
      Theme.of(context).extension<AppPalette>() ?? AppPalette.light;

  @override
  AppPalette copyWith({
    Color? ground,
    Color? surface,
    Color? surfaceAlt,
    Color? ink,
    Color? inkSoft,
    Color? inkFaint,
    Color? line,
    Color? teal,
    Color? tealDeep,
    Color? brass,
    Color? brassBright,
    Color? danger,
    Color? success,
    Color? ringTrack,
  }) => AppPalette(
    ground: ground ?? this.ground,
    surface: surface ?? this.surface,
    surfaceAlt: surfaceAlt ?? this.surfaceAlt,
    ink: ink ?? this.ink,
    inkSoft: inkSoft ?? this.inkSoft,
    inkFaint: inkFaint ?? this.inkFaint,
    line: line ?? this.line,
    teal: teal ?? this.teal,
    tealDeep: tealDeep ?? this.tealDeep,
    brass: brass ?? this.brass,
    brassBright: brassBright ?? this.brassBright,
    danger: danger ?? this.danger,
    success: success ?? this.success,
    ringTrack: ringTrack ?? this.ringTrack,
  );

  @override
  AppPalette lerp(ThemeExtension<AppPalette>? other, double t) {
    if (other is! AppPalette) return this;
    return AppPalette(
      ground: Color.lerp(ground, other.ground, t)!,
      surface: Color.lerp(surface, other.surface, t)!,
      surfaceAlt: Color.lerp(surfaceAlt, other.surfaceAlt, t)!,
      ink: Color.lerp(ink, other.ink, t)!,
      inkSoft: Color.lerp(inkSoft, other.inkSoft, t)!,
      inkFaint: Color.lerp(inkFaint, other.inkFaint, t)!,
      line: Color.lerp(line, other.line, t)!,
      teal: Color.lerp(teal, other.teal, t)!,
      tealDeep: Color.lerp(tealDeep, other.tealDeep, t)!,
      brass: Color.lerp(brass, other.brass, t)!,
      brassBright: Color.lerp(brassBright, other.brassBright, t)!,
      danger: Color.lerp(danger, other.danger, t)!,
      success: Color.lerp(success, other.success, t)!,
      ringTrack: Color.lerp(ringTrack, other.ringTrack, t)!,
    );
  }
}

/// The digits themselves: a monospaced stack, so a code never reflows as the
/// numbers change and the eye can compare digit positions.
const List<String> kCodeFontFallback = <String>[
  'IBM Plex Mono',
  'Roboto Mono',
  'DejaVu Sans Mono',
  'Courier New',
  'monospace',
];

ThemeData buildAppTheme(AppPalette palette, Brightness brightness) {
  final ColorScheme scheme =
      ColorScheme.fromSeed(
        seedColor: palette.teal,
        brightness: brightness,
      ).copyWith(
        primary: palette.teal,
        onPrimary: brightness == Brightness.light
            ? const Color(0xFFF6F3EC)
            : const Color(0xFF06100F),
        secondary: palette.brass,
        surface: palette.surface,
        onSurface: palette.ink,
        error: palette.danger,
      );

  final TextTheme base = brightness == Brightness.light
      ? Typography.material2021().black
      : Typography.material2021().white;

  return ThemeData(
    useMaterial3: true,
    brightness: brightness,
    colorScheme: scheme,
    scaffoldBackgroundColor: palette.ground,
    canvasColor: palette.ground,
    dividerColor: palette.line,
    extensions: <ThemeExtension<dynamic>>[palette],
    textTheme: base.apply(bodyColor: palette.ink, displayColor: palette.ink),
    appBarTheme: AppBarTheme(
      backgroundColor: palette.ground,
      foregroundColor: palette.ink,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: false,
    ),
    cardTheme: CardThemeData(
      color: palette.surface,
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(18),
        side: BorderSide(color: palette.line),
      ),
    ),
    listTileTheme: ListTileThemeData(
      textColor: palette.ink,
      iconColor: palette.inkSoft,
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: palette.surface,
      hintStyle: TextStyle(color: palette.inkFaint),
      labelStyle: TextStyle(color: palette.inkSoft),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: BorderSide(color: palette.line),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: BorderSide(color: palette.line),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: BorderSide(color: palette.teal, width: 2),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: BorderSide(color: palette.danger),
      ),
      focusedErrorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: BorderSide(color: palette.danger, width: 2),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: palette.teal,
        foregroundColor: scheme.onPrimary,
        minimumSize: const Size.fromHeight(52),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
        ),
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: palette.teal,
        minimumSize: const Size.fromHeight(48),
        side: BorderSide(color: palette.line),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
        ),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(foregroundColor: palette.teal),
    ),
    snackBarTheme: SnackBarThemeData(
      backgroundColor: palette.tealDeep,
      contentTextStyle: const TextStyle(color: Color(0xFFF6F3EC)),
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: palette.surface,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
    ),
    switchTheme: SwitchThemeData(
      thumbColor: WidgetStateProperty.resolveWith<Color?>(
        (Set<WidgetState> states) =>
            states.contains(WidgetState.selected) ? palette.teal : null,
      ),
      trackColor: WidgetStateProperty.resolveWith<Color?>(
        (Set<WidgetState> states) => states.contains(WidgetState.selected)
            ? palette.teal.withValues(alpha: 0.35)
            : null,
      ),
    ),
  );
}
