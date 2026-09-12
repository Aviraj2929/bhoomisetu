# BhoomiSetu – Intelligent Land Record Digitization and Validation System

BhoomiSetu is an enterprise-grade AI platform designed specifically to convert unstructured, handwritten, printed, damaged, and multilingual Indian land records (Khasra, Khatauni, Jamabandi, Deeds) into structured, database-verified administrative records with field-level confidence and pixel bounding-box source evidence.

---

## 🌟 Key Engineering Philosophy

> **"AI performs 85%+ of the transcription work; human verifiers review only low-confidence fields or flagged exceptions. Every extracted value is immutably linked to source visual bounding box evidence."**

---

## 🛠️ Complete System Architecture

```
Uploaded Document (PDF / Image)
  │
  ▼
OpenCV Preprocessing (Deskewing, Denoising, CLAHE Contrast)
  │
  ▼
OCR / HTR Engine (Sarvam AI Provider / Offline Mock Indic Adapter)
  │
  ▼
NLP Information Extraction & 8 Core Field Normalization
  │
  ▼
Field-Level Confidence Scoring & Source Bounding Box Traceability
  │
  ▼
Validation Engine & Multi-Signal Duplicate Detection
  │
  ├── Confidence >= 0.85 & Valid ──► [APPROVED]
  │
  └── Confidence < 0.85 ───────────► [REQUIRES_VERIFICATION] (3-Pane HITL Workspace)
                                           │
                                           ▼
                                [PostgreSQL + Audit Trail & Feedback Store]
```

---

## 📋 Core 8 MVP Land Record Fields
- `owner_name`
- `survey_number`
- `khata_number`
- `plot_area`
- `area_unit`
- `village`
- `tehsil`
- `district`

*(Database schema natively supports additional fields: `khasra_number`, `father_name`, `mother_name`, `spouse_name`, `state`, `land_classification`, `ownership_type`, `mutation_number/date`, `registration_number/date`, `remarks`).*

---

## 🔒 Security & RBAC Roles
BhoomiSetu enforces strict role-based access control across 6 roles:
1. **ADMIN**: Full system configuration, user management, and rule editing.
2. **SUPERVISOR**: Batch verification oversight, approval/rejection sign-off.
3. **VERIFIER**: Access to targeted 3-pane verification workspace and field editing.
4. **OPERATOR**: Upload scanned land record files.
5. **AUDITOR**: Read-only access to immutable system audit logs.
6. **READ_ONLY**: Viewing finalized digitized master land records.

---

## 🚀 How to Run the Project

### Option 1: Docker Compose (Recommended)
Make sure Docker Desktop / Docker Engine is running on your system, then execute:

```bash
cd /home/shounak/Desktop/bhoomisetu
docker-compose up --build
```

- **Frontend Application**: `http://localhost:5173`
- **FastAPI OpenAPI Swagger Docs**: `http://localhost:8000/docs`

---

### Option 2: Local Python + React Setup

#### 1. Backend Setup (FastAPI)
```bash
cd backend
pip install -r requirements.txt
python3 main.py
```
*(FastAPI server launches on `http://localhost:8000`)*

#### 2. Run Test Suite
```bash
cd backend
PYTHONPATH=. python3 -m pytest
```

#### 3. Frontend Setup (React + TypeScript + Vite)
```bash
cd frontend
npm install
npm run dev
```
*(React frontend launches on `http://localhost:5173`)*

---

## 📄 Demonstration Guide
Refer to **[PROJECT_DEMO.md](file:///home/shounak/Desktop/bhoomisetu/PROJECT_DEMO.md)** for a step-by-step 5 to 10 minute live product demonstration script.
