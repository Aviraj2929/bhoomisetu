# BhoomiSetu – 5 to 10 Minute Live Product Demonstration Guide

## 🎯 Core Pitch & Value Proposition

> **"BhoomiSetu is an AI-powered platform designed for Indian land record digitization. AI performs 85%+ of the transcription work; human verifiers review only low-confidence fields or flagged exceptions. Every extracted value is immutably linked to source visual bounding box evidence."**

---

## ⏱️ Step-by-Step Live Demo Script (5–10 Minutes)

### Step 1: Open the Application Dashboard (1 Minute)
1. Open your browser and navigate to **`http://localhost:5173`**.
2. **Key Talking Point**: Highlight the **Operational Dashboard**. Point out that the screen immediately answers: *"What needs attention right now?"*
3. Show the KPI summary cards: **Total Documents**, **83.1% Auto-Approval Rate**, **Average Field Confidence (89.2%)**, and **Pending Verification Queue Count**.

---

### Step 2: Upload a Scanned Land Record (2 Minutes)
1. On the top section of the Dashboard, locate the **Upload Land Record Document** drag-and-drop box.
2. Click to select a sample land record scan or PDF file (e.g., `khasra_register_bhopal_1985.pdf`).
3. Click **Upload & Trigger Asynchronous Extraction**.
4. **Key Talking Point**: *"Behind the scenes, the backend runs OpenCV conditional preprocessing (deskewing, contrast tuning), calls the Sarvam AI Indic OCR Provider, maps 8 core fields, calculates confidence, and checks validation rules."*

---

### Step 3: Demonstrate the 3-Pane Verification Workspace (4 Minutes)
1. Click the **Verification Workspace** tab on the top navigation bar (or click **Open Verification Queue**).
2. Point out the **3-Pane Workspace Layout**:
   - **Left Pane**: Original high-resolution document scan with zoom controls.
   - **Middle Pane**: Raw OCR text snippet, character confidence score, and **Rule Validation Engine** results (`RULE_VAL_01: plot_area PASS`, `Suspected Duplicate Flagged`).
   - **Right Pane**: Targeted extracted fields prioritized by low confidence (`owner_name` - 45% confidence).
3. **Demonstrate Bounding Box Source Highlighting**:
   - Click on the `owner_name` field on the right pane.
   - **Observe**: The Left Document Pane automatically highlights the exact visual bounding box (`[120, 220, 300, 260]`) on the document scan.
4. **Demonstrate Human Verifier Correction**:
   - Change the `owner_name` value from `"राम साहाय"` to `"राम सहाय"`.
   - **Key Talking Point**: *"Notice how the verifier does NOT re-type the whole document. They simply fix the single misrecognized character."*
   - Behind the scenes, `PATCH /api/v1/verification/fields/{id}` logs an immutable JSON audit entry and saves the pair to the **Active Learning Feedback Store**.

---

### Step 4: Finalize & Approve Record (1 Minute)
1. Click **Approve & Complete Task (Ctrl+Enter)**.
2. Click the **Digitized Records** tab on the navigation bar.
3. Show the newly added, 100% verified master record in the digitized land database table.

---

## 🏆 Key Demo Takeaways
1. **AI Automates Bulk Work**: 83%+ of clean land records bypass human review automatically.
2. **Pixel-Accurate Traceability**: Every field is linked to visual bounding box source evidence.
3. **No Overwrite / Full Auditability**: Corrections do not delete history; every edit is logged for future model fine-tuning.
