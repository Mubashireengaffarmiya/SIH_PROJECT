# SMART-LM (Smart Legal Metrology Compliance & Inspection System)

**SIH 2026 Prototype — Problem Statement SIH26034**

SMART-LM is an AI-powered inspection assistance tool designed for Legal Metrology officers. It uses Optical Character Recognition (OCR) and a deterministic rule engine to automatically extract and verify mandatory declarations on packaged commodities, flagging potential violations for human review.

---

## Architecture & Technology Stack

The project is built as a single cohesive application using a modern tech stack:

- **Frontend:** React + Vite + TypeScript + Tailwind CSS (v4)
- **Backend:** Python + FastAPI + Uvicorn
- **Image Processing & OCR:** OpenCV, NumPy, Pillow, PaddleOCR (with Tesseract 5 fallback)
- **Database:** SQLite (SQLAlchemy ORM, structured to easily swap to PostgreSQL)
- **Reporting:** ReportLab (PDF) and python-docx (DOCX)

### Why this stack?
- **FastAPI** handles multipart file uploads quickly and provides automatic API documentation.
- **PaddleOCR** provides state-of-the-art text extraction including orientation handling, with a seamless fallback to **Tesseract** if installation issues occur on Windows.
- **Deterministic regex extraction** is used instead of LLMs for reliability, speed, and exact evidence highlighting without hallucinations.
- **React + Tailwind** provides a responsive, professional, government-style dashboard that works on desktop and mobile without needing a separate mobile app.

---

## Setup & Installation

### Prerequisites
- Node.js (v18+)
- Python (3.10+)

### 1. Backend Setup

Open a terminal and navigate to the `backend` directory:

```bash
cd backend
python -m venv venv

# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

> **Note on OCR Installation (Windows):**
> PaddleOCR (`paddlepaddle`) can sometimes have complex C++ redistributable requirements on Windows. If `pip install paddlepaddle paddleocr` fails, the application will automatically fall back to **Tesseract**.
> To use Tesseract, install the Tesseract binary from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) and ensure it is in your system PATH, then `pip install pytesseract`.

### 2. Frontend Setup

Open a second terminal and navigate to the `frontend` directory:

```bash
cd frontend
npm install
```

---

## Running the Application

You must run both the backend and frontend simultaneously.

### Start Backend
In the backend terminal (with the virtual environment activated):

```bash
cd backend
uvicorn main:app --reload --port 8000
```
The API will be available at `http://localhost:8000`
API Documentation (Swagger UI) is automatically available at `http://localhost:8000/docs`

### Start Frontend
In the frontend terminal:

```bash
cd frontend
npm run dev
```
The web dashboard will be available at `http://localhost:5173`

---

## Testing & Demo Data

### Seeding Demo Data

To see the application in action without needing to take perfect photos immediately, you can seed the database with synthetic demo data (generated using Pillow) as well as the initial demo users (inspector, reviewer, admin):

```bash
cd backend
# Ensure virtual environment is activated
python demo/seed_demo.py
```
This will generate 5 synthetic product label images (good, blurry, missing MRP, dark, angled) in the `uploads/` directory and populate the SQLite database. It will also create three demo accounts:
- **inspector** / `Inspector@123` (Role: INSPECTOR)
- **reviewer** / `Reviewer@123` (Role: REVIEWER)
- **admin** / `Admin@123` (Role: ADMIN)

### Running Tests

The extraction and compliance engines are fully tested using Pytest.

```bash
cd backend
# Ensure virtual environment is activated
pytest tests/ -v
```

---

## Project Structure

```
SMART-LM/
├── backend/
│   ├── database/       # SQLAlchemy models and SQLite connection
│   ├── demo/           # Demo data generator script
│   ├── models/         # Pydantic v2 schemas for API validation
│   ├── rules/          # rules.json containing the compliance ruleset
│   ├── services/       # Core business logic
│   │   ├── compliance.py       # Rule evaluation engine
│   │   ├── extraction.py       # Regex-based declaration extraction
│   │   ├── image_processing.py # OpenCV quality assessment
│   │   ├── ocr.py              # PaddleOCR / Tesseract wrapper
│   │   └── reports.py          # PDF/DOCX generation
│   ├── tests/          # Pytest suite
│   ├── main.py         # FastAPI application entry point
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/        # Axios API client
│   │   ├── components/ # Reusable UI components (Layout, Badges)
│   │   ├── pages/      # Dashboard, New Inspection, Analysis Result, History
│   │   ├── types/      # TypeScript interfaces matching backend models
│   │   ├── App.tsx     # React Router setup
│   │   └── index.css   # Tailwind configuration and custom CSS
│   └── vite.config.ts  # Vite configuration (includes backend proxy)
│
└── data/
    └── test_images/    # Generated demo images for testing
```

---

## Important Limitations & Disclaimers

⚠️ **Prototype Status:** This system is a prototype built for the SIH 2026 hackathon.
- It does **not** make official legal determinations.
- It serves as an **inspection assistance tool** to flag potential issues.
- All OCR findings and compliance statuses (VERIFIED COMPLIANT, POTENTIAL VIOLATION, NEEDS HUMAN REVIEW) must be physically verified by a qualified Legal Metrology Inspector.
- If a field is marked as "Not detected", it means the OCR engine could not confidently read it. It does not automatically mean the declaration is legally missing.

## Future Enhancements
The codebase is designed to be extensible for future improvements:
- Swapping SQLite for PostgreSQL (change one line in `database.py`).
- Adding YOLO object detection to find the exact region of interest before OCR.
- Implementing multilingual Indian language OCR.
