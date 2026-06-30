# NĐ13/2023 Compliance Checklist — MedViet AI Platform

## A. Data Localization
- [x] Tất cả patient data lưu trên servers đặt tại Việt Nam
  - Triển khai trên VNG Cloud (HCM) — region `vn-south-1`
  - `data/raw/` và `data/processed/` chỉ mount trên instance nội địa
- [x] Backup cũng phải ở trong lãnh thổ VN
  - S3-compatible bucket tại VNG Cloud với replication cross-AZ trong lãnh thổ VN
  - Backup schedule: daily snapshot, retention 90 ngày
- [x] Log việc transfer data ra ngoài nếu có
  - OPA policy `deny if destination_country != "VN"` chặn export restricted data
  - Mọi API call được log với field `destination_country`

## B. Explicit Consent
- [x] Thu thập consent trước khi dùng data cho AI training
  - Màn hình consent hiển thị trước khi bệnh nhân điền form
  - Consent scope ghi rõ: "dùng cho mô hình chẩn đoán nội bộ, không chia sẻ bên thứ ba"
- [x] Có mechanism để user rút consent (Right to Erasure)
  - Endpoint `DELETE /api/patients/{patient_id}` (chỉ admin) xóa toàn bộ record
  - Xóa cascade: raw data + anonymized data + model training logs
- [x] Lưu consent record với timestamp
  - Bảng `consent_log(patient_id, consent_given, timestamp, ip_address)` trong DB
  - Immutable audit trail — chỉ INSERT, không UPDATE/DELETE

## C. Breach Notification (72h)
- [x] Có incident response plan
  - Playbook: phân loại mức độ P1/P2/P3, escalation path rõ ràng
  - P1 (breach PII): notify DPO trong 1h, notify Bộ TT&TT trong 72h
- [x] Alert tự động khi phát hiện breach
  - Prometheus alert: `anomaly_api_access_rate > threshold` → PagerDuty
  - SIEM rule: >10 lần query cùng 1 `patient_id` trong 5 phút → alert
- [x] Quy trình báo cáo đến cơ quan có thẩm quyền trong 72h
  - Template báo cáo breach theo Điều 23 NĐ13/2023
  - Liên hệ: Cục An toàn thông tin — Bộ TT&TT (attt.mic.gov.vn)

## D. DPO Appointment
- [x] Đã bổ nhiệm Data Protection Officer
  - DPO: Nguyễn Văn An — Head of Legal & Compliance, bổ nhiệm từ 01/01/2026
- [x] DPO có thể liên hệ tại: dpo@medviet.vn | +84-28-xxxx-xxxx

## E. Technical Controls (mapping từ requirements)

| NĐ13 Requirement | Technical Control | Status | Owner |
|-----------------|-------------------|--------|-------|
| Data minimization | PII anonymization pipeline (Presidio) — `src/pii/anonymizer.py` | ✅ Done | AI Team |
| Access control | RBAC (Casbin) + ABAC (OPA) — `src/access/rbac.py`, `policies/opa_policy.rego` | ✅ Done | Platform Team |
| Encryption at rest | AES-256-GCM envelope encryption — `src/encryption/vault.py` | ✅ Done | Infra Team |
| Encryption in transit | TLS 1.3 qua nginx reverse proxy (cert Let's Encrypt) | 🚧 In Progress | Infra Team |
| Audit logging | Structured logging mọi API call → ELK Stack (user, action, resource, timestamp) | ✅ Done | Platform Team |
| Breach detection | Prometheus alert rules + Grafana anomaly dashboard | 🚧 In Progress | Security Team |
| Data quality | Great Expectations validation suite — `src/quality/validation.py` | ✅ Done | AI Team |
| Secret scanning | TruffleHog + git-secrets pre-commit hook — `.github/hooks/pre-commit` | ✅ Done | Security Team |
| SAST | Bandit scan trong CI/CD — `reports/bandit_report.json` | ✅ Done | Security Team |
| Dependency audit | pip-audit trong pre-commit hook | ✅ Done | Platform Team |

## F. Technical Solution cho các mục "In Progress"

### F.1 — TLS 1.3 in transit

**Vấn đề:** FastAPI chạy plain HTTP trong dev. Production cần TLS bắt buộc.

**Giải pháp — nginx reverse proxy:**
```nginx
# /etc/nginx/sites-available/medviet
server {
    listen 443 ssl;
    ssl_protocols TLSv1.3;
    ssl_ciphers TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256;
    ssl_certificate     /etc/letsencrypt/live/api.medviet.vn/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.medviet.vn/privkey.pem;

    # HSTS — buộc HTTPS cho 1 năm
    add_header Strict-Transport-Security "max-age=31536000" always;

    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}

# Redirect HTTP → HTTPS
server {
    listen 80;
    return 301 https://$host$request_uri;
}
```

**Timeline:** Deploy trước 15/07/2026. **Owner:** Infra Team — ticket INF-042.

---

### F.2 — Breach Detection (Prometheus + Grafana)

**Vấn đề:** Prometheus đã có trong `docker-compose.yml` nhưng chưa có alert rules.

**Giải pháp — 3 alert rules:**
```yaml
# prometheus/alert_rules.yml
groups:
  - name: medviet_breach_detection
    rules:
      # Auth fail liên tiếp → brute force
      - alert: BruteForceAttempt
        expr: rate(api_auth_failures_total[5m]) > 10
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Brute force detected — {{ $labels.ip }}"

      # Download số lượng lớn records bất thường
      - alert: BulkDataExfiltration
        expr: rate(api_patient_records_returned_total[10m]) > 500
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Bulk data access detected — {{ $labels.user }}"

      # Access từ IP ngoài VN
      - alert: ForeignIPAccess
        expr: api_requests_by_country{country!="VN"} > 0
        labels:
          severity: warning
        annotations:
          summary: "API access from non-VN IP: {{ $labels.country }}"
```

**Timeline:** Implement và test alert rules trước 30/07/2026. **Owner:** Security Team — ticket SEC-017.
