# الاطلاع على قاعدة البيانات وفهم التشفير
# Database & Encryption Access Guide — Inspection Portal
# الجمهورية العربية السورية — وزارة الإعلام — مديرية الرقابة والتفتيش

> ⚠️ هذا الملف **للاستخدام الإداري/التطويري فقط** على البيئة المحلية الخاصة بك. لا تُشارك بيانات الاعتماد أو المفاتيح الظاهرة هنا خارج فريق التطوير — راجع أيضًا `security_audit_report_ar.md` ففيه ملاحظة مهمة حول أن هذه القيم حاليًا **مرفوعة إلى Git** ويجب تدويرها قبل أي بيئة إنتاج فعلية.

---

## ١. بيانات الاتصال بقاعدة البيانات

القيم الفعلية موجودة في ملف `.env` (جذر المشروع) و`docker-compose.yml`:

| المعامل | القيمة الحالية (بيئة التطوير) | مصدرها |
|---|---|---|
| المحرك | PostgreSQL 16 | `docker-compose.yml` |
| اسم قاعدة البيانات | `inspection_portal` | `docker-compose.yml` |
| المستخدم | `inspection_app` | `docker-compose.yml` |
| كلمة المرور | قيمة `DB_PASSWORD` في `.env` | `.env` |
| المنفذ داخل شبكة Docker | `5432` | — |
| المنفذ من جهازك | **غير مُعرَّض للخارج حاليًا** (لا يوجد `ports:` لخدمة `db` في `docker-compose.yml`) | — |

بما أن منفذ `5432` غير معروض على المضيف، الوصول لقاعدة البيانات يتم إما من داخل حاوية `backend`/`db` مباشرة، أو بإضافة تحويل منفذ مؤقت.

---

## ٢. طرق الاتصال العملية

### الطريقة الأولى (الأسهل) — `psql` داخل حاوية `db`
```bash
docker exec -it inspection-db psql -U inspection_app -d inspection_portal
```
أوامر مفيدة داخل `psql`:
```sql
\dt                     -- عرض كل الجداول
\d users                -- عرض أعمدة جدول معيّن
SELECT * FROM departments;
```

### الطريقة الثانية — أمر مباشر بدون جلسة تفاعلية
```bash
docker exec inspection-db psql -U inspection_app -d inspection_portal -c "SELECT username, role, is_active FROM users;"
```

### الطريقة الثالثة — أداة رسومية (DBeaver / pgAdmin / TablePlus) من جهازك
قاعدة البيانات غير معروضة على المضيف افتراضيًا. لفتح اتصال مؤقت من جهازك:
```bash
docker run --rm -it --network inspection-portal_inspection-network -p 5432:5432 alpine/socat \
  tcp-listen:5432,fork,reuseaddr tcp-connect:inspection-db:5432
```
ثم اتصل من الأداة الرسومية على `localhost:5432` بنفس بيانات الاعتماد أعلاه. (أو الأبسط: أضف مؤقتًا `ports: ["5432:5432"]` تحت خدمة `db` في `docker-compose.yml` ثم `docker compose up -d db` — **تذكّر إزالتها بعد الانتهاء**، فهذا يعرّض قاعدة البيانات مباشرة على شبكتك المحلية.)

### الطريقة الرابعة — من داخل كود Python (لقراءة الحقول المشفرة مباشرة)
موضّحة بالتفصيل في القسم ٤.

---

## ٣. مخطط الجداول (Schema Reference)

| الجدول | أهم الأعمدة | ملاحظات |
|---|---|---|
| `departments` | `id, name_ar, name_en, code, parent_id, created_at` | — |
| `users` | `id, username, password_hash, full_name_ar/en, email🔒, phone🔒, role, department_id, totp_secret🔒, is_active, failed_login_attempts, locked_until, last_login_at, created_at, updated_at` | 🔒 = مشفّر (`bytea`) |
| `complaints` | `id, complaint_number, title_ar/en, description🔒, complainant_name/phone/email🔒, source, category, priority, status, assigned_to, created_by, erp_reference_id, is_anonymous, created_at, updated_at, closed_at, first_response_at` | — |
| `investigation_notes` | `id, complaint_id, note_content🔒, note_type, is_confidential, created_by, created_at` | لا يوجد جدول ORM مستقل له، يُستعلَم عبر SQL مباشر |
| `complaint_logs` | `id, complaint_id, action, description, performed_by, created_at` | سجل نشاط كل شكوى (نص صريح غير مشفّر — بيانات تشغيلية وليست حسّاسة) |
| `activity_logs` | `id, entity_type, entity_id, action, description, performed_by, created_at` | سجل نشاط النظام العام (نص صريح غير مشفّر) |
| `audit_logs` | `id, table_name, record_id, action, old_values🔒, new_values🔒, performed_by, ip_address_hash, timestamp` | **موجود في المخطط لكن غير مُستخدَم فعليًا حاليًا** |
| `digital_signatures` | `id, report_id, signer_id, signature_data, certificate_thumbprint, signed_at` | **موجود في المخطط لكن لا يُكتب فيه شيء حاليًا** |

للاطلاع على كامل تعريف الأعمدة (الأنواع، القيود، الفهارس) راجع ملفات الترحيل (Migrations) في `backend/alembic/versions/001` حتى `006` — كل تغيير بنيوي موثّق هناك بالترتيب الزمني.

---

## ٤. آلية التشفير المستخدمة

الخدمة: `backend/app/core/encryption.py` (`EncryptionService`).

- **الخوارزمية:** AES-256-GCM (تشفير متماثل مع مصادقة/سلامة بيانات مدمجة).
- **اشتقاق المفتاح:** لكل عملية تشفير، يُشتق مفتاح فريد من "المفتاح الرئيسي" (`MASTER_ENCRYPTION_KEY`) عبر **PBKDF2-HMAC-SHA256** (١٠٠,٠٠٠ تكرار)، بإدخال `salt` عشوائي (١٦ بايت) **+ اسم السياق (`context`)** — أي أن نفس القيمة النصية تُنتج تشفيرًا مختلفًا تمامًا حسب الحقل الذي تنتمي إليه (`email` مختلف عن `phone` حتى لو كانا لنفس المستخدم بنفس القيمة).
- **متجه التهيئة (IV):** ١٢ بايت عشوائي لكل عملية تشفير (لا يتكرر أبدًا، وهذا صحيح ومطلوب لأمان GCM).
- **الشكل المخزَّن في العمود (`bytea`):** `salt (16 بايت) + iv (12 بايت) + نص مشفّر+وسم مصادقة (GCM tag)` متتالية في مصفوفة بايتات واحدة.
- **المفتاح الرئيسي نفسه:** قيمة Base64 مُخزَّنة في `.env` تحت `MASTER_ENCRYPTION_KEY`. من دون هذا المفتاح، لا يمكن فك أي حقل مشفّر إطلاقًا — **فقدانه يعني فقدان البيانات المشفّرة نهائيًا**، وتسريبه يعني كشف كل الحقول الحسّاسة.

### الحقول المشفّرة فعليًا الآن (وسياق كل حقل)

| الجدول.العمود | السياق (`context`) |
|---|---|
| `users.email` | `email` |
| `users.phone` | `phone` (ملاحظة: هذا الحقل لا يُجمَع فعليًا من نموذج إنشاء المستخدم حاليًا، فيُخزَّن دائمًا كسلسلة فارغة مشفّرة) |
| `users.totp_secret` | `totp_secret` |
| `complaints.description` | `description` |
| `complaints.complainant_name` | `complainant_name` |
| `complaints.complainant_phone` | `complainant_phone` |
| `complaints.complainant_email` | `complainant_email` |
| `investigation_notes.note_content` | `note_content` |

الحقول **غير المشفّرة عمدًا** (نص صريح في قاعدة البيانات): اسم المستخدم، الاسم الكامل (عربي/إنجليزي)، الدور، عنوان الشكوى، الحالة، الأولوية، الفئة، رقم الشكوى، ونصوص سجلات النشاط — كلها بيانات تشغيلية/بحث تحتاج فهرسة وفلترة سريعة، وليست بيانات شخصية حسّاسة بحد ذاتها.

---

## ٥. كيف تقرأ حقلًا مشفّرًا يدويًا؟

الطريقة الصحيحة الوحيدة هي عبر كود Python يستخدم نفس `EncryptionService` (لأن فك التشفير يحتاج معرفة الـ `context` بالضبط). لا يمكن فك التشفير بأداة SQL عادية.

مثال جاهز (نفّذه داخل حاوية `backend`):
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
        print('Phone:', enc.decrypt(user.phone, context='phone'))
        # TOTP secret — لا تطبعه إلا لأغراض تطويرية محلية بحتة
        print('TOTP secret:', enc.decrypt(user.totp_secret, context='totp_secret'))

asyncio.run(main())
"
```

لفك تشفير حقل شكوى (مثال: وصف الشكوى واسم الشاكي):
```python
from app.models import Complaint
complaint = (await s.execute(select(Complaint).where(Complaint.complaint_number == 'INS-2026-0001'))).scalar_one()
print(enc.decrypt(complaint.description, context='description'))
print(enc.decrypt(complaint.complainant_name, context='complainant_name'))
```

> إذا استخدمت `context` خاطئًا، فك التشفير سيفشل (استثناء تحقق GCM) — هذا سلوك مقصود يمنع الخلط بين الحقول.

---

## ٦. توليد/قراءة رمز TOTP لمستخدم تجريبي (لتسجيل الدخول يدويًا)

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

## ٧. تحذيرات أمنية سريعة (تفصيلها الكامل في تقرير الثغرات)

- **`.env` (يحوي `SECRET_KEY` و`MASTER_ENCRYPTION_KEY` وكلمات مرور قاعدة البيانات/Redis) وملف المفتاح الخاص `ssl/inspection-portal.key` مضافان فعليًا إلى Git حاليًا** (لا يوجد ملف `.gitignore` في المشروع إطلاقًا). هذا يعني أن أي شخص يحصل على نسخة من المستودع يحصل على كل المفاتيح. **يجب تدوير (Rotate) كل هذه القيم فورًا قبل أي نشر حقيقي**، وإضافتها إلى `.gitignore`.
- تشفير الحقول (AES-256-GCM) سليم تقنيًا، لكنه **لا يحمي من مستخدم يملك صلاحية `admin`/`super_admin` في التطبيق نفسه** — فالتطبيق يفك التشفير تلقائيًا عند العرض عبر الـ API لأي مستخدم لديه صلاحية الوصول للسجل. التشفير هنا يحمي بيانات القرص/النسخ الاحتياطي من قاعدة البيانات في حال تسريبها بمعزل عن التطبيق، وليس بديلاً عن ضبط الصلاحيات داخل التطبيق.
