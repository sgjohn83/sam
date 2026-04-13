# Smart & Automated Student Admission System

## Project Summary

A college admission system that eliminates manual data entry using OCR (Google Vision + LLM with Pydantic schemas) to auto-extract data from Aadhar Cards, 10th/12th Marksheets, and Entrance Rank Cards. Students upload documents, OCR auto-fills their application, verification staff validates via split-screen view, admission officers allocate seats, and management gets real-time dashboards.

## Tech Stack

- **Frontend:** React.js (web), React Native (mobile)
- **Backend:** Python / Django
- **OCR:** Google Vision API + LLM with Pydantic schema for structured extraction
- **Database:** PostgreSQL (primary), Redis (caching)
- **Auth:** Google SSO
- **Payments:** Manual process
- **Notifications:** Email (SMTP)
- **Hosting:** Local server (no cloud, no CI/CD)

## Project Structure

```
student-admission/
├── backend/              # Django project
│   ├── config/           # Django settings, urls, wsgi
│   ├── accounts/         # User models, Google SSO, roles (Student, Staff, Officer, Agent, Principal, Admin)
│   ├── students/         # Student registration, profile, application
│   ├── documents/        # Document upload, OCR processing, confidence scoring
│   ├── verification/     # Staff verification queue, split-screen, digital locking
│   ├── admissions/       # Seat allocation, walk-in, fee payment
│   ├── agents/           # Agent portal, bulk upload, commission tracking
│   ├── dashboard/        # Principal KPI dashboard, compliance reports
│   ├── administration/   # System admin config (seat matrix, fees, academic year)
│   ├── notifications/    # Email/SMTP notification service
│   └── erp_sync/         # ERP export (Academic, Library, Hostel)
├── frontend/             # React.js web app
│   ├── src/
│   │   ├── components/   # Shared UI components
│   │   ├── pages/        # Role-based page views
│   │   ├── services/     # API client layer
│   │   └── utils/        # Helpers, OCR confidence color mapping
│   └── public/
├── mobile/               # React Native app
├── PROJECT_PLAN.md       # Full 24-week delivery plan
└── CLAUDE.md             # This file
```

## User Roles

1. **Student** — Self-service registration, document upload, OCR auto-fill, branch selection, fee payment
2. **Verification Staff** — Color-coded task queue, split-screen validation, re-upload requests, digital locking
3. **Admission Officer** — Seat allocation, walk-in handling, fee link generation
4. **Agent** — Bulk upload, commission tracking, fee negotiations
5. **Principal/Management** — KPI dashboard, fee concession approval, JNTU/AICTE compliance reports
6. **System Admin** — Seat matrix config, fee structures, RBAC, OCR health monitoring, ERP sync

## Key Design Decisions

- OCR pipeline: Google Vision for raw text extraction → LLM with Pydantic schemas for structured field extraction with confidence scores
- Confidence scoring: Green (>90%), Yellow (70-90%), Red (<70%) — drives verification queue priority
- Digital locking: Verified data becomes immutable with audit trail
- ERP sync is batch/end-of-season (not real-time)
- Payments are manual (no payment gateway integration)

## Development Commands

```bash
# Backend
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend
cd frontend
npm install
npm start
```

## Coding Conventions

- Backend: Follow Django conventions, use Django REST Framework for APIs
- Frontend: Functional React components with hooks, no class components
- API format: RESTful JSON APIs
- All document types use Pydantic models for OCR schema validation
- Use PostgreSQL-specific features where beneficial (JSONField for OCR raw data)
