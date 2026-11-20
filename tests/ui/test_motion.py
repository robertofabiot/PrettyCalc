"""Sistema de movimiento: tokens, interruptor, ayudantes y capa de coreografía."""

import pytest

from PySide6.QtCore import QRect, QRectF, QSettings
from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from prettycalc.ui import motion


def _window(qtbot, w=600, h=400):
    window = QWidget()
    qtbot.addWidget(window)
    window.resize(w, h)
    window.show()
    qtbot.waitExposed(window)
    return window


def test_tokens_stay_in_their_ranges():
    assert 100 <= motion.FAST <= 140
    assert motion.FAST < motion.BASE < motion.SLOW < motion.EMPHASIS
    assert motion.EMPHASIS <= 600
    assert 450 <= motion.SIGNATURE <= 750
    assert 40 <= motion.STAGGER <= 60
    assert motion.STAGGER_TOTAL <= 300


def test_stagger_never_exceeds_total():
    for count in (1, 2, 5, 12, 40):
        step = motion.stagger_step(count)
        assert step * max(0, count - 1) <= motion.STAGGER_TOTAL or step == 8


def test_reduce_motion_zeroes_every_duration(monkeypatch):
    motion.set_reduce_motion(True, persist=False)
    assert motion.ms(motion.SIGNATURE) == 0
    assert not motion.motion_enabled()
    motion.set_reduce_motion(False, persist=False)
    assert motion.ms(motion.BASE) == motion.BASE


def test_environment_forces_reduce_motion(monkeypatch):
    monkeypatch.setenv("PRETTYCALC_REDUCE_MOTION", "1")
    assert motion.load_reduce_motion() is True
    monkeypatch.setenv("PRETTYCALC_REDUCE_MOTION", "0")
    assert motion.load_reduce_motion() is False
    monkeypatch.delenv("PRETTYCALC_REDUCE_MOTION")
    # Bajo pytest el valor por defecto es determinista.
    assert motion.load_reduce_motion() is False


def test_motion_scale_from_environment(monkeypatch):
    monkeypatch.setenv("PRETTYCALC_MOTION_SCALE", "4")
    motion.reset_motion_state()
    motion._STATE["reduce"] = False
    assert motion.motion_scale() == 4.0
    assert motion.ms(motion.BASE) == 4 * motion.BASE
    monkeypatch.setenv("PRETTYCALC_MOTION_SCALE", "nada")
    motion.reset_motion_state()
    assert motion.motion_scale() == 1.0


def test_preference_is_saved_and_read(tmp_path, monkeypatch):
    settings = QSettings(str(tmp_path / "prefs.ini"), QSettings.IniFormat)
    import prettycalc.ui.theme as theme

    monkeypatch.setattr(theme, "_settings", lambda: settings)
    assert motion.stored_reduce_motion(settings) is None
    motion.set_reduce_motion(True)
    assert motion.stored_reduce_motion(settings) is True
    assert motion.reduce_motion() is True
    motion.set_reduce_motion(False)
    assert motion.stored_reduce_motion(settings) is False


def test_preferences_dialog_applies_reduce_motion_without_restart(qtbot, tmp_path, monkeypatch):
    settings = QSettings(str(tmp_path / "prefs.ini"), QSettings.IniFormat)
    import prettycalc.ui.theme as theme
    import prettycalc.ui.preferences_dialog as prefs

    monkeypatch.setattr(theme, "_settings", lambda: settings)
    monkeypatch.setattr(prefs, "save_appearance", lambda *_args: True)
    dialog = prefs.PreferencesDialog()
    qtbot.addWidget(dialog)
    assert dialog.reduce_motion_check.isChecked() is False
    dialog.reduce_motion_check.setChecked(True)
    dialog._save()
    assert motion.reduce_motion() is True
    assert dialog.restart_requested is False


def test_system_preference_only_queried_on_windows():
    assert motion.system_prefers_reduced_motion("linux") is False
    assert motion.system_prefers_reduced_motion("darwin") is False


def test_tween_runs_and_finish_all_jumps_to_end(qtbot):
    owner = _window(qtbot)
    values = []
    done = []
    motion.run(owner, 5000, values.append, lambda: done.append(True))
    assert motion.running_count() == 1
    motion.finish_all()
    assert done == [True]
    assert values[-1] == pytest.approx(1.0)
    assert motion.running_count() == 0


def test_run_with_reduce_motion_applies_final_state_immediately(qtbot):
    owner = _window(qtbot)
    motion.set_reduce_motion(True, persist=False)
    values, done = [], []
    assert motion.run(owner, motion.ms(motion.SLOW), values.append, lambda: done.append(1)) is None
    assert values == [1.0] and done == [1]
    assert motion.running_count() == 0


def test_destroying_owner_mid_animation_is_safe(qtbot):
    owner = QWidget()
    owner.show()
    calls = []
    motion.run(owner, 5000, calls.append, lambda: calls.append("fin"))
    owner.deleteLater()
    qtbot.wait(20)
    motion.finish_all()
    assert motion.running_count() == 0


def test_fade_in_removes_its_effect(qtbot):
    window = _window(qtbot)
    label = QLabel("hola", window)
    label.show()
    assert motion.fade_in(label)
    assert label.graphicsEffect() is not None
    motion.finish_all()
    assert label.graphicsEffect() is None


def test_fade_in_skips_nested_effects(qtbot):
    window = _window(qtbot)
    parent = QWidget(window)
    child = QLabel("x", parent)
    parent.show()
    assert motion.fade_in(parent)
    assert not motion.fade_in(child)
    motion.finish_all()
    assert parent.graphicsEffect() is None and child.graphicsEffect() is None


def test_fade_in_does_nothing_with_reduce_motion(qtbot):
    window = _window(qtbot)
    label = QLabel("hola", window)
    label.show()
    motion.set_reduce_motion(True, persist=False)
    assert not motion.fade_in(label)
    assert label.graphicsEffect() is None


def test_burst_gate_detects_fast_triggers(monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(motion.time, "monotonic", lambda: clock[0])
    gate = motion.BurstGate()
    assert gate.hit(600) is False
    clock[0] += 0.1
    assert gate.hit(600) is True
    clock[0] += 1.0
    assert gate.hit(600) is False
    assert gate.hit(600, autorepeat=True) is True


def _scroll_fixture(qtbot):
    window = _window(qtbot, 400, 300)
    area = QScrollArea(window)
    area.resize(400, 300)
    content = QWidget()
    layout = QVBoxLayout(content)
    labels = []
    for index in range(40):
        label = QLabel(f"fila {index}")
        label.setFixedHeight(40)
        layout.addWidget(label)
        labels.append(label)
    area.setWidget(content)
    area.setWidgetResizable(True)
    area.show()
    qtbot.wait(10)
    area._keep_window = window
    return area, labels


def test_scroll_to_widget_matches_ensure_widget_visible(qtbot):
    area, labels = _scroll_fixture(qtbot)
    area.ensureWidgetVisible(labels[30], 0, 0)
    expected = area.verticalScrollBar().value()
    area.verticalScrollBar().setValue(0)
    motion.scroll_to_widget(area, labels[30], 0, 0)
    motion.finish_all()
    assert area.verticalScrollBar().value() == expected


def test_scroll_is_instant_with_reduce_motion(qtbot):
    area, labels = _scroll_fixture(qtbot)
    motion.set_reduce_motion(True, persist=False)
    motion.scroll_to_widget(area, labels[35], 0, 0)
    assert area.verticalScrollBar().value() > 0
    assert motion.running_count() == 0


def test_choreography_layer_hidden_when_idle_and_cancelled_by_resize(qtbot):
    window = _window(qtbot)
    label = QLabel("7", window)
    label.setGeometry(10, 10, 40, 30)
    label.show()
    layer = motion.layer_for(window)
    assert layer is not None and not layer.isVisible()
    layer.add_flight(
        motion.Flight(label.grab(), QRectF(10, 10, 40, 30), QRectF(300, 200, 40, 30), 0.0, 5000.0)
    )
    assert layer.play()
    assert layer.isVisible() and layer.is_active()
    window.resize(620, 410)
    qtbot.wait(10)
    assert not layer.isVisible()
    assert not layer.is_active()


def test_choreography_layer_adds_without_restarting(qtbot):
    window = _window(qtbot)
    layer = motion.layer_for(window)
    first = motion.Mark(QRectF(0, 0, 10, 10), "#ffffff", 0.0, 400.0, fill=0.2)
    layer.add_mark(first)
    layer.play()
    qtbot.wait(120)
    second = motion.Mark(QRectF(0, 0, 10, 10), "#ffffff", 0.0, 400.0, fill=0.2)
    layer.add_mark(second)
    layer.play()
    assert first.start == 0.0
    assert second.start > 0.0
    motion.finish_all()
    assert not layer.isVisible()


def test_on_screen_respects_scroll_viewport(qtbot):
    area, labels = _scroll_fixture(qtbot)
    assert motion.on_screen(labels[0])
    assert not motion.on_screen(labels[35])


def test_crossfade_and_settle_leave_no_visible_layer(qtbot):
    window = _window(qtbot)
    label = QLabel("Veredicto", window)
    label.setGeometry(20, 20, 160, 30)
    label.show()
    assert motion.crossfade_out(label)
    assert motion.settle(label, "#2F2A37")
    assert motion.pulse(label, "#81B29A")
    motion.finish_all()
    layer = motion.layer_for(window)
    assert not layer.isVisible()
