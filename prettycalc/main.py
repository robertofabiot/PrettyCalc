"""Punto de entrada principal de la aplicación PrettyCalc."""

import sys
from pathlib import Path

# Asegurar que el directorio raíz esté en sys.path para ejecuciones directas
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from prettycalc.ui.main_window import run_app

if __name__ == "__main__":
    run_app()
