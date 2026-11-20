"""================================================================================
UNIVERSIDAD AMERICANA (UAM) - FIA | ÁLGEBRA LINEAL (MTM0120) - GRUPO 4
MÓDULO 5: Métodos Iterativos de Jacobi y Gauss-Seidel para SEL (A·x = b)
================================================================================
"""

from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path
from typing import List, Optional

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Asegurar importaciones relativas limpias
calc_dir = Path(__file__).resolve().parent.parent
parent_dir = calc_dir.parent
for p in (str(calc_dir), str(parent_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from Calculadora_Algebra_Lineal.teoremas.resumen_teoremas import mostrar_teoremas_iterativos
except ImportError:
    try:
        from teoremas.resumen_teoremas import mostrar_teoremas_iterativos
    except ImportError:
        def mostrar_teoremas_iterativos() -> None:
            print("Teoremas de métodos iterativos.")

# Importar lógica central del Programa 8
import importlib
p8 = importlib.import_module("Programa 8_Grupo4")


def imprimir_logo_iterativos() -> None:
    """Imprime el logotipo ASCII característico del Módulo 5."""
    print("=" * 68)
    print(r"""
  ╔══════════════════════════════════════════════════════════════════╗
  ║       [ 🔄 T_J · x + c ] MÓDULO 5: MÉTODOS ITERATIVOS (SEL)      ║
  ║                   Métodos: Jacobi y Gauss-Seidel                 ║
  ║          Análisis de Dominancia, Radio Espectral y Divergencia   ║
  ╚══════════════════════════════════════════════════════════════════╝
    """)
    print("=" * 68)


def menu_iterativos() -> None:
    """Menú interactivo del Módulo 5 dentro de la Calculadora Modular."""
    while True:
        imprimir_logo_iterativos()
        print(" Opciones Disponibles:")
        print("   0. 📖 Ver Teoremas Clave del Módulo (Dominancia, ρ(T), Stein-Rosenberg)")
        print("   1. 🔄 Resolver SEL por Método de Jacobi (Paso a Paso)")
        print("   2. ⚡ Resolver SEL por Método de Gauss-Seidel (Paso a Paso)")
        print("   3. ⚖️  Comparar Jacobi vs Gauss-Seidel en el Mismo Sistema")
        print("   4. 🧪 Demostración de Casos de Prueba Didácticos Preconfigurados")
        print("   5. 🚪 Volver al Menú Principal")
        print("=" * 68)

        opc = input("Seleccione una opción (0-5): ").strip()

        if opc == "0":
            mostrar_teoremas_iterativos()
            input("\nPresione ENTER para continuar...")
        elif opc == "1":
            try:
                p8.resolver_sistema_interactivo(modo="jacobi")
            except Exception as exc:
                print(f"\n⚠️  Error durante la ejecución: {exc}")
            input("\nPresione ENTER para continuar...")
        elif opc == "2":
            try:
                p8.resolver_sistema_interactivo(modo="gauss_seidel")
            except Exception as exc:
                print(f"\n⚠️  Error durante la ejecución: {exc}")
            input("\nPresione ENTER para continuar...")
        elif opc == "3":
            try:
                p8.resolver_sistema_interactivo(modo="ambos")
            except Exception as exc:
                print(f"\n⚠️  Error durante la ejecución: {exc}")
            input("\nPresione ENTER para continuar...")
        elif opc == "4":
            p8.run_didactic_case_interactive()
        elif opc == "5":
            break
        else:
            print("   ⚠️  Opción no válida. Ingrese un número entre 0 y 5.")
            input("Presione ENTER para continuar...")


if __name__ == "__main__":
    menu_iterativos()
