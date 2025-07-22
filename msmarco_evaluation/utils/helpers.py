"""Utility functions."""

import os
import shutil
from typing import Optional

def check_disk_space(directory: str, required_gb: float) -> bool:
    """Check if there's enough disk space available."""
    free_space = shutil.disk_usage(directory).free
    return (free_space / 1e9) >= required_gb

def get_device_info() -> dict:
    """Get information about available compute devices."""
    import torch
    
    device_info = {
        'device': 'cuda' if torch.cuda.is_available() else 'cpu',
        'cuda_available': torch.cuda.is_available(),
        'cuda_device_count': torch.cuda.device_count() if torch.cuda.is_available() else 0
    }
    
    if torch.cuda.is_available():
        device_info['cuda_device_name'] = torch.cuda.get_device_name(0)
        device_info['cuda_memory'] = torch.cuda.get_device_properties(0).total_memory
        
    return device_info
