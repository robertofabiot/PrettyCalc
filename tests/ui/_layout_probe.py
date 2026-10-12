"""Sonda de layout para las pruebas multiplataforma.

Se ejecuta en un proceso aparte (cada variante necesita su propio entorno:
DPI lógico distinto o sin fuentes del sistema) y vuelca en JSON la geometría
de cada widget visible de la ventana principal con el caso I cargado.
"""

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QWidget  # noqa: E402


def main(target: str) -> None:
    app = QApplication(sys.argv[:1])
    from prettycalc.ui.main_window import MainWindow

    window = MainWindow()
    window.resize(1366, 768)
    window.show()
    window.linear_systems_view.load_sample_case1()
    for _ in range(6):
        app.processEvents()
    geometry = {}
    for index, child in enumerate(window.findChildren(QWidget)):
        if not child.isVisible():
            continue
        top_left = child.mapTo(window, child.rect().topLeft())
        key = f"{child.metaObject().className()}#{child.objectName()}#{index}"
        geometry[key] = [top_left.x(), top_left.y(), child.width(), child.height()]
    with open(target, "w", encoding="utf-8") as handle:
        json.dump(geometry, handle)
    window.close()
    app.quit()


if __name__ == "__main__":
    main(sys.argv[1])
