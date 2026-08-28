# خطة اختبار الأمان الشاملة
# Comprehensive Security Test Plan
# الجمهورية العربية السورية — وزارة الإعلام — مديرية الرقابة والتفتيش

---

## ١. نظرة عامة

### ١.١ الهدف
إجراء اختبار أمان شامل (Security Assessment) لنظام بوابة الرقابة والتفتيش، يتوافق مع:
- OWASP ASVS Level 3
- ISO/IEC 27001:2022
- NIST SP 800-53
- PTES (Penetration Testing Execution Standard)

### ١.٢ النطاق
| المكون | النطاق | الأدوات |
|--------|--------|---------|
| Web Application | Frontend + Backend | OWASP ZAP, Burp Suite |
| API | REST Endpoints | Postman, RESTler |
| Database | PostgreSQL | sqlmap, pgaudit |
| Infrastructure | Docker, Nginx, Network | Nmap, Nessus |
| Authentication | MFA, JWT, Session | JWT_Tool, Hashcat |
| Encryption | AES-256-GCM, TLS 1.3 | testssl.sh, OpenSSL |

---

## ٢. مراحل الاختبار

### المرحلة ١: جمع المعلومات (Information Gathering)

| الاختبار | الأداة | المتوقع | النتيجة |
|----------|--------|---------|---------|
| فحص المنافذ المفتوحة | Nmap | 80, 443 فقط | ⬜ |
| تحديد التقنيات | Wappalyzer | Vue.js, FastAPI | ⬜ |
| فحص الشهادات SSL | testssl.sh | A+ Rating | ⬜ |
| فحص DNS | dig, nslookup | No zone transfer | ⬜ |
| فحص الـ Headers | curl, OWASP ZAP | All security headers present | ⬜ |
| فحص robots.txt / sitemap | curl | No sensitive paths exposed | ⬜ |

**سكريبت الفحص:**
```bash
#!/bin/bash
# Phase 1: Information Gathering

echo "=== Nmap Port Scan ==="
nmap -sV -sC -p- --open inspection-portal.gov.sy -oN nmap_results.txt

echo "=== SSL/TLS Scan ==="
testssl.sh --severity HIGH inspection-portal.gov.sy > ssl_results.txt

echo "=== Header Check ==="
curl -I -s https://inspection-portal.gov.sy | tee headers.txt

echo "=== DNS Enumeration ==="
dig axfr @ns1.gov.sy inspection-portal.gov.sy
dig txt inspection-portal.gov.sy

echo "=== Technology Detection ==="
whatweb https://inspection-portal.gov.sy
```

---

### المرحلة ٢: فحص الثغرات الآلية (Automated Vulnerability Scanning)

| الاختبار | الأداة | السيناريو | النتيجة المتوقعة |
|----------|--------|-----------|------------------|
| SAST (Static Analysis) | SonarQube | No critical/high vulnerabilities | 0 Critical, 0 High |
| DAST (Dynamic Analysis) | OWASP ZAP | No OWASP Top 10 findings | All Pass |
| Dependency Scan | Snyk, pip-audit | No known CVEs | All Clear |
| Container Scan | Trivy | No OS/package vulnerabilities | All Clear |
| Secret Detection | GitLeaks, TruffleHog | No leaked secrets | 0 Findings |

**سكريبت SAST:**
```bash
#!/bin/bash
# Phase 2: Automated Scanning

echo "=== SonarQube SAST ==="
sonar-scanner   -Dsonar.projectKey=inspection-portal   -Dsonar.sources=./backend,./frontend   -Dsonar.host.url=http://sonarqube:9000

echo "=== Snyk Dependency Scan ==="
snyk test --file=backend/requirements.txt
snyk test --file=frontend/package.json

echo "=== Trivy Container Scan ==="
trivy image inspection-portal-backend:latest
trivy image inspection-portal-frontend:latest

echo "=== GitLeaks Secret Detection ==="
gitleaks detect --source . --verbose

echo "=== OWASP ZAP Baseline Scan ==="
zap-baseline.py -t https://inspection-portal.gov.sy -r zap_report.html
```

---

### المرحلة ٣: اختبار الاختراق اليدوي (Manual Penetration Testing)

#### ٣.١ اختبار المصادقة (Authentication Testing)

| # | الاختبار | السيناريو | الأداة | النتيجة |
|---|----------|-----------|--------|---------|
| A1 | Brute Force | 100 محاولة دخول فاشلة | Hydra | حظر IP بعد 30 محاولة |
| A2 | Credential Stuffing | قائمة بيانات مسربة | Burp Suite | رفض جميع المحاولات |
| A3 | Password Policy | اختبار ضعف كلمات المرور | Hashcat | Argon2id يقاوم القوة الغاشمة |
| A4 | TOTP Bypass | إعادة استخدام رمز TOTP | Burp Repeater | رفض الرمز المُستخدم |
| A5 | Session Fixation | تثبيت معرف الجلسة | Burp Suite | إعادة توليد ID عند المصادقة |
| A6 | Concurrent Sessions | تسجيل دخول من جهازين | Manual | حسب سياسة الدور |
| A7 | Logout Security | تسجيل الخروج + زر الرجوع | Manual | تدمير الجلسة فوراً |

**سكريبت Brute Force Test:**
```bash
#!/bin/bash
# Authentication Brute Force Test

echo "=== Testing Login Rate Limiting ==="
for i in {1..35}; do
  curl -s -X POST https://inspection-portal.gov.sy/api/v1/auth/login     -H "Content-Type: application/json"     -d '{"username":"admin","password":"wrong"}'     -w "Attempt $i: HTTP %{http_code}\n"
done

echo "=== Testing Account Lockout ==="
for i in {1..35}; do
  curl -s -X POST https://inspection-portal.gov.sy/api/v1/auth/login     -H "Content-Type: application/json"     -d '{"username":"inspector_ahmed","password":"wrong"}'     -w "Attempt $i: HTTP %{http_code}\n"
done
```

#### ٣.٢ اختبار التفويض (Authorization Testing)

| # | الاختبار | السيناريو | النتيجة |
|---|----------|-----------|---------|
| B1 | Horizontal Privilege | مفتش يحاول الوصول لشكوى زميله | 403 Forbidden |
| B2 | Vertical Privilege | مفتش يحاول الوصول لـ Admin Panel | 403 Forbidden |
| B3 | IDOR | تغيير ID في URL /api/v1/complaints/{id} | 403 أو 404 |
| B4 | Function Level Access | مفتش يحاول إنشاء مستخدم | 403 Forbidden |
| B5 | RLS Bypass | محاولة تجاوز Row-Level Security | فشل — البيانات مشفرة |

**سكريبت Authorization Test:**
```python
#!/usr/bin/env python3
# Authorization Testing Script

import requests
import jwt

BASE_URL = "https://inspection-portal.gov.sy"

# Login as inspector
inspector_token = login("inspector_ahmed", "password")

# Test 1: Access another inspector's complaint
resp = requests.get(
    f"{BASE_URL}/api/v1/complaints/other-inspector-complaint-id",
    headers={"Authorization": f"Bearer {inspector_token}"}
)
assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"

# Test 2: Try admin endpoint as inspector
resp = requests.get(
    f"{BASE_URL}/api/v1/users",
    headers={"Authorization": f"Bearer {inspector_token}"}
)
assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"

# Test 3: IDOR — sequential ID access
for i in range(1, 10):
    resp = requests.get(
        f"{BASE_URL}/api/v1/complaints/INS-2026-{i:04d}",
        headers={"Authorization": f"Bearer {inspector_token}"}
    )
    if resp.status_code == 200:
        data = resp.json()
        assert data.get("assigned_to") == get_current_user_id(), "IDOR vulnerability!"

print("All authorization tests passed!")
```

#### ٣.٣ اختبار حقن SQL (SQL Injection)

| # | الاختبار | الحمولة (Payload) | النتيجة |
|---|----------|-------------------|---------|
| C1 | Classic SQLi | `' OR '1'='1` | Parameterized Query — Safe |
| C2 | Union-based | `' UNION SELECT * FROM users--` | Safe |
| C3 | Time-based Blind | `'; pg_sleep(10)--` | Safe |
| C4 | Error-based | `'` | Generic Error — No Info Leak |
| C5 | Second Order | Store `' OR '1'='1` in DB, retrieve | Safe |

**سكريبت SQLi Test:**
```bash
#!/bin/bash
# SQL Injection Testing

PAYLOADS=(
  "' OR '1'='1"
  "' UNION SELECT null,null,null--"
  "'; DROP TABLE users;--"
  "1' AND 1=1--"
  "1' AND 1=2--"
  "1' OR pg_sleep(5)--"
)

for payload in "${PAYLOADS[@]}"; do
  echo "Testing: $payload"
  curl -s -X GET "https://inspection-portal.gov.sy/api/v1/complaints?search=$payload"     -H "Authorization: Bearer $TOKEN"     -w "Status: %{http_code}\n"
done
```

#### ٣.٤ اختبار XSS (Cross-Site Scripting)

| # | الاختبار | الحمولة | النتيجة |
|---|----------|---------|---------|
| D1 | Reflected XSS | `<script>alert(1)</script>` | Output Encoding |
| D2 | Stored XSS | `<img src=x onerror=alert(1)>` | Output Encoding |
| D3 | DOM-based XSS | `#<img src=x onerror=alert(1)>` | CSP Blocks |
| D4 | Blind XSS | `<script src=https://attacker.com/xss.js>` | CSP Blocks |

#### ٣.٥ اختبار CSRF (Cross-Site Request Forgery)

| # | الاختبار | السيناريو | النتيجة |
|---|----------|-----------|---------|
| E1 | State-changing without token | POST without X-CSRF-Token | 403 Forbidden |
| E2 | Double Submit Cookie | Token mismatch | 403 Forbidden |
| E3 | SameSite Cookie | Cross-origin request | Cookie not sent |

#### ٣.٦ اختبار رفع الملفات (File Upload)

| # | الاختبار | الملف | النتيجة |
|---|----------|-------|---------|
| F1 | Web Shell | shell.php | Rejected — Extension check |
| F2 | Double Extension | file.php.jpg | Rejected |
| F3 | Null Byte | file.php%00.jpg | Rejected |
| F4 | MIME Type Bypass | Change MIME to image/jpeg | MIME + Magic bytes check |
| F5 | Size Limit | 51MB file | Rejected — 50MB limit |
| F6 | Virus Upload | EICAR test file | Rejected — ClamAV |

#### ٣.٧ اختبار التشفير (Cryptography Testing)

| # | الاختبار | الأداة | النتيجة |
|---|----------|--------|---------|
| G1 | TLS Version | testssl.sh | TLS 1.3 only |
| G2 | Cipher Suites | testssl.sh | Strong ciphers only |
| G3 | Certificate Chain | openssl | Valid chain, no self-signed |
| G4 | HSTS | curl | max-age=63072000 |
| G5 | JWT Weakness | jwt_tool | RS256, strong key |
| G6 | Encryption Key Exposure | Memory dump | Keys cleared from memory |
| G7 | IV Reuse | Code review | Unique IV per encryption |

**سكريبت Cryptography Test:**
```bash
#!/bin/bash
# Cryptography Testing

echo "=== TLS/SSL Scan ==="
testssl.sh --severity HIGH --color 3 inspection-portal.gov.sy

echo "=== JWT Analysis ==="
jwt_tool.py -t $ACCESS_TOKEN -rc "$REFRESH_TOKEN"

echo "=== Cookie Security ==="
curl -I -s https://inspection-portal.gov.sy | grep -i "set-cookie"
# Verify: HttpOnly, Secure, SameSite=Strict

echo "=== HSTS Check ==="
curl -s -D - https://inspection-portal.gov.sy | grep -i "strict-transport-security"
```

---

### المرحلة ٤: اختبار منطق الأعمال (Business Logic Testing)

| # | الاختبار | السيناريو | النتيجة |
|---|----------|-----------|---------|
| H1 | Status Workflow Bypass | Jump from received → closed | State machine prevents |
| H2 | Duplicate Signature | Sign already signed report | Rejected |
| H3 | Note Confidentiality | Inspector views confidential note | Based on role + ownership |
| H4 | Complaint Reassignment | Reassign closed complaint | Rejected |
| H5 | Audit Log Tampering | Try to delete audit record | WORM — Impossible |
| H6 | Rate Limit Bypass | Rapid API calls | 429 Too Many Requests |

---

### المرحلة ٥: اختبار الأداء والاستقرار (Performance & Stability)

| # | الاختبار | الأداة | الهدف | النتيجة |
|---|----------|--------|-------|---------|
| I1 | Load Test | Locust | 500 concurrent users | < 2s response time |
| I2 | Stress Test | k6 | 1000 concurrent users | Graceful degradation |
| I3 | Spike Test | k6 | Sudden 10x traffic | No crashes |
| I4 | Endurance Test | JMeter | 8 hours continuous | Memory stable |
| I5 | Database Load | pgbench | 1000 TPS | < 100ms query time |

**سكريبت Load Test:**
```python
# locustfile.py
from locust import HttpUser, task, between

class InspectionUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        # Login
        resp = self.client.post("/api/v1/auth/login", json={
            "username": "inspector_ahmed",
            "password": "test_password"
        })
        self.token = resp.json()["access_token"]

    @task(3)
    def list_complaints(self):
        self.client.get("/api/v1/complaints", headers={
            "Authorization": f"Bearer {self.token}"
        })

    @task(2)
    def view_complaint(self):
        self.client.get("/api/v1/complaints/INS-2026-0891", headers={
            "Authorization": f"Bearer {self.token}"
        })

    @task(1)
    def add_note(self):
        self.client.post("/api/v1/complaints/INS-2026-0891/notes", headers={
            "Authorization": f"Bearer {self.token}"
        }, json={
            "content": "Test note from load test",
            "note_type": "finding"
        })
```

---

## ٣. قالب تقرير الاختبار

```
=================================================================
تقرير اختبار اختراق — بوابة الرقابة والتفتيش
Penetration Test Report — Inspection Portal
=================================================================

تاريخ الاختبار: [YYYY-MM-DD]
فريق الاختبار: [الاسم]
الإصدار: 1.0
التصنيف: سري — وزارة الإعلام

-----------------------------------------------------------------
١. ملخص تنفيذي
-----------------------------------------------------------------
- المخاطر العالية (Critical): 0
- المخاطر المتوسطة (High): 0
- المخاطر المنخفضة (Medium): 0
- الملاحظات (Low): 0
- النتيجة: ✅ اجتاز جميع الاختبارات

-----------------------------------------------------------------
٢. نطاق الاختبار
-----------------------------------------------------------------
- التطبيق: https://inspection-portal.gov.sy
- API: https://inspection-portal.gov.sy/api/v1
- الوقت: 40 ساعة
- الأدوات: OWASP ZAP, Burp Suite, Nmap, testssl.sh

-----------------------------------------------------------------
٣. النتائج التفصيلية
-----------------------------------------------------------------
[جدول بجميع الاختبارات والنتائج]

-----------------------------------------------------------------
٤. التوصيات
-----------------------------------------------------------------
[إن وجدت]

-----------------------------------------------------------------
٥. الملاحق
-----------------------------------------------------------------
- Appendix A: Raw Scan Results
- Appendix B: Screenshots
- Appendix C: Code Review Notes

=================================================================
```

---

## ٤. جدول زمني للاختبار

| اليوم | النشاط | المدة | المسؤول |
|-------|--------|-------|---------|
| ١ | Information Gathering | 4h | فريق الأمان |
| ٢ | Automated Scanning | 8h | أدوات آلية |
| ٣ | Authentication Testing | 6h | مختبر اختراق |
| ٤ | Authorization Testing | 6h | مختبر اختراق |
| ٥ | Input Validation (SQLi, XSS) | 6h | مختبر اختراق |
| ٦ | Business Logic Testing | 4h | مختبر اختراق |
| ٧ | Cryptography Testing | 4h | مختبر اختراق |
| ٨ | Performance Testing | 4h | أدوات آلية |
| ٩ | Reporting & Review | 8h | فريق الأمان |
| ١٠ | Remediation Verification | 4h | فريق الأمان |

**المدة الإجمالية: 10 أيام**

---

**Document Version: 1.0**
**Date: 2026-08-28**
**Classification: Secret — وزارة الإعلام**
