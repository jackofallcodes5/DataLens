import pytest
import io
import pandas as pd
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SAMPLE_CSV = """EmployeeID,Name,Department,Salary,JoiningDate,Email
101, Alice Smith ,Engineering,85000,2021-03-15,alice@example.com
102,Bob Jones,Marketing,62000,2020-07-01,bob@example.com
103,Charlie Brown,Engineering,,2019-11-20,charlie@example.com
104,Diana Prince,HR,58000,15/01/2022,diana@example.com
105,Evan Wright ,Finance,71000,2021-09-10,invalid-email
106,Fiona Gallagher,Engineering,89000,2018-05-23,fiona@example.com
107,George Clark,Marketing,,2022-02-14,george@example.com
108,Hannah Abbott,HR,59000,2021-12-01,hannah@example.com
109,Ian Malcolm,Finance,450000,2017-04-12,ian@example.com
102,Bob Jones,Marketing,62000,2020-07-01,bob@example.com
"""

def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

def test_full_workflow():
    # 1. Upload CSV
    file_bytes = io.BytesIO(SAMPLE_CSV.encode("utf-8"))
    res = client.post(
        "/api/datasets",
        files={"file": ("test_employees.csv", file_bytes, "text/csv")}
    )
    assert res.status_code == 201
    dataset = res.json()
    dataset_id = dataset["id"]
    assert dataset["row_count"] == 10
    assert dataset["column_count"] == 6

    # 2. Preview
    res = client.get(f"/api/datasets/{dataset_id}/preview?page=1&page_size=5")
    assert res.status_code == 200
    preview = res.json()
    assert len(preview["rows"]) == 5
    assert preview["total_rows"] == 10

    # 3. Profile & Issues
    res = client.get(f"/api/datasets/{dataset_id}/profile")
    assert res.status_code == 200
    profile = res.json()
    assert profile["summary"]["duplicate_rows"] == 1
    assert profile["summary"]["total_missing_cells"] == 2

    res = client.get(f"/api/datasets/{dataset_id}/issues")
    assert res.status_code == 200
    issues = res.json()
    categories = [i["category"] for i in issues]
    assert "duplicates" in categories
    assert "missing_values" in categories

    # 4. Preview Cleaning (Remove Duplicates)
    res = client.post(
        f"/api/datasets/{dataset_id}/clean/preview",
        json={"operation_type": "remove_duplicates", "parameters": {}}
    )
    assert res.status_code == 200
    clean_preview = res.json()
    assert clean_preview["expected_rows"] == 9
    assert clean_preview["rows_affected"] == 1

    # 5. Apply Cleaning (Remove Duplicates)
    res = client.post(
        f"/api/datasets/{dataset_id}/clean/apply",
        json={"operation_type": "remove_duplicates", "parameters": {}}
    )
    assert res.status_code == 200
    apply_res = res.json()
    assert apply_res["success"] is True
    assert apply_res["new_version_number"] == 2

    # Verify latest dataset row count updated to 9
    res = client.get(f"/api/datasets/{dataset_id}")
    assert res.json()["row_count"] == 9

    # 6. Apply Missing Values Imputation (Salary with Median)
    res = client.post(
        f"/api/datasets/{dataset_id}/clean/apply",
        json={
            "operation_type": "handle_missing_values",
            "parameters": {"column": "Salary", "strategy": "median"}
        }
    )
    assert res.status_code == 200
    assert res.json()["new_version_number"] == 3

    # Check profile now has 0 missing salaries
    res = client.get(f"/api/datasets/{dataset_id}/profile")
    salary_col = next(c for c in res.json()["columns"] if c["column_name"] == "Salary")
    assert salary_col["missing_count"] == 0

    # 7. Undo Cleaning
    res = client.post(f"/api/datasets/{dataset_id}/undo")
    assert res.status_code == 200
    undone_version = res.json()
    assert undone_version["version_number"] == 2

    # Verify missing salary is back (version 2)
    res = client.get(f"/api/datasets/{dataset_id}/profile")
    salary_col = next(c for c in res.json()["columns"] if c["column_name"] == "Salary")
    assert salary_col["missing_count"] == 2

    # 8. Visualization data generation
    res = client.post(
        f"/api/datasets/{dataset_id}/charts/data",
        json={
            "chart_type": "bar",
            "x_axis": "Department",
            "y_axis": "Salary",
            "aggregation": "avg"
        }
    )
    assert res.status_code == 200
    chart_data = res.json()
    assert "categories" in chart_data
    assert "series" in chart_data
    assert len(chart_data["categories"]) > 0

    # 9. Chart Recommendations
    res = client.get(f"/api/datasets/{dataset_id}/charts/recommendations")
    assert res.status_code == 200
    recs = res.json()
    assert len(recs) > 0

    # 10. Save Chart
    res = client.post(
        "/api/charts",
        json={
            "dataset_id": dataset_id,
            "title": "Avg Salary by Dept",
            "chart_type": "bar",
            "configuration": {"x_axis": "Department", "y_axis": "Salary", "aggregation": "avg"}
        }
    )
    assert res.status_code == 201
    chart_id = res.json()["id"]

    # 11. Export CSV
    res = client.get(f"/api/datasets/{dataset_id}/export?format=csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "EmployeeID" in res.text

    # 12. Export Excel
    res = client.get(f"/api/datasets/{dataset_id}/export?format=xlsx")
    assert res.status_code == 200
    assert "openxmlformats" in res.headers["content-type"]

    # 13. Export Report
    res = client.get(f"/api/datasets/{dataset_id}/export?format=report")
    assert res.status_code == 200
    report = res.json()
    assert report["dataset_name"] == "test_employees.csv"
    assert "profile_summary" in report

    print("\n--- ALL BACKEND INTEGRATION & WORKFLOW TESTS PASSED ---")
