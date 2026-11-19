# LogLens AI — Log File Parser & AI-Assisted Log Visualization System

> **College Data Visualization Project (DVP)**  
> An end-to-end, domain-specific platform for ingesting raw, unstructured log files, normalizing them into structured schemas, computing high-performance Pandas analytics, and leveraging AI to recommend and render interactive operational visualizations.

---

## 🌟 Overview & Key Capabilities

LogLens AI is designed specifically for **observability and systems reliability engineering (SRE)**. Rather than being a generic CSV dashboard, it handles the nuances of real-world operational logs:

1. **Modular Parser Engine & Format Registry**:
   - **Common Timestamped Microservices Logs**: Extracted timestamps, severities, services, status codes, and latency tokens.
   - **Python Logs with Multiline Stack Traces**: Tracebacks (`Traceback (most recent call last):`) are automatically grouped into the parent log event without dropping lines.
   - **Apache/Nginx Web Server Access Logs**: Parses client IPs, timestamps, HTTP methods, endpoints, response codes, sizes, and request durations.
   - **JSON Lines Logs (`.jsonl`)**: Dynamic schema mapping for varied naming conventions (`@timestamp`, `level`, `duration_ms`, etc.).
   - **CSV / Delimited Logs**: Column mapping for custom delimited formats.
   - **Automatic Format Detection**: Heuristic scoring engine inspects sample lines and identifies the most confident parser.
   - **Malformed Line Preservation**: Every invalid line is preserved with its original source line number and downloadable for debugging.

2. **Verified Analytics & Anomaly Detection**:
   - Computes exact error/warning/info/debug ratios.
   - Ranks top recurring error signatures by frequency and affected services.
   - Computes latency percentiles: Average, Median, p90, p95, and p99 tail outliers.
   - Statistical Anomaly Detection: Labels sudden error surges (`> mean + 2*std`), volume bursts, and service failure spikes using transparent heuristics.
   - Hourly and daily error activity density matrices (heatmaps).

3. **AI-Assisted Visualization Recommendations with Allowlist Validation**:
   - Inspects dataset profile and metadata.
   - Proposes targeted chart types (`line`, `stacked_bar`, `bar`, `pie`, `donut`, `histogram`, `heatmap`), analytical questions, and suitability scores.
   - **Safety Boundary**: The AI only recommends the chart metadata; the backend deterministically calculates all chart values from the raw data.
   - **Deterministic Fallback**: Runs locally when Gemini is unconfigured or unavailable.

4. **Recommendation Evaluation & Decision Tracking**:
   - Users can **Accept**, **Reject** (with reason), or **Modify** (change chart type) recommendations.
   - Calculates acceptance rate: `(Accepted Recommendations / Total Proposed) * 100`.
   - Generates an audit report comparing original AI proposals against human selections.

5. **AI-Assisted SRE Investigation**:
   - Natural language queries (e.g. *"What should I inspect first?"*, *"Which service generates the most errors?"*, *"When did errors surge?"*).
   - Separates **Observed Empirical Evidence** (factual calculations) from **Working Hypotheses** and **Recommended Action Items**.

6. **Comprehensive Artifact Export**:
   - Normalized CSV table export.
   - Full JSON object array export.
   - Unparsed / malformed lines `.txt` export for regex tuning.
   - Self-contained printable HTML / PDF summary report.

---

## 🛠️ Technology Stack

- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Lucide React, Recharts.
- **Backend**: Python 3.12, FastAPI, Pandas, NumPy, Regular Expressions, Pydantic v2.
- **AI Integration**: Optional Gemini API (`gemini-3.5-flash-lite`) with a local rule-based fallback.
- **Testing**: Pytest, Pytest-Asyncio, FastAPI TestClient.

---

## 📁 Repository Structure

```text
d:\dvp\
├── run_app.py                 # Single-command application runner
├── backend\
│   ├── app\
│   │   ├── config.py          # Environment configs, file limits, paths
│   │   ├── main.py            # FastAPI entrypoint with CORS & static mount
│   │   ├── models\
│   │   │   └── schemas.py     # Pydantic models for entries, analytics, recs, evals
│   │   ├── parsers\           # Modular parsing engine
│   │   │   ├── base.py        # BaseParser interface & normalizers
│   │   │   ├── app_log.py     # Microservice timestamped parser
│   │   │   ├── python_log.py  # Python parser with multiline tracebacks
│   │   │   ├── access_log.py  # Nginx/Apache Combined/CLF parser
│   │   │   ├── json_log.py    # JSON Lines parser
│   │   │   ├── csv_log.py     # Delimited CSV parser
│   │   │   └── registry.py    # Parser registry & auto-detection
│   │   ├── services\
│   │   │   ├── storage.py     # Session storage & profiling
│   │   │   ├── analytics.py   # Pandas analytics & anomaly engine
│   │   │   ├── ai_recommender.py # AI recommender with allowlist validation
│   │   │   ├── investigator.py   # Factual query engine & AI investigator
│   │   │   ├── exporter.py       # CSV, JSON, TXT & HTML report generator
│   │   │   └── sample_generator.py # Synthetic sample generator
│   │   └── api\
│   │       └── routes.py      # REST API endpoints
│   ├── tests\                 # Comprehensive unit & E2E tests
│   ├── samples\               # 5 synthetic realistic sample logs
│   ├── requirements.txt
│   └── .env.example
├── frontend\
│   ├── src\
│   │   ├── api\client.ts      # Typed API client
│   │   ├── types\index.ts     # TypeScript models
│   │   ├── components\
│   │   │   ├── layout\        # Header, Sidebar
│   │   │   ├── upload\        # LogUploader, DataQualityView
│   │   │   ├── explorer\      # Searchable table, filter bar, modal
│   │   │   ├── analytics\     # KPI cards, anomalies, service tables
│   │   │   ├── recommendations\ # AI Rec cards, evaluation tracker
│   │   │   ├── visualizations\ # Recharts dashboards
│   │   │   ├── investigate\   # SRE question interface
│   │   │   ├── export\        # Export modal
│   │   │   └── info\          # Project synopsis modal
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
└── README.md
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.12)
- Node.js 18+ & npm (tested on Node v22.14)

### Option 1: One-Command All-in-One Runner (Recommended)

Run the root launcher script:
```powershell
python run_app.py
```
This script will:
1. Verify the Python virtual environment and dependencies.
2. Generate all synthetic sample logs under `backend/samples/` if missing.
3. Build the frontend assets under `frontend/dist/`.
4. Launch the unified FastAPI web server on `http://127.0.0.1:8000`.

Open your browser to: **`http://127.0.0.1:8000`**

---

### Option 2: Running Backend & Frontend in Development Mode

#### 1. Backend Setup
```powershell
cd d:\dvp\backend
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# (Optional) Copy the example, then set GEMINI_API_KEY in .env
Copy-Item .env.example .env

# Generate synthetic samples
$env:PYTHONPATH="."
python -m app.services.sample_generator

# Start FastAPI server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be available at: `http://127.0.0.1:8000/docs`

#### 2. Frontend Setup
```powershell
cd d:\dvp\frontend
# Install dependencies
npm install

# Run Vite development server (with built-in API proxy to port 8000)
npm run dev
```
Development UI will be available at: `http://localhost:5173`

---

## 🧪 Running the Test Suite

The test suite thoroughly covers all parser engines, edge-case timestamps, multiline Python tracebacks, analytics calculations, anomaly detection, AI fallback, recommendation evaluation metrics, and end-to-end API workflows.

Run all tests via pytest:
```powershell
cd d:\dvp
$env:PYTHONPATH="backend"
backend\venv\Scripts\pytest.exe backend\tests -v
```

### Verified Test Cases:
- `test_level_normalization`: Normalizes `WARN` -> `WARNING`, `ERR` -> `ERROR`, `CRIT`/`FATAL` -> `CRITICAL`.
- `test_timestamp_parsing`: Handles ISO, Python comma milliseconds, Apache CLF timestamps, and malformed inputs.
- `test_app_log_parser`: Validates microservices format and auxiliary token extraction (status codes, latency).
- `test_python_log_parser_multiline_stack_traces`: Tests traceback grouping without losing stack lines.
- `test_access_log_parser`: Tests Apache/Nginx Combined log parsing, status codes, and latency extraction.
- `test_json_log_parser`: Tests JSON Lines parsing and key alias resolution.
- `test_csv_log_parser`: Tests CSV parsing, delimiter sniffing, and column mapping.
- `test_registry_detection`: Validates confidence scoring and automatic format detection.
- `test_analytics_and_anomalies`: Validates Pandas aggregations, top error groupings, and z-score anomaly rules.
- `test_ai_recommender_fallback_and_allowlist`: Validates strict allowlists and offline fallback.
- `test_investigator_factual_calculation`: Tests verified SRE evidence calculation.
- `test_evaluations_and_acceptance_rate`: Tests human-in-the-loop tracking and acceptance rate calculation.
- `test_exporter`: Tests CSV, JSON, and unparsed lines text exports.
- `test_complete_end_to_end_dvp_workflow`: Tests the full user journey from sample intake to PDF/HTML report.

---

## ⚙️ Environment Configuration

Configuration is managed via environment variables (or a `backend/.env` file):

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | *Empty* | Optional Gemini API key. With no key, both AI features use local rules. |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | Gemini model for chart recommendations and investigation suggestions. |
| `PORT` | `8000` | Server listening port. |
| `HOST` | `0.0.0.0` | Server host binding. |
| `MAX_FILE_SIZE_MB` | `50` | Maximum file size for upload. |

Create a key in [Google AI Studio](https://aistudio.google.com/api-keys), set it in `backend/.env`,
and restart the backend. The recommendations and investigation screens indicate when Gemini contributed
or local rules were used. Backend logs report Gemini request failures. Chart recommendations send
dataset metadata to Gemini. Investigations send the question and derived findings, which can include
log message excerpts, service names and request paths.

---

## 📊 End-to-End Workflow Demonstration

1. **Upload & Intake**:
   - Drag and drop any `.log`, `.txt`, `.csv`, `.json`, or `.jsonl` file.
   - Alternatively, click any synthetic sample:
     - `application.log`: Microservices application with database bursts & malformed lines.
     - `python_app.log`: Python exceptions with full multiline tracebacks.
     - `web_access.log`: Nginx access logs with varied HTTP status codes and response latencies.
     - `service_events.jsonl`: JSON Lines structured event stream.
     - `system_audit.csv`: Delimited audit logs with custom column headers.
2. **Format Review & Execution**:
   - Confirm detected parser and fit score.
   - Click **Execute Parser Engine**.
3. **Data Quality Review**:
   - Review success rate percentage and schema coverage.
   - Download any unparsed lines for regex inspection.
4. **Log Explorer**:
   - Search across messages and raw text.
   - Filter by severity, service, or HTTP status code.
   - Click the expand icon to inspect the raw line and extracted fields.
5. **Analytics & Anomalies**:
   - Inspect KPI cards, heuristic anomaly alerts, top error signatures, and service failure rankings.
6. **AI Recommendations**:
   - Review proposed charts with suitability scores and analytical questions.
   - Click **Accept**, **Reject** (with reason), or **Modify** (custom chart type).
7. **Interactive Visualizations**:
   - Explore Recharts visualizations: volume over time, severity stacked bars, service errors, top recurring errors, donut severity distribution, HTTP status code distribution, latency histogram, and day/hour activity heatmap.
8. **AI SRE Investigation**:
   - Ask questions like *"What should I inspect first?"* or *"Which service generates the most errors?"* to receive verified empirical evidence, working hypotheses, and action items.
9. **Evaluation Audit Report**:
   - View the acceptance rate and the comparison matrix of proposed vs. user-selected visualizations.
10. **Export & Report**:
    - Download normalized CSV, JSON, unparsed lines `.txt`, or generate a printable HTML report.

---

## ⚠️ Known Limitations & Scope Boundaries

- **Log Content Untrusted Boundary**: Log strings are sanitized and never executed as commands or prompt instructions.
- **Timestamp Coverage**: If an uploaded format lacks timestamps, time-series charts will display an informative banner suggesting categorical aggregations instead.
- **Acceptance Rate Interpretation**: The acceptance rate is a metric of human alignment with recommendations, not an objective benchmark of AI accuracy.

