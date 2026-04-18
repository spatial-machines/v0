#!/usr/bin/env python3
"""Run the spatial-machines demo. See scripts/demo.py for details."""
import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))
runpy.run_module("demo", run_name="__main__")
