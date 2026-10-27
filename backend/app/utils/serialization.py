import numpy as np
import pandas as pd
from typing import Any

def clean_for_json(val: Any) -> Any:
    """Recursively convert float/int/timestamp/NaN/Inf values into JSON-serializable types."""
    if val is None:
        return None
    if isinstance(val, (np.integer, int)):
        return int(val)
    if isinstance(val, (np.floating, float)):
        if np.isnan(val) or np.isinf(val):
            return None
        return float(val)
    if isinstance(val, (np.bool_, bool)):
        return bool(val)
    if isinstance(val, (pd.Timestamp, np.datetime64)):
        return str(val)
    if isinstance(val, dict):
        return {k: clean_for_json(v) for k, v in val.items()}
    if isinstance(val, (list, tuple, set)):
        return [clean_for_json(v) for v in val]
    return str(val) if not isinstance(val, (str, int, float, bool, list, dict)) else val
