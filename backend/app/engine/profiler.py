import re
import numpy as np
import pandas as pd
from typing import Dict, Any, List

class DataProfiler:
    @staticmethod
    def infer_column_type(series: pd.Series) -> str:
        """Infer intelligent column type: integer, decimal, boolean, datetime, categorical, or text."""
        # Non-null values
        valid_series = series.dropna()
        if len(valid_series) == 0:
            return "empty"

        # Check boolean
        unique_vals = set(valid_series.astype(str).str.strip().str.lower().unique())
        if unique_vals.issubset({"true", "false", "0", "1", "yes", "no", "t", "f"}):
            return "boolean"

        # Check numeric types
        if pd.api.types.is_numeric_dtype(valid_series):
            # Check if all are integer values
            if (valid_series % 1 == 0).all():
                return "integer"
            return "decimal"

        # Try parsing strings as numeric, but protect codes/IDs like "00123"
        str_vals = valid_series.astype(str).str.strip()
        has_leading_zero_code = str_vals.str.match(r"^0\d+$").any()
        if not has_leading_zero_code:
            try:
                converted = pd.to_numeric(str_vals, errors="raise")
                if (converted % 1 == 0).all():
                    return "integer"
                return "decimal"
            except Exception:
                pass

        # Try parsing as datetime if string-like and formatted
        # Only test if string values look like dates (contain -, /, or :)
        date_pattern = r"^(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})"
        if str_vals.str.contains(date_pattern, regex=True).mean() > 0.6:
            try:
                pd.to_datetime(str_vals, errors="raise", format="mixed")
                return "datetime"
            except Exception:
                pass

        # Check cardinality for categorical vs free-form text
        unique_count = valid_series.nunique()
        total_count = len(valid_series)
        avg_len = str_vals.str.len().mean()

        if unique_count <= 50 or (unique_count / total_count < 0.2 and avg_len < 40):
            return "categorical"
        
        return "text"

    @classmethod
    def profile_dataframe(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute comprehensive dataset and column-level statistics."""
        total_rows = len(df)
        total_cols = len(df.columns)

        if total_rows == 0:
            return {
                "summary": {
                    "total_rows": 0,
                    "total_columns": total_cols,
                    "duplicate_rows": 0,
                    "empty_rows": 0,
                    "empty_columns": total_cols,
                    "total_missing_cells": 0,
                    "missing_percentage": 0.0,
                    "numeric_columns_count": 0,
                    "categorical_columns_count": 0,
                    "datetime_columns_count": 0,
                    "boolean_columns_count": 0,
                },
                "columns": []
            }

        duplicate_rows = int(df.duplicated().sum())
        empty_rows = int(df.isna().all(axis=1).sum())
        total_missing = int(df.isna().sum().sum())
        total_cells = total_rows * total_cols
        missing_pct = round((total_missing / total_cells) * 100, 2) if total_cells > 0 else 0.0

        num_count = 0
        cat_count = 0
        date_count = 0
        bool_count = 0
        empty_col_count = 0

        columns_profile = []

        for col_name in df.columns:
            series = df[col_name]
            inferred_type = cls.infer_column_type(series)
            
            missing_count = int(series.isna().sum())
            non_missing = total_rows - missing_count
            col_missing_pct = round((missing_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
            unique_count = int(series.nunique(dropna=True))
            unique_pct = round((unique_count / non_missing) * 100, 2) if non_missing > 0 else 0.0

            if inferred_type == "integer" or inferred_type == "decimal":
                num_count += 1
            elif inferred_type == "categorical":
                cat_count += 1
            elif inferred_type == "datetime":
                date_count += 1
            elif inferred_type == "boolean":
                bool_count += 1
            elif inferred_type == "empty":
                empty_col_count += 1

            # Examples (up to 5 unique non-null values)
            examples = [str(x) for x in series.dropna().unique()[:5]]

            # Numeric metrics
            min_val = None
            max_val = None
            mean_val = None
            median_val = None
            std_val = None

            if inferred_type in ("integer", "decimal"):
                num_series = pd.to_numeric(series, errors="coerce").dropna()
                if len(num_series) > 0:
                    min_val = float(num_series.min())
                    max_val = float(num_series.max())
                    mean_val = round(float(num_series.mean()), 2)
                    median_val = round(float(num_series.median()), 2)
                    std_val = round(float(num_series.std()), 2) if len(num_series) > 1 else 0.0

            # Most frequent value
            most_frequent = None
            if non_missing > 0:
                mode_vals = series.mode(dropna=True)
                if not mode_vals.empty:
                    most_frequent = str(mode_vals.iloc[0])

            columns_profile.append({
                "column_name": col_name,
                "inferred_type": inferred_type,
                "missing_count": missing_count,
                "missing_percentage": col_missing_pct,
                "non_missing_count": non_missing,
                "unique_count": unique_count,
                "unique_percentage": unique_pct,
                "examples": examples,
                "min": min_val,
                "max": max_val,
                "mean": mean_val,
                "median": median_val,
                "std": std_val,
                "most_frequent": most_frequent
            })

        return {
            "summary": {
                "total_rows": total_rows,
                "total_columns": total_cols,
                "duplicate_rows": duplicate_rows,
                "empty_rows": empty_rows,
                "empty_columns": empty_col_count,
                "total_missing_cells": total_missing,
                "missing_percentage": missing_pct,
                "numeric_columns_count": num_count,
                "categorical_columns_count": cat_count,
                "datetime_columns_count": date_count,
                "boolean_columns_count": bool_count,
            },
            "columns": columns_profile
        }
