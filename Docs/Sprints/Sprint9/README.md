# Sprint 9: Capa de presentación matemática y RichText

**Fecha de Inicio:** 2026-10-11  
**Fecha de Fin:** 2026-10-11  
**Estado:** Implementado  
**Rama Git de Trabajo:** `feature/sprint-9-renderizado-latex-richtext`  
**Rama Destino:** `main`  
**Asignatura:** Álgebra Lineal (MTM0120) — II Semestre 2026  
**Institución:** Universidad Americana (UAM) — Facultad de Ingeniería y Arquitectura (FIA)

---

## 1. Objetivo del Sprint (Sprint Goal)

Cerrar el hueco entre el LaTeX que escribe `StepTracer` y la notación de libro que ve el estudiante. A partir de este sprint, subíndices, superíndices, normas, determinantes y bloques `\text{...}` se pintan como HTML de `Qt.RichText`, y un test centinela falla si un cambio futuro vuelve a filtrar `\`, `{`, `}`, `_` o `^` a la interfaz.

El motor no cambia de contrato: sigue emitiendo LaTeX puro. La conversión vive solo en `prettycalc.ui.mathtext`.

---

## 2. Requerimientos Específicos de la Iteración

- [x] **REQ-9.1:** `latex_to_book_html` procesa el resto de la fórmula cuando hay `\text{...}`. El bloque de prosa no anula subíndices, superíndices ni operadores.
- [x] **REQ-9.2:** Subíndices (`A_{ij}`, `u_i`, `C_3H_8`, filas `f_{2}` → `F₂`) y superíndices (`A^T`, `A^{-1}`, `k^{n}`, `\|v\|^2`) salen como `<sub>` / `<sup>` o como glifos Unicode de libro.
- [x] **REQ-9.3:** Los comandos de las sesiones 1 a 12 (`\det`, `\sqrt`, `\sum`, `\prod`, `\|`, flechas, desigualdades, `\frac`, `\mathbb{R}`, `\begin{bmatrix}`) tienen equivalente tipográfico.
- [x] **REQ-9.4:** El carrusel, el tooltip paramétrico, Cramer y las sustituciones LU usan `Qt.RichText` y el conversor que corresponde.
- [x] **REQ-9.5:** `Docs/latex-rendering-spec.md` fija el contrato y `Docs/architecture.md` lo referencia.
- [x] **REQ-9.6:** `tests/ui/test_mathtext.py` incluye la cobertura por familia de fórmulas y el test centinela de más de 20 expresiones. La suite previa sigue en verde.

---

## 3. Desglose de Tareas Técnicas

### 3.1. Motor Matemático

- [x] Sin cambios de algoritmo. `latex_formula` y `latex_title` siguen en LaTeX estándar.

### 3.2. Interfaz / Visualización

- [x] Reescribir el pipeline de `prettycalc/ui/mathtext.py`.
- [x] Carrusel: `formula_label` ya estaba en `Qt.RichText`; ahora el conversor cubre las fórmulas nuevas.
- [x] `results_dashboard.py`: tooltip paramétrico, resumen de Cramer y componentes.
- [x] `lu_factorization_view.py`: pasos `y_1`, `b_1`, `x_1` en `<sub>`.
- [x] `vectors_view.py`: el resumen de norma, distancia y producto exterior queda en `Qt.RichText`. Determinantes, TMI e identidades siguen el carrusel compartido.

### 3.3. Pruebas y Validación

- [x] Tests por familia (filas, inversa, determinantes, vectores, PLU, aplicaciones).
- [x] Test centinela anti-fugas.
- [x] Test del `QLabel` del carrusel con una fórmula que mezcla `\text` y `\det`.
- [x] `QT_QPA_PLATFORM=offscreen pytest`: 335 pruebas en verde (las 326 anteriores más las de este sprint).

---

## 4. Criterios de Aceptación (Definition of Done)

- [x] `prettycalc/ui/mathtext.py` convierte el LaTeX del trazador a HTML de libro.
- [x] Los widgets que muestran esas fórmulas usan `Qt.RichText` y el conversor.
- [x] `Docs/latex-rendering-spec.md` existe y `Docs/architecture.md` lo cita.
- [x] El centinela está en `tests/ui/test_mathtext.py`.
- [x] La suite completa pasa.

---

## 5. Notas y Decisiones Técnicas del Sprint

1. **Esto es el sprint 9**, no un parche suelto. El fallo no era de un módulo: cada fórmula nueva volvía a pintar LaTeX porque no había contrato ni prueba de frontera. La rama sale de `main` en `ea20fdc` (merge del sprint 8).
2. **`\text{...}` se aparta y se restaura al final.** Así «Etapa 1:» no impide convertir `f_{2}` ni `\det`.
3. **Filas `f_{n}` usan `F` y subíndice Unicode** (`F₁`) porque las pruebas de operaciones elementales ya exigían esa forma. El resto de los subíndices van en `<sub>`.
4. **Exponentes cortos van en glifos** (`⁻¹`, `ᵀ`, `²`, `ⁿ`). Un exponente como `swaps` va en `<sup>` porque no tiene glifo por carácter.
5. **El menos tipográfico `−` solo se aplica al LaTeX**, y solo fuera de las etiquetas. `plain_formula_to_html` deja el `-` ASCII de `-7` para no cambiar el significado de las sustituciones ya cubiertas por la suite.
6. **`\left\{` y `\right\}` producen llaves de verdad.** El centinela prohíbe `{` `}` en su corpus; esas fórmulas de conjuntos no entran en ese bucle y, si aparecen, llevan su propio test.
7. **Un comando desconocido pierde la barra** para no mostrar `\`. No cuenta como implementado: hay que registrarlo en la tabla y en el corpus.

---

## 6. Guía de Commits Atómicos Mínimos

1. `feat(ui): convertir LaTeX del trazador a HTML de libro`
2. `test(ui): agregar tests centinela contra fugas de LaTeX`
3. `docs(sprint-9): especificar el renderizado matematico y registrar el sprint`

---

## 7. Retrospectiva / Cierre

El sprint quedó en `feature/sprint-9-renderizado-latex-richtext`, partido desde `main` (`ea20fdc`).

* El atajo de `\text{` era la causa de que etapas PLU y títulos con prosa salieran sin transformar. El pipeline ya no tiene ese retorno anticipado.
* El carrusel es el único pintor de `latex_formula` en determinantes, TMI, identidades, LU, vectores y sistemas. Arreglar `mathtext.py` los cubre a la vez.
* La especificación queda en `Docs/latex-rendering-spec.md` para que el siguiente sprint añada el comando y el test en el mismo cambio.
* La suite completa pasa: 335 pruebas.
