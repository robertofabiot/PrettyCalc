"""Pantalla del compendio. El texto está en ``prettycalc.core.theorems``."""

from __future__ import annotations

import sys

from prettycalc.core.theorems import (
    text_applications,
    text_determinants,
    text_factorization,
    text_linear_systems,
    text_matrices,
    text_vectors,
)

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def mostrar_teoremas_sistemas() -> None:
    """Muestra los teoremas y propiedades clave del Modulo 1 (SEL)."""
    print(text_linear_systems())


def mostrar_teoremas_vectores() -> None:
    """Muestra los teoremas y propiedades clave del Modulo 2 (Vectores e Indep. Lineal)."""
    print(text_vectors())


def mostrar_teoremas_matrices() -> None:
    """Muestra los teoremas y propiedades clave del Modulo 3 (Algebra de Matrices e Inversa)."""
    print(text_matrices())


def mostrar_teoremas_determinantes() -> None:
    """Muestra los teoremas y propiedades clave del Modulo 4 (Determinantes)."""
    print(text_determinants())


def mostrar_teoremas_aplicaciones() -> None:
    """Muestra Leontief, el balanceo químico, la dieta y las redes de flujo."""
    print(text_applications())


def mostrar_teoremas_factorizacion() -> None:
    """Muestra la factorización LU y las dos sustituciones."""
    print(text_factorization())


def mostrar_todos_los_teoremas() -> None:
    """Muestra el compendio completo de teoremas de la asignatura."""
    blocks = (
        mostrar_teoremas_sistemas,
        mostrar_teoremas_vectores,
        mostrar_teoremas_matrices,
        mostrar_teoremas_determinantes,
        mostrar_teoremas_aplicaciones,
        mostrar_teoremas_factorizacion,
    )
    for index, show in enumerate(blocks):
        show()
        if index < len(blocks) - 1:
            input("\nPresione ENTER para continuar...")
