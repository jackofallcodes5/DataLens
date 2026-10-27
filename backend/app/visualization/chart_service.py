import numpy as np
import pandas as pd
from typing import Dict, Any, List
from fastapi import HTTPException
from app.utils.serialization import clean_for_json

class ChartService:
    @staticmethod
    def generate_chart_data(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
        chart_type = config.get("chart_type")
        x_axis = config.get("x_axis")
        y_axis = config.get("y_axis")
        aggregation = config.get("aggregation", "count")  # count, sum, avg, min, max
        sort_by = config.get("sort_by", "none")  # asc, desc, none
        top_n = config.get("top_n", 50)
        bins = config.get("bins", 10)

        if not chart_type:
            raise HTTPException(status_code=400, detail="chart_type must be specified.")

        total_rows = len(df)
        if total_rows == 0:
            return {"categories": [], "series": [], "metadata": {"total_points": 0}}

        # 1. Bar, Line, Pie, Area (Aggregated categorical/time-series)
        if chart_type in ("bar", "line", "pie", "area"):
            if not x_axis or x_axis not in df.columns:
                raise HTTPException(status_code=400, detail=f"Valid x_axis column required for {chart_type} chart.")

            # Prepare grouping
            grouped_df = df.dropna(subset=[x_axis]).copy()

            if aggregation == "count":
                counts = grouped_df[x_axis].value_counts()
                if sort_by == "asc":
                    counts = counts.sort_values(ascending=True)
                elif sort_by == "desc":
                    counts = counts.sort_values(ascending=False)
                
                if top_n and top_n > 0:
                    counts = counts.head(top_n)

                categories = [str(x) for x in counts.index.tolist()]
                values = [int(v) for v in counts.values.tolist()]

            else:
                if not y_axis or y_axis not in df.columns:
                    raise HTTPException(status_code=400, detail=f"y_axis required for '{aggregation}' aggregation.")

                num_series = pd.to_numeric(grouped_df[y_axis], errors="coerce")
                grouped_df["_metric"] = num_series
                grouped_df = grouped_df.dropna(subset=["_metric"])

                if len(grouped_df) == 0:
                    raise HTTPException(status_code=400, detail=f"No valid numeric data in '{y_axis}' to aggregate.")

                grouped = grouped_df.groupby(x_axis)["_metric"]
                if aggregation == "sum":
                    res = grouped.sum()
                elif aggregation in ("avg", "mean"):
                    res = grouped.mean()
                elif aggregation == "min":
                    res = grouped.min()
                elif aggregation == "max":
                    res = grouped.max()
                else:
                    raise HTTPException(status_code=400, detail=f"Unsupported aggregation '{aggregation}'.")

                if sort_by == "asc":
                    res = res.sort_values(ascending=True)
                elif sort_by == "desc":
                    res = res.sort_values(ascending=False)

                if top_n and top_n > 0:
                    res = res.head(top_n)

                categories = [str(x) for x in res.index.tolist()]
                values = [round(float(v), 2) for v in res.values.tolist()]

            if chart_type == "pie":
                series_data = [{"name": cat, "value": val} for cat, val in zip(categories, values)]
                return {
                    "categories": categories,
                    "series": [{"name": config.get("title", x_axis), "type": "pie", "data": series_data}],
                    "metadata": {"total_categories": len(categories)}
                }

            return {
                "categories": categories,
                "series": [{
                    "name": f"{aggregation.upper()}({y_axis or 'rows'})",
                    "type": "line" if chart_type in ("line", "area") else "bar",
                    "areaStyle": {} if chart_type == "area" else None,
                    "data": values
                }],
                "metadata": {"total_categories": len(categories)}
            }

        # 2. Histogram
        elif chart_type == "histogram":
            if not x_axis or x_axis not in df.columns:
                raise HTTPException(status_code=400, detail="x_axis required for histogram.")
            
            num_series = pd.to_numeric(df[x_axis], errors="coerce").dropna()
            if len(num_series) == 0:
                raise HTTPException(status_code=400, detail=f"Column '{x_axis}' contains no numeric data for histogram.")

            counts, bin_edges = np.histogram(num_series, bins=bins)
            categories = [f"{round(bin_edges[i], 1)} - {round(bin_edges[i+1], 1)}" for i in range(len(counts))]
            values = [int(c) for c in counts]

            return {
                "categories": categories,
                "series": [{
                    "name": "Frequency",
                    "type": "bar",
                    "data": values
                }],
                "metadata": {"bins": bins, "total_records": len(num_series)}
            }

        # 3. Scatter Plot
        elif chart_type == "scatter":
            if not x_axis or not y_axis or x_axis not in df.columns or y_axis not in df.columns:
                raise HTTPException(status_code=400, detail="Both x_axis and y_axis are required for scatter plot.")

            sub_df = df[[x_axis, y_axis]].copy()
            sub_df[x_axis] = pd.to_numeric(sub_df[x_axis], errors="coerce")
            sub_df[y_axis] = pd.to_numeric(sub_df[y_axis], errors="coerce")
            clean_sub = sub_df.dropna()

            # Limit scatter points for browser performance
            sampled = clean_sub.sample(n=min(len(clean_sub), 1000), random_state=42) if len(clean_sub) > 1000 else clean_sub
            scatter_data = [[round(float(r[x_axis]), 2), round(float(r[y_axis]), 2)] for _, r in sampled.iterrows()]

            return {
                "series": [{
                    "name": f"{x_axis} vs {y_axis}",
                    "type": "scatter",
                    "data": scatter_data
                }],
                "metadata": {
                    "total_points": len(clean_sub),
                    "sampled": len(clean_sub) > 1000,
                    "x_name": x_axis,
                    "y_name": y_axis
                }
            }

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported chart type '{chart_type}'.")

    @staticmethod
    def get_recommendations(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Rule-based automatic chart suggestions based on column data types."""
        from app.engine.profiler import DataProfiler

        col_types = {col: DataProfiler.infer_column_type(df[col]) for col in df.columns}
        num_cols = [c for c, t in col_types.items() if t in ("integer", "decimal")]
        cat_cols = [c for c, t in col_types.items() if t == "categorical"]
        date_cols = [c for c, t in col_types.items() if t == "datetime"]

        recommendations = []

        # Rule 1: Date column + numeric column -> Line chart
        if date_cols and num_cols:
            recommendations.append({
                "chart_type": "line",
                "title": f"{num_cols[0]} Over Time ({date_cols[0]})",
                "x_axis": date_cols[0],
                "y_axis": num_cols[0],
                "aggregation": "avg",
                "rationale": f"Time-series trend analysis of {num_cols[0]} by {date_cols[0]}."
            })

        # Rule 2: Categorical + numeric -> Bar chart
        if cat_cols and num_cols:
            recommendations.append({
                "chart_type": "bar",
                "title": f"Average {num_cols[0]} by {cat_cols[0]}",
                "x_axis": cat_cols[0],
                "y_axis": num_cols[0],
                "aggregation": "avg",
                "rationale": f"Compares average {num_cols[0]} across distinct {cat_cols[0]} groups."
            })

        # Rule 3: Low cardinality categorical -> Pie chart
        for cat in cat_cols:
            if 2 <= df[cat].nunique() <= 8:
                recommendations.append({
                    "chart_type": "pie",
                    "title": f"Distribution of {cat}",
                    "x_axis": cat,
                    "y_axis": None,
                    "aggregation": "count",
                    "rationale": f"{cat} has {df[cat].nunique()} distinct values, optimal for proportion breakdown."
                })
                break

        # Rule 4: Numeric column -> Histogram
        if num_cols:
            recommendations.append({
                "chart_type": "histogram",
                "title": f"Distribution of {num_cols[0]}",
                "x_axis": num_cols[0],
                "bins": 10,
                "rationale": f"Visualizes frequency distribution and skewness of {num_cols[0]}."
            })

        # Rule 5: Two numeric columns -> Scatter plot
        if len(num_cols) >= 2:
            recommendations.append({
                "chart_type": "scatter",
                "title": f"{num_cols[1]} vs {num_cols[0]} Correlation",
                "x_axis": num_cols[0],
                "y_axis": num_cols[1],
                "rationale": f"Evaluates correlation between {num_cols[0]} and {num_cols[1]}."
            })

        return recommendations
