"""Pruebas de interfaz gráfica con pytest-qt."""

from prettycalc.ui.main_window import MainWindow
from prettycalc.ui.book_matrix import BookMatrixWidget
from prettycalc.core.types import Matrix


def test_main_window_init(qtbot):
    """Verifica que la ventana principal inicialice correctamente en formato 2x2."""
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.matrix_grid.num_rows == 2
    assert window.matrix_grid.num_vars == 2
    assert window.windowTitle() == "PrettyCalc — Álgebra lineal"


def test_main_window_chrome_has_no_emojis(qtbot):
    """La cromática de la ventana no debe usar emojis decorativos."""
    window = MainWindow()
    qtbot.addWidget(window)
    texts = [
        window.windowTitle(),
        window.solve_btn.text(),
        window.reset_btn.text(),
        window.dashboard_card.status_badge.text(),
    ]
    blob = " ".join(texts)
    for char in "✨⚡🧹📝📚🔍📊🔢✅🟢🟡🔴🔑⚠️💡":
        assert char not in blob


def test_main_window_solve_sample_case1(qtbot):
    """Verifica la carga y resolución del Caso 1 (Solución Única)."""
    window = MainWindow()
    qtbot.addWidget(window)

    window.load_sample_case1()

    assert "Consistente determinado" in window.dashboard_card.status_badge.text()
    assert len(window.stepper_carousel._steps) > 0


def test_main_window_reset(qtbot):
    """Verifica que el botón de reinicio devuelva la matriz a 2x2 limpia."""
    window = MainWindow()
    qtbot.addWidget(window)

    window.load_sample_case1()
    window.reset_matrix()

    assert window.matrix_grid.num_rows == 2
    assert window.matrix_grid.num_vars == 2
    assert len(window.stepper_carousel._steps) == 0
    assert "Esperando" in window.dashboard_card.status_badge.text()


def test_book_matrix_widget_accepts_augmented_matrix(qtbot):
    """El visor de libro acepta una matriz aumentada con pivote."""
    widget = BookMatrixWidget()
    qtbot.addWidget(widget)
    mat = Matrix([[1, "1/2", 3], [0, 1, "2/3"]])
    widget.set_matrix(mat, split_col=2, pivot=(1, 1), mode="fraction")
    widget.resize(400, 280)
    widget.show()
    assert widget._matrix == mat
    assert widget._split_col == 2
    assert widget._pivot == (1, 1)


def test_ghost_buttons_visible_for_rows_and_columns(qtbot):
    """Las celdas fantasma de fila y columna muestran el símbolo + de forma permanente."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    grid = window.matrix_grid

    assert grid.ghost_row_btn.text() == "+"
    assert grid.ghost_col_btn.text() == "+"
    assert not grid.ghost_row_btn.isHidden()
    assert not grid.ghost_col_btn.isHidden()
    assert grid.ghost_col_btn.minimumWidth() >= 28 or grid.ghost_col_btn.width() >= 28

    grid.ghost_row_btn.click()
    assert grid.num_rows == 3
    assert grid.ghost_col_btn.height() >= 38 * grid.num_rows
    grid.ghost_col_btn.click()
    assert grid.num_vars == 3
    assert grid.ghost_col_btn.text() == "+"
    assert grid.ghost_row_btn.text() == "+"
