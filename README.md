# SMART-LM

Smart Legal Metrology Compliance & Inspection System for SIH 2026 Problem Statement SIH26034.

## Proposed Solution

SMART-LM is a digital inspection-assistance system for Legal Metrology officers. It analyzes packaged-product label images and automatically checks whether mandatory declarations are present and readable.

The solution:

- accepts a product-label image from the inspector;
- checks image quality and improves the image for recognition;
- reads label text using OCR;
- extracts product name, MRP, net quantity, manufacturer, dates, country of origin, and consumer-care details;
- compares extracted declarations with configurable Legal Metrology rules;
- displays compliance status, confidence, and supporting evidence;
- sends uncertain or incomplete results to a human reviewer;
- stores inspection history and generates PDF or DOCX reports.

SMART-LM supports the officer's decision-making process. It does not replace the final legal decision or physical verification by a qualified inspector.

## Technology Stack Details

### Programming Languages

- **Python:** Backend API, OCR pipeline, image processing, extraction, compliance evaluation, database access, and report generation.
- **TypeScript:** React frontend pages, components, routing, API client, authentication state, and shared data types.
- **JavaScript:** Frontend tooling and Vite runtime modules.
- **HTML:** Frontend document entry point.
- **CSS:** Responsive styling and Tailwind CSS utilities.

### Frameworks and Libraries

- **React:** User interface for login, dashboard, inspection upload, history, review queue, and reports.
- **Vite:** Frontend development server and production bundler.
- **Tailwind CSS:** Responsive application styling.
- **FastAPI:** Backend REST API and request validation.
- **Uvicorn:** ASGI server for running the FastAPI application.
- **Axios:** Frontend-to-backend HTTP communication.
- **OpenCV:** Image quality assessment and OCR preprocessing.
- **NumPy and Pillow:** Image and numerical data processing.
- **PaddleOCR:** Primary OCR engine when available.
- **Tesseract 5 with pytesseract:** OCR fallback and targeted MRP digit recognition.
- **SQLAlchemy:** Object-relational database access.
- **Pydantic:** API request and response schemas.
- **ReportLab:** PDF report generation.
- **python-docx:** DOCX report generation.
- **Pytest:** Backend testing.

### Database and Configuration

- **SQLite:** Local prototype database for users, inspections, declarations, rule evaluations, review actions, and audit logs.
- **JSON rules:** Configurable compliance rules are stored in `backend/rules/rules.json`.
- **Vite proxy:** Frontend `/api` and `/uploads` requests are forwarded to the FastAPI backend on port `8000`.

## Solution Workflow

```mermaid
flowchart TD
    A[Legal Metrology officer opens SMART-LM] --> B[Login and role-based access]
    B --> C[Upload or capture package-label image]
    C --> D{Image readable?}
    D -- No --> E[Request clearer image or manual inspection]
    D -- Yes --> F[Validate file type and upload size]
    F --> G[Assess image quality with OpenCV]
    G --> H[Preprocess image variants]
    H --> I[Run PaddleOCR or Tesseract fallback]
    I --> J[Extract mandatory declarations]
    J --> K[Run targeted MRP digit recognition when needed]
    K --> L[Compare declarations with Legal Metrology rules]
    L --> M{Compliance result}
    M -- Compliant --> N[Show verified compliant result]
    M -- Missing or invalid field --> O[Flag potential violation]
    M -- Low OCR confidence --> P[Send to human reviewer]
    O --> Q[Display evidence and rule reference]
    P --> R[Reviewer confirms, rejects, or requests retake]
    N --> S[Save inspection history]
    Q --> S
    R --> S
    S --> T[Generate PDF or DOCX report]
```

### Workflow Stages

1. **Authentication:** The user logs in as an inspector, reviewer, or administrator.
2. **Image submission:** The inspector uploads a supported package-label image.
3. **Image preparation:** The backend checks quality and creates OCR-friendly image variants.
4. **OCR processing:** Text and bounding boxes are detected from the package label.
5. **Field extraction:** Deterministic patterns identify mandatory declarations; the MRP crop receives an additional digit-focused OCR pass when necessary.
6. **Compliance evaluation:** Each extracted field is evaluated against the rules in `rules.json`.
7. **Decision support:** The system displays status, confidence, evidence text, and rule references.
8. **Human review:** Low-confidence or potentially non-compliant cases are reviewed by an authorized reviewer.
9. **Storage and reporting:** Results, declarations, evaluations, and review actions are stored and can be exported as reports.
