import numpy as np
from typing import Any, Dict, List, Union

def convert_numpy_values(obj: Any) -> Any:
    """Convert NumPy values to Python native types for serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_values(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_values(item) for item in obj]
    else:
        return obj 