import uuid
import re
import numpy as np
import pandas as pd
from typing import List, Dict, Any

class IssueDetector:
    @staticmethod
    def detect_issues(df: pd.DataFrame) -> List[Dict[str, Any]]:
        issues = []
        total_rows = len(df)
        if total_rows == 0:
            return [{
                "id": str(uuid.uuid4()),
                "category": "empty_dataset",
                "severity": "high",
                "column_name": None,
                "affected_rows": 0,
                "description": "Dataset has 0 rows.",
                "suggested_action": "upload_data",
                "suggestion_rationale": "Cannot process empty dataset.",
                "example_values": []
            }]

        # 1. Duplicate rows
        dup_mask = df.duplicated()
        dup_count = int(dup_mask.sum())
        if dup_count > 0:
            dup_examples = df[dup_mask].head(2).to_dict(orient="records")
            issues.append({
                "id": str(uuid.uuid4()),
                "category": "duplicates",
                "severity": "medium",
                "column_name": None,
                "affected_rows": dup_count,
                "description": f"Found {dup_count} duplicate rows in dataset.",
                "suggested_action": "remove_duplicates",
                "suggestion_rationale": "Exact duplicate rows can bias statistical metrics and machine learning models.",
                "example_values": [str(d) for d in dup_examples]
            })

        for col in df.columns:
            series = df[col]
            missing_count = int(series.isna().sum())
            non_missing_count = total_rows - missing_count
            non_missing_series = series.dropna()

            # 2. Empty columns
            if missing_count == total_rows:
                issues.append({
                    "id": str(uuid.uuid4()),
                    "category": "empty_column",
                    "severity": "high",
                    "column_name": col,
                    "affected_rows": total_rows,
                    "description": f"Column '{col}' is completely empty (100% missing values).",
                    "suggested_action": "remove_empty_columns",
                    "suggestion_rationale": "Empty columns provide no informational value and consume memory.",
                    "example_values": []
                })
                continue

            # 3. Missing values
            if missing_count > 0:
                missing_pct = round((missing_count / total_rows) * 100, 1)
                is_numeric = pd.api.types.is_numeric_dtype(non_missing_series)
                
                # Determine suggested action & rationale
                if is_numeric:
                    suggested_action = "fill_median"
                    rationale = f"Fill {missing_count} ({missing_pct}%) missing numeric values with the column median to preserve distribution."
                else:
                    suggested_action = "fill_mode"
                    rationale = f"Fill {missing_count} ({missing_pct}%) missing categorical/text values with the most frequent value (mode)."

                severity = "high" if missing_pct > 30 else "medium"
                issues.append({
                    "id": str(uuid.uuid4()),
                    "category": "missing_values",
                    "severity": severity,
                    "column_name": col,
                    "affected_rows": missing_count,
                    "description": f"Column '{col}' has {missing_count} missing values ({missing_pct}%).",
                    "suggested_action": suggested_action,
                    "suggestion_rationale": rationale,
                    "example_values": []
                })

            # 4. Constant columns
            if non_missing_count > 1 and series.nunique(dropna=True) == 1:
                val = str(non_missing_series.iloc[0])
                issues.append({
                    "id": str(uuid.uuid4()),
                    "category": "constant_column",
                    "severity": "low",
                    "column_name": col,
                    "affected_rows": total_rows,
                    "description": f"Column '{col}' has only one constant value across all rows: '{val}'.",
                    "suggested_action": "remove_constant_columns",
                    "suggestion_rationale": "Zero variance features usually provide no predictive or analytical utility.",
                    "example_values": [val]
                })

            # 5. Whitespace in strings
            if non_missing_series.dtype == object or isinstance(non_missing_series.iloc[0], str):
                str_series = non_missing_series.astype(str)
                has_whitespace = str_series.str.startswith(" ") | str_series.str.endswith(" ")
                whitespace_count = int(has_whitespace.sum())
                if whitespace_count > 0:
                    ws_examples = str_series[has_whitespace].head(3).tolist()
                    issues.append({
                        "id": str(uuid.uuid4()),
                        "category": "whitespace",
                        "severity": "low",
                        "column_name": col,
                        "affected_rows": whitespace_count,
                        "description": f"Column '{col}' contains {whitespace_count} values with leading or trailing whitespace.",
                        "suggested_action": "trim_whitespace",
                        "suggestion_rationale": "Trailing or leading spaces cause joins, filtering, and groupings to fail silently.",
                        "example_values": ws_examples
                    })

                # Inconsistent casing check
                # If there are variations in casing, e.g. "HR", "hr", "Hr"
                lowered = str_series.str.lower()
                if str_series.nunique() > lowered.nunique():
                    diff_count = str_series.nunique() - lowered.nunique()
                    issues.append({
                        "id": str(uuid.uuid4()),
                        "category": "inconsistent_casing",
                        "severity": "low",
                        "column_name": col,
                        "affected_rows": diff_count,
                        "description": f"Column '{col}' has case inconsistencies ({str_series.nunique()} distinct vs {lowered.nunique()} lower-case).",
                        "suggested_action": "normalize_case",
                        "suggestion_rationale": "Inconsistent casing creates artificial duplicate categories in groupings.",
                        "example_values": str_series.head(4).tolist()
                    })

                # Invalid email detection if column name suggests email or contains @
                if "email" in col.lower() or str_series.str.contains("@").mean() > 0.3:
                    email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
                    invalid_emails = ~str_series.str.match(email_pattern)
                    invalid_email_count = int(invalid_emails.sum())
                    if invalid_email_count > 0:
                        examples = str_series[invalid_emails].head(3).tolist()
                        issues.append({
                            "id": str(uuid.uuid4()),
                            "category": "invalid_email",
                            "severity": "medium",
                            "column_name": col,
                            "affected_rows": invalid_email_count,
                            "description": f"Column '{col}' contains {invalid_email_count} invalid email addresses.",
                            "suggested_action": "filter_rows",
                            "suggestion_rationale": "Email addresses should match standard user@domain.tld formatting.",
                            "example_values": examples
                        })

            # 6. Potential Outliers (IQR Method for numeric columns)
            numeric_vals = pd.to_numeric(non_missing_series, errors="coerce").dropna()
            if len(numeric_vals) >= 8:  # Only for sufficiently populated columns
                q1 = float(numeric_vals.quantile(0.25))
                q3 = float(numeric_vals.quantile(0.75))
                iqr = q3 - q1
                if iqr > 0:
                    lower_bound = round(q1 - 1.5 * iqr, 2)
                    upper_bound = round(q3 + 1.5 * iqr, 2)
                    outliers_mask = (numeric_vals < lower_bound) | (numeric_vals > upper_bound)
                    outlier_count = int(outliers_mask.sum())
                    if outlier_count > 0:
                        examples = [str(x) for x in numeric_vals[outliers_mask].head(3).tolist()]
                        issues.append({
                            "id": str(uuid.uuid4()),
                            "category": "outliers",
                            "severity": "medium",
                            "column_name": col,
                            "affected_rows": outlier_count,
                            "description": f"Column '{col}' has {outlier_count} potential outliers outside [{lower_bound}, {upper_bound}].",
                            "suggested_action": "handle_outliers",
                            "suggestion_rationale": f"Values below {lower_bound} or above {upper_bound} (1.5x IQR rule) may distort summary statistics.",
                            "example_values": examples
                        })

        return issues
