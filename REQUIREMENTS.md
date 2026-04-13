# Software Requirements Specification (SRS)
# Smart & Automated Student Admission System

**Version:** 1.0  
**Date:** 2026-04-10  
**Status:** Finalized

---

## Table of Contents

1. [Functional Requirements](#1-functional-requirements)
2. [Non-Functional Requirements](#2-non-functional-requirements)
3. [Data Models](#3-data-models)
4. [API Endpoints](#4-api-endpoints)
5. [OCR Pipeline Specification](#5-ocr-pipeline-specification)
6. [Notification Specification](#6-notification-specification)
7. [ERP Sync Specification](#7-erp-sync-specification)

---

## 1. Functional Requirements

### 1.1 Authentication & User Management

| ID | Requirement |
|----|-------------|
| AUTH-01 | System shall support Google SSO as the sole authentication method |
| AUTH-02 | Students shall additionally register via email OTP before linking Google SSO |
| AUTH-03 | Each user account shall have exactly one role: Student, Verification Staff, Admission Officer, Agent, Principal, System Admin |
| AUTH-04 | System Admin shall assign and revoke roles via the admin panel |
| AUTH-05 | Sessions shall expire after 8 hours of inactivity |
| AUTH-06 | All role-based access control shall be enforced server-side on every API request |

---

### 1.2 Student Module

| ID | Requirement |
|----|-------------|
| STU-01 | Student shall register using a valid email address, verified via OTP |
| STU-02 | Student shall create a profile with: full name, date of birth, gender, mobile number, address, category (General/OBC/SC/ST), and domicile state |
| STU-03 | Student shall upload the following documents: Aadhar Card (JPG/PNG/PDF), 10th Marksheet (JPG/PNG/PDF), 12th Marksheet (JPG/PNG/PDF), Entrance Rank Card (JPG/PNG/PDF) |
| STU-04 | File size limit per document: 5 MB |
| STU-05 | System shall trigger OCR processing immediately upon each document upload |
| STU-06 | OCR-extracted fields shall auto-populate the application form; student may review and correct any field |
| STU-07 | Student shall select preferred branch(es) in priority order from available branches |
| STU-08 | Student shall submit the application only after all required documents are uploaded |
| STU-09 | Student shall view real-time application status: Submitted → Under Verification → Verified → Seat Allocated → Fee Pending → Admitted |
| STU-10 | Student shall receive email notification for every status change |
| STU-11 | Student shall receive email notification with re-upload instructions when a document is rejected |
| STU-12 | Student shall be able to re-upload a rejected document; re-upload triggers fresh OCR processing |
| STU-13 | Student shall view seat allocation details (branch, quota) once allocated |
| STU-14 | Student shall complete fee payment via the manual payment process and upload proof of payment |

---

### 1.3 Document & OCR Module

| ID | Requirement |
|----|-------------|
| OCR-01 | System shall extract the following fields from Aadhar Card: Name, Date of Birth, Gender, Aadhar Number, Address |
| OCR-02 | System shall extract the following fields from 10th Marksheet: Student Name, School Name, Board, Year of Passing, Subject-wise marks, Total marks, Percentage/CGPA |
| OCR-03 | System shall extract the following fields from 12th Marksheet: Student Name, School Name, Board, Year of Passing, Subject-wise marks, Total marks, Percentage/CGPA |
| OCR-04 | System shall extract the following fields from Entrance Rank Card: Student Name, Hall Ticket Number, Rank, Category Rank, Exam Name, Year |
| OCR-05 | Each extracted field shall have an associated confidence score (0.0 – 1.0) |
| OCR-06 | Overall document confidence shall be the average of all field confidence scores |
| OCR-07 | Confidence thresholds: Green >= 0.90, Yellow 0.70–0.89, Red < 0.70 |
| OCR-08 | Raw OCR output (full text) shall be stored alongside structured extracted fields |
| OCR-09 | System shall support re-processing of a document without deleting prior OCR results (versioned) |
| OCR-10 | OCR processing shall complete within 30 seconds per document |

---

### 1.4 Verification Staff Module

| ID | Requirement |
|----|-------------|
| VER-01 | Verification staff shall see a task queue of applications with pending verification |
| VER-02 | Queue shall be sorted by OCR confidence: Red (lowest) first, then Yellow, then Green |
| VER-03 | Each queue item shall display: Student name, application ID, documents count, overall confidence badge (color-coded), time since submission |
| VER-04 | Staff shall open a split-screen view: left panel shows the original document image/PDF, right panel shows extracted data fields |
| VER-05 | Staff shall approve or correct each extracted field individually |
| VER-06 | Staff shall mark a document as Verified or Rejected |
| VER-07 | On rejection, staff shall enter a reason; system shall email the student with re-upload instructions |
| VER-08 | Staff shall lock verified application data — once locked, no field may be edited by any non-admin user |
| VER-09 | All field edits by staff shall be recorded in an audit log (field name, old value, new value, staff user, timestamp) |
| VER-10 | Staff shall not see applications assigned to other staff members (queue is shared; first-come, first-served locking) |
| VER-11 | Application shall auto-unlock if staff holds it for more than 30 minutes without action |

---

### 1.5 Admission Officer Module

| ID | Requirement |
|----|-------------|
| OFF-01 | Officer shall view a list of all verified (locked) applications with filters: branch preference, category/quota, verification date, current status |
| OFF-02 | Officer shall view real-time seat availability per branch and quota |
| OFF-03 | Officer shall allocate a seat to a student by selecting branch and quota; system shall decrement available seat count |
| OFF-04 | System shall prevent over-allocation — seat count shall never go below zero |
| OFF-05 | Officer shall handle walk-in admissions: scan documents on the spot, OCR extracts fields, staff verifies inline, officer allocates seat in a single workflow |
| OFF-06 | After seat allocation, officer shall generate a fee payment instruction (amount, bank details, deadline) and email it to the student |
| OFF-07 | Officer shall mark an application as Admitted after confirming fee payment proof |
| OFF-08 | Officer shall be able to revoke a seat allocation before fee payment is confirmed |

---

### 1.6 Agent Module

| ID | Requirement |
|----|-------------|
| AGT-01 | Agent shall access a dedicated partner portal with a separate login |
| AGT-02 | Agent shall bulk-upload documents for multiple students in a single drag-and-drop operation (ZIP file or multiple files) |
| AGT-03 | System shall auto-create a student profile for each student in the bulk upload; agent shall provide a CSV manifest (student name, mobile, email) alongside documents |
| AGT-04 | Agent shall track per-student status: processing, verified, seat allocated, fee paid, admitted |
| AGT-05 | Agent shall be notified (email) when any student in their batch requires re-upload |
| AGT-06 | System shall calculate agent commission per admitted student based on a pre-configured commission rate |
| AGT-07 | Agent shall view a commission dashboard: total students submitted, admitted count, commission earned, payment status |
| AGT-08 | Agent shall export commission report as CSV/PDF |

---

### 1.7 Principal / Management Module

| ID | Requirement |
|----|-------------|
| PRI-01 | Principal shall access a real-time KPI dashboard showing: total applications, verified count, seats allocated, admitted count, fee collected, seat fill % by branch |
| PRI-02 | Dashboard shall support date range filtering and branch-wise breakdown |
| PRI-03 | Principal shall approve or reject fee concession requests raised by Admission Officers |
| PRI-04 | System shall generate JNTU/AICTE compliance report as a downloadable PDF/Excel with: student list, documents verified, category-wise seat fill, dates |
| PRI-05 | Compliance report shall be generated within 5 minutes |
| PRI-06 | Principal shall view audit logs (read-only) for any application |

---

### 1.8 System Admin Module

| ID | Requirement |
|----|-------------|
| ADM-01 | Admin shall configure academic year (start date, end date, admission open/close dates) |
| ADM-02 | Admin shall configure seat matrix: branch name, total seats, quota-wise breakup (General, OBC, SC, ST, Management, NRI) |
| ADM-03 | Admin shall configure fee structures: branch-wise tuition fee, hostel fee, other charges |
| ADM-04 | Admin shall create and deactivate user accounts and assign roles |
| ADM-05 | Admin shall configure agent commission rates (flat per student or percentage of fee) |
| ADM-06 | Admin shall view OCR API health: request count, average response time, error rate |
| ADM-07 | Admin shall trigger end-of-season ERP sync manually; system shall export admitted student data to Academic ERP, Library, and Hostel systems |
| ADM-08 | Admin shall view ERP sync logs: records exported, errors, timestamp |
| ADM-09 | Admin shall configure email SMTP settings |

---

## 2. Non-Functional Requirements

### 2.1 Performance

| ID | Requirement |
|----|-------------|
| PER-01 | OCR processing shall complete within 30 seconds per document |
| PER-02 | All page loads shall complete within 3 seconds under normal load |
| PER-03 | API responses shall complete within 1 second for non-OCR endpoints |
| PER-04 | System shall support up to 500 concurrent users during peak admission season |
| PER-05 | Redis shall cache seat availability counts; cache TTL = 10 seconds |

### 2.2 Security

| ID | Requirement |
|----|-------------|
| SEC-01 | All API endpoints shall require authentication; no anonymous access except login |
| SEC-02 | All data in transit shall use HTTPS (TLS 1.2+) |
| SEC-03 | Document files shall be stored outside the web root; accessible only via authenticated signed URLs |
| SEC-04 | Digitally locked application data shall be immutable at the database level (no UPDATE allowed via ORM; only Admin can unlock via a dedicated unlock API with audit log) |
| SEC-05 | All admin actions shall be logged with user, action, timestamp, and IP address |
| SEC-06 | Passwords/secrets shall never be stored in code; use environment variables |

### 2.3 Reliability

| ID | Requirement |
|----|-------------|
| REL-01 | System shall have daily database backups retained for 30 days |
| REL-02 | OCR failures shall not block the application — student can manually fill fields if OCR fails |
| REL-03 | Email delivery failures shall be retried up to 3 times with exponential backoff |

### 2.4 Usability

| ID | Requirement |
|----|-------------|
| USA-01 | Student portal shall be mobile-responsive (works on 360px+ viewport) |
| USA-02 | Document upload shall support drag-and-drop and file browser selection |
| USA-03 | OCR confidence colors (Green/Yellow/Red) shall also use icons/labels (not color alone) for accessibility |
| USA-04 | All forms shall display inline validation errors |

---

## 1.9 Allocation Module

### Seat Matrix Configuration

| ID | Requirement |
|----|-------------|
| ALLOC-01 | Admin shall define seat matrix per branch/quota/academic year |
| ALLOC-02 | Seat counts shall default to 0 for new academic years |
| ALLOC-03 | Total seats shall not be reducible below currently allocated seats |
| ALLOC-04 | All seat matrix changes shall be logged in audit trail |

### Quota Eligibility Logic

| ID | Requirement |
|----|-------------|
| ALLOC-10 | General quota: open to all categories |
| ALLOC-11 | OBC quota: open to OBC, General category only |
| ALLOC-12 | SC quota: open to SC, OBC, General categories |
| ALLOC-13 | ST quota: open to ST, SC, OBC, General categories |
| ALLOC-14 | Management quota: open to General category only (under Management seats) |
| ALLOC-15 | NRI quota: open to General category only (fee structure differs) |

**Eligibility Matrix**
| Student Category | General | OBC | SC | ST | Management | NRI |
|----------------|---------|-----|----|----|------------|-----|
| General | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| OBC | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| SC | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ |
| ST | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ |

### Allocation Rules

| ID | Requirement |
|----|-------------|
| ALLOC-20 | Application must have status = VERIFIED or UNDER_VERIFICATION for allocation |
| ALLOC-21 | Selected branch must be in student's branch_preferences (warning if not) |
| ALLOC-22 | Student category must be eligible for requested quota |
| ALLOC-23 | Seat allocation uses SELECT FOR UPDATE to prevent race conditions |
| ALLOC-24 | Allocation increments allocated_seats atomically |
| ALLOC-25 | Concurrent allocation attempts for same seat: first wins, others get "no seats available" (409) |
| ALLOC-26 | Double allocation attempt returns 409 Conflict |
| ALLOC-27 | Deallocation requires admin/officer role + mandatory reason (min 10 chars) |
| ALLOC-28 | Bulk allocate max 50 applications per request |
| ALLOC-29 | Auto-allocate fills by merit score (fee_amount DESC, submitted_at ASC tiebreaker) |

### Merit Ranking

| ID | Requirement |
|----|-------------|
| ALLOC-30 | Merit score = fee_amount (higher = better rank) |
| ALLOC-31 | Tiebreaker: submitted_at (earlier submission ranks higher) |
| ALLOC-32 | Suggest API returns ranked eligible candidates for a branch/quota |

---

## 3. Data Models

### 3.1 User
```
User
├── id (UUID)
├── email (unique)
├── full_name
├── role (ENUM: student | verification_staff | admission_officer | agent | principal | admin)
├── google_sso_id
├── is_active
├── created_at
└── last_login
```

### 3.2 StudentProfile
```
StudentProfile
├── id (UUID)
├── user (FK → User)
├── date_of_birth
├── gender
├── mobile_number
├── address (JSONField: street, city, state, pincode)
├── category (ENUM: General | OBC | SC | ST)
├── domicile_state
└── agent (FK → AgentProfile, nullable)
```

### 3.3 Document
```
Document
├── id (UUID)
├── student (FK → StudentProfile)
├── document_type (ENUM: aadhar | marksheet_10 | marksheet_12 | rank_card)
├── file_path
├── upload_version (integer, increments on re-upload)
├── status (ENUM: processing | extracted | verified | rejected)
├── rejection_reason (nullable)
├── uploaded_at
└── uploaded_by (FK → User)
```

### 3.4 OCRResult
```
OCRResult
├── id (UUID)
├── document (FK → Document)
├── raw_text (TextField)
├── extracted_fields (JSONField)   ← Pydantic-validated structured data
├── confidence_scores (JSONField)  ← per-field confidence
├── overall_confidence (Float)
├── processing_duration_ms (Integer)
├── created_at
└── ocr_version (integer, matches document.upload_version)
```

### 3.5 Application
```
Application
├── id (UUID)
├── student (FK → StudentProfile, unique)
├── application_number (auto-generated, human-readable)
├── status (ENUM: draft | submitted | under_verification | verified | seat_allocated | fee_pending | admitted | rejected)
├── branch_preferences (JSONField: ordered list of branch IDs)
├── submitted_at
├── is_locked (Boolean)
├── locked_at
├── locked_by (FK → User, nullable)
└── allocated_branch (FK → Branch, nullable)
```

### 3.6 Branch & SeatMatrix
```
Branch
├── id (UUID)
├── name
├── code
└── is_active

SeatMatrix
├── id (UUID)
├── branch (FK → Branch)
├── academic_year
├── quota (ENUM: General | OBC | SC | ST | Management | NRI)
├── total_seats
└── allocated_seats
```

### 3.7 AuditLog
```
AuditLog
├── id (UUID)
├── user (FK → User)
├── application (FK → Application, nullable)
├── action (CharField)
├── field_name (nullable)
├── old_value (nullable)
├── new_value (nullable)
├── ip_address
└── timestamp
```

### 3.8 AgentProfile & Commission
```
AgentProfile
├── id (UUID)
├── user (FK → User)
├── agency_name
├── commission_rate (Decimal)
└── commission_type (ENUM: flat | percentage)

Commission
├── id (UUID)
├── agent (FK → AgentProfile)
├── application (FK → Application)
├── amount (Decimal)
├── status (ENUM: pending | approved | paid)
└── calculated_at
```

---

## 4. API Endpoints

### Auth
```
POST   /api/auth/register/          ← Student email OTP registration
POST   /api/auth/verify-otp/        ← Verify OTP
POST   /api/auth/google/            ← Google SSO callback
POST   /api/auth/logout/
GET    /api/auth/me/                ← Current user + role
```

### Student
```
GET    /api/student/profile/
PUT    /api/student/profile/
GET    /api/student/application/
POST   /api/student/application/submit/
GET    /api/student/application/status/
```

### Documents
```
POST   /api/documents/upload/           ← Upload document, triggers OCR
GET    /api/documents/{id}/
GET    /api/documents/{id}/ocr-result/
POST   /api/documents/{id}/reupload/    ← Re-upload rejected document
```

### Verification Staff
```
GET    /api/verification/queue/                    ← Prioritized application queue
POST   /api/verification/queue/{app_id}/claim/     ← Claim application for review
GET    /api/verification/{app_id}/split-screen/    ← Document + extracted data
PATCH  /api/verification/{app_id}/field/           ← Correct a field value
POST   /api/verification/{app_id}/document/{doc_id}/verify/
POST   /api/verification/{app_id}/document/{doc_id}/reject/
POST   /api/verification/{app_id}/lock/            ← Digitally lock application
```

### Admission Officer
```
GET    /api/admissions/applications/        ← Verified applications with filters
GET    /api/admissions/seats/               ← Real-time seat availability
POST   /api/admissions/{app_id}/allocate/   ← Allocate seat
DELETE /api/admissions/{app_id}/allocate/   ← Revoke allocation
POST   /api/admissions/{app_id}/walkin/     ← Walk-in flow
POST   /api/admissions/{app_id}/confirm-payment/
```

### Agent
```
GET    /api/agents/students/
POST   /api/agents/bulk-upload/
GET    /api/agents/commission/
GET    /api/agents/commission/export/
```

### Principal
```
GET    /api/principal/dashboard/
GET    /api/principal/compliance-report/    ← Returns PDF/Excel download
POST   /api/principal/concessions/{id}/approve/
POST   /api/principal/concessions/{id}/reject/
```

### System Admin
```
GET/PUT  /api/admin/academic-year/
GET/POST/PUT/DELETE  /api/admin/seat-matrix/
GET/POST/PUT/DELETE  /api/admin/fee-structures/
GET/POST/PUT/DELETE  /api/admin/users/
GET/PUT  /api/admin/commission-rates/
GET      /api/admin/ocr-health/
POST     /api/admin/erp-sync/trigger/
GET      /api/admin/erp-sync/logs/
```

---

## 5. OCR Pipeline Specification

### Processing Flow

```
Document Upload
      │
      ▼
Google Vision API  ──► Raw text (full page OCR)
      │
      ▼
LLM Extraction Layer
  - Input: raw text + document_type
  - Output: Pydantic-validated structured fields + per-field confidence
      │
      ▼
Store OCRResult (raw_text + extracted_fields + confidence_scores)
      │
      ▼
Auto-populate Application form fields
      │
      ▼
Display to Student for review
```

### Pydantic Schemas (per document type)

**AadharCard**
```python
class AadharCard(BaseModel):
    name: str
    date_of_birth: date
    gender: str
    aadhar_number: str        # 12 digits
    address: str
    confidence: dict[str, float]
```

**Marksheet10 / Marksheet12**
```python
class Marksheet(BaseModel):
    student_name: str
    school_name: str
    board: str
    year_of_passing: int
    subjects: list[SubjectMark]
    total_marks: int
    obtained_marks: int
    percentage: float
    confidence: dict[str, float]

class SubjectMark(BaseModel):
    subject: str
    max_marks: int
    obtained_marks: int
```

**RankCard**
```python
class RankCard(BaseModel):
    student_name: str
    hall_ticket_number: str
    exam_name: str
    year: int
    overall_rank: int
    category_rank: int | None
    confidence: dict[str, float]
```

---

## 6. Notification Specification

### Email Triggers (SMTP)

| Trigger | Recipient | Subject |
|---------|-----------|---------|
| OTP registration | Student | Your OTP for Admission Portal |
| Application submitted | Student | Application Received – [Application No.] |
| Document rejected | Student | Action Required: Re-upload [Document Type] |
| Verification complete | Student | Documents Verified – Await Seat Allocation |
| Seat allocated | Student | Seat Allocated – [Branch Name] |
| Fee payment instructions | Student | Fee Payment Details – [Application No.] |
| Admission confirmed | Student | Admission Confirmed – Welcome! |
| Agent batch re-upload needed | Agent | Student [Name] Requires Document Re-upload |

---

## 7. ERP Sync Specification

### Trigger
- Manual: System Admin triggers via admin panel
- Scope: Only students with status = `admitted`

### Export Format
- Primary: REST API POST to ERP endpoint (if ERP provides API)
- Fallback: CSV export with agreed column mapping

### Data Exported to Academic ERP
```
student_id, full_name, date_of_birth, gender, category, mobile,
email, branch, quota, academic_year, admission_date, fee_paid
```

### Data Exported to Library System
```
student_id, full_name, branch, academic_year
```

### Data Exported to Hostel System
```
student_id, full_name, gender, mobile, hostel_preference (if collected)
```

### Sync Log fields
```
sync_id, triggered_by, triggered_at, total_records, success_count,
error_count, errors (JSONField), completed_at
```

---

*SRS Version 1.0 — Finalized 2026-04-10*
*All requirements require stakeholder sign-off before development begins.*
