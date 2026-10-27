import io
import json
import pandas as pd
from typing import Dict, Any
from fastapi.responses import StreamingResponse
from app.engine.profiler import DataProfiler

class ExportService:
    @staticmethod
    def sanitize_spreadsheet_cell(val: Any) -> Any:
        """Prevent Formula Injection (CSV/Excel injection: =, +, -, @)."""
        if isinstance(val, str) and len(val) > 0:
            if val[0] in ("=", "+", "-", "@", "\t", "\r"):
                return f"'{val}"
        return val

    @classmethod
    def sanitize_dataframe_for_export(cls, df: pd.DataFrame) -> pd.DataFrame:
        df_safe = df.copy()
        for col in df_safe.columns:
            if df_safe[col].dtype == object:
                df_safe[col] = df_safe[col].apply(cls.sanitize_spreadsheet_cell)
        return df_safe

    @classmethod
    def export_csv_stream(cls, df: pd.DataFrame, filename: str) -> StreamingResponse:
        df_safe = cls.sanitize_dataframe_for_export(df)
        stream = io.StringIO()
        df_safe.to_csv(stream, index=False, encoding="utf-8")
        stream.seek(0)
        
        response = StreamingResponse(
            iter([stream.getvalue()]),
            media_type="text/csv"
        )
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}.csv"'
        return response

    @classmethod
    def export_excel_stream(cls, df: pd.DataFrame, filename: str) -> StreamingResponse:
        df_safe = cls.sanitize_dataframe_for_export(df)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_safe.to_excel(writer, index=False, sheet_name="DataLens_Cleaned")
            # Auto-fit column widths
            worksheet = writer.sheets["DataLens_Cleaned"]
            for col in worksheet.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = col[0].column_letter
                worksheet.column_dimensions[col_letter].width = min(max(max_len + 3, 10), 50)

        output.seek(0)
        response = StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}.xlsx"'
        return response

    @classmethod
    def export_quality_report_json(cls, df: pd.DataFrame, dataset_name: str, version_num: int, history: list) -> Dict[str, Any]:
        profile = DataProfiler.profile_dataframe(df)
        return {
            "dataset_name": dataset_name,
            "version_number": version_num,
            "profile_summary": profile["summary"],
            "columns": profile["columns"],
            "cleaning_history": history,
            "system": "DataLens Quality Engine v1.0"
        }
