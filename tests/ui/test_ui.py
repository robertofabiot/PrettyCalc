"""Pruebas de interfaz gráfica con pytest-qt."""

from prettycalc.ui.main_window import MainWindow
from prettycalc.ui.book_matrix import BookMatrixWidget
from prettycalc.ui.theme import COLOR_TEXT_PRIMARY
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


def test_remove_row_and_column_keep_minimum(qtbot):
    """El menú contextual puede recortar filas y columnas sin dejar la matriz vacía."""
    window = MainWindow()
    qtbot.addWidget(window)
    grid = window.matrix_grid

    grid.add_row()
    grid.add_column()
    assert grid.num_rows == 3
    assert grid.num_vars == 3

    grid.remove_row(1)
    assert grid.num_rows == 2
    grid.remove_column(0)
    assert grid.num_vars == 2

    grid.remove_row(0)
    grid.remove_column(0)
    assert grid.num_rows == 1
    assert grid.num_vars == 1

    grid.remove_row(0)
    grid.remove_column(0)
    assert grid.num_rows == 1
    assert grid.num_vars == 1


def test_cell_selects_all_on_focus(qtbot):
    """Al enfocar una celda se selecciona el valor, no se borra el cero."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    cell = window.matrix_grid.cells[0][0]
    assert cell.text() == "0"
    cell.setFocus()
    qtbot.wait(20)
    assert cell.text() == "0"
    assert cell.hasSelectedText()
    assert cell.selectedText() == "0"


def test_action_buttons_live_in_matrix_card(qtbot):
    """Resolver y Reiniciar están junto a la matriz, no en el encabezado."""
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.solve_btn.parentWidget() is not window.centralWidget()
    assert window.reset_btn.objectName() == "secondaryAction"
    assert window.solve_btn.objectName() == "primaryAction"


def test_fractions_toggle_shows_current_state(qtbot):
    """Fracciones es un interruptor: el estado checked marca la vista actual."""
    window = MainWindow()
    qtbot.addWidget(window)
    btn = window.stepper_carousel.mode_btn
    assert btn.isCheckable()
    assert btn.objectName() == "modeToggle"
    assert btn.isChecked()
    assert btn.text() == "Fracciones"
    from prettycalc.ui.theme import get_global_stylesheet
    assert "QPushButton#modeToggle:checked" in get_global_stylesheet()

    btn.click()
    assert not btn.isChecked()
    assert btn.text() == "Decimales"
    assert window.stepper_carousel._display_mode == "decimal"

    btn.click()
    assert btn.isChecked()
    assert btn.text() == "Fracciones"
    assert window.stepper_carousel._display_mode == "fraction"


def test_book_matrix_row_roles_flash_without_crash(qtbot):
    """El visor acepta actor/objetivo y anima el flash de la fila mutada."""
    from PySide6.QtCore import QAbstractAnimation

    widget = BookMatrixWidget()
    qtbot.addWidget(widget)
    mat = Matrix([[1, "1/2", 3], [0, 1, "2/3"]])
    widget.set_matrix(
        mat,
        split_col=2,
        pivot=(0, 0),
        actor_row=0,
        affected_rows=(1,),
        animate=True,
    )
    widget.resize(400, 280)
    widget.show()
    assert widget._actor_row == 0
    assert widget._affected_rows == (1,)
    assert widget._flash.state() == QAbstractAnimation.Running
    qtbot.wait(50)
    widget.repaint()


def test_verification_substitution_uses_high_contrast(qtbot):
    """Las líneas de sustitución de la comprobación no usan gris oscuro ni itálica."""
    from PySide6.QtWidgets import QLabel

    window = MainWindow()
    qtbot.addWidget(window)
    window.load_sample_case1()

    labels = window.dashboard_card.findChildren(QLabel)
    subs = [lbl for lbl in labels if "padding-left: 28px" in lbl.styleSheet()]
    assert subs
    for lbl in subs:
        sheet = lbl.styleSheet()
        assert COLOR_TEXT_PRIMARY in sheet
        assert "italic" not in sheet
        assert lbl.text().strip()


def test_next_step_highlights_actor_and_affected_rows(qtbot):
    """Al avanzar un paso, el visor recibe la fila actor y la fila objetivo."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.load_sample_case1()
    carousel = window.stepper_carousel
    found = False
    while carousel._current_index < len(carousel._steps) - 1:
        carousel.next_step()
        step = carousel._steps[carousel._current_index]
        if step.affected_rows:
            assert carousel.matrix_view._affected_rows == step.affected_rows
            assert carousel.matrix_view._actor_row == step.actor_row
            found = True
            break
    assert found
