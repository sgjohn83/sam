# Database Design Document
# Smart & Automated Student Admission System

**Version:** 1.0  
**Date:** 2026-04-10  
**Database:** PostgreSQL 15+  
**Cache:** Redis

---

## Table of Contents

1. [Entity Relationship Diagram](#1-entity-relationship-diagram)
2. [Table Definitions](#2-table-definitions)
3. [Enumerations](#3-enumerations)
4. [Relationships & Cardinality](#4-relationships--cardinality)
5. [Indexes](#5-indexes)
6. [Constraints & Business Rules](#6-constraints--business-rules)
7. [JSON Field Schemas](#7-json-field-schemas)
8. [Redis Cache Design](#8-redis-cache-design)
9. [Data Lifecycle & Retention](#9-data-lifecycle--retention)
10. [Migration Strategy](#10-migration-strategy)

---

## 1. Entity Relationship Diagram

```
┌─────────────────────┐
│        User         │
│─────────────────────│
│ id (PK, UUID)       │
│ email (UNIQUE)      │
│ full_name           │
│ role (ENUM)         │
│ google_sso_id       │
│ phone_number        │
│ is_active           │
│ created_at          │
│ updated_at          │
│ last_login          │
└────────┬────────────┘
         │
         │ 1:1
         ▼
┌─────────────────────────┐        ┌──────────────────────────┐
│    StudentProfile       │        │     AgentProfile         │
│─────────────────────────│        │──────────────────────────│
│ id (PK, UUID)           │        │ id (PK, UUID)            │
│ user_id (FK, UNIQUE)    │        │ user_id (FK, UNIQUE)     │
│ date_of_birth           │        │ agency_name              │
│ gender (ENUM)           │        │ contact_person           │
│ mobile_number           │        │ commission_rate          │
│ address (JSON)          │        │ commission_type (ENUM)   │
│ category (ENUM)         │        │ is_active                │
│ domicile_state          │        │ created_at               │
│ agent_id (FK, nullable) │───────►│ updated_at               │
│ created_at              │        └────────────┬─────────────┘
│ updated_at              │                     │
└────┬──────────┬─────────┘                     │ 1:N
     │          │                               ▼
     │          │                    ┌──────────────────────┐
     │          │                    │    Commission        │
     │          │                    │──────────────────────│
     │          │                    │ id (PK, UUID)        │
     │ 1:1      │ 1:N               │ agent_id (FK)        │
     │          │                    │ application_id (FK)  │
     ▼          ▼                    │ amount               │
┌────────────────────┐               │ status (ENUM)        │
│   Application      │               │ calculated_at        │
│────────────────────│               │ updated_at           │
│ id (PK, UUID)      │◄──────────────└──────────────────────┘
│ student_id (FK, UQ)│
│ application_number │    ┌────────────────────────────────────┐
│ status (ENUM)      │    │          Document                  │
│ branch_preferences │    │────────────────────────────────────│
│   (JSON)           │    │ id (PK, UUID)                      │
│ submitted_at       │    │ student_id (FK)                    │
│ is_locked          │    │ document_type (ENUM)               │
│ locked_at          │    │ file_path                          │
│ locked_by (FK)     │    │ file_name                          │
│ allocated_branch   │    │ file_size_bytes                    │
│   (FK, nullable)   │    │ mime_type                          │
│ allocated_quota    │    │ upload_version                     │
│   (ENUM, nullable) │    │ status (ENUM)                      │
│ fee_amount         │    │ rejection_reason                   │
│ fee_paid           │    │ uploaded_at                        │
│ fee_paid_at        │    │ uploaded_by (FK)                   │
│ admitted_at        │    └──────────────┬─────────────────────┘
│ created_at         │                   │
│ updated_at         │                   │ 1:N
└────────────────────┘                   ▼
                              ┌──────────────────────────────┐
                              │        OCRResult             │
                              │──────────────────────────────│
                              │ id (PK, UUID)                │
                              │ document_id (FK)             │
                              │ raw_text (TEXT)              │
                              │ extracted_fields (JSON)      │
                              │ confidence_scores (JSON)     │
                              │ overall_confidence (FLOAT)   │
                              │ processing_duration_ms (INT) │
                              │ ocr_version (INT)            │
                              │ llm_model_used (VARCHAR)     │
                              │ created_at                   │
                              └──────────────────────────────┘

┌────────────────────┐     ┌──────────────────────────┐
│      Branch        │     │     AcademicYear         │
│────────────────────│     │──────────────────────────│
│ id (PK, UUID)      │     │ id (PK, UUID)            │
│ name               │     │ year_label (e.g. 2026-27)│
│ code (UNIQUE)      │     │ start_date               │
│ is_active          │     │ end_date                 │
│ created_at         │     │ admission_open_date      │
│ updated_at         │     │ admission_close_date     │
└────────┬───────────┘     │ is_current               │
         │                 │ created_at               │
         │ 1:N             └────────────┬─────────────┘
         ▼                              │
┌─────────────────────────┐             │
│      SeatMatrix         │             │
│─────────────────────────│             │
│ id (PK, UUID)           │             │
│ branch_id (FK)          │◄────────────┘
│ academic_year_id (FK)   │
│ quota (ENUM)            │
│ total_seats (INT)       │
│ allocated_seats (INT)   │
│ created_at              │
│ updated_at              │
│ UNIQUE(branch, year,    │
│        quota)           │
└─────────────────────────┘

┌────────────────────────────┐     ┌──────────────────────────────┐
│       FeeStructure         │     │        AuditLog              │
│────────────────────────────│     │──────────────────────────────│
│ id (PK, UUID)              │     │ id (PK, UUID)                │
│ branch_id (FK)             │     │ user_id (FK)                 │
│ academic_year_id (FK)      │     │ application_id (FK, nullable)│
│ fee_type (ENUM)            │     │ action (VARCHAR)             │
│ amount (DECIMAL)           │     │ entity_type (VARCHAR)        │
│ is_active                  │     │ entity_id (UUID, nullable)   │
│ created_at                 │     │ field_name (nullable)        │
│ updated_at                 │     │ old_value (TEXT, nullable)   │
│ UNIQUE(branch, year, type) │     │ new_value (TEXT, nullable)   │
└────────────────────────────┘     │ ip_address (INET)            │
                                   │ user_agent (TEXT, nullable)   │
┌────────────────────────────┐     │ timestamp                    │
│     FeeConcession          │     └──────────────────────────────┘
│────────────────────────────│
│ id (PK, UUID)              │     ┌──────────────────────────────┐
│ application_id (FK)        │     │      Notification            │
│ original_amount            │     │──────────────────────────────│
│ concession_amount          │     │ id (PK, UUID)                │
│ reason (TEXT)              │     │ recipient_id (FK → User)     │
│ requested_by (FK → User)   │     │ notification_type (ENUM)     │
│ approved_by (FK, nullable) │     │ subject                      │
│ status (ENUM)              │     │ body (TEXT)                  │
│ requested_at               │     │ status (ENUM)                │
│ decided_at                 │     │ retry_count (INT)            │
│ updated_at                 │     │ sent_at (nullable)           │
└────────────────────────────┘     │ created_at                   │
                                   └──────────────────────────────┘
┌─────────────────────────────┐
│       OTPVerification       │     ┌──────────────────────────────┐
│─────────────────────────────│     │       ERPSyncLog             │
│ id (PK, UUID)               │     │──────────────────────────────│
│ email                       │     │ id (PK, UUID)                │
│ otp_code (VARCHAR 6)        │     │ triggered_by (FK → User)     │
│ is_verified                 │     │ sync_type (ENUM)             │
│ attempts (INT)              │     │ total_records (INT)          │
│ expires_at                  │     │ success_count (INT)          │
│ created_at                  │     │ error_count (INT)            │
└─────────────────────────────┘     │ errors (JSON, nullable)      │
                                    │ started_at                   │
                                    │ completed_at (nullable)      │
                                    │ status (ENUM)                │
                                    └──────────────────────────────┘
```

---

## 2. Table Definitions

### 2.1 `users`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | Primary key |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | Login email |
| `full_name` | VARCHAR(255) | NOT NULL | Display name |
| `role` | VARCHAR(30) | NOT NULL, CHECK(role IN enum) | System role |
| `google_sso_id` | VARCHAR(255) | UNIQUE, nullable | Google OAuth subject ID |
| `phone_number` | VARCHAR(15) | nullable | Contact number |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Soft delete flag |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Auto-updated |
| `last_login` | TIMESTAMPTZ | nullable | Last successful login |

---

### 2.2 `student_profiles`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `user_id` | UUID | FK → users(id), UNIQUE, NOT NULL | One profile per user |
| `date_of_birth` | DATE | NOT NULL | |
| `gender` | VARCHAR(10) | NOT NULL, CHECK(gender IN enum) | |
| `mobile_number` | VARCHAR(15) | NOT NULL | |
| `address` | JSONB | NOT NULL | {street, city, state, pincode} |
| `category` | VARCHAR(20) | NOT NULL, CHECK(category IN enum) | Reservation category |
| `domicile_state` | VARCHAR(100) | NOT NULL | |
| `agent_id` | UUID | FK → agent_profiles(id), nullable | Referring agent |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

---

### 2.3 `applications`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `student_id` | UUID | FK → student_profiles(id), UNIQUE, NOT NULL | One application per student |
| `application_number` | VARCHAR(20) | UNIQUE, NOT NULL | Human-readable (e.g. ADM-2026-00001) |
| `status` | VARCHAR(30) | NOT NULL, DEFAULT 'draft' | Application lifecycle state |
| `branch_preferences` | JSONB | nullable | Ordered list of branch UUIDs |
| `submitted_at` | TIMESTAMPTZ | nullable | |
| `is_locked` | BOOLEAN | NOT NULL, DEFAULT FALSE | Verification lock |
| `locked_at` | TIMESTAMPTZ | nullable | |
| `locked_by` | UUID | FK → users(id), nullable | Staff who locked |
| `claimed_by` | UUID | FK → users(id), nullable | Staff currently reviewing |
| `claimed_at` | TIMESTAMPTZ | nullable | Auto-expires after 30 min |
| `allocated_branch_id` | UUID | FK → branches(id), nullable | Allocated branch |
| `allocated_quota` | VARCHAR(20) | nullable | Quota used for allocation |
| `fee_amount` | DECIMAL(10,2) | nullable | Total fee due |
| `fee_concession` | DECIMAL(10,2) | DEFAULT 0 | Approved concession |
| `fee_paid` | BOOLEAN | NOT NULL, DEFAULT FALSE | |
| `fee_paid_at` | TIMESTAMPTZ | nullable | |
| `payment_proof_path` | VARCHAR(500) | nullable | Uploaded receipt path |
| `admitted_at` | TIMESTAMPTZ | nullable | |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Application Number Generation:**
```sql
-- Format: ADM-{YEAR}-{SEQUENCE}
-- Example: ADM-2026-00001
CREATE SEQUENCE application_number_seq START 1;

-- Generated on insert via Django or trigger:
-- 'ADM-' || EXTRACT(YEAR FROM NOW()) || '-' || LPAD(nextval('application_number_seq')::text, 5, '0')
```

---

### 2.4 `documents`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `student_id` | UUID | FK → student_profiles(id), NOT NULL | |
| `document_type` | VARCHAR(20) | NOT NULL, CHECK IN enum | aadhar, marksheet_10, etc. |
| `file_path` | VARCHAR(500) | NOT NULL | Server file system path |
| `file_name` | VARCHAR(255) | NOT NULL | Original upload filename |
| `file_size_bytes` | INTEGER | NOT NULL | For validation (max 5MB) |
| `mime_type` | VARCHAR(50) | NOT NULL | image/jpeg, image/png, application/pdf |
| `upload_version` | INTEGER | NOT NULL, DEFAULT 1 | Increments on re-upload |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'processing' | Document review state |
| `rejection_reason` | TEXT | nullable | Required when status = rejected |
| `uploaded_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `uploaded_by` | UUID | FK → users(id), NOT NULL | Student or Agent user |

**Constraint:** `UNIQUE(student_id, document_type)` — one active document per type per student (re-upload replaces in-place via version increment).

---

### 2.5 `ocr_results`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `document_id` | UUID | FK → documents(id), NOT NULL | |
| `raw_text` | TEXT | NOT NULL | Full Google Vision output |
| `extracted_fields` | JSONB | NOT NULL | Pydantic-validated structured data |
| `confidence_scores` | JSONB | NOT NULL | Per-field confidence {field: 0.0–1.0} |
| `overall_confidence` | FLOAT | NOT NULL | Average of all field confidences |
| `processing_duration_ms` | INTEGER | NOT NULL | OCR pipeline latency |
| `ocr_version` | INTEGER | NOT NULL | Matches document.upload_version |
| `llm_model_used` | VARCHAR(100) | nullable | LLM identifier for traceability |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Constraint:** `UNIQUE(document_id, ocr_version)` — one OCR result per version.

---

### 2.6 `branches`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `name` | VARCHAR(200) | NOT NULL | e.g. "Computer Science and Engineering" |
| `code` | VARCHAR(10) | UNIQUE, NOT NULL | e.g. "CSE" |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

---

### 2.7 `academic_years`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `year_label` | VARCHAR(10) | UNIQUE, NOT NULL | e.g. "2026-27" |
| `start_date` | DATE | NOT NULL | |
| `end_date` | DATE | NOT NULL | |
| `admission_open_date` | DATE | NOT NULL | |
| `admission_close_date` | DATE | NOT NULL | |
| `is_current` | BOOLEAN | NOT NULL, DEFAULT FALSE | Only one row TRUE at a time |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Constraint:** Partial unique index — `UNIQUE(is_current) WHERE is_current = TRUE` — enforces exactly one current academic year.

---

### 2.8 `seat_matrix`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `branch_id` | UUID | FK → branches(id), NOT NULL | |
| `academic_year_id` | UUID | FK → academic_years(id), NOT NULL | |
| `quota` | VARCHAR(20) | NOT NULL, CHECK IN enum | |
| `total_seats` | INTEGER | NOT NULL, CHECK >= 0 | |
| `allocated_seats` | INTEGER | NOT NULL, DEFAULT 0, CHECK >= 0 | |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Constraints:**
- `UNIQUE(branch_id, academic_year_id, quota)`
- `CHECK(allocated_seats <= total_seats)` — prevents over-allocation at DB level

---

### 2.9 `fee_structures`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `branch_id` | UUID | FK → branches(id), NOT NULL | |
| `academic_year_id` | UUID | FK → academic_years(id), NOT NULL | |
| `fee_type` | VARCHAR(30) | NOT NULL | tuition, hostel, lab, library, etc. |
| `amount` | DECIMAL(10,2) | NOT NULL, CHECK > 0 | |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Constraint:** `UNIQUE(branch_id, academic_year_id, fee_type)`

---

### 2.10 `fee_concessions`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `application_id` | UUID | FK → applications(id), NOT NULL | |
| `original_amount` | DECIMAL(10,2) | NOT NULL | Total fee before concession |
| `concession_amount` | DECIMAL(10,2) | NOT NULL | Amount waived |
| `reason` | TEXT | NOT NULL | Justification |
| `requested_by` | UUID | FK → users(id), NOT NULL | Officer who raised |
| `approved_by` | UUID | FK → users(id), nullable | Principal who approved |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | pending, approved, rejected |
| `requested_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `decided_at` | TIMESTAMPTZ | nullable | |

---

### 2.11 `agent_profiles`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `user_id` | UUID | FK → users(id), UNIQUE, NOT NULL | |
| `agency_name` | VARCHAR(255) | NOT NULL | |
| `contact_person` | VARCHAR(255) | nullable | |
| `commission_rate` | DECIMAL(5,2) | NOT NULL | Rate value |
| `commission_type` | VARCHAR(15) | NOT NULL | flat or percentage |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

---

### 2.12 `commissions`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `agent_id` | UUID | FK → agent_profiles(id), NOT NULL | |
| `application_id` | UUID | FK → applications(id), UNIQUE, NOT NULL | One commission per application |
| `amount` | DECIMAL(10,2) | NOT NULL | Calculated commission |
| `status` | VARCHAR(15) | NOT NULL, DEFAULT 'pending' | pending, approved, paid |
| `calculated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

---

### 2.13 `audit_logs`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `user_id` | UUID | FK → users(id), NOT NULL | Who performed the action |
| `application_id` | UUID | FK → applications(id), nullable | Related application |
| `action` | VARCHAR(100) | NOT NULL | e.g. "field_edit", "lock", "allocate_seat" |
| `entity_type` | VARCHAR(50) | NOT NULL | Table name affected |
| `entity_id` | UUID | nullable | Row affected |
| `field_name` | VARCHAR(100) | nullable | Column changed |
| `old_value` | TEXT | nullable | Previous value (serialized) |
| `new_value` | TEXT | nullable | New value (serialized) |
| `ip_address` | INET | NOT NULL | Client IP |
| `user_agent` | TEXT | nullable | Browser/client identifier |
| `timestamp` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Note:** This table is append-only — no UPDATE or DELETE allowed (enforced via Django model and DB permissions).

---

### 2.14 `notifications`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `recipient_id` | UUID | FK → users(id), NOT NULL | |
| `notification_type` | VARCHAR(50) | NOT NULL | otp, status_change, reupload, fee, etc. |
| `subject` | VARCHAR(255) | NOT NULL | Email subject line |
| `body` | TEXT | NOT NULL | Email body (HTML) |
| `status` | VARCHAR(15) | NOT NULL, DEFAULT 'pending' | pending, sent, failed |
| `retry_count` | INTEGER | NOT NULL, DEFAULT 0 | Max 3 retries |
| `error_message` | TEXT | nullable | Last failure reason |
| `sent_at` | TIMESTAMPTZ | nullable | |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

---

### 2.15 `otp_verifications`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `email` | VARCHAR(255) | NOT NULL | |
| `otp_code` | VARCHAR(6) | NOT NULL | 6-digit code |
| `is_verified` | BOOLEAN | NOT NULL, DEFAULT FALSE | |
| `attempts` | INTEGER | NOT NULL, DEFAULT 0 | Max 5 attempts |
| `expires_at` | TIMESTAMPTZ | NOT NULL | 10 minutes from creation |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

---

### 2.16 `erp_sync_logs`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | |
| `triggered_by` | UUID | FK → users(id), NOT NULL | Admin who triggered |
| `sync_type` | VARCHAR(20) | NOT NULL | academic, library, hostel |
| `total_records` | INTEGER | NOT NULL | |
| `success_count` | INTEGER | NOT NULL, DEFAULT 0 | |
| `error_count` | INTEGER | NOT NULL, DEFAULT 0 | |
| `errors` | JSONB | nullable | [{student_id, error_msg}] |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'running' | running, completed, failed |
| `started_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `completed_at` | TIMESTAMPTZ | nullable | |

---

## 3. Enumerations

```sql
-- User roles
CREATE TYPE user_role AS ENUM (
    'student', 'verification_staff', 'admission_officer',
    'agent', 'principal', 'admin'
);

-- Gender
CREATE TYPE gender_type AS ENUM ('male', 'female', 'other');

-- Student category (reservation)
CREATE TYPE student_category AS ENUM ('general', 'obc', 'sc', 'st');

-- Document types
CREATE TYPE document_type AS ENUM (
    'aadhar', 'marksheet_10', 'marksheet_12', 'rank_card'
);

-- Document status
CREATE TYPE document_status AS ENUM (
    'processing', 'extracted', 'verified', 'rejected'
);

-- Application status
CREATE TYPE application_status AS ENUM (
    'draft', 'submitted', 'under_verification', 'verified',
    'seat_allocated', 'fee_pending', 'admitted', 'rejected'
);

-- Seat quota
CREATE TYPE quota_type AS ENUM (
    'general', 'obc', 'sc', 'st', 'management', 'nri'
);

-- Commission type
CREATE TYPE commission_type AS ENUM ('flat', 'percentage');

-- Fee type
CREATE TYPE fee_type AS ENUM (
    'tuition', 'hostel', 'lab', 'library', 'exam',
    'transport', 'other'
);

-- Concession status
CREATE TYPE concession_status AS ENUM ('pending', 'approved', 'rejected');

-- Commission status
CREATE TYPE commission_status AS ENUM ('pending', 'approved', 'paid');

-- Notification status
CREATE TYPE notification_status AS ENUM ('pending', 'sent', 'failed');

-- ERP sync type
CREATE TYPE erp_sync_type AS ENUM ('academic', 'library', 'hostel');

-- ERP sync status
CREATE TYPE erp_sync_status AS ENUM ('running', 'completed', 'failed');
```

**Django Implementation:** These will be defined as `TextChoices` classes in each model rather than PostgreSQL-native enums, for easier migration management:

```python
class ApplicationStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    SUBMITTED = 'submitted', 'Submitted'
    UNDER_VERIFICATION = 'under_verification', 'Under Verification'
    VERIFIED = 'verified', 'Verified'
    SEAT_ALLOCATED = 'seat_allocated', 'Seat Allocated'
    FEE_PENDING = 'fee_pending', 'Fee Pending'
    ADMITTED = 'admitted', 'Admitted'
    REJECTED = 'rejected', 'Rejected'
```

---

## 4. Relationships & Cardinality

```
User ──────────── 1:1 ──── StudentProfile
User ──────────── 1:1 ──── AgentProfile
StudentProfile ── 1:1 ──── Application
StudentProfile ── 1:N ──── Document
StudentProfile ── N:1 ──── AgentProfile (nullable)
Document ──────── 1:N ──── OCRResult (versioned)
Application ───── N:1 ──── Branch (allocated, nullable)
Application ───── 1:N ──── FeeConcession
Application ───── 1:1 ──── Commission (via agent)
Branch ────────── 1:N ──── SeatMatrix
Branch ────────── 1:N ──── FeeStructure
AcademicYear ──── 1:N ──── SeatMatrix
AcademicYear ──── 1:N ──── FeeStructure
AgentProfile ──── 1:N ──── Commission
AgentProfile ──── 1:N ──── StudentProfile
User ──────────── 1:N ──── AuditLog
User ──────────── 1:N ──── Notification
Application ───── 1:N ──── AuditLog
```

---

## 5. Indexes

### Primary Queries and Their Indexes

```sql
-- Verification queue: sort by confidence, filter by status
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_status_submitted
    ON applications(status, submitted_at)
    WHERE status = 'submitted';

-- OCR confidence-based queue sorting
CREATE INDEX idx_ocr_results_confidence
    ON ocr_results(overall_confidence);
CREATE INDEX idx_ocr_results_document_version
    ON ocr_results(document_id, ocr_version DESC);

-- Document lookup per student
CREATE INDEX idx_documents_student_type
    ON documents(student_id, document_type);

-- Seat availability lookup
CREATE INDEX idx_seat_matrix_branch_year
    ON seat_matrix(branch_id, academic_year_id);

-- Audit log queries
CREATE INDEX idx_audit_logs_application
    ON audit_logs(application_id, timestamp DESC);
CREATE INDEX idx_audit_logs_user
    ON audit_logs(user_id, timestamp DESC);
CREATE INDEX idx_audit_logs_timestamp
    ON audit_logs(timestamp DESC);

-- Agent's students
CREATE INDEX idx_student_profiles_agent
    ON student_profiles(agent_id)
    WHERE agent_id IS NOT NULL;

-- Notification retry queue
CREATE INDEX idx_notifications_pending
    ON notifications(status, retry_count)
    WHERE status = 'pending' AND retry_count < 3;

-- Commission per agent
CREATE INDEX idx_commissions_agent
    ON commissions(agent_id, status);

-- OTP lookup
CREATE INDEX idx_otp_email_active
    ON otp_verifications(email, expires_at DESC)
    WHERE is_verified = FALSE;

-- Application number search
CREATE INDEX idx_applications_number
    ON applications(application_number);

-- Current academic year (partial unique)
CREATE UNIQUE INDEX idx_academic_year_current
    ON academic_years(is_current)
    WHERE is_current = TRUE;

-- Application claim timeout
CREATE INDEX idx_applications_claimed
    ON applications(claimed_by, claimed_at)
    WHERE claimed_by IS NOT NULL;
```

---

## 6. Constraints & Business Rules

### Database-Level Constraints

```sql
-- Seat matrix: prevent over-allocation
ALTER TABLE seat_matrix
    ADD CONSTRAINT chk_seats_not_over_allocated
    CHECK (allocated_seats <= total_seats);

ALTER TABLE seat_matrix
    ADD CONSTRAINT chk_seats_non_negative
    CHECK (total_seats >= 0 AND allocated_seats >= 0);

-- Document file size: max 5MB
ALTER TABLE documents
    ADD CONSTRAINT chk_file_size_limit
    CHECK (file_size_bytes <= 5242880);

-- OTP: max 5 attempts
ALTER TABLE otp_verifications
    ADD CONSTRAINT chk_otp_max_attempts
    CHECK (attempts <= 5);

-- Notification: max 3 retries
ALTER TABLE notifications
    ADD CONSTRAINT chk_max_retries
    CHECK (retry_count <= 3);

-- Fee amounts must be positive
ALTER TABLE fee_structures
    ADD CONSTRAINT chk_fee_positive
    CHECK (amount > 0);

-- Concession cannot exceed original amount
ALTER TABLE fee_concessions
    ADD CONSTRAINT chk_concession_limit
    CHECK (concession_amount <= original_amount);

-- OCR confidence range
ALTER TABLE ocr_results
    ADD CONSTRAINT chk_confidence_range
    CHECK (overall_confidence >= 0.0 AND overall_confidence <= 1.0);
```

### Application-Level Business Rules (Django)

| Rule | Enforcement |
|------|-------------|
| Student can submit only after all 4 required documents are uploaded | Django model validation on `Application.submit()` |
| Locked applications cannot be edited by non-admin users | Django permission check + model `save()` override |
| Seat allocation decrements `allocated_seats` atomically | `F()` expression with `SELECT ... FOR UPDATE` |
| Claimed applications auto-release after 30 minutes | Periodic task or query filter: `WHERE claimed_at < NOW() - INTERVAL '30 min'` |
| Application number is generated on first submission only | Django `pre_save` signal or `save()` override |
| Commission is calculated only when application reaches `admitted` status | Django signal on application status change |

### Seat Allocation — Concurrency Safety

```python
# Django: Atomic seat allocation with row-level locking
from django.db import transaction
from django.db.models import F

def allocate_seat(application, branch, quota):
    with transaction.atomic():
        seat = SeatMatrix.objects.select_for_update().get(
            branch=branch,
            academic_year=current_year,
            quota=quota
        )
        if seat.allocated_seats >= seat.total_seats:
            raise SeatUnavailableError()

        seat.allocated_seats = F('allocated_seats') + 1
        seat.save(update_fields=['allocated_seats', 'updated_at'])

        application.allocated_branch = branch
        application.allocated_quota = quota
        application.status = 'seat_allocated'
        application.save()
```

---

## 7. JSON Field Schemas

### 7.1 `student_profiles.address`
```json
{
    "street": "1-2-3, Kukatpally",
    "city": "Hyderabad",
    "state": "Telangana",
    "pincode": "500072"
}
```

### 7.2 `applications.branch_preferences`
```json
["uuid-cse", "uuid-ece", "uuid-eee"]
```

### 7.3 `ocr_results.extracted_fields` (Aadhar example)
```json
{
    "name": "Rajesh Kumar",
    "date_of_birth": "1998-05-15",
    "gender": "male",
    "aadhar_number": "1234 5678 9012",
    "address": "1-2-3, Kukatpally, Hyderabad, Telangana 500072"
}
```

### 7.4 `ocr_results.extracted_fields` (Marksheet example)
```json
{
    "student_name": "Rajesh Kumar",
    "school_name": "Delhi Public School",
    "board": "CBSE",
    "year_of_passing": 2016,
    "subjects": [
        {"subject": "Mathematics", "max_marks": 100, "obtained_marks": 92},
        {"subject": "Physics", "max_marks": 100, "obtained_marks": 88},
        {"subject": "Chemistry", "max_marks": 100, "obtained_marks": 85}
    ],
    "total_marks": 500,
    "obtained_marks": 445,
    "percentage": 89.0
}
```

### 7.5 `ocr_results.confidence_scores`
```json
{
    "name": 0.97,
    "date_of_birth": 0.93,
    "gender": 0.99,
    "aadhar_number": 0.85,
    "address": 0.72
}
```

### 7.6 `erp_sync_logs.errors`
```json
[
    {"student_id": "uuid-123", "error": "Duplicate roll number in ERP"},
    {"student_id": "uuid-456", "error": "Missing hostel preference"}
]
```

---

## 8. Redis Cache Design

| Key Pattern | Value | TTL | Purpose |
|-------------|-------|-----|---------|
| `seats:{branch_id}:{quota}` | `{total: 60, allocated: 42}` | 10s | Real-time seat availability display |
| `session:{session_id}` | User session data (JSON) | 8h | Session management |
| `otp:{email}` | `{code, attempts, expires}` | 10m | Rate-limit OTP generation |
| `ocr:processing:{document_id}` | `"in_progress"` | 5m | Prevent duplicate OCR submissions |
| `dashboard:kpi` | Aggregated KPI JSON | 30s | Principal dashboard cache |
| `app:claimed:{application_id}` | `{staff_id, claimed_at}` | 30m | Verification claim lock |

### Cache Invalidation Strategy

| Event | Keys Invalidated |
|-------|------------------|
| Seat allocated/revoked | `seats:{branch_id}:{quota}` |
| Application status change | `dashboard:kpi` |
| Verification claim/release | `app:claimed:{application_id}` |
| OTP verified | `otp:{email}` |

---

## 9. Data Lifecycle & Retention

| Data | Retention | Action |
|------|-----------|--------|
| `otp_verifications` | 24 hours after expiry | Periodic cleanup (Django management command) |
| `audit_logs` | 3 years | Archive to cold storage after 1 year |
| `notifications` | 6 months | Purge sent notifications older than 6 months |
| `ocr_results` (old versions) | Indefinite | Retain for audit trail |
| `documents` (file storage) | Duration of academic year + 1 year | Archive after admission cycle closes |
| Database backups | 30 days | Daily automated backup with 30-day rotation |
| `erp_sync_logs` | 2 years | Archive after review |

### Backup Strategy

```
Daily:   Full PostgreSQL backup (pg_dump) at 2:00 AM
         Retained for 30 days
Weekly:  Copy to separate local drive
Monthly: Archived to external storage
```

---

## 10. Migration Strategy

### Django Migration Order (respecting FK dependencies)

```
1. academic_years     ← no dependencies
2. branches           ← no dependencies
3. users              ← no dependencies
4. agent_profiles     ← depends on users
5. student_profiles   ← depends on users, agent_profiles
6. applications       ← depends on student_profiles, branches, users
7. documents          ← depends on student_profiles, users
8. ocr_results        ← depends on documents
9. seat_matrix        ← depends on branches, academic_years
10. fee_structures    ← depends on branches, academic_years
11. fee_concessions   ← depends on applications, users
12. commissions       ← depends on agent_profiles, applications
13. audit_logs        ← depends on users, applications
14. notifications     ← depends on users
15. otp_verifications ← no dependencies
16. erp_sync_logs     ← depends on users
```

### Initial Data Seeding

```
1. Create System Admin user
2. Create AcademicYear (current year)
3. Create Branches (CSE, ECE, EEE, ME, CE, etc.)
4. Create SeatMatrix (per branch × quota)
5. Create FeeStructures (per branch × fee_type)
```

---

## Appendix: Table Summary

| # | Table | Rows (Estimated per year) | Growth Rate |
|---|-------|---------------------------|-------------|
| 1 | users | ~5,000 | Per admission cycle |
| 2 | student_profiles | ~4,500 | Per cycle |
| 3 | applications | ~4,500 | Per cycle |
| 4 | documents | ~18,000 (4 per student) | Per cycle |
| 5 | ocr_results | ~20,000 (includes re-uploads) | Per cycle |
| 6 | branches | ~10 | Static |
| 7 | academic_years | 1 | Per year |
| 8 | seat_matrix | ~60 (10 branches × 6 quotas) | Per year |
| 9 | fee_structures | ~70 | Per year |
| 10 | fee_concessions | ~200 | Per cycle |
| 11 | agent_profiles | ~50 | Slow growth |
| 12 | commissions | ~1,000 | Per cycle |
| 13 | audit_logs | ~100,000 | High — append-only |
| 14 | notifications | ~30,000 | Per cycle |
| 15 | otp_verifications | ~10,000 | Per cycle (auto-purged) |
| 16 | erp_sync_logs | ~10 | Per cycle |

---

*Document Version: 1.0 — Finalized 2026-04-10*
