# Smart & Automated Student Admission System — Project Plan

## 1. Project Overview

| Field            | Detail                                                                 |
|------------------|------------------------------------------------------------------------|
| **Project Name** | Smart & Automated Student Admission System                            |
| **Objective**    | Eliminate manual data entry in college admissions using OCR to achieve 100% data accuracy |
| **Sponsor**      | College Management / Principal                                         |
| **Project Manager** | To Be Assigned                                                      |
| **Target Users** | Students, Verification Staff, Admission Officers, Agents, Principal, System Admin |
| **Duration**     | 24 Weeks (6 Months)                                                   |
| **Budget**       | To Be Determined                                                       |

---

## 2. Scope

### 2.1 In Scope

- OCR-based auto-extraction from Aadhar Card, 10th/12th Marksheets, Entrance Rank Cards
- Student self-service portal with smart upload and auto-fill
- Verification staff split-screen validation workflow
- Admission officer seat allocation and walk-in handling
- Agent bulk upload portal with commission tracking
- Principal executive dashboard with compliance reporting
- System admin configuration panel (seat matrix, fee structures, roles)
- OTP-based registration (mobile and email)
- Online fee payment integration
- SMS/WhatsApp notifications for document re-upload
- Final ERP sync (Academic ERP, Library, Hostel systems)

### 2.2 Out of Scope

- Development of the college Academic ERP itself
- Hardware procurement (scanners, kiosks)
- Offline-only admission workflows without internet connectivity

---

## 3. Technology Stack

| Layer            | Technology                                        |
|------------------|---------------------------------------------------|
| Frontend         | React.js / React Native (mobile), Responsive Web  |
| Backend          | Python (Django)                                    |
| OCR Engine       | Google Vision + LLM with Pydantic schema           |
| Database         | PostgreSQL (primary), Redis (caching)              |
| Authentication   | Google SSO                                         |
| Payments         | Manual                                             |
| Notifications    | Email (SMTP)                                       |
| Hosting          | Local                                              |
| CI/CD            | Not needed                                         |

---

## 4. User Journeys

### Journey 1: Student (Self-Service & Auto-Fill)
- Register via mobile/email OTP
- Upload Aadhar, Marksheets, Rank Card (photos/PDFs)
- OCR auto-fills application; student reviews & submits
- Select branch, track status, pay fees online

### Journey 2: Verification Staff (Gatekeepers)
- Prioritized task queue color-coded by OCR confidence
- Split-screen validation (document vs extracted data)
- One-click re-upload request via SMS/WhatsApp
- Digital locking of verified data

### Journey 3: Admission Officer (Seat Allocation)
- View verified applications
- Check branch/quota against real-time seat availability
- Walk-in handling via direct document scan + OCR
- Approve and trigger fee payment link

### Journey 4: Admission Agent (Bulk Processing)
- Dedicated partner portal
- Drag-and-drop bulk document upload with auto-profile creation
- Track approvals, re-uploads, fee negotiations
- Automatic commission calculation

### Journey 5: Principal / Management (Oversight & Analytics)
- Real-time KPI dashboard (admissions, revenue, seat fill)
- Approve fee concessions on verified data
- One-click JNTU/AICTE compliance reports

### Journey 6: System Admin (Configuration & Maintenance)
- Configure academic year, seat matrix, fee structures
- Role-based access control management
- Monitor OCR API and payment gateway health
- End-of-season ERP sync (Academic, Library, Hostel)

---

## 5. Phase-wise Delivery Plan (24 Weeks)

### Phase 1: Foundation & Setup (Weeks 1–4)

| Week | Tasks | Deliverables |
|------|-------|--------------|
| W1 | Project kickoff, finalize requirements, set up dev environment | Signed-off requirements document |
| W2 | Database schema design (PostgreSQL), Django project scaffold | ER diagram, initial Django project with apps structure |
| W3 | Authentication module — Google SSO integration, user role models | Login/logout flow, role-based user model |
| W4 | Base React.js project setup, component library selection, routing | Frontend scaffold with auth screens, navigation shell |

**Milestone 1:** Dev environment ready, authentication working, DB schema finalized.

---

### Phase 2: OCR Engine & Student Portal (Weeks 5–9)

| Week | Tasks | Deliverables |
|------|-------|--------------|
| W5 | Google Vision API integration, document upload service | Raw OCR text extraction from uploaded images/PDFs |
| W6 | LLM + Pydantic schema pipeline — structured field extraction from Aadhar, Marksheets, Rank Cards | Structured JSON output per document type with confidence scores |
| W7 | Student registration flow (OTP via email), profile creation | Student registration & OTP verification screens |
| W8 | Student document upload UI (drag-drop, camera capture), OCR auto-fill form | Upload screen → OCR processing → pre-filled application form |
| W9 | Student review/edit flow, branch selection, application submission | Complete student self-service journey end-to-end |

**Milestone 2:** Student can register, upload documents, get auto-filled form, and submit application.

---

### Phase 3: Verification & Staff Workflows (Weeks 10–13)

| Week | Tasks | Deliverables |
|------|-------|--------------|
| W10 | Verification staff dashboard — task queue with OCR confidence color-coding (green/yellow/red) | Prioritized queue UI with filtering and sorting |
| W11 | Split-screen validation view (original document side-by-side with extracted data) | Split-screen component with field-level edit/approve |
| W12 | Re-upload request workflow — trigger email notification to student, track re-upload status | One-click re-upload request, student notification, status tracking |
| W13 | Digital locking mechanism — verified data becomes immutable, audit trail logging | Lock/unlock flow, audit log table, verification completion |

**Milestone 3:** Verification staff can review, correct, request re-uploads, and lock verified applications.

---

### Phase 4: Admission Officer & Seat Allocation (Weeks 14–16)

| Week | Tasks | Deliverables |
|------|-------|--------------|
| W14 | Admission officer dashboard — view verified applications, filter by branch/quota/status | Officer dashboard with application list and filters |
| W15 | Seat matrix management — real-time seat availability, branch/quota allocation engine | Seat allocation logic, availability counter, allocation UI |
| W16 | Walk-in admission flow (direct scan + OCR + instant processing), fee payment link generation | Walk-in workflow, payment link trigger via email |

**Milestone 4:** Officers can allocate seats, handle walk-ins, and initiate fee collection.

---

### Phase 5: Agent Portal & Commission Tracking (Weeks 17–18)

| Week | Tasks | Deliverables |
|------|-------|--------------|
| W17 | Agent partner portal — login, bulk document upload (drag-drop multiple students), auto-profile creation | Agent portal with bulk upload and batch processing |
| W18 | Commission tracking — per-student tracking, approval status, fee negotiation log, commission report | Commission dashboard, calculation engine, export reports |

**Milestone 5:** Agents can bulk-upload student documents and track commissions.

---

### Phase 6: Principal Dashboard & Compliance (Weeks 19–20)

| Week | Tasks | Deliverables |
|------|-------|--------------|
| W19 | Executive KPI dashboard — real-time metrics (total admissions, revenue, seat fill rate, branch-wise breakdown) | Interactive dashboard with charts and filters |
| W20 | Fee concession approval workflow, JNTU/AICTE compliance report generation (one-click export) | Concession approval UI, downloadable compliance reports |

**Milestone 6:** Management has full visibility and compliance reporting.

---

### Phase 7: System Admin, Integration & Hardening (Weeks 21–23)

| Week | Tasks | Deliverables |
|------|-------|--------------|
| W21 | Admin configuration panel — academic year setup, seat matrix config, fee structure management | Admin config screens with CRUD operations |
| W22 | Role-based access control fine-tuning, OCR/payment health monitoring dashboard, Redis caching layer | RBAC enforcement, system health page, performance optimization |
| W23 | ERP sync module — batch export to Academic ERP, Library, Hostel systems (API or file-based) | ERP sync scripts, data mapping, sync status dashboard |

**Milestone 7:** System fully configurable, monitored, and integrated with downstream systems.

---

### Phase 8: Testing, UAT & Launch (Week 24)

| Week | Tasks | Deliverables |
|------|-------|--------------|
| W24 | End-to-end testing across all roles, UAT with real users, bug fixes, production deployment, training | Test reports, UAT sign-off, deployed system, user training |

**Milestone 8:** System live in production, users trained, admission cycle begins.

---

## 6. Summary Timeline

```
W1–W4   ████████░░░░░░░░░░░░░░░░  Phase 1: Foundation & Setup
W5–W9   ░░░░████████████░░░░░░░░  Phase 2: OCR Engine & Student Portal
W10–W13 ░░░░░░░░░████████░░░░░░░  Phase 3: Verification & Staff Workflows
W14–W16 ░░░░░░░░░░░░░░███░░░░░░░  Phase 4: Admission Officer & Seat Allocation
W17–W18 ░░░░░░░░░░░░░░░░██░░░░░░  Phase 5: Agent Portal & Commission
W19–W20 ░░░░░░░░░░░░░░░░░░██░░░░  Phase 6: Principal Dashboard & Compliance
W21–W23 ░░░░░░░░░░░░░░░░░░░░███░  Phase 7: Admin, Integration & Hardening
W24     ░░░░░░░░░░░░░░░░░░░░░░░█  Phase 8: Testing, UAT & Launch
```

---

## 7. Risk Management

| # | Risk | Impact | Mitigation |
|---|------|--------|------------|
| R1 | Low OCR accuracy on handwritten or blurry documents | High | Confidence scoring with color-coded flags; re-upload for low confidence; train on local document samples |
| R2 | Payment gateway downtime during peak admission season | High | Retry logic; offline receipt generation |
| R3 | Scope creep from additional document types or workflows | Medium | Strict change request process; phase additions into future releases |
| R4 | Google Vision API rate limits or cost overruns | Medium | Request batching; caching of processed results; budget alerts |
| R5 | User resistance to new digital workflow | Medium | Early UAT involvement; training sessions; parallel run with manual process |

---

## 8. Success Criteria

- OCR data extraction accuracy >= 98% on standard printed documents
- Average application processing time reduced by 70% vs manual process
- 100% of verified data digitally locked and tamper-proof
- Successful ERP sync with zero data mismatches at end of admission cycle
- Compliance reports generated in under 5 minutes (vs days manually)
- Staff and student satisfaction score >= 85% in post-launch survey

---

## 9. Assumptions & Dependencies

**Assumptions:**
- Students have access to smartphones
- Internet connectivity is available at college premises

**Dependencies:**
- Google Vision API access and credentials
- Google SSO configuration for college domain
- ERP system API documentation or file format specification for end-of-season sync
- College-provided seat matrix, fee structures, and quota rules before Phase 4

---

## 10. Team Structure (Recommended)

| Role | Count | Responsibility |
|------|-------|----------------|
| Project Manager | 1 | Planning, tracking, stakeholder communication |
| Backend Developer (Django) | 2 | API development, OCR pipeline, business logic |
| Frontend Developer (React) | 2 | Web portal, mobile-responsive UI |
| Mobile Developer (React Native) | 1 | Mobile app (if native app required) |
| QA Engineer | 1 | Testing across all user journeys |
| DevOps / SysAdmin | 1 | Local server setup, deployment, monitoring |
| UI/UX Designer | 1 | Wireframes, design system, user flows |

---

*Document created: 2026-04-10*
*Status: Draft — Pending stakeholder review and approval*
