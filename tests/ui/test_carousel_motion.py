"""Transiciones del carrusel: operación de fila, ráfaga, saltos y reproducción."""

from fractions import Fraction

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

from prettycalc.core import step_diff
from prettycalc.core.cramer import solve_cramer
from prettycalc.core.elimination import gauss_jordan_elimination
from prettycalc.core.types import Matrix, Vector
from prettycalc.ui import motion
from prettycalc.ui.book_matrix import TRANSITION_BACK, TRANSITION_FORWARD, TRANSITION_JUMP, TRANSITION_SHORT
from prettycalc.ui.stepper_carousel import (
    ALERT_SINGULAR,
    ALERT_SYSTEM,
    AlgorithmStepperCarousel,
    reading_time_ms,
)

SYSTEM = Matrix([[0, 1, 1, 4], [2, -1, 1, 4], [1, 2, -1, 3]])


def _carousel(qtbot, matrix=SYSTEM, alert_mode=ALERT_SYSTEM):
    _result, tracer = gauss_jordan_elimination(matrix, split_col=matrix.cols - 1)
    carousel = AlgorithmStepperCarousel(alert_mode=alert_mode)
    qtbot.addWidget(carousel)
    carousel.resize(640, 560)
    carousel.set_steps(tracer.get_steps())
    carousel.show()
    qtbot.waitExposed(carousel)
    return carousel


def _key(widget, key, autorepeat=False):
    QApplication.sendEvent(widget, QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier, "", autorepeat))


def test_forward_step_plays_the_confirmed_row_operation(qtbot):
    carousel = _carousel(qtbot)
    steps = carousel.steps()
    for index in range(1, len(steps)):
        carousel._gate.reset()
        carousel.next_step()
        step = steps[index]
        view = carousel.matrix_view
        # El estado ya es el final desde el primer fotograma.
        assert view.matrix() == step.matrix
        assert carousel.formula_label.text()
        assert carousel.last_transition() == TRANSITION_FORWARD
        op = view.transition_operation()
        assert op is not None, step.heuristic_text
        if step.actor_row is not None:
            assert op.kind == step_diff.ADD and op.source == step.actor_row
        elif len(step.affected_rows) == 2:
            assert op.kind == step_diff.SWAP
        else:
            assert op.kind == step_diff.SCALE
        motion.finish_all()
        assert not view.is_animating()
        assert view.matrix() == step.matrix


def test_back_and_jump_use_the_short_crossfade(qtbot):
    carousel = _carousel(qtbot)
    carousel.next_step()
    carousel.next_step()
    motion.finish_all()
    carousel.prev_step()
    assert carousel.last_transition() == TRANSITION_BACK
    assert carousel.matrix_view.transition_kind() in ("", TRANSITION_BACK)
    assert carousel.matrix_view.transition_operation() is None
    motion.finish_all()
    carousel.step_slider.setValue(len(carousel.steps()))
    assert carousel.last_transition() == TRANSITION_JUMP
    assert carousel.matrix_view.transition_operation() is None
    _key(carousel, Qt.Key_Home)
    assert carousel.current_index() == 0
    assert carousel.last_transition() == TRANSITION_JUMP


def test_fast_navigation_switches_to_short_variant(qtbot):
    carousel = _carousel(qtbot)
    carousel.next_step()
    assert carousel.last_transition() == TRANSITION_FORWARD
    carousel.next_step()  # llega con la secuencia anterior en curso
    assert carousel.last_transition() == TRANSITION_SHORT
    assert carousel.matrix_view.transition_operation() is None


def test_held_arrow_key_is_always_short(qtbot):
    carousel = _carousel(qtbot)
    _key(carousel, Qt.Key_Right, autorepeat=True)
    assert carousel.last_transition() == TRANSITION_SHORT


def test_ten_rapid_steps_never_leave_intermediate_state(qtbot):
    carousel = _carousel(qtbot)
    for _ in range(10):
        carousel.next_step()
    for _ in range(10):
        carousel.prev_step()
    for _ in range(10):
        _key(carousel, Qt.Key_Right, autorepeat=True)
    motion.finish_all()
    steps = carousel.steps()
    assert carousel.current_index() == len(steps) - 1
    assert carousel.matrix_view.matrix() == steps[-1].matrix
    assert not carousel.matrix_view.is_animating()
    assert motion.running_count() == 0


def test_reduce_motion_shows_final_state_without_animating(qtbot):
    carousel = _carousel(qtbot)
    motion.set_reduce_motion(True, persist=False)
    for _ in range(len(carousel.steps()) - 1):
        carousel.next_step()
        assert not carousel.matrix_view.is_animating()
        assert motion.running_count() == 0
    view = carousel.matrix_view
    assert view.matrix() == carousel.steps()[-1].matrix
    # El realce pedagógico queda como estado final estático.
    assert view.header_roles() == {0: "basic", 1: "basic", 2: "basic"}


def test_final_form_lights_pivots_and_marks_columns(qtbot):
    carousel = _carousel(qtbot, Matrix([[1, 2, 1, 3], [2, 4, 0, 2], [3, 6, 1, 5]]))
    while carousel.current_index() < len(carousel.steps()) - 1:
        carousel._gate.reset()
        carousel.next_step()
    view = carousel.matrix_view
    final = carousel.steps()[-1].matrix
    leads = step_diff.leading_entries(final, 3)
    assert view._transition is not None
    assert view._transition.lead_cells == leads
    roles = view.header_roles()
    assert roles[1] == "free"
    assert {c for c, role in roles.items() if role == "basic"} == {c for _r, c in leads}


def test_inconsistent_row_dims_zeros_and_marks_c(qtbot):
    carousel = _carousel(qtbot, Matrix([[1, 1, 2], [1, 1, 5]]))
    carousel.go_to_step(len(carousel.steps()) - 1)
    motion.finish_all()
    assert carousel.matrix_view.contradiction_rows() == (1,)
    assert carousel.alert_label.isVisible()


def test_cramer_step_replaces_the_column_with_b(qtbot):
    result = solve_cramer(Matrix([[2, 1], [1, 3]]), Vector([3, 5]))
    carousel = AlgorithmStepperCarousel(alert_mode=ALERT_SINGULAR, variable_headers=False)
    qtbot.addWidget(carousel)
    carousel.resize(600, 500)
    carousel.set_steps(result.tracer.get_steps())
    carousel.show()
    steps = carousel.steps()
    base = steps[0].matrix
    target = next(i for i, s in enumerate(steps) if step_diff.replaced_column(base, s.matrix, s.highlight_cells) is not None)
    carousel.go_to_step(target - 1)
    motion.finish_all()
    carousel._gate.reset()
    carousel.next_step()
    transition = carousel.matrix_view._transition
    assert transition is not None and transition.replaced_col == 0
    motion.finish_all()
    assert carousel.matrix_view.matrix().get(0, 0) == Fraction(3)


def test_destroying_the_carousel_mid_animation_is_safe(qtbot):
    carousel = _carousel(qtbot)
    carousel.next_step()
    assert carousel.matrix_view.is_animating()
    carousel.deleteLater()
    qtbot.wait(20)
    motion.finish_all()
    assert motion.running_count() == 0


def test_resetting_steps_mid_animation_leaves_no_transition(qtbot):
    carousel = _carousel(qtbot)
    carousel.next_step()
    carousel.set_steps([])
    assert not carousel.matrix_view.is_animating()


def test_playback_advances_and_stops_at_the_end(qtbot, monkeypatch):
    carousel = _carousel(qtbot)
    monkeypatch.setattr(carousel, "next_playback_delay", lambda: 5)
    assert carousel.start_playback()
    assert carousel.is_playing()
    assert carousel.play_btn.is_playing()
    qtbot.waitUntil(lambda: not carousel.is_playing(), timeout=5000)
    assert carousel.current_index() == len(carousel.steps()) - 1


def test_playback_stops_on_user_interaction_and_new_steps(qtbot):
    carousel = _carousel(qtbot)
    carousel.start_playback()
    carousel.next_step()
    assert not carousel.is_playing()
    carousel.start_playback()
    _key(carousel, Qt.Key_Left)
    assert not carousel.is_playing()
    carousel.start_playback()
    carousel.set_steps(carousel.steps())
    assert not carousel.is_playing()
    carousel.start_playback()
    carousel.hide()
    assert not carousel.is_playing()


def test_space_toggles_playback(qtbot):
    carousel = _carousel(qtbot)
    _key(carousel, Qt.Key_Space)
    assert carousel.is_playing()
    _key(carousel, Qt.Key_Space)
    assert not carousel.is_playing()


def test_playback_restarts_from_the_beginning_at_the_end(qtbot):
    carousel = _carousel(qtbot)
    carousel.go_to_step(len(carousel.steps()) - 1)
    carousel.start_playback()
    assert carousel.current_index() == 0
    carousel.stop_playback()


def test_playback_speed_scales_the_reading_time(qtbot):
    carousel = _carousel(qtbot)
    carousel.go_to_step(2)
    base = carousel.next_playback_delay()
    carousel.cycle_speed()
    assert carousel.playback_speed() == 2.0
    assert carousel.speed_btn.text() == "2×"
    assert carousel.next_playback_delay() < base
    carousel.cycle_speed()
    assert carousel.playback_speed() == 0.5
    assert carousel.next_playback_delay() > base
    carousel.cycle_speed()
    assert carousel.playback_speed() == 1.0


def test_playback_works_with_reduce_motion(qtbot, monkeypatch):
    carousel = _carousel(qtbot)
    motion.set_reduce_motion(True, persist=False)
    monkeypatch.setattr(carousel, "next_playback_delay", lambda: 5)
    carousel.start_playback()
    qtbot.waitUntil(lambda: not carousel.is_playing(), timeout=5000)
    assert carousel.current_index() == len(carousel.steps()) - 1
    assert motion.running_count() == 0


def test_reading_time_grows_with_the_text():
    assert reading_time_ms("corto") == 1200
    assert reading_time_ms("x" * 200) > 1200
    assert reading_time_ms("x" * 5000) <= 4200


def test_playback_controls_have_accessible_names(qtbot):
    carousel = _carousel(qtbot)
    assert carousel.play_btn.accessibleName()
    assert "Espacio" in carousel.play_btn.toolTip()
    assert carousel.speed_btn.accessibleName()
    carousel.set_steps([])
    assert not carousel.play_btn.isVisible()
