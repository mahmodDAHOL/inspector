# الاطلاع على قاعدة البيانات وفهم التشفير
# Database & Encryption Access Guide — Inspection Portal
# الجمهورية العربية السورية — وزارة الإعلام — مديرية الرقابة والتفتيش

> ⚠️ هذا الملف **للاستخدام الإداري/التطويري فقط**. لا تُشارك بيانات الاعتماد الفعلية (الموجودة في `.env` المحلي غير المرفوع إلى Git) خارج فريق التطوير.
>
> **تحديث ٢٠٢٦-٠٨-٢٨:** كل الأسرار المذكورة سابقًا في هذا الملف (والتي كانت مرفوعة إلى Git عبر الخطأ الموثّق سابقًا) تم **تدويرها بالكامل** (`SECRET_KEY`, `MASTER_ENCRYPTION_KEY`, كلمتا مرور DB/Redis، شهادة TLS)، و`.env` أُزيل من تاريخ Git بالكامل، وأُضيف `.gitignore`. القيم الحالية موجودة فقط في `.env` المحلي — راجع `security_audit_report_ar.md` للتفاصيل.

---

## ١. بيانات الاتصال بقاعدة البيانات

| المعامل | القيمة | المصدر |
|---|---|---|
| المحرك | PostgreSQL 16 | `docker-compose.yml` |
| اسم قاعدة البيانات | `inspection_portal` | `docker-compose.yml` |
| المستخدم | `inspection_app` | `docker-compose.yml` |
| كلمة المرور | قيمة `DB_PASSWORD` في `.env` المحلي (دُوِّرت، غير مرفوعة إلى Git) | `.env` |
| المنفذ | `5432` داخل شبكة Docker فقط — **غير معروض على المضيف** | — |

---

## ٢. طرق الاتصال العملية

### الأسهل — `psql` داخل حاوية `db`
```bash
docker exec -it inspection-db psql -U inspection_app -d inspection_portal
```
```sql
\dt                     -- عرض كل الجداول
\d complaint_logs       -- عرض أعمدة جدول معيّن
SELECT * FROM departments;
```

### أمر مباشر بدون جلسة تفاعلية
```bash
docker exec inspection-db psql -U inspection_app -d inspection_portal -c "SELECT username, role, is_active FROM users;"
```

### أداة رسومية (DBeaver / pgAdmin) من جهازك
المنفذ غير معروض افتراضيًا. لفتح اتصال مؤقت:
```bash
docker run --rm -it --network inspection-portal_inspection-network -p 5432:5432 alpine/socat \
  tcp-listen:5432,fork,reuseaddr tcp-connect:inspection-db:5432
```
ثم اتصل على `localhost:5432` بكلمة المرور من `.env` المحلي.

### من داخل كود Python (لقراءة الحقول المشفّرة)
موضّح في القسم ٥.

---

## ٣. مخطط الجداول (بعد التحصين الأمني — ٧ ترحيلات)

| الجدول | أهم الأعمدة | ملاحظات |
|---|---|---|
| `departments` | `id, name_ar, name_en, code, parent_id, created_at` | — |
| `users` | `..., email🔒, phone🔒, totp_secret🔒, failed_login_attempts, locked_until, last_login_at` | 🔒 = مشفّر (`bytea`) |
| `complaints` | `..., description🔒, complainant_name/phone/email🔒, first_response_at` | `first_response_at` أساس مؤشرات زمن الاستجابة |
| `investigation_notes` | `..., note_content🔒, is_confidential` | السرّية مُنفَّذة فعليًا في الـ API (تُفلتَر بالدور) |
| `complaint_logs` | `..., prev_hash, row_hash` | **محصّن**: سلسلة تجزئة + Trigger يرفض UPDATE/DELETE |
| `activity_logs` | `entity_type, entity_id, action, ..., prev_hash, row_hash` | **محصّن** بنفس الآلية — سجل النظام العام (دخول/مستخدمون/إدارات/تقارير) |
| `digital_signatures` | `report_id, signer_id, signature_data, certificate_thumbprint, signed_at` | **يُكتب فيه فعليًا الآن** (توقيع RSA-PSS/SHA-384 حقيقي) |
| `alembic_version` | — | تقني بحت |

> الجدول القديم `audit_logs` (مصمَّم مسبقًا لكن غير مُستخدَم أبدًا، مع الكود المرتبط `AuditLogger`) **أُزيل نهائيًا** — `complaint_logs`/`activity_logs` هما المرجع الوحيد الآن.

للتحقق من التحصين حيًّا:
```bash
docker exec inspection-db psql -U inspection_app -d inspection_portal -c \
  "DELETE FROM activity_logs WHERE true;"
# ERROR: This table is append-only: DELETE is not permitted
```

---

## ٤. آلية التشفير المستخدمة (بلا تغيير في التصميم)

الخدمة: `backend/app/core/encryption.py` (`EncryptionService`).

- **الخوارزمية:** AES-256-GCM.
- **اشتقاق المفتاح:** PBKDF2-HMAC-SHA256 (١٠٠,٠٠٠ تكرار) من `MASTER_ENCRYPTION_KEY` + `salt` عشوائي (١٦ بايت) + اسم السياق (`context`) — نفس القيمة تُنتج تشفيرًا مختلفًا حسب الحقل.
- **IV:** ١٢ بايت عشوائي لكل عملية.
- **الشكل المخزَّن:** `salt + iv + ciphertext+tag` في عمود `bytea` واحد.
- **المفتاح الرئيسي:** الآن مُدوَّر، Base64 في `.env` المحلي فقط. فقدانه = فقدان كل البيانات المشفّرة نهائيًا (ولهذا أُعيد بذر البيانات التجريبية بعد كل تدوير للمفتاح، بدل محاولة إعادة تشفير بيانات تجريبية عديمة القيمة).

### الحقول المشفّرة وسياق كل حقل

| الجدول.العمود | السياق |
|---|---|
| `users.email` | `email` |
| `users.phone` | `phone` |
| `users.totp_secret` | `totp_secret` |
| `complaints.description` | `description` |
| `complaints.complainant_name/phone/email` | نفس اسم الحقل |
| `investigation_notes.note_content` | `note_content` |

---

## ٥. كيف تقرأ حقلًا مشفّرًا يدويًا؟

```bash
docker exec -it inspection-backend python -c "
import asyncio
from sqlalchemy import select
from app.db.session import async_session_maker
from app.models import User
from app.core.encryption import get_encryption_service

async def main():
    enc = get_encryption_service()
    async with async_session_maker() as s:
        user = (await s.execute(select(User).where(User.username == 'admin'))).scalar_one()
        print('Email:', enc.decrypt(user.email, context='email'))

asyncio.run(main())
"
```

## ٦. توليد/قراءة رمز TOTP لمستخدم (لتسجيل الدخول يدويًا)

```bash
docker exec -it inspection-backend python -c "
import asyncio, pyotp
from sqlalchemy import select
from app.db.session import async_session_maker
from app.models import User
from app.core.encryption import get_encryption_service

async def main():
    enc = get_encryption_service()
    async with async_session_maker() as s:
        u = (await s.execute(select(User).where(User.username == 'admin'))).scalar_one()
        secret = enc.decrypt(u.totp_secret, context='totp_secret')
        print('رمز التحقق الحالي (صالح ٣٠ ثانية):', pyotp.TOTP(secret).now())

asyncio.run(main())
"
```

---

## ٧. التوقيع الرقمي — أين يُخزَّن مفتاحه؟

مفتاح RSA-2048 الخاص بالنظام (`backend/app/core/signing.py`) يُولَّد **مرة واحدة فقط** عند أول توقيع، ويُخزَّن في وحدة تخزين Docker الدائمة (`uploads_data`، مربوطة على `UPLOAD_DIR`) في `system/signing_key.pem`. لعرض بصمة المفتاح العام الحالية:
```bash
docker exec inspection-backend python -c "
from app.core.signing import certificate_thumbprint
print(certificate_thumbprint())
"
```

---

## ٨. تحذيرات أمنية سريعة (محدَّثة)

- تشفير الحقول (AES-256-GCM) سليم تقنيًا، لكنه **لا يحمي من مستخدم يملك صلاحية `admin`/`super_admin` في التطبيق نفسه** — التطبيق يفك التشفير تلقائيًا عند العرض لمن لديه صلاحية الوصول. التشفير يحمي بيانات القرص/النسخ الاحتياطي المعزولة عن التطبيق، وليس بديلاً عن ضبط الصلاحيات داخل التطبيق (المُنفَّذ الآن فعليًا — راجع `application_overview_ar.md`).
- الأسرار كانت مرفوعة إلى Git سابقًا — **تم إصلاح ذلك بالكامل**: أُزيلت من التاريخ، ودُوِّرت كل القيم. التفاصيل والتحقق في `security_audit_report_ar.md`.
- سجلات النشاط (`complaint_logs`/`activity_logs`) نصوصها غير مشفّرة عمدًا (بيانات تشغيلية وصفية، وليست بيانات شخصية حسّاسة) لكنها الآن محصّنة ضد التلاعب (سلسلة تجزئة + منع UPDATE/DELETE على مستوى القاعدة).
