# DataLens 🔍
### Data Cleaning, Quality Analysis, Visualization, and Export Platform

DataLens is a full-stack data analytics and cleaning platform built with **FastAPI**, **React**, **Tailwind CSS**, and **Apache ECharts**. It provides an end-to-end workflow to upload real datasets, profile data quality issues, apply non-destructive cleaning transformations with full versioning and undo, explore data with interactive charts, and export sanitized results.

---

## 🚀 Setting Up on a New Device

Follow these step-by-step instructions to set up and run DataLens from scratch on any new device (Linux, macOS, or Windows).

### 1. Prerequisites
Ensure your machine has the following installed:
- **Python 3.10+**: Check with `python3 --version` (or `python --version` on Windows)
- **Node.js 18+** & **npm**: Check with `node -v` and `npm -v`
- **Git** (if cloning from a repository)

---

### 2. Backend Setup (Terminal 1)

1. Open your terminal and navigate to the backend folder:
   ```bash
   cd DataLens/backend
   ```

2. Create a Python virtual environment:
   ```bash
   python3 -m venv venv
   ```
   *(On Windows, use: `python -m venv venv`)*

3. Activate the virtual environment:
   - **Linux / macOS**:
     ```bash
     source venv/bin/activate
     ```
   - **Windows (Command Prompt / PowerShell)**:
     ```cmd
     venv\Scripts\activate
     ```

4. Install the backend dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. *(Optional)* Run backend verification tests:
   ```bash
   PYTHONPATH=. pytest tests/test_integration.py -v
   ```

6. Start the FastAPI backend server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   - Backend API will be live at: `http://localhost:8000`
   - Interactive Swagger API documentation: `http://localhost:8000/docs`

---

### 3. Frontend Setup (Terminal 2)

1. Open a **second terminal window** and navigate to the frontend folder:
   ```bash
   cd DataLens/frontend
   ```

2. Install npm dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   - Open your browser at: `http://localhost:5173`

---

### 4. Testing with Sample Data

A synthetic dataset containing common real-world data quality issues (missing values, duplicates, whitespace, outliers, and invalid emails) is included in the project:
```
DataLens/sample_data/employees_sample.csv
```
Upload this file on the `/upload` page to test the complete workflow:
1. **Upload & Preview**: See real columns and paginated rows.
2. **Quality Profiling**: Review missing cell counts, data types, and detected anomalies.
3. **Cleaning Studio**: Preview and apply deduplication, median imputation, or outlier removal.
4. **Interactive Charts**: Render automatic suggestions or custom bar/line/scatter charts.
5. **Export**: Download sanitized CSV, Excel workbook, or JSON audit reports.

---

### 🌐 Accessing Across a Local Network (LAN)

To access DataLens from another computer or mobile device on the same Wi-Fi:
1. Start the frontend with the `--host` flag:
   ```bash
   npm run dev -- --host
   ```
2. Open `http://<YOUR_COMPUTER_LOCAL_IP>:5173` on the other device.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.12, FastAPI, Pandas, NumPy, SQLAlchemy, Pydantic, Uvicorn, OpenPyXL.
- **Frontend**: React 18, Vite, Tailwind CSS, Apache ECharts (`echarts-for-react`), React Router 6, Lucide React.
- **Database**: SQLite (default zero-config local development) or PostgreSQL (production).

---

## 📚 Architectural & Learning Documentation

For software engineering interviews and in-depth study of the implementation:
- [Architecture Overview](docs/ARCHITECTURE.md): Modular monolith patterns and design choices.
- [Data Flow Lifecycle](docs/DATA_FLOW.md): Step-by-step lifecycle from ingestion to export.
- [REST API Reference](docs/API.md): Detailed endpoint definitions, request bodies, and responses.
- [Step-by-Step Learning Guide](docs/LEARNING_GUIDE.md): 10-stage interview guide breaking down key functions.
- [ETL Pipeline Documentation](docs/ETL_PIPELINE.md): Production ETL pipeline with dead-letter queue and retry guide.
- [Testing Guide](docs/TESTING.md): Verification test suites and coverage instructions.
