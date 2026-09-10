/// Every user-visible string, in Arabic and English.
///
/// The portal itself keeps ar.json/en.json with no hardcoded text left in the
/// UI; this app holds to the same rule. A plain Dart table (rather than ARB +
/// codegen) keeps it one file with no build step, and the compiler still
/// catches a missing string.
library;

import 'package:flutter/widgets.dart';

import '../core/portal_api.dart';

enum AppLanguage {
  arabic('ar', 'العربية'),
  english('en', 'English');

  const AppLanguage(this.code, this.nativeName);

  final String code;
  final String nativeName;

  Locale get locale => Locale(code);

  static AppLanguage fromCode(String? code) => AppLanguage.values
      .where((AppLanguage l) => l.code == code)
      .firstOrNull ??
      AppLanguage.arabic;
}

class AppStrings {
  const AppStrings(this.language);

  final AppLanguage language;

  static AppStrings of(BuildContext context) {
    final Locale locale = Localizations.localeOf(context);
    return AppStrings(AppLanguage.fromCode(locale.languageCode));
  }

  String _t(String ar, String en) =>
      language == AppLanguage.arabic ? ar : en;

  // ---- shell ----
  String get appTitle => _t('مُصادق الرقابة', 'Inspection Authenticator');
  String get appSubtitle => _t(
    'رموز تحقق بوابة الرقابة والتفتيش',
    'Verification codes for the Inspection Portal',
  );
  String get cancel => _t('إلغاء', 'Cancel');
  String get close => _t('إغلاق', 'Close');
  String get retry => _t('إعادة المحاولة', 'Try again');
  String get next => _t('متابعة', 'Continue');
  String get save => _t('حفظ', 'Save');
  String get remove => _t('حذف', 'Delete');
  String get done => _t('تم', 'Done');

  // ---- accounts screen ----
  String get accountsTitle => _t('حساباتي', 'My accounts');
  String get emptyTitle => _t('لا حسابات بعد', 'No accounts yet');
  String get emptyBody => _t(
    'أضف حسابك في البوابة لتبدأ برؤية رمز التحقق الخاص بك هنا، ولو كنت دون اتصال.',
    'Add your portal account to start seeing your verification code here, even offline.',
  );
  String get addAccount => _t('إضافة حساب', 'Add account');
  String get settingsTitle => _t('الإعدادات', 'Settings');
  String get copyCode => _t('نسخ', 'Copy');
  String get copied => _t('تم نسخ الرمز', 'Code copied');
  String get copyFailed => _t('تعذر النسخ — انسخه يدويًا', 'Could not copy — copy it by hand');
  String get tapToCopyHint => _t('اضغط على الرمز لنسخه', 'Tap the code to copy it');
  String get verifiedBadge => _t('مُتحقق من الخادم', 'Confirmed by the portal');
  String get unverifiedBadge => _t('غير مُتحقق', 'Not confirmed');
  String secondsLeft(int seconds) => _t('$seconds ث', '${seconds}s');
  String get removeAccountTitle => _t('حذف هذا الحساب؟', 'Delete this account?');
  String removeAccountBody(String username) => _t(
    'سيُحذف سرّ الحساب "$username" من هذا الجهاز نهائيًا، ولن تستطيع توليد رموزه بعدها. تحتاج إلى إعادة الربط بسرّ جديد من مسؤول النظام.',
    'The secret for "$username" will be permanently erased from this device and you will no longer be able to generate its codes. Re-enrolling needs a fresh secret from an administrator.',
  );
  String get vaultCorruptTitle => _t('تعذر قراءة الحسابات', 'Could not read your accounts');
  String get vaultCorruptBody => _t(
    'البيانات المخزّنة على هذا الجهاز غير قابلة للقراءة. لم يُحذف شيء تلقائيًا — يمكنك المحاولة مرة أخرى، أو حذف كل شيء وإعادة الربط.',
    'The data stored on this device could not be read. Nothing was deleted automatically — you can retry, or erase everything and re-enroll.',
  );

  // ---- add account ----
  String get addAccountTitle => _t('ربط حساب', 'Enroll an account');
  String get stepIdentity => _t('١ — أثبت ملكية الحساب', '1 — Prove the account is yours');
  String get stepIdentityBody => _t(
    'أدخل اسم المستخدم وكلمة المرور كما في البوابة. تُستخدم كلمة المرور لهذا التحقق فقط ولا تُحفظ على الجهاز.',
    'Enter your portal username and password. The password is used for this one check and is never stored on the device.',
  );
  String get stepSecret => _t('٢ — أدخل السرّ', '2 — Enter the secret');
  String get stepSecretBody => _t(
    'الصق السرّ (Base32) أو رابط otpauth:// الذي أعطاك إياه مسؤول النظام. لا يُرسل السرّ إلى أي خادم أبدًا.',
    'Paste the Base32 secret or the otpauth:// link your administrator gave you. The secret itself is never sent to any server.',
  );
  String get usernameLabel => _t('اسم المستخدم', 'Username');
  String get passwordLabel => _t('كلمة المرور', 'Password');
  String get usernameRequired => _t('اسم المستخدم مطلوب', 'Username is required');
  String get passwordRequired => _t('كلمة المرور مطلوبة', 'Password is required');
  String get secretLabel => _t('السرّ أو رابط otpauth', 'Secret or otpauth link');
  String get secretHint => 'JBSWY3DPEHPK3PXP';
  String get pasteFromClipboard => _t('لصق من الحافظة', 'Paste from clipboard');
  String get clipboardEmpty => _t('الحافظة فارغة', 'The clipboard is empty');
  String get checkingCredentials => _t('يتحقق...', 'Checking…');
  String get confirmingSecret => _t('يؤكد السرّ...', 'Confirming the secret…');
  String get secretTooShort => _t(
    'السرّ قصير جدًا — تأكد من نسخه كاملًا.',
    'The secret is too short — make sure you copied all of it.',
  );
  String get secretInvalid => _t(
    'السرّ ليس بترميز Base32 صحيح.',
    'The secret is not valid Base32.',
  );
  String accountExists(String username) => _t(
    'الحساب "$username" مربوط على هذا الجهاز بالفعل.',
    'The account "$username" is already enrolled on this device.',
  );
  String get enrollOffline => _t('الربط دون تحقق من الخادم', 'Enroll without contacting the portal');
  String get enrollOfflineTitle => _t('ربط دون تحقق؟', 'Enroll without confirmation?');
  String get enrollOfflineBody => _t(
    'لن يتأكد التطبيق من صحة السرّ، وقد تحصل على رموز مرفوضة عند الدخول. استخدم هذا الخيار فقط إن كان الخادم غير متاح الآن.',
    'The app will not be able to tell whether the secret is correct, so the codes it shows may be rejected at login. Use this only when the portal is unreachable.',
  );
  String get enrollOfflineConfirm => _t('اربط بلا تحقق', 'Enroll anyway');
  String get enrolledTitle => _t('تم ربط الحساب', 'Account enrolled');
  String enrolledVerifiedBody(String username) => _t(
    'قبلت البوابة رمزًا من هذا السرّ، فحساب "$username" جاهز للاستخدام.',
    'The portal accepted a code from this secret, so "$username" is ready to use.',
  );
  String enrolledUnverifiedBody(String username) => _t(
    'حُفظ حساب "$username" على هذا الجهاز دون تحقق من الخادم.',
    '"$username" was saved on this device without portal confirmation.',
  );
  String get serverUrlMissing => _t(
    'أضف عنوان البوابة في الإعدادات أولًا.',
    'Set the portal address in Settings first.',
  );
  String get mfaNotRequired => _t(
    'لم تطلب البوابة رمز تحقق لهذا الحساب، فلا يمكن تأكيد السرّ الآن. يمكنك الربط دون تحقق.',
    'The portal did not ask for a verification code for this account, so the secret cannot be confirmed right now. You can still enroll without confirmation.',
  );
  String get openSettings => _t('فتح الإعدادات', 'Open settings');

  // ---- settings ----
  String get serverSection => _t('البوابة', 'Portal');
  String get serverUrlLabel => _t('عنوان البوابة', 'Portal address');
  String get serverUrlHint => 'https://inspector.momc.sy';
  String get serverUrlHelp => _t(
    'العنوان نفسه الذي تفتح به البوابة في المتصفح.',
    'The same address you use to open the portal in a browser.',
  );
  String get serverUrlInvalid => _t(
    'عنوان غير صالح — يجب أن يبدأ بـ https:// أو http://',
    'Not a valid address — it must start with https:// or http://',
  );
  String get testConnection => _t('اختبار الاتصال', 'Test connection');
  String get testingConnection => _t('يختبر...', 'Testing…');
  String get connectionOk => _t('الاتصال بالبوابة يعمل', 'The portal is reachable');
  String get allowSelfSignedTitle => _t(
    'قبول شهادة موقّعة ذاتيًا',
    'Accept a self-signed certificate',
  );
  String get allowSelfSignedBody => _t(
    'للتجربة فقط: يقبل شهادة TLS غير موثوقة من مضيف البوابة المُحدد وحده. في التشغيل الفعلي استخدم شهادة صادرة عن جهة موثوقة.',
    'For testing only: accepts an untrusted TLS certificate from the configured portal host alone. In production, use a certificate from a trusted authority.',
  );
  String get appearanceSection => _t('المظهر', 'Appearance');
  String get languageLabel => _t('اللغة', 'Language');
  String get themeLabel => _t('السمة', 'Theme');
  String get themeSystem => _t('حسب النظام', 'System');
  String get themeLight => _t('فاتحة', 'Light');
  String get themeDark => _t('داكنة', 'Dark');
  String get securitySection => _t('الأمان', 'Security');
  String get appLockTitle => _t('قفل التطبيق', 'App lock');
  String get appLockBody => _t(
    'اطلب البصمة أو رمز الجهاز قبل عرض الرموز.',
    'Require your fingerprint or device credential before codes are shown.',
  );
  String get appLockUnavailable => _t(
    'لا يوجد قفل شاشة أو بصمة مُهيّأة على هذا الجهاز.',
    'This device has no screen lock or biometrics set up.',
  );
  String get dangerSection => _t('منطقة الحذف', 'Danger zone');
  String get removeAllTitle => _t('حذف كل الحسابات', 'Delete all accounts');
  String get removeAllBody => _t(
    'يمسح كل الأسرار من هذا الجهاز نهائيًا.',
    'Permanently erases every secret from this device.',
  );
  String get aboutSection => _t('عن التطبيق', 'About');
  String get aboutBody => _t(
    'يولّد هذا التطبيق رموز TOTP وفق RFC 6238 محليًا على جهازك. تبقى الأسرار في مخزن المفاتيح المُؤمّن للنظام، ولا تُرسل عبر الشبكة، ويعمل توليد الرموز دون اتصال بالكامل.',
    'This app generates RFC 6238 TOTP codes locally on your device. Secrets stay in the platform keystore, are never sent over the network, and code generation works entirely offline.',
  );
  String accountCount(int count) {
    if (language == AppLanguage.arabic) {
      if (count == 0) return 'لا حسابات';
      if (count == 1) return 'حساب واحد';
      if (count == 2) return 'حسابان';
      if (count <= 10) return '$count حسابات';
      return '$count حسابًا';
    }
    return count == 1 ? '1 account' : '$count accounts';
  }

  // ---- lock screen ----
  String get lockedTitle => _t('التطبيق مقفل', 'Locked');
  String get lockedBody => _t(
    'أثبت هويتك لعرض رموز التحقق.',
    'Authenticate to see your verification codes.',
  );
  String get unlock => _t('فتح القفل', 'Unlock');
  String get unlockReason => _t(
    'أثبت هويتك لعرض رموز التحقق',
    'Authenticate to see your verification codes',
  );
  String get unlockFailed => _t('لم يتم التحقق', 'Not authenticated');
  String get unlockLockedOut => _t(
    'تم تعطيل البصمة مؤقتًا بعد محاولات فاشلة — استخدم رمز الجهاز.',
    'Biometrics are temporarily locked after failed attempts — use your device credential.',
  );

  // ---- network / API errors ----
  String portalError(PortalApiException error) {
    switch (error.kind) {
      case PortalErrorKind.badUrl:
        return serverUrlMissing;
      case PortalErrorKind.network:
        return _t(
          'تعذر الاتصال بالبوابة. تحقق من الشبكة ومن عنوان البوابة.',
          'Could not reach the portal. Check your network and the portal address.',
        );
      case PortalErrorKind.certificate:
        return _t(
          'شهادة البوابة غير موثوقة. إن كان الخادم يستخدم شهادة موقّعة ذاتيًا، فمكّن ذلك في الإعدادات.',
          'The portal certificate is not trusted. If the server uses a self-signed certificate, enable that in Settings.',
        );
      case PortalErrorKind.hostNotAllowed:
        return _t(
          'ترفض البوابة الطلبات القادمة باسم هذا المضيف. على مسؤول الخادم إضافة اسم المضيف إلى ALLOWED_HOSTS في إعدادات الخادم ثم إعادة تشغيل الخدمة.',
          'The portal rejects requests arriving under this host name. A server administrator needs to add it to ALLOWED_HOSTS in the server settings and restart the service.',
        );
      case PortalErrorKind.invalidCredentials:
        return _t(
          'اسم المستخدم أو كلمة المرور غير صحيحة.',
          'Wrong username or password.',
        );
      case PortalErrorKind.accountDisabled:
        return _t('الحساب معطَّل.', 'This account is disabled.');
      case PortalErrorKind.accountLocked:
        return _t(
          'الحساب مقفل مؤقتًا بسبب محاولات فاشلة متكررة — حاول لاحقًا.',
          'The account is temporarily locked after repeated failed attempts — try again later.',
        );
      case PortalErrorKind.rateLimited:
        final int? seconds = error.retryAfterSeconds;
        if (seconds != null) {
          return _t(
            'محاولات كثيرة — أعد المحاولة بعد $seconds ثانية.',
            'Too many attempts — try again in $seconds seconds.',
          );
        }
        return _t(
          'محاولات كثيرة من هذا الجهاز — انتظر قليلًا ثم أعد المحاولة.',
          'Too many attempts from this device — wait a moment and try again.',
        );
      case PortalErrorKind.invalidCode:
        return _t(
          'رفضت البوابة الرمز الناتج عن هذا السرّ. تأكد من السرّ، ومن أن ساعة الجهاز مضبوطة تلقائيًا.',
          'The portal rejected the code this secret produced. Check the secret, and that your device clock is set automatically.',
        );
      case PortalErrorKind.serverError:
        return _t(
          'خطأ في خادم البوابة. حاول لاحقًا.',
          'The portal server returned an error. Try again later.',
        );
      case PortalErrorKind.unexpectedResponse:
        return _t(
          'رد غير متوقع من البوابة — تأكد من أن العنوان يشير إلى البوابة الصحيحة.',
          'Unexpected response from the portal — check that the address points at the right server.',
        );
    }
  }
}
