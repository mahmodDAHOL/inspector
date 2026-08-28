# المواصفات التقنية الشاملة
# Inspection Portal — Technical Specification
# الجمهورية العربية السورية — وزارة الإعلام — مديرية الرقابة والتفتيش

---

## ١. نظرة عامة

### ١.١ الهدف
بناء نظام ويب مستقل وآمن لمديرية الرقابة والتفتيش في وزارة الإعلام، مخصص لمتابعة شكاوى الفساد والمخالفات الإدارية، مع ربط آمن مع بوابة MediaGate عبر آلية Polling.

### ١.٢ النطاق
- استقبال الشكاوى من MediaGate (Polling)
- إدارة دورة حياة الشكوى (من الاستلام إلى الإغلاق)
- نظام مصادقة متعدد العوامل (MFA)
- تشفير كامل للبيانات الحساسة
- توقيع إلكتروني على التقارير النهائية
- سجل تدقيق غير قابل للتعديل (Immutable Audit Trail)
- دعم اللغتين العربية والإنجليزية
- الوضع الليلي والنهاري

### ١.٣ المعايير الدولية المطبقة
| المعيار | التطبيق |
|---------|---------|
| ISO/IEC 27001:2022 | إدارة أمن المعلومات |
| ISO/IEC 27017:2015 | أمن الخدمات السحابية |
| ISO/IEC 27018:2019 | حماية البيانات الشخصية في السحابة |
| ISO 9001:2015 | إدارة الجودة |
| ISO/IEC 25010:2011 | جودة أنظمة البرمجيات |
| OWASP ASVS 4.0 | معايير التحقق من أمان التطبيقات |
| NIST SP 800-53 | ضوابط الأمن السيبراني |

---

## ٢. المعمارية التقنية

### ٢.١ المكونات

```
┌─────────────────────────────────────────────────────────────────┐
│                        طبقة العرض (Frontend)                     │
│  Vue.js 3 + Vite + Pinia + Vue i18n + Tailwind CSS             │
│  Dark/Light Mode | RTL/LTR | AR/EN                              │
├─────────────────────────────────────────────────────────────────┤
│                      طبقة واجهة البرمجة (API)                    │
│  FastAPI (Python 3.12) | Uvicorn | Gunicorn                     │
│  OAuth2 + TOTP | JWT (Access 15min / Refresh 7days)             │
├─────────────────────────────────────────────────────────────────┤
│                    طبقة الخدمات (Services)                       │
│  Encryption Service (AES-256-GCM) | Digital Signature (PKCS#12) │
│  Audit Logger | Notification Service | File Scanner (ClamAV)    │
├─────────────────────────────────────────────────────────────────┤
│                    طبقة البيانات (Data Layer)                    │
│  PostgreSQL 16 (TDE + RLS + pgaudit) | Redis (Sessions/Cache)  │
│  Audit Log Partition | Encrypted File Storage                   │
├─────────────────────────────────────────────────────────────────┤
│              طبقة الربط الخارجي (External Integration)           │
│  Polling Service → MediaGate API (REST + API Key)              │
│  Status Push API ← MediaGate (Read-Only Status)                │
└─────────────────────────────────────────────────────────────────┘
```

### ٢.٢ متطلبات البنية التحتية

| المكون | المواصفة | الكمية |
|--------|----------|--------|
| خادم التطبيق | 8 vCPU / 16GB RAM / 200GB SSD | ٢ (Production + Staging) |
| خادم قاعدة البيانات | 4 vCPU / 8GB RAM / 500GB SSD | ٢ (Primary + Replica) |
| خادم Redis | 2 vCPU / 4GB RAM / 50GB SSD | ١ |
| خادم النسخ الاحتياطي | Off-site / Cloud | ١ |
| Load Balancer | Nginx / HAProxy | ١ |

---

## ٣. قاعدة البيانات

### ٣.١ الجداول الرئيسية

#### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,        -- Argon2id
    full_name_ar VARCHAR(100) NOT NULL,
    full_name_en VARCHAR(100),
    email BYTEA NOT NULL,                        -- AES-256-GCM encrypted
    phone BYTEA,                                 -- AES-256-GCM encrypted
    role VARCHAR(30) NOT NULL CHECK (role IN (
        'super_admin', 'inspection_director', 'department_head',
        'senior_inspector', 'inspector', 'viewer'
    )),
    department_id UUID REFERENCES departments(id),
    totp_secret BYTEA NOT NULL,                  -- AES-256-GCM encrypted
    is_active BOOLEAN DEFAULT TRUE,
    failed_login_attempts INT DEFAULT 0,
    locked_until TIMESTAMP,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### complaints
```sql
CREATE TABLE complaints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_number VARCHAR(20) UNIQUE NOT NULL, -- INS-YYYY-XXXX
    title_ar VARCHAR(200) NOT NULL,
    title_en VARCHAR(200),
    description BYTEA NOT NULL,                   -- AES-256-GCM encrypted
    complainant_name BYTEA,                       -- AES-256-GCM encrypted
    complainant_phone BYTEA,                      -- AES-256-GCM encrypted
    complainant_email BYTEA,                      -- AES-256-GCM encrypted
    source VARCHAR(10) NOT NULL CHECK (source IN ('ERP', 'Direct')),
    category VARCHAR(30) NOT NULL,
    priority VARCHAR(10) NOT NULL CHECK (priority IN ('urgent', 'normal')),
    status VARCHAR(30) NOT NULL DEFAULT 'received',
    assigned_to UUID REFERENCES users(id),
    created_by UUID REFERENCES users(id),
    erp_reference_id VARCHAR(50),
    is_anonymous BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    closed_at TIMESTAMP
);
```

#### investigation_notes
```sql
CREATE TABLE investigation_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id UUID NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
    note_content BYTEA NOT NULL,                  -- AES-256-GCM encrypted
    note_type VARCHAR(20) NOT NULL CHECK (note_type IN (
        'finding', 'interview', 'evidence', 'decision', 'confidential'
    )),
    created_by UUID NOT NULL REFERENCES users(id),
    is_confidential BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### audit_logs (Immutable)
```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(10) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_values BYTEA,                             -- AES-256-GCM encrypted JSONB
    new_values BYTEA,                             -- AES-256-GCM encrypted JSONB
    performed_by UUID REFERENCES users(id),
    ip_address_hash VARCHAR(64) NOT NULL,         -- SHA-256
    user_agent_hash VARCHAR(64),                  -- SHA-256
    session_id VARCHAR(100),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (timestamp);

-- Disable UPDATE/DELETE on audit_logs via trigger
CREATE RULE audit_logs_no_update AS ON UPDATE TO audit_logs DO INSTEAD NOTHING;
CREATE RULE audit_logs_no_delete AS ON DELETE TO audit_logs DO INSTEAD NOTHING;
```

#### digital_signatures
```sql
CREATE TABLE digital_signatures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL,
    signer_id UUID NOT NULL REFERENCES users(id),
    signature_data BYTEA NOT NULL,                -- PKCS#7/CMS detached signature
    certificate_thumbprint VARCHAR(64) NOT NULL,  -- SHA-256 of cert
    signed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    verified_at TIMESTAMP,
    is_valid BOOLEAN DEFAULT TRUE
);
```

### ٣.٢ Row-Level Security (RLS)

```sql
-- Enable RLS on complaints
ALTER TABLE complaints ENABLE ROW LEVEL SECURITY;

-- Policy: Inspectors see only assigned complaints
CREATE POLICY inspector_complaint_access ON complaints
    FOR ALL TO inspector_role
    USING (assigned_to = current_setting('app.current_user_id')::UUID);

-- Policy: Department heads see all in their department
CREATE POLICY dept_head_complaint_access ON complaints
    FOR ALL TO dept_head_role
    USING (EXISTS (
        SELECT 1 FROM users u
        WHERE u.id = complaints.assigned_to
        AND u.department_id = current_setting('app.current_dept_id')::UUID
    ));

-- Policy: Directors see all
CREATE POLICY director_complaint_access ON complaints
    FOR ALL TO director_role
    USING (TRUE);
```

---

## ٤. خدمة التشفير (Encryption Service)

### ٤.١ المعمارية

```
┌─────────────────────────────────────────┐
│  Master Key (32 bytes)                  │
│  Stored in: HashiCorp Vault / File      │
│  Protected by: OS-level permissions     │
├─────────────────────────────────────────┤
│  Data Encryption Keys (DEKs)            │
│  One per table/field type               │
│  Encrypted by Master Key (Envelope)     │
├─────────────────────────────────────────┤
│  Field-Level Encryption                 │
│  AES-256-GCM + Unique IV per field      │
│  Authenticated Encryption (AEAD)        │
└─────────────────────────────────────────┘
```

### ٤.٢ خوارزمية التشفير

- **Algorithm**: AES-256-GCM (Galois/Counter Mode)
- **Key Size**: 256 bits
- **IV Size**: 96 bits (random per encryption)
- **Tag Size**: 128 bits
- **Key Derivation**: PBKDF2-HMAC-SHA256 (100,000 iterations) for password-based keys

### ٤.٣ إدارة المفاتيح

| المفتاح | الاستخدام | مدة الحياة | آلية التدوير |
|---------|-----------|------------|--------------|
| Master Key | تشفير DEKs | سنوي | تدوير يدوي مع إعادة تشفير |
| DEK-PII | بيانات المُبلّغين | نصف سنوي | تدوير تلقائي |
| DEK-Notes | ملاحظات التحقيق | نصف سنوي | تدوير تلقائي |
| DEK-Audit | سجل التدقيق | سنوي | تدوير يدوي |

---

## ٥. التوقيع الإلكتروني

### ٥.١ المعمارية

بما أنه لا يوجد HSM، نستخدم الحل التالي المتوافق مع ISO/IEC 27001:

```
┌─────────────────────────────────────────────┐
│  PKCS#12 Certificate (.p12)                 │
│  - Self-signed CA (Internal)                │
│  - أو: National CA Certificate (إن توفر)    │
│  - Private Key: AES-256 encrypted in DB     │
│  - Certificate: Stored in DB                │
├─────────────────────────────────────────────┤
│  Signing Process:                           │
│  1. User authenticates with MFA             │
│  2. System decrypts private key (in-memory) │
│  3. Sign PDF report using PKCS#7/CMS        │
│  4. Store signature + certificate hash      │
│  5. Clear key from memory immediately       │
└─────────────────────────────────────────────┘
```

### ٥.٢ متطلبات الشهادة

| الخاصية | القيمة |
|---------|--------|
| Algorithm | RSA-4096 or ECDSA P-384 |
| Hash | SHA-384 |
| Validity | ٢ سنة |
| Key Usage | Digital Signature, Non-Repudiation |
| Extended Key Usage | Document Signing |

### ٥.٣ سير عمل التوقيع

```
1. Inspector completes investigation
2. Generates final report (PDF/A-3 format)
3. System hashes the report (SHA-384)
4. Inspector enters signing PIN (second factor)
5. System decrypts private key temporarily
6. Creates PKCS#7 detached signature
7. Embeds signature in PDF
8. Stores signature record in DB
9. Clears private key from memory
10. Marks report as "signed and final"
```

---

## ٦. آلية الربط مع MediaGate (Polling)

### ٦.١ سير العمل

```
┌─────────────┐     Polling (every 5 min)     ┌─────────────────┐
│  MediaGate  │ ◄──────────────────────────── │  Inspection     │
│  (ERPNext)  │                               │  Polling Service│
└─────────────┘                               └─────────────────┘
       │                                              │
       │  1. Fetch new complaints                     │
       │  2. Validate & Anonymize                     │
       │  3. Encrypt sensitive fields                 │
       │  4. Store in Inspection DB                   │
       ▼                                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Inspection Portal Database                      │
│  (Independent, Encrypted, No Direct ERP Access)             │
└─────────────────────────────────────────────────────────────┘
```

### ٦.٢ API Endpoints

#### MediaGate → Inspection (Polling)
```http
GET /api/v1/external/poll/complaints
Headers:
  X-API-Key: <mediagate_api_key>
  X-Request-ID: <uuid>
  X-Timestamp: <ISO8601>

Response 200:
{
  "complaints": [
    {
      "erp_reference_id": "ERP-2026-0891",
      "title_ar": "...",
      "description": "...",
      "category": "procurement_violation",
      "priority": "urgent",
      "submitted_at": "2026-08-28T14:30:00Z",
      "mediagate_complaint_id": "MG-2026-1234"
    }
  ],
  "pagination": {
    "total": 50,
    "page": 1,
    "per_page": 20
  }
}
```

#### Inspection → MediaGate (Status Push)
```http
POST /api/v1/external/push/status
Headers:
  X-API-Key: <mediagate_api_key>
  Content-Type: application/json

Body:
{
  "mediagate_complaint_id": "MG-2026-1234",
  "inspection_complaint_number": "INS-2026-0891",
  "status": "under_investigation",
  "status_ar": "قيد التحقيق",
  "status_en": "Under Investigation",
  "updated_at": "2026-08-29T09:00:00Z",
  "can_be_escalated": false,
  "estimated_resolution_date": "2026-09-15"
}
```

### ٦.٣ ضوابط الأمان للـ Polling

| الضوابط | التنفيذ |
|---------|---------|
| Authentication | API Key + HMAC-SHA256 Signature |
| Rate Limiting | 12 requests/hour (every 5 min) |
| IP Whitelisting | MediaGate IPs only |
| Request ID | UUID unique per request (replay protection) |
| Timestamp | ± 5 minutes tolerance |
| Encryption | TLS 1.3 mandatory |

---

## ٧. المصادقة والتفويض

### ٧.١ MFA Flow

```
┌─────────┐    username/password     ┌──────────┐
│  User   │ ───────────────────────► │  Backend │
│         │                          │          │
│         │ ◄──── Temp Token (JWT) ─ │          │
│         │    (valid 5 minutes)     │          │
│         │                          │          │
│         │ ───── TOTP Code (6-digit)│          │
│         │ ───────────────────────► │          │
│         │                          │          │
│         │ ◄── Access + Refresh ─── │          │
│         │     Token (JWT)          │          │
└─────────┘                          └──────────┘
```

### ٧.٢ JWT Specifications

| Token Type | Algorithm | Expiration | Storage |
|------------|-----------|------------|---------|
| Temporary | HS256 | 5 minutes | Memory only |
| Access | RS256 | 15 minutes | httpOnly Secure Cookie |
| Refresh | RS256 | 7 days | httpOnly Secure Cookie + Redis |

### ٧.٣ Session Management

- Sessions stored in Redis with TTL = 15 minutes
- Auto-refresh on activity (sliding window)
- Concurrent session limit: 1 per user (or 2 for directors)
- Force logout on password change or role change
- Device fingerprinting (browser + OS + screen resolution)

---

## ٨. سجل التدقيق (Audit Trail)

### ٨.١ متطلبات ISO 27001

| المتطلب | التنفيذ |
|---------|---------|
| A.12.4.1 | تسجيل جميع أحداث الأمان |
| A.12.4.2 | حماية سجلات التدقيق |
| A.12.4.3 | سجلات مسؤولي الأنظمة |
| A.12.4.4 | تزامن الساعات (NTP) |
| A.12.4.5 | حماية أدوات التسجيل |

### ٨.٢ الأحداث المسجلة

| الفئة | الأحداث |
|-------|---------|
| Authentication | login_success, login_failure, logout, mfa_success, mfa_failure, password_change |
| Authorization | access_denied, role_changed, permission_elevated |
| Data Access | complaint_viewed, note_viewed, report_downloaded |
| Data Modification | complaint_created, status_changed, assigned_changed, note_added |
| System | backup_completed, key_rotated, config_changed, error_occurred |
| Integration | poll_initiated, status_pushed, api_error |

### ٨.٣ حماية السجلات

- WORM (Write Once Read Many) storage for audit_logs
- Daily export to immutable backup
- Separate database user with INSERT-only privileges
- No DELETE/UPDATE permissions on audit_logs table
- Retention period: 7 years (as per legal requirements)

---

## ٩. الواجهة الأمامية (Frontend)

### ٩.١ التقنيات

| التقنية | الاستخدام |
|---------|-----------|
| Vue.js 3 (Composition API) | إطار العمل |
| Vite | Bundler |
| Pinia | State Management |
| Vue i18n | التعريب (AR/EN) |
| Vue Router | التوجيه |
| Tailwind CSS | التصميم |
| Chart.js / D3.js | الرسوم البيانية |
| PDF-LIB.js | توليد التقارير PDF |
| QRCode.js | رموز QR للتحقق |

### ٩.٢ متطلبات التصميم

| العنصر | المواصفة |
|--------|----------|
| الألوان الرئيسية | Teal #1B5E5E + Gold #A68B5B |
| الخط | Noto Sans Arabic / Inter |
| RTL | دعم كامل للعربية (RTL) |
| Responsive | Mobile + Tablet + Desktop |
| Accessibility | WCAG 2.1 Level AA |
| Dark Mode | تبديل تلقائي/يدوي |

### ٩.٣ الشاشات الرئيسية

1. **Login**: MFA (username/password + TOTP)
2. **Dashboard**: إحصائيات + شكاوى عاجلة + إشعارات
3. **Complaints List**: جدول + فلترة + بحث
4. **Complaint Detail**: معلومات + ملاحظات + مرفقات + سير العمل
5. **Investigation Notes**: إضافة/تعديل ملاحظات (مشفرة)
6. **Reports**: توليد تقارير + توقيع إلكتروني
7. **Audit Log**: عرض سجل التدقيق (للمدراء فقط)
8. **Settings**: إعدادات المستخدم + تغيير اللغة/الوضع

---

## ١٠. النسخ الاحتياطي والاستعادة

### ١٠.١ استراتيجية النسخ الاحتياطي

| النوع | التكرار | الاحتفاظ | التخزين |
|-------|---------|----------|---------|
| Full Database | يومي | 30 يوم | Off-site encrypted |
| Incremental | كل 6 ساعات | 7 أيام | Off-site encrypted |
| Audit Logs | فوري (streaming) | 7 سنوات | WORM storage |
| File Attachments | يومي | 90 يوم | Off-site encrypted |
| Configuration | بعد كل تغيير | 1 سنة | Git + Off-site |

### ١٠.٢ التشفير

- جميع النسخ الاحتياطية مشفرة بـ AES-256-GCM
- مفاتيح النسخ الاحتياطي منفصلة عن مفاتيح الإنتاج
- اختبار استعادة شهري (Disaster Recovery Drill)

---

## ١١. خطة الاختبار

### ١١.١ أنواع الاختبار

| النوع | الأدوات | التغطية |
|-------|---------|---------|
| Unit Tests | pytest | > 80% |
| Integration Tests | pytest + TestClient | API endpoints |
| Security Tests | OWASP ZAP, Burp Suite | OWASP Top 10 |
| Penetration Test | External vendor | سنوي |
| Performance | Locust / k6 | 500 concurrent users |
| Accessibility | axe-core | WCAG 2.1 AA |

### ١١.٢ سيناريوهات الاختبار الأمني

1. SQL Injection على جميع المدخلات
2. XSS (Stored, Reflected, DOM)
3. CSRF protection validation
4. JWT token manipulation
5. Brute force login protection
6. Session hijacking prevention
7. File upload vulnerabilities
8. IDOR (Insecure Direct Object Reference)
9. Rate limiting bypass attempts
10. Encryption key extraction attempts

---

## ١٢. التوثيق والتدريب

### ١٢.١ الوثائق المطلوبة

| الوثيقة | الجمهور | اللغة |
|---------|---------|-------|
| System Architecture Document | فريق التقنية | EN |
| API Specification (OpenAPI 3.0) | المطورون | EN |
| Database Schema Documentation | فريق التقنية | EN |
| Security Policy | الأمن السيبراني | AR/EN |
| User Manual | المفتشون | AR |
| Administrator Guide | مسؤولو النظام | AR/EN |
| Training Materials | جميع المستخدمين | AR |
| Disaster Recovery Plan | فريق التقنية | AR/EN |
| Incident Response Plan | فريق الأمن | AR/EN |

### ١٢.٢ خطة التدريب

| المرحلة | المدة | المحتوى | الجمهور |
|---------|-------|---------|---------|
| Orientation | 2 hours | نظرة عامة + سياسات الأمان | الجميع |
| Basic Training | 4 hours | تسجيل الدخول + إدارة الشكاوى | المفتشون |
| Advanced Training | 4 hours | التحقيق + الملاحظات + التقارير | المفتشون المتقدمون |
| Admin Training | 6 hours | إدارة المستخدمين + الإعدادات + النسخ الاحتياطي | المسؤولون |
| Security Training | 2 hours | التعرف على التهديدات + الإبلاغ | الجميع |

---

## ١٣. خطة التنفيذ (Revised)

| المرحلة | المدة | المخرجات | المعايير |
|---------|-------|----------|----------|
| **Phase 1: Foundation** | 2 weeks | Infrastructure, Docker, CI/CD, Vault setup | ISO 27001 A.12 |
| **Phase 2: Core Backend** | 3 weeks | Auth, Encryption, Complaint CRUD, Audit | ISO 27001 A.9, A.10 |
| **Phase 3: External API** | 2 weeks | Polling service, Status push, API docs | ISO 27001 A.13 |
| **Phase 4: Frontend** | 4 weeks | All screens, i18n, Dark/Light, Responsive | ISO 25010 |
| **Phase 5: Digital Signature** | 2 weeks | PKCS#12 integration, PDF signing, verification | ISO 27001 A.10 |
| **Phase 6: Security Hardening** | 2 weeks | Pen test, code review, security fixes | OWASP ASVS |
| **Phase 7: Documentation & Training** | 2 weeks | All docs, training sessions, handover | ISO 9001 |
| **Phase 8: UAT & Launch** | 1 week | User acceptance testing, production deployment | ISO 9001 |

**Total Duration: 18 weeks**

---

## ١٤. مصفوفة الامتثال (Compliance Matrix)

### ISO/IEC 27001:2022 Controls

| Control | Title | Implementation | Evidence |
|---------|-------|----------------|----------|
| A.5.1 | Policies for information security | Security Policy document | Document |
| A.5.2 | Information security roles | RBAC matrix | Configuration |
| A.6.1 | Screening | Background checks for admins | HR records |
| A.7.1 | Physical security | Server room access control | Access logs |
| A.8.1 | User endpoint devices | Device policy | Policy doc |
| A.9.1 | Access to networks | VPN + Firewall rules | Config |
| A.9.2 | Access to information | RBAC + RLS | DB config |
| A.9.3 | Access rights | User provisioning process | Procedure |
| A.9.4 | Access control | MFA + JWT | Code + Config |
| A.10.1 | Cryptographic controls | AES-256-GCM + TLS 1.3 | Code review |
| A.10.2 | Cryptographic keys | Key management procedure | Procedure |
| A.12.1 | Operations security | Change management | Procedure |
| A.12.2 | Protection from malware | ClamAV + policies | Config |
| A.12.3 | Backup | Backup strategy | Procedure |
| A.12.4 | Logging | Audit trail | DB + Code |
| A.12.5 | Control of operational software | Approved software list | Document |
| A.12.6 | Technical vulnerability management | Patch management | Procedure |
| A.13.1 | Network security management | Firewall + IDS | Config |
| A.13.2 | Information transfer | Secure API + TLS | Code |
| A.14.1 | Security requirements of information systems | Secure SDLC | Procedure |

---

## ١٥. الملحقات

### أ. قائمة المنافذ (Ports)

| Service | Port | Protocol | Description |
|---------|------|----------|-------------|
| Nginx | 443 | HTTPS | Reverse proxy |
| FastAPI | 8000 | HTTP | Internal only |
| PostgreSQL | 5432 | TCP | Internal only |
| Redis | 6379 | TCP | Internal only |
| Vault | 8200 | HTTPS | Internal only |

### ب. متطلبات البرمجيات

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.12+ | Backend |
| Node.js | 20+ | Frontend build |
| PostgreSQL | 16+ | Database |
| Redis | 7+ | Cache/Sessions |
| Nginx | 1.24+ | Reverse proxy |
| Docker | 24+ | Containerization |
| Docker Compose | 2.20+ | Orchestration |

---

**Document Version: 1.0**
**Date: 2026-08-28**
**Classification: Internal — وزارة الإعلام**
**Owner: مديرية تقانة المعلومات والتحول الرقمي**

