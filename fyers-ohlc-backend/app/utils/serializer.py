"""
Serialization utilities for converting numpy/pandas types to JSON-serializable Python types
"""
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Union


def convert_to_serializable(obj: Any) -> Any:
    """
    Recursively convert numpy/pandas types to native Python types for JSON serialization.
    
    Args:
        obj: Object to convert (can be dict, list, numpy type, pandas type, etc.)
    
    Returns:
        JSON-serializable Python object
    """
    # Handle None
    if obj is None:
        return None
    
    # Handle numpy types - check type name strings for compatibility with all numpy versions
    obj_type = type(obj).__name__
    
    # Handle numpy integers (np.integer is the base class, works in all numpy versions)
    if isinstance(obj, np.integer):
        return int(obj)
    
    # Handle numpy floats (np.floating is the base class, works in all numpy versions)
    if isinstance(obj, np.floating):
        return float(obj)
    
    # Handle numpy booleans (check by type name for numpy 2.0 compatibility)
    if obj_type == 'bool_' or isinstance(obj, bool):
        return bool(obj)
    
    # Handle numpy arrays
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    
    # Handle numpy generic types by checking if it's a numpy scalar
    if hasattr(np, 'generic') and isinstance(obj, np.generic):
        return obj.item()
    
    # Handle pandas types
    if isinstance(obj, (pd.Series, pd.Index)):
        return obj.tolist()
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient='records')
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    
    # Check for pandas NA/NaT using pd.isna (works for all NA types)
    try:
        if pd.isna(obj):
            return None
    except (TypeError, ValueError):
        # pd.isna might fail on some objects, that's okay
        pass
    
    # Handle dictionaries recursively
    if isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    
    # Handle lists/tuples recursively
    if isinstance(obj, (list, tuple)):
        return [convert_to_serializable(item) for item in obj]
    
    # Return as-is for native Python types
    return obj


def serialize_dataframe_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Convert DataFrame to list of dictionaries with all numpy types converted to Python types.
    
    Args:
        df: Pandas DataFrame
    
    Returns:
        List of dictionaries with native Python types
    """
    records = df.to_dict(orient='records')
    return convert_to_serializable(records)


def serialize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert dictionary containing numpy/pandas types to native Python types.
    
    Args:
        data: Dictionary that may contain numpy/pandas types
    
    Returns:
        Dictionary with native Python types
    """
    return convert_to_serializable(data)
