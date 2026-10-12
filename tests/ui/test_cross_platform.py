"""Sprint 10: PrettyCalc debe verse igual en Windows y en Linux.

Qt toma del sistema el estilo, las fuentes y el DPI lógico. Estas pruebas
fijan las tres cosas: estilo Fusion, fuentes empaquetadas que cubren todos
los caracteres de la interfaz y tamaños en píxeles que no dependen del DPI.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from prettycalc.ui.main_window import MainWindow
from prettycalc.ui.platform_setup import (
    BUNDLED_FONT_FILES,
    FONTS_DIR,
    MONO_FAMILY,
    SANS_FAMILY,
    SYMBOL_FAMILY,
    load_bundled_fonts,
    make_font,
    missing_glyphs,
)

ROOT = Path(__file__).resolve().parents[2]
UI_SOURCES = sorted((ROOT / "prettycalc").rglob("*.py"))
PROBE = Path(__file__).with_name("_layout_probe.py")


def _ui_text() -> str:
    """Todos los caracteres no ASCII que la interfaz puede mostrar."""
    chars = set()
    for path in UI_SOURCES:
        chars.update(ch for ch in path.read_text(encoding="utf-8") if ord(ch) > 127)
    return "".join(sorted(chars))


def test_bundled_fonts_exist_and_have_licenses():
    for name in BUNDLED_FONT_FILES:
        assert (FONTS_DIR / name).is_file(), name
    for license_name in ("LICENSE-Inter.txt", "LICENSE-FiraCode.txt", "LICENSE-DejaVu.txt"):
        assert (FONTS_DIR / license_name).is_file(), license_name


def test_bundled_fonts_register_the_three_families(qtbot):
    families = load_bundled_fonts()
    assert SANS_FAMILY in families
    assert MONO_FAMILY in families
    assert SYMBOL_FAMILY in families


def test_weights_resolve_to_real_faces_not_synthetic(qtbot):
    from PySide6.QtGui import QFontInfo

    load_bundled_fonts()
    expected = {400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold"}
    for weight, style in expected.items():
        info = QFontInfo(make_font(15, weight=weight))
        assert info.family() == SANS_FAMILY
        assert info.styleName() == style
    assert QFontInfo(make_font(15, mono=True, weight=600)).styleName() == "SemiBold"


def test_every_ui_character_is_covered_by_a_bundled_font(qtbot):
    """Si falta un glifo, cada sistema lo tomaría de una fuente distinta."""
    assert missing_glyphs(_ui_text()) == ""


def test_no_emoji_in_the_interface():
    emoji = re.compile("[\U0001F300-\U0001FAFF☀-⛿⭐⭕️]")
    offenders = []
    for path in UI_SOURCES:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if emoji.search(line):
                offenders.append(f"{path.relative_to(ROOT)}:{number}")
    assert offenders == []


def test_fonts_are_sized_in_pixels_not_points():
    """Un punto mide distinto según el DPI lógico de cada sistema; un píxel lógico no."""
    pattern = re.compile(r"setPointSize|setPointSizeF|QFont\(\s*\"[^\"]+\"\s*,\s*\d+|font-size:\s*\d+pt")
    offenders = []
    for path in UI_SOURCES:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line):
                offenders.append(f"{path.relative_to(ROOT)}:{number}")
    assert offenders == []


def test_no_generic_system_font_families_in_rich_text():
    """``font-family: sans-serif`` a secas cae en Segoe UI o en Cantarell según el sistema."""
    pattern = re.compile(r"font-family\s*:\s*(sans-serif|serif|monospace)\b")
    offenders = []
    for path in UI_SOURCES:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line):
                offenders.append(f"{path.relative_to(ROOT)}:{number}")
    assert offenders == []


def test_main_window_uses_fusion_and_the_bundled_default_font(qtbot):
    from PySide6.QtWidgets import QApplication

    window = MainWindow()
    qtbot.addWidget(window)
    app = QApplication.instance()
    assert app.style().name().lower() == "fusion"
    font = app.font()
    assert font.families()[0] == SANS_FAMILY
    assert font.pixelSize() > 0


def test_message_box_icons_are_drawn_by_the_app(qtbot):
    from PySide6.QtWidgets import QMessageBox
    from prettycalc.ui.theme import apply_message_box_theme

    box = QMessageBox()
    qtbot.addWidget(box)
    box.setIcon(QMessageBox.Warning)
    apply_message_box_theme(box)
    pixmap = box.iconPixmap()
    assert not pixmap.isNull()
    assert box.icon() == QMessageBox.NoIcon or pixmap.width() >= 40


def _probe(env_overrides: dict) -> dict:
    with tempfile.TemporaryDirectory() as folder:
        target = os.path.join(folder, "geometry.json")
        env = dict(os.environ)
        env.update(env_overrides)
        env["QT_QPA_PLATFORM"] = "offscreen"
        subprocess.run([sys.executable, str(PROBE), target], env=env, check=True, timeout=120)
        with open(target, encoding="utf-8") as handle:
            return json.load(handle)


@pytest.mark.slow
def test_layout_does_not_depend_on_logical_dpi():
    """Windows reporta 96 ppp lógicos; muchos escritorios Linux, 120 o 144."""
    base = _probe({"QT_FONT_DPI": "96"})
    other = _probe({"QT_FONT_DPI": "144"})
    assert len(base) > 50
    moved = {key: (base[key], other.get(key)) for key in base if base[key] != other.get(key)}
    assert moved == {}


@pytest.mark.slow
@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="fontconfig solo existe en Linux")
def test_layout_is_identical_without_any_system_font():
    """Sin una sola fuente del sistema (como en un Windows sin Inter ni Fira Code)."""
    with tempfile.TemporaryDirectory() as folder:
        config = Path(folder) / "fonts.conf"
        config.write_text(
            '<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd">'
            f"<fontconfig><cachedir>{folder}/cache</cachedir></fontconfig>",
            encoding="utf-8",
        )
        base = _probe({})
        isolated = _probe({"FONTCONFIG_FILE": str(config)})
    moved = {key: (base[key], isolated.get(key)) for key in base if base[key] != isolated.get(key)}
    assert moved == {}
