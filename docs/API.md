# DataLens REST API Reference

All endpoints are served under the `/api` route prefix.

### Health
- **`GET /api/health`**
  - Response: `{"status": "healthy", "service": "DataLens", "debug": true, "storage": "connected"}`

### Projects
- **`GET /api/projects`**: List all projects.
- **`POST /api/projects`**: Create a new project. Body: `{"name": "...", "description": "..."}`
- **`GET /api/projects/{id}`**: Get project by ID.
- **`PATCH /api/projects/{id}`**: Update project.
- **`DELETE /api/projects/{id}`**: Delete project.

### Datasets
- **`GET /api/datasets`**: List all datasets. Optional query param `project_id`.
- **`POST /api/datasets`**: Upload dataset multipart form `file`. Optional form field `project_id`.
- **`GET /api/datasets/{id}`**: Get dataset metadata.
- **`DELETE /api/datasets/{id}`**: Delete dataset and associated filesystem version files.
- **`GET /api/datasets/{id}/versions`**: List versions for a dataset.
- **`GET /api/datasets/{id}/preview`**: Paginated preview. Query params: `version_id`, `page`, `page_size`.

### Profiling & Issues
- **`GET /api/datasets/{id}/profile`**: Returns summary metrics (row counts, missing percentages, data types) and column-level distributions.
- **`GET /api/datasets/{id}/issues`**: Returns list of detected anomalies (duplicates, missing values, empty columns, whitespace, outliers).

### Cleaning Engine
- **`POST /api/datasets/{id}/clean/preview`**:
  - Simulates transformation in-memory without changing dataset state.
  - Body: `{"operation_type": "...", "parameters": {...}}`
  - Returns expected row count, affected cell count, and before/after sample records.
- **`POST /api/datasets/{id}/clean/apply`**:
  - Executes transformation, writes new version file, logs operation in history, and increments version number.
- **`GET /api/datasets/{id}/history`**:
  - List of past transformations executed on this dataset.
- **`POST /api/datasets/{id}/undo`**:
  - Reverts the dataset's `latest_version_id` to its parent version.

### Visualization
- **`POST /api/datasets/{id}/charts/data`**:
  - Body: `{"chart_type": "bar|line|pie|histogram|scatter", "x_axis": "...", "y_axis": "...", "aggregation": "avg|sum|count|min|max"}`
  - Returns aggregation response compatible with ECharts.
- **`GET /api/datasets/{id}/charts/recommendations`**:
  - Returns rule-based automatic suggestions.
- **`GET /api/charts`**: List saved charts.
- **`POST /api/charts`**: Save a chart configuration.
- **`DELETE /api/charts/{id}`**: Delete a saved chart.

### Exports
- **`GET /api/datasets/{id}/export?format=csv&version_id=...`**: Download cleaned CSV.
- **`GET /api/datasets/{id}/export?format=xlsx&version_id=...`**: Download Excel workbook.
- **`GET /api/datasets/{id}/export?format=report&version_id=...`**: Download JSON audit report.
