#!/usr/bin/env python3
"""Build script for Lambda layers."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def build_layer(layer_dir: str) -> None:
    """Build a Lambda layer by installing requirements into the correct directory structure.
    
    Args:
        layer_dir: Path to the layer directory containing requirements.txt
    """
    layer_path = Path(layer_dir)
    requirements_file = layer_path / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"No requirements.txt found in {layer_dir}")
        sys.exit(1)
    
    # Create the Python package directory structure
    package_dir = layer_path / "python" / "lib" / "python3.11" / "site-packages"
    package_dir.mkdir(parents=True, exist_ok=True)
    
    # Install requirements into the package directory
    try:
        subprocess.run([
            sys.executable, 
            "-m", 
            "pip", 
            "install",
            "-r", 
            str(requirements_file),
            "-t", 
            str(package_dir),
            "--no-cache-dir"
        ], check=True)
        print(f"Successfully built layer in {layer_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install requirements: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: build_layer.py <layer_directory>")
        sys.exit(1)
    
    build_layer(sys.argv[1])
