"""Diagnóstico de entradas escalares: explica por qué un texto no es un número.

Asignatura: Álgebra Lineal MTM0120, Universidad Americana (UAM).
Sprint 10 (heurística de Nielsen #5, prevención de errores y #9, ayuda a
reconocer y recuperarse de errores). Las celdas marcadas en rojo ahora dicen
qué carácter falló y cómo corregirlo, en lugar de un borde mudo.

100% Python estándar.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from prettycalc.core.types import parse_scalar

_ALLOWED = set("0123456789+-./ ")
_DECIMAL_COMMA = re.compile(r"^[+-]?\d*,\d+$")
_SCIENTIFIC = re.compile(r"^[+-]?\d+(\.\d+)?[eE][+-]?\d+$")


@dataclass(frozen=True)
class ScalarDiagnosis:
    """Resultado de revisar una entrada escalar.

    Attributes:
        is_valid: Si el texto se interpreta como número exacto.
        message: Explicación breve en español (vacía si es válido).
        suggestion: Texto corregido que el usuario podría escribir, si se puede inferir.
    """

    is_valid: bool
    message: str = ""
    suggestion: Optional[str] = None


def _try(text: str) -> bool:
    try:
        parse_scalar(text)
        return True
    except (ValueError, TypeError, ZeroDivisionError):
        return False


def diagnose_scalar_text(text: str, *, allow_empty: bool = True) -> ScalarDiagnosis:
    """Revisa ``text`` y explica el primer problema que encuentra.

    Se admiten enteros (``-3``), fracciones (``a/b``) y decimales con punto
    (``0.75``). Una celda vacía cuenta como 0 cuando ``allow_empty`` es verdadero.
    """
    raw = text if text is not None else ""
    cleaned = raw.strip()
    if not cleaned:
        if allow_empty:
            return ScalarDiagnosis(True)
        return ScalarDiagnosis(False, "Escribe un número: entero, fracción a/b o decimal.", "0")

    if _try(cleaned):
        return ScalarDiagnosis(True)

    compact = cleaned.replace(" ", "")

    if _DECIMAL_COMMA.match(compact):
        fixed = compact.replace(",", ".")
        return ScalarDiagnosis(
            False,
            f"«{cleaned}» usa coma decimal. Escribe el punto: {fixed}.",
            fixed,
        )

    if _SCIENTIFIC.match(compact):
        return ScalarDiagnosis(
            False,
            f"«{cleaned}» está en notación científica. Escríbelo como decimal o fracción.",
        )

    if any(ch in "oO" for ch in compact) and all(ch in _ALLOWED or ch in "oO" for ch in compact):
        fixed = compact.replace("o", "0").replace("O", "0")
        if _try(fixed):
            return ScalarDiagnosis(
                False,
                f"«{cleaned}» contiene la letra O. ¿Quisiste escribir el número cero? Prueba {fixed}.",
                fixed,
            )

    if any(ch in "lI" for ch in compact) and all(ch in _ALLOWED or ch in "lI" for ch in compact):
        fixed = compact.replace("l", "1").replace("I", "1")
        if _try(fixed):
            return ScalarDiagnosis(
                False,
                f"«{cleaned}» contiene una letra l/I. ¿Quisiste escribir el número uno? Prueba {fixed}.",
                fixed,
            )

    if "/" in compact:
        parts = compact.split("/")
        if len(parts) != 2:
            return ScalarDiagnosis(False, f"«{cleaned}» tiene más de una barra. Una fracción se escribe a/b.")
        num, den = parts
        if not num or not den:
            missing = "numerador" if not num else "denominador"
            return ScalarDiagnosis(False, f"«{cleaned}» está incompleta. Falta el {missing} de a/b.")
        try:
            if int(den) == 0:
                return ScalarDiagnosis(
                    False, f"«{cleaned}» divide entre cero. El denominador debe ser distinto de 0."
                )
        except ValueError:
            pass
        if "." in compact:
            return ScalarDiagnosis(
                False, f"«{cleaned}» mezcla fracción y decimal. Usa enteros en a/b (por ejemplo 3/4)."
            )
        return ScalarDiagnosis(
            False, f"«{cleaned}» no es una fracción válida. Numerador y denominador deben ser enteros."
        )

    if compact.count(".") > 1:
        return ScalarDiagnosis(False, f"«{cleaned}» tiene más de un punto decimal.")

    if any(sign in compact[1:] for sign in "+-"):
        return ScalarDiagnosis(
            False, f"«{cleaned}» tiene un signo fuera de lugar. El signo va solo al inicio."
        )

    bad = next((ch for ch in compact if ch not in _ALLOWED), None)
    if bad is not None:
        return ScalarDiagnosis(
            False,
            f"«{cleaned}» contiene «{bad}», que no es parte de un número. "
            "Se admiten enteros, fracciones a/b y decimales con punto.",
        )

    return ScalarDiagnosis(
        False,
        f"«{cleaned}» no es un número. Se admiten enteros, fracciones a/b y decimales con punto.",
    )


def decimal_hint(text: str, digits: int = 6) -> str:
    """Aproximación decimal de una fracción para mostrar junto al campo (``≈ 1.5``).

    Devuelve cadena vacía si el texto no es válido o si no es una fracción.
    """
    cleaned = (text or "").strip()
    if not cleaned or "/" not in cleaned:
        return ""
    try:
        value = parse_scalar(cleaned)
    except (ValueError, TypeError, ZeroDivisionError):
        return ""
    if value.denominator == 1:
        return f"= {value.numerator}"
    approx = f"{float(value):.{digits}f}".rstrip("0").rstrip(".")
    return f"≈ {approx}"
