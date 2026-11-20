"""Fixtures comunes de las pruebas de interfaz."""

import pytest


@pytest.fixture(autouse=True)
def _motion_isolated():
    """Cada prueba parte con animaciones activas y termina sin nada en vuelo.

    Las animaciones corren de verdad (con su duración real) para que las
    pruebas vean el mismo estado que el usuario; al terminar, todo salta a
    su final para que ninguna animación sobreviva a los widgets de la prueba.
    """
    from prettycalc.ui import motion

    motion.reset_motion_state()
    motion._STATE["reduce"] = False
    yield
    motion.finish_all()
    motion.reset_motion_state()
