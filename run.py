#!/usr/bin/env python3
"""Lanzador directo de la aplicación PrettyCalc desde la raíz del proyecto."""

import sys
from pathlib import Path

# Añadir raíz al sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from prettycalc.ui.main_window import run_app

if __name__ == "__main__":
    run_app()
