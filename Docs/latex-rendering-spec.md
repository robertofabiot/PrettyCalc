# Especificación de renderizado LaTeX → HTML de libro

**Módulo:** `prettycalc.ui.mathtext`
**Función de entrada:** `latex_to_book_html(latex: str) -> str`
**Consumidor:** `QLabel` con `Qt.TextFormat.RichText`
**Pruebas de contrato:** `tests/ui/test_mathtext.py`

Esta especificación es el contrato entre el motor y la interfaz. Un sprint nuevo no la sustituye: la amplía en la tabla de comandos y en el corpus de pruebas.

---

## 1. Contrato backend → frontend

`StepTracer` (`prettycalc.core.tracer`) registra LaTeX estándar en dos campos:

| Campo | Quién lo escribe | Ejemplo |
| :--- | :--- | :--- |
| `latex_title` | `record_initial` | `\text{Etapa 1: } Ly = Pb` |
| `latex_formula` | `record_step` y los generadores de `operations.py` | `f_{2} \rightarrow f_{2} - 3f_{1}` |

Reglas:

1. **El core no conoce Qt.** Las cadenas de `latex_formula` y `latex_title` siguen siendo LaTeX puro: comandos con `\`, llaves y subíndices `_{ }`. No se les incrustan etiquetas HTML.
2. **La UI no muestra esa cadena cruda.** Ningún `QLabel`, tooltip ni checklist pinta `step.latex_formula` con `setText` directo. El paso obligatorio es `latex_to_book_html`.
3. **El texto ASCII que ya trae subíndices `y_1` o `x1`** (sustituciones LU, componentes de Cramer, ecuación paramétrica en texto plano) usa `plain_formula_to_html` o `to_html_subscripts`. No es LaTeX y no debe pasar por el reemplazo de guiones del conversor LaTeX, porque ahí el signo `-` es un menos tipográfico y rompería aserciones numéricas como `-7`.
4. **`\text{...}` no apaga el resto de la fórmula.** El contenido de `\text` es prosa (sans-serif, estilo normal). Todo lo que está fuera del bloque se transforma igual que una fórmula sin prosa.

El HTML final va envuelto así:

```html
<span style='font-size:22px; font-weight:500; letter-spacing:0.03em; color:{COLOR_TEXT_PRIMARY}; font-family:{FONT_FAMILY_SANS};'>{contenido}</span>
```

Los tokens salen de `prettycalc.ui.theme`. El bloque `\text{contenido}` queda, además, en:

```html
<span style="font-family:sans-serif; font-style:normal;">contenido</span>
```

## 2. Dónde se aplica

| Superficie | Widget | Conversor |
| :--- | :--- | :--- |
| Carrusel de pasos | `AlgorithmStepperCarousel.formula_label` | `latex_to_book_html(step.latex_formula)` y `Qt.RichText` |
| Forma vectorial paramétrica | tooltip de `parametricVectorEquation` | `latex_to_book_html(solution.to_latex_equation())` |
| Regla de Cramer | resumen, `cramerComponent*`, `cramerDeterminant*` | `plain_formula_to_html` y `Qt.RichText` |
| Factorización LU | `forwardSteps`, `backwardSteps` | `plain_formula_to_html` y `Qt.RichText` |
| Norma, distancia, producto exterior | `metricSummary` (`Qt.RichText`) y el carrusel del módulo | el resumen ya viene en Unicode; la fórmula del trazador pasa por el carrusel |
| Determinantes, TMI, identidades, PLU | el carrusel de cada vista | el mismo `formula_label` |

`DeterminantsView`, `LUFactorizationView`, `MatrixOperationsView` y `VectorsView` no tienen un segundo pintor de LaTeX: muestran el paso en `AlgorithmStepperCarousel`.

## 3. Orden del pipeline

`latex_to_book_html` delega en `_render_math`. El orden es fijo. Cambiarlo vuelve a filtrar comandos o se come espacios entre `\frac` y `\cdot`.

1. Extraer cada `\text{...}` a un hueco y restaurarlo al final, ya como `<span>`.
2. Entornos `\begin{bmatrix}...\end{bmatrix}`: cada fila separada por `\\` se vuelve `[a ; b]`.
3. `\sqrt{...}`, `\frac{...}{...}` (también `\dfrac` y `\tfrac`) y `\mathbb{...}`, con llaves balanceadas y recursión sobre el interior.
4. Flechas `\underset{\sim}{\rightarrow}` y `\underset{\sim}\rightarrow`, normas `\|` y `\Vert`, negaciones `\not\geq` / `\not\le`, delimitadores `\left` / `\right`, espacios finos `\,` `\;` `\:` `\!` y comandos con nombre.
5. Subíndices y superíndices, primero con llaves y después en forma plana.
6. Guiones algebraicos `-` → `−` solo fuera de las etiquetas HTML. `+ -` y `+-` se leen como un solo menos.
7. Restaurar los bloques `\text`.
8. Envolver el resultado en el `<span>` de 22px.

Un comando desconocido pierde la barra (`\foo` → `foo`) para no pintar `\`. Eso no es soporte: es un último recurso. El comando nuevo se añade a la tabla y al corpus.

## 4. Tabla canónica

### 4.1. Subíndices

| Entrada | Salida | Nota |
| :--- | :--- | :--- |
| `f_{1}`, `f_1`, `F_{2}`, `F_2` | `F₁`, `F₂` | Fila de matriz: dígitos Unicode. La `f` pasa a `F`. |
| `f_{i}`, `f_i`, `F_i` | `F<sub>i</sub>` | El índice no es un dígito. |
| `A_{ij}`, `C_{11}`, `x_{12}`, `u_{i}` | `A<sub>ij</sub>`, `C<sub>11</sub>`, `x<sub>12</sub>`, `u<sub>i</sub>` | Cualquier base que no sea una fila. |
| `A_1`, `b_1`, `u_i`, `v_j`, `I_n` | `A<sub>1</sub>`, `b<sub>1</sub>`, `u<sub>i</sub>`, `v<sub>j</sub>`, `I<sub>n</sub>` | Forma plana: dígitos o letras. |
| `C_3H_8`, `H_2O`, `CO_2` | `C<sub>3</sub>H<sub>8</sub>`, `H<sub>2</sub>O`, `CO<sub>2</sub>` | El subíndice plano numérico no se traga el elemento siguiente. |
| `x1` en texto ASCII | `<i>x</i><sub>1</sub>` | Solo `plain_formula_to_html` / `to_html_subscripts`, no el LaTeX. |

`prettify_math_text` sigue normalizando ecuaciones ASCII del verificador (`2*x1` → `2x₁`). No sustituye a `latex_to_book_html`.

### 4.2. Superíndices

| Entrada | Salida |
| :--- | :--- |
| `A^{T}`, `A^T`, `v^{T}` | `Aᵀ`, `vᵀ` |
| `A^{-1}`, `(AB)^{-1}`, `(A^{-1})^{-1}` | `A⁻¹`, `(AB)⁻¹`, `(A⁻¹)⁻¹` |
| `(A^T)^{-1} = (A^{-1})^T` | `(Aᵀ)⁻¹ = (A⁻¹)ᵀ` |
| `x^2`, `\|v\|^2`, `2^{2}`, `(-1)^{2}` | `x²`, `‖v‖²`, `2²`, `(−1)²` |
| `k^{n}`, `k^n` | `kⁿ` |
| `(-1)^{swaps}` | `(−1)<sup>swaps</sup>` |

Si cada carácter del exponente está en `0-9`, `+`, `-`, `n`, `i`, `T` o paréntesis, se usa el glifo Unicode. En cualquier otro caso se usa `<sup>`.

### 4.3. Comandos y símbolos

| LaTeX | Libro |
| :--- | :--- |
| `\det` | `<i>det</i>` |
| `\sqrt{x}` | `√<span style="text-decoration:overline;">x</span>` |
| `\|`, `\Vert` | `‖` |
| `\cdot` | `·` |
| `\times` | `×` |
| `\pm`, `\mp` | `±`, `∓` |
| `\neq`, `\ne` | `≠` |
| `\leq`, `\le` | `≤` |
| `\geq`, `\ge` | `≥` |
| `\not\geq`, `\not\ge` | `≱` |
| `\not\leq`, `\not\le` | `≰` |
| `\sum`, `\prod` | `∑`, `∏` |
| `\rightarrow`, `\to`, `\underset{\sim}{\rightarrow}`, `\underset{\sim}\rightarrow` | `→` |
| `\leftarrow`, `\longleftarrow` | `←` |
| `\leftrightarrow` | `↔` |
| `\Rightarrow`, `\Leftrightarrow` | `⇒`, `⇔` |
| `\mathbb{R}`, y también `N`, `Z`, `Q`, `C` | `ℝ`, `ℕ`, `ℤ`, `ℚ`, `ℂ` |
| `\in`, `\forall` | `∈`, `∀` |
| `\mid`, `\vert` | `|` |
| `\infty` | `∞` |
| `\cdots`, `\ldots`, `\dots`, `\vdots` | `⋯`, `…`, `…`, `⋮` |
| `\frac{a}{b}`, `\dfrac`, `\tfrac` | `(a/b)`, con el interior ya convertido |
| `\left( \right)`, `\left[ \right]`, `\left| \right|` | `( )`, `[ ]`, `|` |
| `\left\{ \right\}` | `{` `}` |
| `\,` `\;` `\:` `\!` y `\` + espacio | espacio |
| `\quad`, `\qquad` | espacio |
| `\begin{bmatrix} a \\ b \end{bmatrix}` | `[a ; b]` |
| guion algebraico `-` | `−` |
| `\text{prosa}` | prosa en `<span style="font-family:sans-serif; font-style:normal;">`, y la matemática de afuera sigue |

`\mid` produce `|`. No produce `‖`. La norma es solo `\|` o `\Vert`.

Los delimitadores de conjunto `\left\{` y `\right\}` sí dejan llaves `{` `}` en el HTML. El corpus centinela de la sección 6 no incluye esas fórmulas: su aserción prohíbe cualquier `{` o `}`. Una fórmula futura que necesite llaves de conjunto se prueba aparte y no se mete en ese bucle.

## 5. Reglas para quien añada un paso

Al registrar una operación en el trazador:

1. Escribir `latex_formula` en LaTeX estándar, en el módulo de `prettycalc.core` que calcula. No importar `prettycalc.ui` desde el core.
2. Si el comando no está en la tabla de la sección 4, añadirlo en `_NAMED_COMMANDS` o en el pasador de llaves de `mathtext.py`, y añadir la fila a esta tabla en el mismo cambio.
3. Añadir la cadena literal a `_BOOK_FORMULAS` en `tests/ui/test_mathtext.py`, o un test con el fragmento de libro esperado (`F₁`, `⁻¹`, `<i>det</i>`, `‖`).
4. El test nuevo tiene que fallar si se borra el caso del conversor. No basta con mirar la pantalla.
5. El `QLabel` que lo muestre usa `Qt.RichText`. Si el texto no es LaTeX sino `y_1` o `x1`, usar `plain_formula_to_html`.
6. No reintroducir un atajo del estilo «si la cadena contiene `\text{`, devolver el resto sin transformar». Ese atajo fue el fallo que esta especificación cierra.

## 6. Pruebas centinela

`tests/ui/test_mathtext.py` recorre más de veinte expresiones de las sesiones 1 a 12 (filas, inversa, determinantes, norma, PLU, química, Leontief y cotas). Para cada HTML exige:

* no queda `\`, salvo una comilla escapada `\'` si alguna hoja de estilo la usara;
* no quedan `{` ni `}`;
* no quedan `_` ni `^` sin convertir;
* el contenedor lleva `font-size:22px` y `letter-spacing:0.03em`.

`test_carousel_formula_label_uses_rich_text` comprueba que el carrusel aplica ese HTML con `Qt.RichText`, incluida una fórmula que mezcla `\text` y `\det`.

Esas pruebas se ejecutan con el resto de la suite:

```bash
QT_QPA_PLATFORM=offscreen pytest
```
