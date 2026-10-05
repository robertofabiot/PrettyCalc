"""================================================================================
UNIVERSIDAD AMERICANA (UAM)
Facultad de Ingeniería y Arquitectura (FIA)
Asignatura: Álgebra Lineal (MTM0120)
CALCULADORA DE ÁLGEBRA LINEAL — SUITE MODULAR PROFESIONAL (GRUPO 4)
================================================================================
Punto de Entrada Principal (main.py)
"""

from __future__ import annotations

import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Asegurar importaciones relativas limpias sin importar el CWD
_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent
for d in (_current_dir, _parent_dir):
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))

try:
    from Calculadora_Algebra_Lineal.modulos.modulo_sistemas import menu_sistemas
    from Calculadora_Algebra_Lineal.modulos.modulo_vectores import menu_vectores
    from Calculadora_Algebra_Lineal.modulos.modulo_matrices import menu_matrices
    from Calculadora_Algebra_Lineal.modulos.modulo_determinantes import menu_determinantes
    from Calculadora_Algebra_Lineal.teoremas.resumen_teoremas import mostrar_todos_los_teoremas
except ImportError:
    from modulos.modulo_sistemas import menu_sistemas
    from modulos.modulo_vectores import menu_vectores
    from modulos.modulo_matrices import menu_matrices
    from modulos.modulo_determinantes import menu_determinantes
    from teoremas.resumen_teoremas import mostrar_todos_los_teoremas



def imprimir_banner_principal() -> None:
    """Imprime el logotipo ASCII principal de la Calculadora Modular."""
    print("=" * 70)
    print(r"""
 ╔════════════════════════════════════════════════════════════════════╗
 ║               UNIVERSIDAD AMERICANA (UAM) - FIA                    ║
 ║         CALCULADORA DE ÁLGEBRA LINEAL — SUITE INTEGRAL             ║
 ║                 PROYECTO INTEGRADOR (GRUPO 4)                      ║
 ║        100% Python Estándar · Aritmética Exacta de Fracciones      ║
 ╚════════════════════════════════════════════════════════════════════╝
    """)
    print("=" * 70)


def menu_principal() -> None:
    """Bucle del Menú Principal interactivo de la suite modular."""
    while True:
        imprimir_banner_principal()
        print(" Menú de Módulos:")
        print("   1. [ [1 2 | 3] ] MÓDULO 1: Sistemas de Ecuaciones Lineales (SEL)")
        print("   2. [   v ∈ ℝⁿ  ] MÓDULO 2: Vectores e Independencia Lineal (L.I. / L.D.)")
        print("   3. [  [A] [B]  ] MÓDULO 3: Álgebra de Matrices e Inversa")
        print("   4. [  det(A)   ] MÓDULO 4: Determinantes y Propiedades")
        print("   5. [ 📖 Teorema ] Ver Compendio Completo de Teoremas de la Asignatura")
        print("   0. Salir de la Calculadora")
        print("=" * 70)

        opcion = input("Seleccione el módulo o acción (0-5): ").strip()

        if opcion == "1":
            menu_sistemas()
        elif opcion == "2":
            menu_vectores()
        elif opcion == "3":
            menu_matrices()
        elif opcion == "4":
            menu_determinantes()
        elif opcion == "5":
            mostrar_todos_los_teoremas()
            input("\nPresione ENTER para regresar al Menú Principal...")
        elif opcion == "0":
            print("\n" + "=" * 70)
            print(" ¡Gracias por utilizar PrettyCalc - Álgebra Lineal Grupo 4!")
            print(" Sesión finalizada con éxito.")
            print("=" * 70 + "\n")
            break
        else:
            print("\n⚠️  Opción no válida. Por favor, seleccione un número entre 0 y 5.")
            input("Presione ENTER para continuar...")


if __name__ == "__main__":
    menu_principal()
