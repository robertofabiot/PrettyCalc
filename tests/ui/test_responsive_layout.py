"""Ninguna vista se desplaza en horizontal, desde la ventana mínima hasta 1920 px.

Con la barra lateral, las vistas de tres columnas (Sistemas, Determinantes,
LU) bajan su panel de resultados debajo cuando no caben, y la cabecera de
Ecuaciones pasa sus botones a una segunda línea.
"""

import pytest
from PySide6.QtWidgets import QAbstractScrollArea

from prettycalc.ui.main_window import MainWindow


def _load_examples(window):
    window.linear_systems_view.load_sample_case2()
    window.linear_systems_view._solve_now()
    window.matrix_operations_view.load_compatible_product_sample()
    window.matrix_operations_view.compute()
    window.vectors_view.load_basic_sample()
    window.matrix_equations_view.load_sample()
    window.determinants_view.load_session11_example()
    window.determinants_view.compute()
    window.lu_view.load_example_1()
    window.lu_view.solve()
    window.linear_transformations_view.load_example_2()
    window.linear_transformations_view.compute_tv()
    window.vector_spaces_view.load_example_gen1()
    window.vector_spaces_view.compute_generating_set()


def _horizontal_overflow(window, qtbot):
    offenders = []
    for index in range(window.module_stack.count()):
        window.set_module(index)
        qtbot.wait(30)
        view = window.module_stack.widget(index)
        for area in view.findChildren(QAbstractScrollArea):
            bar = area.horizontalScrollBar()
            if area.isVisible() and bar.isVisible() and bar.maximum() > 0:
                offenders.append((type(view).__name__, area.objectName(), bar.maximum()))
    return offenders


def test_minimum_window_width_is_back_to_1080(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.minimumWidth() == 1080


@pytest.mark.parametrize("width", [1080, 1280, 1366, 1920])
def test_no_view_scrolls_horizontally(qtbot, width):
    window = MainWindow()
    qtbot.addWidget(window)
    window.resize(width, 680)
    window.show()
    qtbot.waitExposed(window)
    _load_examples(window)
    assert _horizontal_overflow(window, qtbot) == []


def test_results_column_stacks_below_when_narrow_and_returns_when_wide(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    host = window.linear_systems_view.body_host
    window.resize(1080, 680)
    qtbot.waitUntil(host.is_stacked, timeout=1000)
    assert host.splitter.count() == 2
    window.resize(1920, 1000)
    qtbot.waitUntil(lambda: not host.is_stacked(), timeout=1000)
    assert host.splitter.count() == 3
    assert host.splitter.widget(2) is window.linear_systems_view.dashboard_card.parentWidget().parentWidget()
