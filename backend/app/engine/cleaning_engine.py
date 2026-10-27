import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from fastapi import HTTPException

class CleaningEngine:
    @staticmethod
    def remove_duplicates(df: pd.DataFrame, params: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        subset = params.get("columns") or None
        keep = params.get("keep", "first")
        if keep not in ("first", "last", False):
            keep = "first"

        initial_rows = len(df)
        df_cleaned = df.drop_duplicates(subset=subset, keep=keep).copy()
        removed_count = initial_rows - len(df_cleaned)

        summary = {
            "operation": "remove_duplicates",
            "initial_rows": initial_rows,
            "final_rows": len(df_cleaned),
            "affected_count": removed_count,
            "message": f"Successfully removed {removed_count} duplicate row(s)."
        }
        return df_cleaned, summary

    @staticmethod
    def handle_missing_values(df: pd.DataFrame, params: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        column = params.get("column")
        strategy = params.get("strategy")  # drop, mean, median, mode, constant
        constant_value = params.get("value")

        if not column or column not in df.columns:
            raise HTTPException(status_code=400, detail=f"Column '{column}' does not exist in dataset.")

        initial_rows = len(df)
        df_cleaned = df.copy()
        affected = int(df_cleaned[column].isna().sum())

        if strategy == "drop":
            df_cleaned = df_cleaned.dropna(subset=[column]).copy()
            final_rows = len(df_cleaned)
            summary = {
                "operation": "handle_missing_values",
                "strategy": "drop",
                "column": column,
                "initial_rows": initial_rows,
                "final_rows": final_rows,
                "affected_count": affected,
                "message": f"Dropped {initial_rows - final_rows} row(s) with missing values in '{column}'."
            }
            return df_cleaned, summary

        if affected == 0:
            return df_cleaned, {
                "operation": "handle_missing_values",
                "strategy": strategy,
                "column": column,
                "affected_count": 0,
                "message": f"Column '{column}' contains no missing values."
            }

        if strategy in ("mean", "median"):
            num_series = pd.to_numeric(df_cleaned[column], errors="coerce")
            valid_nums = num_series.dropna()
            if len(valid_nums) == 0:
                raise HTTPException(status_code=400, detail=f"Cannot compute {strategy} on non-numeric or completely empty column '{column}'.")
            
            fill_val = float(valid_nums.mean()) if strategy == "mean" else float(valid_nums.median())
            if (valid_nums % 1 == 0).all() and strategy == "median":
                fill_val = int(fill_val)
            df_cleaned[column] = df_cleaned[column].fillna(fill_val)
            applied_val = str(fill_val)

        elif strategy == "mode":
            mode_vals = df_cleaned[column].mode(dropna=True)
            if mode_vals.empty:
                raise HTTPException(status_code=400, detail=f"Cannot compute mode on completely empty column '{column}'.")
            fill_val = mode_vals.iloc[0]
            df_cleaned[column] = df_cleaned[column].fillna(fill_val)
            applied_val = str(fill_val)

        elif strategy == "constant":
            if constant_value is None:
                raise HTTPException(status_code=400, detail="Constant fill value must be specified.")
            df_cleaned[column] = df_cleaned[column].fillna(constant_value)
            applied_val = str(constant_value)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported strategy '{strategy}'.")

        summary = {
            "operation": "handle_missing_values",
            "strategy": strategy,
            "column": column,
            "affected_count": affected,
            "value_applied": applied_val,
            "message": f"Filled {affected} missing cell(s) in '{column}' with {strategy} ({applied_val})."
        }
        return df_cleaned, summary

    @staticmethod
    def trim_whitespace(df: pd.DataFrame, params: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        columns = params.get("columns") or list(df.columns)
        df_cleaned = df.copy()
        affected_cells = 0

        for col in columns:
            if col in df_cleaned.columns:
                series = df_cleaned[col]
                # If object or string
                mask = series.notna() & series.apply(lambda x: isinstance(x, str))
                if mask.any():
                    initial_strs = series[mask]
                    trimmed_strs = initial_strs.str.strip()
                    changed = (initial_strs != trimmed_strs).sum()
                    affected_cells += int(changed)
                    df_cleaned.loc[mask, col] = trimmed_strs

        summary = {
            "operation": "trim_whitespace",
            "affected_count": affected_cells,
            "columns": columns,
            "message": f"Trimmed whitespace across {len(columns)} column(s), modifying {affected_cells} cell(s)."
        }
        return df_cleaned, summary

    @staticmethod
    def normalize_case(df: pd.DataFrame, params: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        columns = params.get("columns")
        case_type = params.get("case", "lower")  # lower, upper, title

        if not columns:
            raise HTTPException(status_code=400, detail="Must select at least one column to normalize casing.")

        df_cleaned = df.copy()
        affected_cells = 0

        for col in columns:
            if col in df_cleaned.columns:
                series = df_cleaned[col]
                mask = series.notna() & series.apply(lambda x: isinstance(x, str))
                if mask.any():
                    initial_strs = series[mask]
                    if case_type == "lower":
                        transformed = initial_strs.str.lower()
                    elif case_type == "upper":
                        transformed = initial_strs.str.upper()
                    elif case_type == "title":
                        transformed = initial_strs.str.title()
                    else:
                        raise HTTPException(status_code=400, detail=f"Unsupported case type '{case_type}'.")
                    
                    changed = (initial_strs != transformed).sum()
                    affected_cells += int(changed)
                    df_cleaned.loc[mask, col] = transformed

        summary = {
            "operation": "normalize_case",
            "case": case_type,
            "affected_count": affected_cells,
            "columns": columns,
            "message": f"Normalized casing ({case_type}) in {len(columns)} column(s), modifying {affected_cells} cell(s)."
        }
        return df_cleaned, summary

    @staticmethod
    def convert_data_types(df: pd.DataFrame, params: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        column = params.get("column")
        target_type = params.get("target_type")  # string, integer, decimal, boolean, datetime
        on_error = params.get("on_error", "coerce")  # coerce (set invalid to null) or raise

        if not column or column not in df.columns:
            raise HTTPException(status_code=400, detail=f"Column '{column}' does not exist.")

        df_cleaned = df.copy()
        initial_series = df_cleaned[column]
        failed_conversions = 0

        try:
            if target_type == "string":
                df_cleaned[column] = initial_series.astype(str)
            elif target_type == "integer":
                converted = pd.to_numeric(initial_series, errors="coerce")
                failed_conversions = int(initial_series.notna().sum() - converted.notna().sum())
                if failed_conversions > 0 and on_error == "raise":
                    raise HTTPException(status_code=400, detail=f"Failed to convert {failed_conversions} value(s) to integer.")
                df_cleaned[column] = converted.astype("Int64")  # Nullable integer
            elif target_type == "decimal":
                converted = pd.to_numeric(initial_series, errors="coerce")
                failed_conversions = int(initial_series.notna().sum() - converted.notna().sum())
                if failed_conversions > 0 and on_error == "raise":
                    raise HTTPException(status_code=400, detail=f"Failed to convert {failed_conversions} value(s) to decimal.")
                df_cleaned[column] = converted
            elif target_type == "boolean":
                # Convert common truthy/falsy values
                lower_str = initial_series.astype(str).str.strip().str.lower()
                true_vals = {"true", "1", "yes", "t"}
                false_vals = {"false", "0", "no", "f"}
                is_valid = lower_str.isin(true_vals | false_vals) | initial_series.isna()
                failed_conversions = int((~is_valid).sum())
                if failed_conversions > 0 and on_error == "raise":
                    raise HTTPException(status_code=400, detail=f"Failed to convert {failed_conversions} value(s) to boolean.")
                
                bool_series = pd.Series(index=df_cleaned.index, dtype="boolean")
                bool_series[lower_str.isin(true_vals)] = True
                bool_series[lower_str.isin(false_vals)] = False
                df_cleaned[column] = bool_series
            elif target_type == "datetime":
                converted = pd.to_datetime(initial_series, errors="coerce", format="mixed")
                failed_conversions = int(initial_series.notna().sum() - converted.notna().sum())
                if failed_conversions > 0 and on_error == "raise":
                    raise HTTPException(status_code=400, detail=f"Failed to parse {failed_conversions} datetime value(s).")
                df_cleaned[column] = converted.dt.strftime("%Y-%m-%d %H:%M:%S").replace({pd.NaT: None})
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported target type '{target_type}'.")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Type conversion failed: {str(e)}")

        summary = {
            "operation": "convert_data_types",
            "column": column,
            "target_type": target_type,
            "failed_conversions": failed_conversions,
            "message": f"Converted column '{column}' to {target_type} ({failed_conversions} unconvertible cells set to null)."
        }
        return df_cleaned, summary

    @staticmethod
    def remove_columns(df: pd.DataFrame, params: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        columns = params.get("columns", [])
        if not columns:
            raise HTTPException(status_code=400, detail="No columns specified for removal.")

        missing = [c for c in columns if c not in df.columns]
        if missing:
            raise HTTPException(status_code=400, detail=f"Columns not found: {missing}")

        if len(columns) >= len(df.columns):
            raise HTTPException(status_code=400, detail="Cannot delete all columns from the dataset.")

        df_cleaned = df.drop(columns=columns).copy()
        summary = {
            "operation": "remove_columns",
            "removed_columns": columns,
            "remaining_columns": len(df_cleaned.columns),
            "message": f"Successfully removed {len(columns)} column(s): {', '.join(columns)}."
        }
        return df_cleaned, summary

    @staticmethod
    def rename_column(df: pd.DataFrame, params: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        old_name = params.get("old_name")
        new_name = params.get("new_name", "").strip()

        if not old_name or old_name not in df.columns:
            raise HTTPException(status_code=400, detail=f"Column '{old_name}' not found.")
        if not new_name:
            raise HTTPException(status_code=400, detail="New column name cannot be empty.")
        if new_name in df.columns and new_name != old_name:
            raise HTTPException(status_code=400, detail=f"Column '{new_name}' already exists.")

        df_cleaned = df.rename(columns={old_name: new_name}).copy()
        summary = {
            "operation": "rename_column",
            "old_name": old_name,
            "new_name": new_name,
            "message": f"Renamed column '{old_name}' to '{new_name}'."
        }
        return df_cleaned, summary

    @staticmethod
    def filter_rows(df: pd.DataFrame, params: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        column = params.get("column")
        operator = params.get("operator")  # equals, not_equals, contains, gt, lt, between, is_missing, is_not_missing
        value = params.get("value")
        value2 = params.get("value2")

        if not column or column not in df.columns:
            raise HTTPException(status_code=400, detail=f"Column '{column}' not found.")

        initial_rows = len(df)
        series = df[column]

        if operator == "is_missing":
            mask = series.isna()
        elif operator == "is_not_missing":
            mask = series.notna()
        elif operator == "equals":
            mask = series.astype(str) == str(value)
        elif operator == "not_equals":
            mask = series.astype(str) != str(value)
        elif operator == "contains":
            mask = series.astype(str).str.contains(str(value), na=False, case=False)
        elif operator in ("gt", "lt", "between"):
            num_series = pd.to_numeric(series, errors="coerce")
            try:
                num_val = float(value)
            except Exception:
                raise HTTPException(status_code=400, detail=f"Value '{value}' must be numeric for numeric filter.")

            if operator == "gt":
                mask = num_series > num_val
            elif operator == "lt":
                mask = num_series < num_val
            elif operator == "between":
                num_val2 = float(value2)
                mask = (num_series >= num_val) & (num_series <= num_val2)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported operator '{operator}'.")

        df_filtered = df[mask].copy()
        removed_count = initial_rows - len(df_filtered)

        summary = {
            "operation": "filter_rows",
            "column": column,
            "operator": operator,
            "initial_rows": initial_rows,
            "final_rows": len(df_filtered),
            "removed_rows": removed_count,
            "message": f"Filter '{operator}' on '{column}' retained {len(df_filtered)} of {initial_rows} rows."
        }
        return df_filtered, summary

    @staticmethod
    def handle_outliers(df: pd.DataFrame, params: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        column = params.get("column")
        action = params.get("action", "remove")  # remove, cap

        if not column or column not in df.columns:
            raise HTTPException(status_code=400, detail=f"Column '{column}' not found.")

        num_series = pd.to_numeric(df[column], errors="coerce")
        valid_nums = num_series.dropna()
        if len(valid_nums) < 4:
            raise HTTPException(status_code=400, detail=f"Insufficient numeric values in '{column}' to compute IQR.")

        q1 = float(valid_nums.quantile(0.25))
        q3 = float(valid_nums.quantile(0.75))
        iqr = q3 - q1
        lower_bound = round(q1 - 1.5 * iqr, 2)
        upper_bound = round(q3 + 1.5 * iqr, 2)

        outlier_mask = (num_series < lower_bound) | (num_series > upper_bound)
        outlier_count = int(outlier_mask.sum())

        df_cleaned = df.copy()
        if action == "remove":
            df_cleaned = df_cleaned[~outlier_mask].copy()
            message = f"Removed {outlier_count} row(s) containing outliers outside [{lower_bound}, {upper_bound}]."
        elif action == "cap":
            clipped = num_series.clip(lower=lower_bound, upper=upper_bound)
            df_cleaned[column] = clipped
            message = f"Capped {outlier_count} outlier value(s) in '{column}' to threshold bounds [{lower_bound}, {upper_bound}]."
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported outlier action '{action}'.")

        summary = {
            "operation": "handle_outliers",
            "column": column,
            "action": action,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "affected_count": outlier_count,
            "message": message
        }
        return df_cleaned, summary

    @classmethod
    def apply_operation(cls, df: pd.DataFrame, op_type: str, params: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        registry = {
            "remove_duplicates": cls.remove_duplicates,
            "handle_missing_values": cls.handle_missing_values,
            "trim_whitespace": cls.trim_whitespace,
            "normalize_case": cls.normalize_case,
            "convert_data_types": cls.convert_data_types,
            "remove_columns": cls.remove_columns,
            "rename_column": cls.rename_column,
            "filter_rows": cls.filter_rows,
            "handle_outliers": cls.handle_outliers,
        }

        if op_type not in registry:
            raise HTTPException(status_code=400, detail=f"Unknown cleaning operation '{op_type}'.")

        return registry[op_type](df, params)
