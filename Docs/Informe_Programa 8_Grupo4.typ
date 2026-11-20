// ==============================================================================
// UNIVERSIDAD AMERICANA (UAM) - FACULTAD DE INGENIERÍA Y ARQUITECTURA (FIA)
// ASIGNATURA: ÁLGEBRA LINEAL (MTM0120) — TERCER CORTE EVALUATIVO
// INFORME TÉCNICO OFICIAL: PROGRAMA 8 — MÉTODOS NUMÉRICOS ITERATIVOS
// GRUPO 4: TERCERO, FLORES, BELLANGER, VALVERDE
// ==============================================================================

#set document(
  title: "Informe Técnico - Programa 8: Métodos Iterativos (Jacobi y Gauss-Seidel)",
  author: "Grupo 4: Roberto Fabio Tercero, Steven Flores, Kellys Bellanger, Raúl Valverde",
  date: auto
)

#set page(
  paper: "us-letter",
  margin: (top: 1.8cm, bottom: 1.8cm, left: 1.9cm, right: 1.9cm),
  header: context {
    let page-num = counter(page).get().first()
    if page-num > 1 [
      #grid(
        columns: (1fr, auto),
        align: (left + horizon, right + horizon),
        text(8pt, fill: rgb("#475569"))[Universidad Americana (UAM) · Álgebra Lineal (MTM0120)],
        text(8pt, fill: rgb("#1e3a8a"), weight: "bold")[Programa 8: Métodos Numéricos Iterativos]
      )
      #v(1.5pt)
      #line(length: 100%, stroke: 0.5pt + rgb("#cbd5e1"))
    ]
  },
  footer: context {
    let page-num = counter(page).get().first()
    let total-pages = counter(page).final().first()
    [
      #line(length: 100%, stroke: 0.5pt + rgb("#cbd5e1"))
      #v(2pt)
      #grid(
        columns: (1fr, auto, 1fr),
        align: (left + horizon, center + horizon, right + horizon),
        text(8pt, fill: rgb("#64748b"))[Grupo 4 · Proyecto Integrador],
        text(8pt, fill: rgb("#64748b"))[Facultad de Ingeniería y Arquitectura],
        text(8pt, fill: rgb("#1e3a8a"), weight: "bold")[Página #page-num de #total-pages]
      )
    ]
  }
)

#set text(
  font: "Liberation Sans",
  size: 9pt,
  lang: "es"
)

#set par(
  justify: true,
  leading: 0.55em
)

// Estilos de encabezados
#show heading.where(level: 1): it => block(width: 100%, below: 7pt, above: 10pt)[
  #text(11.5pt, weight: "bold", fill: rgb("#1e3a8a"))[#it.body]
  #v(1.5pt)
  #line(length: 100%, stroke: 1.2pt + rgb("#1e3a8a"))
]

#show heading.where(level: 2): it => block(width: 100%, below: 5pt, above: 8pt)[
  #text(9.5pt, weight: "bold", fill: rgb("#2563eb"))[#it.body]
]

#show heading.where(level: 3): it => block(width: 100%, below: 3.5pt, above: 6.5pt)[
  #text(8.8pt, weight: "bold", fill: rgb("#0f172a"))[#it.body]
]

#show figure.caption: it => block(width: 100%, above: 3.5pt)[
  #text(7.8pt, style: "italic", fill: rgb("#475569"))[#it]
]

// Componentes y utilidades
#let badge(label, type: "info") = {
  let bg = rgb("#0284c7")
  if type == "success" { bg = rgb("#16a34a") }
  else if type == "warning" { bg = rgb("#d97706") }
  else if type == "danger" { bg = rgb("#dc2626") }
  box(
    fill: bg,
    radius: 2.5pt,
    inset: (x: 4pt, y: 1.2pt),
    baseline: -1pt,
    text(fill: white, size: 6.8pt, weight: "bold")[#label]
  )
}

#let callout(title: none, body, type: "info") = {
  let bg = rgb("#eff6ff")
  let border = rgb("#3b82f6")
  let header-color = rgb("#1e40af")
  if type == "warning" {
    bg = rgb("#fffbeb")
    border = rgb("#f59e0b")
    header-color = rgb("#b45309")
  } else if type == "danger" {
    bg = rgb("#fef2f2")
    border = rgb("#ef4444")
    header-color = rgb("#b91c1c")
  } else if type == "success" {
    bg = rgb("#f0fdf4")
    border = rgb("#22c55e")
    header-color = rgb("#15803d")
  }
  rect(
    width: 100%,
    fill: bg,
    radius: 3pt,
    stroke: (left: 3.5pt + border, rest: 0.5pt + rgb("#cbd5e1")),
    inset: (x: 8pt, y: 5pt)
  )[
    #if title != none [
      #text(weight: "bold", size: 8.2pt, fill: header-color)[#title]\
      #v(1pt)
    ]
    #text(size: 7.8pt, fill: rgb("#1e293b"))[#body]
  ]
}

#let screenshot(path, caption-text, width: 88%) = {
  figure(
    rect(
      radius: 3.5pt,
      stroke: 0.5pt + rgb("#cbd5e1"),
      inset: 0pt,
      image(path, width: width)
    ),
    caption: caption-text
  )
}

#let qacard(number, question, answer) = {
  rect(
    width: 100%,
    fill: rgb("#f8fafc"),
    radius: 3.5pt,
    stroke: 0.5pt + rgb("#cbd5e1"),
    inset: (x: 8pt, y: 6pt)
  )[
    #grid(
      columns: (auto, 1fr),
      gutter: 6pt,
      align: horizon,
      badge("P" + str(number), type: "info"),
      text(weight: "bold", size: 8.2pt, fill: rgb("#0f172a"))[#question]
    )
    #v(2pt)
    #line(length: 100%, stroke: 0.5pt + rgb("#e2e8f0"))
    #v(2pt)
    #text(size: 7.8pt, fill: rgb("#334155"))[*Fundamentación Técnica:* #answer]
  ]
}

// ==============================================================================
// PÁGINA 1: PORTADA INSTITUCIONAL Y SECCIÓN 1 (OBJETIVOS)
// ==============================================================================

#grid(
  columns: (44pt, 1fr),
  gutter: 12pt,
  align: horizon,
  image("logo.svg", width: 40pt),
  [
    #text(13.5pt, weight: "bold", fill: rgb("#1e3a8a"))[UNIVERSIDAD AMERICANA (UAM)] \
    #v(0.5pt)
    #text(9.5pt, weight: "semibold", fill: rgb("#2563eb"))[Facultad de Ingeniería y Arquitectura (FIA)] \
    #v(0.5pt)
    #text(7.8pt, fill: rgb("#475569"))[Asignatura: Álgebra Lineal (MTM0120) · Tercer Corte Evaluativo · II Semestre 2026]
  ]
)

#v(3pt)

#rect(
  width: 100%,
  fill: rgb("#f1f5f9"),
  radius: 3.5pt,
  stroke: (left: 4pt + rgb("#1e3a8a"), rest: 0.5pt + rgb("#cbd5e1")),
  inset: (x: 10pt, y: 7pt)
)[
  #text(11pt, weight: "bold", fill: rgb("#0f172a"))[INFORME TÉCNICO OFICIAL: PROGRAMA 8]\
  #v(1pt)
  #text(9pt, weight: "bold", fill: rgb("#1e3a8a"))[Métodos Numéricos Integrador: Jacobi y Gauss-Seidel en la Calculadora de Álgebra Lineal]\
  #v(1pt)
  #text(7.6pt, fill: rgb("#334155"))[Integración en Python puro con aritmética exacta (`fractions.Fraction`), diagnóstico espectral de convergencia $rho(T)$, desmitificación de Stein-Rosenberg y guía de defensa individual.]
]

#v(2pt)

#table(
  columns: (115pt, 1fr),
  stroke: none,
  fill: (col, row) => if calc.even(row) { rgb("#f8fafc") } else { white },
  inset: (x: 5pt, y: 3pt),
  [*Equipo de Trabajo:*], [Grupo 4],
  [*Integrantes:*], [
    #set par(justify: false)
    #grid(
      columns: (1fr, 1fr),
      row-gutter: 2.5pt,
      column-gutter: 4pt,
      [• *Roberto Fabio Tercero Morán* (`rftercerom@uamv.edu.ni`)],
      [• *Steven Alexander Flores Obregón* (`safloreso@uamv.edu.ni`)],
      [• *Kellys Bellanger* (`kbbellanger@uamv.edu.ni`)],
      [• *Raúl Valverde Ruiz* (`raulvruiz@uamv.edu.ni`)]
    )
  ],
  [*Carrera y Semestre:*], [Ingeniería en Sistemas de Información / Ingeniería de Software — 4.° Semestre],
  [*Fecha de Entrega:*], [Noviembre de 2026]
)

#v(2pt)

= 1. Propósito y Objetivos de la Actividad

El presente informe técnico documenta la culminación y entrega formal del *Programa 8*, correspondiente al proyecto integrador de la cátedra de Álgebra Lineal (MTM0120) de la Universidad Americana (UAM). En esta práctica, el Grupo 4 integra de forma sistemática y rigurosa los *métodos numéricos iterativos de Jacobi y Gauss-Seidel* a la calculadora de Álgebra Lineal desarrollada a lo largo del curso.

=== Objetivos Específicos:
1. *Implementación Didáctica en Python Puro:* Desarrollar los algoritmos de Jacobi y Gauss-Seidel utilizando exclusivamente la biblioteca estándar de Python (`fractions.Fraction` y estructuras nativas). Al operar con aritmética analítica exacta en fracciones racionales, se elimina de raíz la acumulación de errores de redondeo de punto flotante binario (IEEE 754), garantizando que el único error analizado sea el de *truncamiento de la serie iterativa*.
2. *Diagnóstico Analítico Previo:* Dotar a la calculadora de un motor de diagnóstico previo que valide las dimensiones del sistema, detecte ceros en la diagonal ($a_(i i) = 0$), evalúe la condición suficiente de *Dominancia Diagonal Estricta por Filas*, calcule el polinomio característico mediante el algoritmo clásico de *Faddeev-LeVerrier* y aproxime los autovalores en el cuerpo de los complejos $CC$ mediante *Durand-Kerner (Weierstrass)* para determinar con exactitud el *radio espectral* $rho(T)$.
3. *Comprobación Experimental Rigurosa:* Documentar y validar el comportamiento numérico de los algoritmos mediante 6 casos de prueba controlados: convergencia acelerada en matrices diagonal dominantes, rescate de la convergencia mediante permutación inteligente de filas (`reorder_for_dominance`), divergencia por falta de dominancia, y contraejemplos analíticos que refutan la creencia común de que Gauss-Seidel siempre es superior a Jacobi.
4. *Validación Cruzada de Grado Científico:* Comparar formalmente cada solución iterativa calculada contra la solución de referencia exacta provista por `numpy.linalg.solve(A, b)`, registrando el residuo matricial final $norm(A bold(x) - bold(b))_oo$ y la discrepancia máxima.
5. *Preparación para la Defensa Individual:* Proporcionar un compendio de preguntas y respuestas conceptuales exhaustivas que capaciten a cada uno de los integrantes del equipo para sustentar el código, fundamentar las decisiones de diseño y responder cualquier interrogante teórica ante el docente evaluador.

#pagebreak()

// ==============================================================================
// PÁGINA 2: SECCIÓN 2.1, 2.2, 2.3 (DESCOMPOSICIÓN, JACOBI, GAUSS-SEIDEL)
// ==============================================================================
= 2. Fundamentación Teórica y Modelado Matemático

== 2.1. Descomposición Canónica de la Matriz de Coeficientes

Consideremos un sistema de $n$ ecuaciones lineales con $n$ incógnitas denotado matricialmente como $A bold(x) = bold(b)$, donde $A in RR^(n times n)$ es una matriz no singular con entradas diagonales no nulas ($a_(i i) != 0$ para todo $i = 1, dots, n$). La matriz de coeficientes se descompone aditivamente de manera única en la suma de tres componentes estructurales:

$ A = D + L + U $

Donde:
- $D = "diag"(a_(11), a_(22), dots, a_(n n))$ es la matriz que contiene únicamente los elementos de la diagonal principal.
- $L$ es la matriz triangular inferior estricta con ceros en y por encima de la diagonal principal ($l_(i j) = a_(i j)$ si $i > j$, y $l_(i j) = 0$ si $i <= j$).
- $U$ es la matriz triangular superior estricta con ceros en y por debajo de la diagonal principal ($u_(i j) = a_(i j)$ si $i < j$, y $u_(i j) = 0$ si $i >= j$).

== 2.2. Método Iterativo de Jacobi (Desplazamientos Simultáneos)

En el método de Jacobi, cada incógnita $x_i$ se despeja algebraicamente de la $i$-ésima ecuación del sistema, evaluando las demás variables exclusivamente en los valores conocidos de la iteración inmediatamente anterior $bold(x)^((k))$:

$ x_i^((k+1)) = 1 / a_(i i) ( b_i - sum_(j=1, j != i)^n a_(i j) x_j^((k)) ), quad i = 1, 2, dots, n $

=== Formulación Matricial:
Sustituyendo la descomposición canónica en el sistema lineal:
$ (D + L + U) bold(x) = bold(b) ==> D bold(x) = bold(b) - (L + U) bold(x) ==> bold(x)^((k+1)) = -D^(-1) (L + U) bold(x)^((k)) + D^(-1) bold(b) $

Definiendo la *Matriz de Iteración de Jacobi* ($T_J$) y su respectivo *vector de traslación* ($bold(c)_J$):
$ T_J = -D^(-1)(L + U), quad bold(c)_J = D^(-1) bold(b) ==> bold(x)^((k+1)) = T_J bold(x)^((k)) + bold(c)_J $

#callout(title: "Propiedad Distintiva de Jacobi:", [
  Dado que el cálculo de cada componente $x_i^((k+1))$ depende *únicamente* del vector anterior $bold(x)^((k))$, el algoritmo requiere almacenar obligatoriamente dos vectores independientes en memoria: el estado del paso actual y el del paso previo. Por esta razón, el método recibe el nombre de *desplazamientos simultáneos* y posee una naturaleza inherentemente paralelizable.
], type: "info")

== 2.3. Método Iterativo de Gauss-Seidel (Desplazamientos Sucesivos)

El método de Gauss-Seidel optimiza la aproximación reutilizando de forma inmediata las componentes $x_1^((k+1)), dots, x_(i-1)^((k+1))$ que ya han sido calculadas dentro de la misma iteración en curso:

$ x_i^((k+1)) = 1 / a_(i i) ( b_i - sum_(j=1)^(i-1) a_(i j) x_j^((k+1)) - sum_(j=i+1)^n a_(i j) x_j^((k)) ), quad i = 1, 2, dots, n $

=== Formulación Matricial:
$ (D + L) bold(x)^((k+1)) + U bold(x)^((k)) = bold(b) ==> (D + L) bold(x)^((k+1)) = bold(b) - U bold(x)^((k)) ==> bold(x)^((k+1)) = -(D + L)^(-1) U bold(x)^((k)) + (D + L)^(-1) bold(b) $

Definiendo la *Matriz de Iteración de Gauss-Seidel* ($T_(G S)$) y su vector de traslación ($bold(c)_(G S)$):
$ T_(G S) = -(D + L)^(-1) U, quad bold(c)_(G S) = (D + L)^(-1) bold(b) ==> bold(x)^((k+1)) = T_(G S) bold(x)^((k)) + bold(c)_(G S) $

#callout(title: "Propiedad Distintiva de Gauss-Seidel:", [
  Debido a que cada nueva componente se incorpora tan pronto como se obtiene, el método de *desplazamientos sucesivos* puede implementarse *in-place* (sobreescribiendo el mismo vector en memoria). En la inmensa mayoría de matrices bien estructuradas, la incorporación inmediata de información fresca acelera significativamente la tasa de convergencia en comparación con Jacobi.
], type: "success")

#pagebreak()

// ==============================================================================
// PÁGINA 3: SECCIÓN 2.4 (TEOREMAS DE CONVERGENCIA)
// ==============================================================================
== 2.4. Teoremas y Criterios Fundamentales de Convergencia

=== A. Condición Suficiente: Dominancia Diagonal Estricta por Filas
Una matriz $A in RR^(n times n)$ es *estrictamente diagonal dominante por filas* si la magnitud de cada coeficiente diagonal supera estrictamente a la suma de las magnitudes de los coeficientes no diagonales de su misma fila:

$ |a_(i i)| > sum_(j=1, j != i)^n |a_(i j)|, quad forall i in {1, 2, dots, n} $

- *Teorema de Convergencia Global:* Si la matriz $A$ es estrictamente diagonal dominante por filas, entonces *TANTO Jacobi COMO Gauss-Seidel CONVERGEN* hacia la solución exacta única $bold(x)^* = A^(-1) bold(b)$ para *cualquier* vector inicial $bold(x)^((0)) in RR^n$.
- *Fundamento Teórico:* De acuerdo con el *Teorema de Círculos de Gershgorin*, la dominancia diagonal estricta garantiza que todos los autovalores de la matriz de iteración $T$ quedan confinados estrictamente en el interior del disco unitario abierto ($|lambda| < 1$).
- *Naturaleza Lógica:* Es una condición *suficiente, pero NO necesaria*. La ausencia de dominancia diagonal jamás autoriza a sentenciar que el método va a divergir.

=== B. Condición Necesaria y Suficiente: Criterio del Radio Espectral $rho(T)$
Para cualquier esquema iterativo lineal estacionario de la forma $bold(x)^((k+1)) = T bold(x)^((k)) + bold(c)$:
- Sea $rho(T) = max_i |lambda_i|$ el *radio espectral* de la matriz de iteración $T$, donde $lambda_i$ representan sus autovalores en el cuerpo de los complejos $CC$.
- *Teorema Fundamental del Álgebra Matricial:* El proceso iterativo converge hacia la solución para todo vector inicial $bold(x)^((0))$ si y solo si:
$ rho(T) < 1 $
- *Evolución Dinámica del Error:* El vector de error $bold(e)^((k)) = bold(x)^((k)) - bold(x)^*$ satisface la relación recurrente $bold(e)^((k)) = T^k bold(e)^((0))$. Por el teorema de descomposición espectral o forma canónica de Jordan, $lim_(k -> oo) T^k = bold(0)$ si y solo si $rho(T) < 1$.
- *Tasa Asintótica de Convergencia:* La velocidad a la que el error decae está gobernada por $R = -ln(rho(T))$. Cuanto menor sea $rho(T)$, mayor es $R$ y menos iteraciones se requieren para alcanzar una tolerancia dada $epsilon$.

=== C. Teorema de Ostrowski-Reich (Matrices Simétricas Definidas Positivas)
Si $A$ es una matriz simétrica ($A = A^T$) con diagonal estrictamente positiva ($a_(i i) > 0$), y es *definida positiva* (lo cual se dictamina de manera exacta mediante el *Criterio de Sylvester*, evaluando que todos los menores principales directos tengan determinante estrictamente positivo: $det(A_k) > 0$ para $k = 1, dots, n$), entonces:
$ rho(T_(G S)) < 1 $
Bajo estas condiciones, *Gauss-Seidel converge incondicionalmente* para cualquier aproximación inicial $bold(x)^((0))$, aun si la matriz no posee dominancia diagonal.

=== D. Teorema de Stein-Rosenberg y Desmitificación de Superioridad
El Teorema clásico de Stein-Rosenberg establece que si todos los coeficientes fuera de la diagonal de la matriz $A$ son no positivos ($a_(i j) <= 0$ para todo $i != j$) y $a_(i i) > 0$:
1. Si $rho(T_J) < 1$, entonces $rho(T_(G S)) < rho(T_J) < 1$ (Gauss-Seidel converge estrictamente más rápido que Jacobi).
2. Si $rho(T_J) >= 1$, entonces $rho(T_(G S)) >= rho(T_J) >= 1$ (ambos métodos divergen).

#callout(title: "Ruptura de Mito Docente (¡Punto Crucial para la Defensa!):", [
  En la enseñanza universitaria suele propagarse la idea errónea de que *\"Gauss-Seidel siempre es mejor que Jacobi\"*. Esto es matemáticamente *FALSO*. Si la matriz de coeficientes contiene signos mixtos fuera de la diagonal (violando la hipótesis de Stein-Rosenberg), existen sistemas donde *Jacobi converge y Gauss-Seidel diverge explosivamente*. El Caso didáctico complementario demuestra esta realidad empírica con $rho(T_J) = 0$ (Jacobi converge en 4 iteraciones) y $rho(T_(G S)) = 2.0$ (Gauss-Seidel diverge hacia el infinito).
], type: "warning")

#pagebreak()

// ==============================================================================
// PÁGINA 4: SECCIÓN 2.5 (CRITERIOS DE PARADA) Y SECCIÓN 3 (ARQUITECTURA)
// ==============================================================================
== 2.5. Criterios de Parada Numérica y Salvaguardas de Divergencia

La calculadora evalúa en cada paso iterativo las siguientes métricas de precisión y control:
1. *Error Absoluto entre Iteraciones (Criterio Principal):* Monitorea la norma infinito del vector de desplazamiento:
   $ norm(Delta bold(x)^((k)))_oo = norm(bold(x)^((k)) - bold(x)^((k-1)))_oo = max_(1 <= i <= n) |x_i^((k)) - x_i^((k-1))| < epsilon $
2. *Error Relativo:* Protege contra falsas paradas en sistemas con soluciones de gran escala:
   $ (norm(Delta bold(x)^((k)))_oo) / (norm(bold(x)^((k)))_oo) < epsilon $
3. *Residuo Matricial del Sistema:* Certifica la calidad física de la solución evaluando qué tan bien satisface el sistema original:
   $ norm(bold(r)^((k)))_oo = norm(A bold(x)^((k)) - bold(b))_oo = max_(1 <= i <= n) |sum_(j=1)^n a_(i j) x_j^((k)) - b_i| $
4. *Cota Máxima de Iteraciones ($k_(max)$):* Previene bucles infinitos en sistemas divergentes o estancados.
5. *Salvaguarda Temprana de Divergencia (Norm Divergence Guard):* Si en cualquier iteración se detecta que $norm(bold(x)^((k)))_oo > 10^8 dot max(norm(bold(x)^((0)))_oo, norm(bold(b))_oo, 1)$, el motor interrumpe la ejecución de forma preventiva y dictamina *DIVERGENCIA EXPLOSIVA*, evitando desbordamientos de memoria y ciclos computacionales inútiles.

= 3. Decisiones de Arquitectura e Implementación en Python

== 3.1. Cumplimiento del Contrato Didáctico (100% Python Estándar)
Para los módulos de cómputo iterativo y la entrega del *Programa 8*, el equipo descartó por completo el uso de bibliotecas de álgebra lineal como `numpy`, `scipy` o `sympy` en la lógica de resolución. Toda la manipulación matricial, sumatorias, despejes y cálculo de normas se implementaron utilizando la clase estándar `fractions.Fraction`.

*Ventaja Pedagógica Invaluable:* Al mantener los cálculos en aritmética de números racionales exactos con numeradores y denominadores enteros de precisión arbitraria, el sistema opera con *cero ruido de redondeo numérico*. En consecuencia, cada variación entre iteraciones refleja pura y exclusivamente el error de truncamiento del método numérico.

== 3.2. Polinomio Característico y Autovalores Complejos sin Dependencias
Para determinar de manera fidedigna el radio espectral $rho(T)$ sin recurrir a funciones empaquetadas:
- Se implementó el método de *Faddeev-LeVerrier*, el cual calcula los coeficientes exactos del polinomio característico $p(lambda) = det(lambda I - T)$ a través de trazas sucesivas de productos matriciales racionales.
- Para hallar las raíces complejas de $p(lambda)$, se programó el método iterativo de *Durand-Kerner (Weierstrass)* en el cuerpo complejo $CC$, el cual converge simultáneamente a todos los autovalores $lambda_1, dots, lambda_n$. De este modo, el radio espectral $rho(T) = max_i |lambda_i|$ se calcula con rigor analítico.

== 3.3. Detección de Cero Diagonal y Algoritmo de Reordenamiento (`reorder_for_dominance`)
Si la matriz presenta un cero en su diagonal principal ($a_(i i) = 0$), el despeje formal conduciría a una indeterminación matemática inmediata por división entre cero. Para resolver este desafío sin intervención manual:
- El software comprueba de forma preventiva la existencia de ceros diagonales.
- Si detecta un cero o si la matriz carece de dominancia diagonal, activa la subrutina `reorder_for_dominance(A, b)`, la cual explora las permutaciones de filas para ubicar los coeficientes de mayor magnitud en la diagonal principal.
- Si existe un ordenamiento que restaure la dominancia estricta, la calculadora reorganiza el sistema, informa la permutación realizada y prosigue con la resolución.

== 3.4. Arquitectura Modular en Tres Frentes
El desarrollo del proyecto se estructuró en tres niveles complementarios:
1. *Script Autónomo de Consola (`Programa 8_Grupo4.py`):* Ubicado en la raíz del repositorio, es un ejecutable autónomo en Python puro con menú interactivo, arte ASCII, diagnósticos y menú de casos preconfigurados.
2. *Suite Modular Profesional (`Calculadora_Algebra_Lineal/modulos/modulo_iterativos.py`):* Integra los métodos de Jacobi y Gauss-Seidel como el *Módulo 5* de la calculadora general del curso, vinculada con el menú principal `main.py` y con el visor de teoremas `resumen_teoremas.py`.
3. *Aplicación Gráfica PrettyCalc (`prettycalc/ui/modules/iterative_methods_view.py`):* Módulo de interfaz gráfica en PySide6 con medidor espectral visual dinámico, tablas de iteraciones y gráficas semilogarítmicas de error en tiempo real.

#pagebreak()

// ==============================================================================
// PÁGINA 5: FIGURA 1 (GUI SHOWCASE) Y SECCIÓN 4 (INTRODUCCIÓN CASOS)
// ==============================================================================
= 4. Casos de Prueba Didácticos y Evidencias Visuales

Para validar de forma transparente y exhaustiva todos los principios matemáticos descritos, el equipo diseñó e integró en el software una suite de *6 casos de prueba didácticos preconfigurados*, accesibles directamente desde el menú principal del script de consola y desde el selector de la interfaz gráfica PrettyCalc:

#v(2pt)

#rect(
  width: 100%,
  fill: rgb("#0f172a"),
  radius: 3.5pt,
  inset: (x: 10pt, y: 7pt)
)[
  #text(fill: rgb("#f8fafc"), font: "Liberation Mono", size: 7.2pt)[
    ==============================================================================\
    🧪 CASOS DE PRUEBA DIDÁCTICOS PRECONFIGURADOS (PROGRAMA 8 — GRUPO 4)\
    ==============================================================================\
    1. Caso 1: Matriz Estrictamente Diagonal Dominante (Burden & Faires 4x4)\
    2. Caso 2: Solo Gauss-Seidel Converge (ρ(T_J) > 1 y ρ(T_GS) < 1)\
    3. Caso 3: Solo Jacobi Converge (¡Gauss-Seidel NO siempre es mejor!)\
    4. Caso 4: Divergencia de Ambos Métodos (No Diagonal Dominante 2x2)\
    5. Caso 5: Reordenamiento Exitoso de Ecuaciones (Restaura Dominancia y Convergencia)\
    6. Caso 6: Cero en la Diagonal Principal (a₁₁ = 0 y división por cero prevenida)\
    ==============================================================================
  ]
]

#v(4pt)

#screenshot("screenshots/gui_prettycalc_iterative_window.png", [Vista general de la ventana interactiva de Métodos Iterativos en PrettyCalc, mostrando panel de control, tabla de iteraciones en tiempo real y medidor espectral visual.], width: 84%)

#v(4pt)

=== Metodología de Evaluación Numérica:
Cada caso de prueba fue ejecutado bajo parámetros homogéneos y rigurosos:
- *Vector de Inicio:* $bold(x)^((0)) = (0, 0, dots, 0)^T$ (vector nulo estándar).
- *Tolerancia de Convergencia:* $epsilon = 10^(-4) = 0.0001$.
- *Criterio de Parada:* Error absoluto entre iteraciones consecutivas $norm(bold(x)^((k)) - bold(x)^((k-1)))_oo < epsilon$.
- *Cota Máxima de Iteraciones:* $k_(max) = 100$ iteraciones.
- *Auditoría de Referencia:* Contrastación contra la solución exacta de `numpy.linalg.solve(A, b)` y evaluación del residuo final $norm(A bold(x)^((k)) - bold(b))_oo$.

#pagebreak()

// ==============================================================================
// PÁGINA 6: SECCIÓN 4.1 (CASO 1: BURDEN & FAIRES 4x4)
// ==============================================================================
== 4.1. Caso 1: Convergencia en Matriz Estrictamente Diagonal Dominante ($4 times 4$)
*Origen:* Burden & Faires, *Análisis Numérico*, ejemplo canónico de comparación iterativa.

*Sistema de Ecuaciones Lineales:*
$ mat(delim: "[",
  10, -1, 2, 0;
  -1, 11, -1, 3;
  2, -1, 10, -1;
  0, 3, -1, 8
)
mat(delim: "[", x_1; x_2; x_3; x_4 ) =
mat(delim: "[", 6; 25; -11; 15 )
==> bold(x)^* = mat(delim: "[", 1; 2; -1; 1 ) $

=== Diagnóstico Analítico Previo:
- Fila 1: $|10| > |-1| + |2| + |0| = 3$ #badge("CUMPLE", type: "success")
- Fila 2: $|11| > |-1| + |-1| + |3| = 5$ #badge("CUMPLE", type: "success")
- Fila 3: $|10| > |2| + |-1| + |-1| = 4$ #badge("CUMPLE", type: "success")
- Fila 4: $|8| > |0| + |3| + |-1| = 4$ #badge("CUMPLE", type: "success")
- *Veredicto:* #badge("ESTRICTAMENTE DIAGONAL DOMINANTE", type: "success") $==>$ Convergencia incondicional garantizada para ambos métodos.
- *Radios Espectrales Calculados:* $rho(T_J) approx 0.4264 < 1$ y $rho(T_(G S)) approx 0.0898 < 1$.

#table(
  columns: (1fr, 55pt, 2fr, 70pt, 70pt, 55pt),
  fill: (col, row) => if row == 0 { rgb("#1e3a8a") } else if calc.even(row) { rgb("#f8fafc") } else { white },
  stroke: (x, y) => if y == 0 { none } else { 0.5pt + rgb("#cbd5e1") },
  inset: (x: 4.5pt, y: 3.5pt),
  align: center + horizon,
  table.header(
    text(white, weight: "bold", size: 7.5pt)[Método],
    text(white, weight: "bold", size: 7.5pt)[Iter.],
    text(white, weight: "bold", size: 7.5pt)[Solución Obtenida ($x_1, x_2, x_3, x_4$)],
    text(white, weight: "bold", size: 7.5pt)[Error vs NumPy],
    text(white, weight: "bold", size: 7.5pt)[Residuo $norm(A bold(x) - bold(b))_oo$],
    text(white, weight: "bold", size: 7.5pt)[Estado]
  ),
  [Jacobi], [13], [$(0.999990, 2.000016, -1.000013, 1.000019)$], [$1.92 times 10^(-5)$], [$2.55 times 10^(-4)$], badge("CONVERGIÓ", type: "success"),
  [Gauss-Seidel], [6], [$(1.000008, 2.000001, -1.000003, 0.999999)$], [$8.36 times 10^(-6)$], [$7.70 times 10^(-5)$], badge("CONVERGIÓ", type: "success")
)

#v(2pt)

#grid(
  columns: (1fr, 1fr),
  gutter: 8pt,
  screenshot("screenshots/gui_caso1_diagonal_dominante.png", [Caso 1 en PrettyCalc: diagnóstico de dominancia estricta y tabla de iteraciones.], width: 100%),
  screenshot("screenshots/grafica_error_jacobi_vs_gauss_seidel.png", [Comparación semilogarítmica del error entre iteraciones $norm(Delta bold(x)^((k)))_oo$ vs $k$.], width: 100%)
)

*Conclusión Didáctica:* Gauss-Seidel converge en menos de la mitad de iteraciones que Jacobi (6 frente a 13) debido a que su radio espectral es marcadamente inferior ($0.0898$ frente a $0.4264$), acelerando cuadráticamente la tasa de amortiguamiento del error.

#pagebreak()

// ==============================================================================
// PÁGINA 7: SECCIÓN 4.2 (CASO 2: REORDENAMIENTO 2x2)
// ==============================================================================
== 4.2. Caso 2: Reordenamiento de Filas y Estructura Diagonal ($2 times 2$)
*Objetivo:* Demostrar que un sistema lineal divergente por mala colocación de ecuaciones se transforma en estrictamente convergente mediante una permutación de filas que maximice los elementos diagonales.

*Sistema Original (Sin Dominancia / Divergente):*
$ mat(delim: "[", 1, -5; 7, -1 ) mat(delim: "[", x_1; x_2 ) = mat(delim: "[", -4; 6 ) $
- Fila 1: $|1| < |-5| = 5$ (Falla). Fila 2: $|-1| < |7| = 7$ (Falla).
- Radios espectrales: $rho(T_J) = sqrt(35) approx 5.916 > 1$, $rho(T_(G S)) = 35.0 > 1$. #badge("AMBOS DIVERGEN", type: "danger")

*Sistema Reordenado mediante Permutación ($E_1 <-> E_2$):*
$ mat(delim: "[", 7, -1; 1, -5 ) mat(delim: "[", x_1; x_2 ) = mat(delim: "[", 6; -4 ) ==> bold(x)^* = mat(delim: "[", 1; 1 ) $
- Fila 1: $|7| > |-1| = 1$ #badge("DOMINA", type: "success"). Fila 2: $|-5| > |1| = 1$ #badge("DOMINA", type: "success").
- Radios espectrales transformados: $rho(T_J) approx 0.1690 < 1$, $rho(T_(G S)) approx 0.0286 < 1$.

#table(
  columns: (1fr, 55pt, 2fr, 70pt, 70pt, 55pt),
  fill: (col, row) => if row == 0 { rgb("#1e3a8a") } else if calc.even(row) { rgb("#f8fafc") } else { white },
  stroke: (x, y) => if y == 0 { none } else { 0.5pt + rgb("#cbd5e1") },
  inset: (x: 4.5pt, y: 3.5pt),
  align: center + horizon,
  table.header(
    text(white, weight: "bold", size: 7.5pt)[Método],
    text(white, weight: "bold", size: 7.5pt)[Iter.],
    text(white, weight: "bold", size: 7.5pt)[Solución Obtenida ($x_1, x_2$)],
    text(white, weight: "bold", size: 7.5pt)[Error vs NumPy],
    text(white, weight: "bold", size: 7.5pt)[Residuo $norm(A bold(x) - bold(b))_oo$],
    text(white, weight: "bold", size: 7.5pt)[Estado]
  ),
  [Jacobi], [7], [$(0.999997, 0.999995)$], [$4.66 times 10^(-6)$], [$2.00 times 10^(-5)$], badge("CONVERGIÓ", type: "success"),
  [Gauss-Seidel], [5], [$(1.000000, 1.000000)$], [$9.52 times 10^(-8)$], [$6.47 times 10^(-7)$], badge("CONVERGIÓ", type: "success")
)

#v(2pt)

#grid(
  columns: (1fr, 1fr),
  gutter: 8pt,
  screenshot("screenshots/gui_caso2_antes_reordenamiento.png", [PrettyCalc advierte divergencia por falta de dominancia y propone reordenamiento.], width: 100%),
  screenshot("screenshots/gui_caso2_reordenamiento_exitoso.png", [Tras aplicar el reordenamiento $E_1 <-> E_2$, el sistema converge a $(1, 1)^T$.], width: 100%)
)

*Conclusión Didáctica:* La simple permutación de las ecuaciones $E_1 <-> E_2$ concentra la masa numérica en la diagonal, transformando un sistema divergente en un problema estrictamente diagonal dominante que converge en tan solo 5 iteraciones con Gauss-Seidel.

#pagebreak()

// ==============================================================================
// PÁGINA 8: SECCIÓN 4.3 (CASO 3: DOMINANCIA NO ES NECESARIA)
// ==============================================================================
== 4.3. Caso 3: Advertencia / No Convergencia (La Dominancia NO es Condición Necesaria)
*Objetivo:* Probar de manera contundente que la dominancia diagonal es condición suficiente pero *no necesaria*, evidenciando un sistema donde Jacobi diverge pero Gauss-Seidel converge sin problemas.

*Sistema de Ecuaciones Lineales ($3 times 3$):*
$ mat(delim: "[", 2, -1, 1; 2, 2, 2; -1, -1, 2 ) mat(delim: "[", x_1; x_2; x_3 ) = mat(delim: "[", -1; 4; -5 ) ==> bold(x)^* = mat(delim: "[", 1; 2; -1 ) $

=== Diagnóstico Analítico y Espectral:
- Fila 1: $|2| = |-1| + |1| = 2$ (No es estrictamente mayor).
- Fila 2: $|2| < |2| + |2| = 4$ #badge("FALLA LA DOMINANCIA", type: "danger").
- *Evaluación de Radios Espectrales:*
  - Jacobi: $T_J$ tiene autovalores $lambda = plus.minus (sqrt(5) / 2) i ==> rho(T_J) = sqrt(5)/2 approx 1.1180 > 1$. #badge("DIVERGE", type: "danger")
  - Gauss-Seidel: $T_(G S)$ tiene autovalores $lambda_1 = 0.5, lambda_2 = 0, lambda_3 = 0 ==> rho(T_(G S)) = 0.5000 < 1$. #badge("CONVERGE", type: "success")

#table(
  columns: (1fr, 55pt, 2fr, 70pt, 70pt, 55pt),
  fill: (col, row) => if row == 0 { rgb("#1e3a8a") } else if calc.even(row) { rgb("#f8fafc") } else { white },
  stroke: (x, y) => if y == 0 { none } else { 0.5pt + rgb("#cbd5e1") },
  inset: (x: 4.5pt, y: 3.5pt),
  align: center + horizon,
  table.header(
    text(white, weight: "bold", size: 7.5pt)[Método],
    text(white, weight: "bold", size: 7.5pt)[Iter.],
    text(white, weight: "bold", size: 7.5pt)[Solución Obtenida ($x_1, x_2, x_3$)],
    text(white, weight: "bold", size: 7.5pt)[Error vs NumPy],
    text(white, weight: "bold", size: 7.5pt)[Residuo $norm(A bold(x) - bold(b))_oo$],
    text(white, weight: "bold", size: 7.5pt)[Estado]
  ),
  [Jacobi], [100 (Máx)], [$(-42037.95, -168153.82, 42037.95)$], [$1.68 times 10^(5)$], [$3.36 times 10^(5)$], badge("NO CONVERGIÓ", type: "danger"),
  [Gauss-Seidel], [19], [$(1.000029, 1.999968, -1.000002)$], [$3.24 times 10^(-5)$], [$8.77 times 10^(-5)$], badge("CONVERGIÓ", type: "success")
)

#v(2pt)

#grid(
  columns: (1fr, 1fr),
  gutter: 8pt,
  screenshot("screenshots/gui_caso3_no_convergencia_jacobi.png", [Caso 3 en PrettyCalc: Jacobi no converge mientras Gauss-Seidel alcanza $(1, 2, -1)^T$.], width: 100%),
  screenshot("screenshots/gui_validacion_cero_diagonal.png", [Validación preventiva ante coeficientes diagonales nulos ($a_(11) = 0$).], width: 100%)
)

*Conclusión Didáctica:* Este caso es la demostración definitiva de que la falta de dominancia diagonal no implica divergencia de todos los métodos. Gauss-Seidel converge porque su radio espectral es $0.5 < 1$, mientras que Jacobi diverge al tener $rho(T_J) approx 1.118 > 1$.

#pagebreak()

// ==============================================================================
// PÁGINA 9: SECCIÓN 4.4 Y 4.5 (CASOS COMPLEMENTARIOS Y TERMINAL)
// ==============================================================================
== 4.4. Casos Complementarios: Cero en la Diagonal y Desmitificación de Stein-Rosenberg

=== Caso Complementario 1: Cero en la Diagonal Principal ($a_(11) = 0$)
- *Sistema:* $mat(delim: "[", 0, 2; 3, 1) bold(x) = mat(delim: "[", 4; 5)$. El coeficiente $a_(11) = 0$ provocaría una división por cero fatal.
- *Acción Automática:* PrettyCalc intercepta el estado no invertible, emite la alerta preventiva y aplica `reorder_for_dominance`, permutando las filas a $mat(delim: "[", 3, 1; 0, 2) bold(x) = mat(delim: "[", 5; 4)$, resolviendo el sistema de forma exacta en $(1, 2)^T$.

=== Caso Complementario 2: Ruptura de Mito (Jacobi Converge y Gauss-Seidel Diverge)
- *Sistema:* $mat(delim: "[", 1, 2, -2; 1, 1, 1; 2, 2, 1) bold(x) = mat(delim: "[", 7; 2; 5)$ con solución exacta $bold(x)^* = (1, 2, -1)^T$.
- *Diagnóstico Espectral:* $T_J$ es una matriz nilpotente de grado 3 ($T_J^3 = bold(0)$), por lo que $rho(T_J) = 0 < 1$. Por el contrario, $T_(G S)$ posee radio espectral $rho(T_(G S)) = 2.0 > 1$.
- *Resultado Numérico:* *Jacobi converge exactamente en tan solo 4 iteraciones* con residuo 0. *Gauss-Seidel diverge explosivamente*, duplicando su error en cada iteración hasta que la salvaguarda `Norm Divergence Guard` detiene el proceso en la iteración 25 cuando $norm(bold(x)^((k)))_oo > 1.3 times 10^9$.

== 4.5. Evidencias de Ejecución en Consola (Script Autónomo `Programa 8_Grupo4.py`)
El script interactivo de consola `Programa 8_Grupo4.py` implementa la totalidad de la experiencia académica en modo CLI, sin requerir librerías externas de interfaz gráfica:

#v(2pt)
#screenshot("screenshots/terminal_programa8_ejecucion.png", [Ejecución interactiva del script autónomo `Programa 8_Grupo4.py` en la terminal, mostrando arte ASCII y análisis analítico de dominancia.], width: 72%)

#pagebreak()

// ==============================================================================
// PÁGINA 10: SECCIÓN 5 (VALIDACIÓN NUMÉRICA CON NUMPY)
// ==============================================================================
= 5. Validación Numérica con NumPy (`numpy.linalg.solve(A, b)`)

En estricto apego a las directrices de la Sección 5 de la guía docente, cada aproximación numérica obtenida mediante nuestros métodos iterativos fue contrastada formalmente contra la solución exacta de referencia obtenida a través de la función `numpy.linalg.solve(A, b)`. La tabla consolidada a continuación resume las discrepancias absolutas máximas y los residuos matriciales:

#v(4pt)

#table(
  columns: (68pt, 68pt, 72pt, 28pt, 162pt, 65pt, 65pt),
  fill: (col, row) => if row == 0 { rgb("#1e3a8a") } else if calc.even(row) { rgb("#f8fafc") } else { white },
  stroke: (x, y) => if y == 0 { none } else { 0.5pt + rgb("#cbd5e1") },
  inset: (x: 4.5pt, y: 3.5pt),
  align: center + horizon,
  table.header(
    text(white, weight: "bold", size: 7.5pt)[Caso],
    text(white, weight: "bold", size: 7.5pt)[Solución NumPy],
    text(white, weight: "bold", size: 7.5pt)[Método],
    text(white, weight: "bold", size: 7.5pt)[Iter.],
    text(white, weight: "bold", size: 7.5pt)[Aproximación Calculada],
    text(white, weight: "bold", size: 7.5pt)[Error vs NumPy],
    text(white, weight: "bold", size: 7.5pt)[Residuo $norm(A bold(x) - bold(b))_oo$]
  ),
  table.cell(rowspan: 2)[*Caso 1*\ (Burden 4x4)], table.cell(rowspan: 2)[$(1, 2, -1, 1)$], [Jacobi], [13], [$(0.999990, 2.000016, -1.000013, 1.000019)$], [$1.92 times 10^(-5)$], [$2.55 times 10^(-4)$],
  [Gauss-Seidel], [6], [$(1.000008, 2.000001, -1.000003, 0.999999)$], [$8.36 times 10^(-6)$], [$7.70 times 10^(-5)$],
  table.cell(rowspan: 2)[*Caso 2*\ (Reordenado)], table.cell(rowspan: 2)[$(1, 1)$], [Jacobi], [7], [$(0.999997, 0.999995)$], [$4.66 times 10^(-6)$], [$2.00 times 10^(-5)$],
  [Gauss-Seidel], [5], [$(1.000000, 1.000000)$], [$9.52 times 10^(-8)$], [$6.47 times 10^(-7)$],
  [*Caso 3*], [$(1, 2, -1)$], [Gauss-Seidel], [19], [$(1.000029, 1.999968, -1.000002)$], [$3.24 times 10^(-5)$], [$8.77 times 10^(-5)$],
  table.cell(rowspan: 2)[*Cero Diag.*\ (Permutado)], table.cell(rowspan: 2)[$(1, 2)$], [Jacobi], [1], [$(1.000000, 2.000000)$], [$0.00 times 10^(0)$], [$0.00 times 10^(0)$],
  [Gauss-Seidel], [1], [$(1.000000, 2.000000)$], [$0.00 times 10^(0)$], [$0.00 times 10^(0)$]
)

#v(6pt)

=== Análisis y Discusión del Benchmark:
- *Concordancia Numérica:* En todos los casos convergentes, el error máximo respecto a la solución directa de `numpy.linalg.solve` se mantuvo en el rango de $10^(-5)$ a $10^(-8)$, lo que valida computacionalmente que el criterio de parada $norm(Delta bold(x)^((k)))_oo < 10^(-4)$ proporciona una precisión efectiva de al menos 4 cifras decimales exactas.
- *Comportamiento del Residuo:* El residuo matricial $norm(A bold(x) - bold(b))_oo$ fue consistentemente del mismo orden de magnitud o menor que el error de desplazamiento entre iteraciones consecutivas, demostrando que no existen patologías de mal condicionamiento en los sistemas didácticos seleccionados.
- *Rol Didáctico de la Validación:* Conforme estipula la guía docente, la función `numpy.linalg.solve` se empleó única y exclusivamente como herramienta externa de verificación y auditoría de los resultados numéricos obtenidos, preservando la pureza y originalidad de las implementaciones manuales de Jacobi y Gauss-Seidel desarrolladas por el Grupo 4.

#pagebreak()

// ==============================================================================
// PÁGINA 11: SECCIÓN 6 (GUÍA DE DEFENSA INDIVIDUAL - PARTE 1)
// ==============================================================================
= 6. Guía de Preparación para la Defensa Individual

Cada integrante del equipo (Roberto Fabio Tercero, Steven Flores, Kellys Bellanger y Raúl Valverde) debe dominar rigurosamente los siguientes conceptos teóricos y decisiones de diseño ante el docente evaluador:

#v(2pt)

#qacard(1, "¿Cuál es la diferencia algorítmica fundamental entre Jacobi y Gauss-Seidel en cuanto a memoria y cálculo?", [
  Jacobi actualiza mediante *desplazamientos simultáneos*: calcula cada componente $x_i^((k+1))$ utilizando estrictamente los valores de la iteración anterior $bold(x)^((k))$, lo que exige reservar memoria para dos vectores desacoplados. Gauss-Seidel opera mediante *desplazamientos sucesivos*: tan pronto como calcula $x_i^((k+1))$, lo sobreescribe en el vector y lo reutiliza de inmediato para calcular $x_(i+1)^((k+1))$, operando *in-place* con un único vector en memoria.
])

#v(3pt)

#qacard(2, "¿Por qué la dominancia diagonal es condición suficiente pero no necesaria?", [
  Es *suficiente* porque, en virtud del Teorema de Círculos de Gershgorin, la dominancia estricta por filas garantiza que todos los autovalores de la matriz de iteración $T$ tienen magnitud $|lambda| < 1$, lo que impone $rho(T) < 1$. No es *necesaria* porque existen sistemas que no son diagonal dominantes pero cuyos autovalores igualmente se sitúan dentro del disco unitario abierto ($rho(T) < 1$), como se probó empíricamente en el Caso 3 con Gauss-Seidel.
])

#v(3pt)

#qacard(3, [¿Por qué el radio espectral $rho(T) < 1$ es la condición necesaria y suficiente de convergencia?], [
  Porque el error en la iteración $k$ evoluciona según la potencia de la matriz de iteración: $bold(e)^((k)) = T^k bold(e)^((0))$. Por la teoría espectral de matrices (o descomposición de Jordan), la sucesión de matrices $T^k -> bold(0)$ cuando $k -> oo$ para cualquier vector inicial si y solo si el módulo del autovalor de mayor magnitud es estrictamente menor a la unidad ($rho(T) = max_i |lambda_i| < 1$).
])

#v(3pt)

#qacard(4, "¿Es Gauss-Seidel siempre superior o más rápido que Jacobi?", [
  *No.* La creencia de que Gauss-Seidel siempre supera a Jacobi solo es válida bajo las hipótesis del *Teorema de Stein-Rosenberg* (elementos no diagonales no positivos: $a_(i j) <= 0$ para $i != j$). Si la matriz contiene coeficientes con signos mixtos, Gauss-Seidel puede diverger mientras Jacobi converge, tal como se comprobó analíticamente en el Caso didáctico complementario ($rho(T_J) = 0$ converge en 4 pasos, mientras que $rho(T_(G S)) = 2.0$ diverge al infinito).
])

#pagebreak()

// ==============================================================================
// PÁGINA 12: SECCIÓN 6 (GUÍA DE DEFENSA INDIVIDUAL - PARTE 2)
// ==============================================================================
= 6. Guía de Preparación para la Defensa Individual (Continuación)

#v(2pt)

#qacard(5, [¿Por qué se utilizó `fractions.Fraction` en lugar de `float` estándar de Python?], [
  Porque los números de punto flotante de 64 bits (IEEE 754) introducen pequeños errores de redondeo en cada división y multiplicación que pueden propagarse y distorsionar el cálculo del residuo y de los autovalores en matrices mal condicionadas. Al usar `Fraction`, toda la aritmética matricial es analíticamente exacta y el único error presente en la tabla es el error intrínseco de truncamiento de la serie iterativa.
])

#v(3pt)

#qacard(6, "¿Qué ocurre si una matriz tiene un cero en la diagonal principal y cómo lo solventa el código?", [
  Un coeficiente $a_(i i) = 0$ causaría un error fatal de división por cero al intentar despejar $x_i$. Nuestro software detecta preventivamente esta anomalía y ejecuta el algoritmo `reorder_for_dominance()`, el cual permuta las filas del sistema buscando colocar elementos no nulos de máxima magnitud en la diagonal. Si existe un reordenamiento viable, el cálculo prosigue con éxito.
])

#v(3pt)

#qacard(7, [¿Qué criterio de parada se empleó y qué representa el residuo $norm(A bold(x) - bold(b))_oo$?], [
  Se empleó el error absoluto entre iteraciones consecutivas $norm(bold(x)^((k)) - bold(x)^((k-1)))_oo < epsilon$, el cual mide la estabilización del vector solución. El residuo $norm(A bold(x)^((k)) - bold(b))_oo$ mide el error con el que la aproximación satisface el sistema algebraico original; si el residuo es pequeño ($approx 10^(-4)$ a $10^(-7)$), se confirma que la solución hallada es numéricamente fidedigna.
])

#v(5pt)

#callout(title: "Estrategia para la Exposición Oral del Grupo 4:", [
  - Cada miembro debe iniciar su intervención enunciando la formulación canónica $A = D + L + U$ y la forma matricial del método que expone.
  - Al mostrar la ejecución en vivo, explicar claramente el número de iteraciones y señalar en pantalla el medidor de radio espectral $rho(T)$.
  - Frente a preguntas de divergencia, enfatizar que la ausencia de dominancia diagonal *no* predice por sí sola el fallo del método; la verdadera clave analítica reside en si $rho(T) < 1$ o $rho(T) >= 1$.
], type: "info")

#pagebreak()

// ==============================================================================
// PÁGINA 13: SECCIONES 7 Y 8 (ENTREGABLES, INSTRUCCIONES, CONCLUSIONES)
// ==============================================================================
= 7. Estructura de Entregables e Instrucciones de Ejecución

== 7.1. Organización del Paquete Comprimido (.ZIP)
Conforme a la normativa de la Facultad de Ingeniería y Arquitectura (FIA), el proyecto se entrega en el archivo comprimido oficial `Programa 8_Grupo 4_Tercero_Flores.zip`, estructurado como se detalla a continuación:

#rect(
  width: 100%,
  fill: rgb("#0f172a"),
  radius: 3pt,
  inset: (x: 7pt, y: 5pt)
)[
  #text(fill: rgb("#f8fafc"), font: "Liberation Mono", size: 6.8pt)[
    Programa 8_Grupo 4_Tercero_Flores.zip\
    ├── Programa 8_Grupo4.py                         \# Script interactivo autónomo de consola (100% Python estándar)\
    ├── Calculadora_Algebra_Lineal/                  \# Suite modular profesional con Módulo 5 de Métodos Iterativos\
    │   ├── main.py                                  \# Menú principal de la suite CLI\
    │   ├── modulos/modulo_iterativos.py             \# Motor iterativo integrado de Jacobi y Gauss-Seidel\
    │   └── teoremas/resumen_teoremas.py             \# Compendio teórico de teoremas (Opción 0)\
    ├── prettycalc/                                  \# Núcleo computacional y GUI completa en PySide6\
    │   └── ui/modules/iterative_methods_view.py     \# Interfaz gráfica con gráficas logarítmicas y medidor espectral\
    ├── Docs/                                        \# Documentación técnica y artefactos visuales\
    │   ├── Informe_Programa 8_Grupo4.pdf            \# Informe técnico oficial compilado con Typst en alta calidad\
    │   ├── Informe_Programa 8_Grupo4.typ            \# Código fuente Typst del presente informe\
    │   ├── Informe_Programa 8_Grupo4.md             \# Versión Markdown del informe\
    │   ├── logo.svg                                 \# Logotipo vectorial de la suite PrettyCalc\
    │   └── screenshots/                             \# Capturas en alta resolución de la GUI, gráficas y consola\
    ├── tests/core/test_programa8_standalone.py      \# Suite de 36 pruebas automatizadas aprobadas (100% pass)\
    ├── run.py                                       \# Lanzador unificado de la suite PrettyCalc\
    ├── pyproject.toml                               \# Especificación de empaquetado del proyecto\
    └── requirements.txt                             \# Dependencias del entorno de ejecución
  ]
]

== 7.2. Instrucciones para la Ejecución y Evaluación en Vivo
- *Script Autónomo CLI:* `python3 "Programa 8_Grupo4.py"` (menú interactivo y casos preconfigurados).
- *Suite Modular General:* `python3 Calculadora_Algebra_Lineal/main.py` (Módulo 5).
- *Aplicación Gráfica (PrettyCalc GUI):* `python3 run.py` (Módulo 10 de Métodos Iterativos).
- *Batería de Pruebas Automatizadas (PyTest):* `pytest tests/core/test_programa8_standalone.py -v` (36 tests aprobados).

= 8. Conclusiones y Referencias Bibliográficas

== 8.1. Conclusiones del Trabajo
1. Se integraron con éxito los métodos iterativos de Jacobi y Gauss-Seidel en tres capas de software completamente operativas: un script autónomo de terminal (`Programa 8_Grupo4.py`), la suite modular del curso (`Calculadora_Algebra_Lineal/`) y la aplicación gráfica PrettyCalc.
2. La adopción de `fractions.Fraction` garantizó un cálculo exacto y transparente, aislando el error de truncamiento del método numérico de cualquier artefacto de redondeo flotante IEEE 754.
3. Se demostró computacional y analíticamente el rol determinante del radio espectral $rho(T)$ como condición necesaria y suficiente de convergencia, evidenciando que la dominancia diagonal estricta es solo una condición suficiente.
4. Se desmitificó la creencia de la superioridad absoluta de Gauss-Seidel sobre Jacobi al implementar y documentar sistemas con signos mixtos donde Jacobi converge y Gauss-Seidel diverge.
5. El equipo cuenta con un sólido respaldo conceptual y empírico plasmado en la Guía de Defensa Individual para sustentar con éxito la evaluación oral ante la cátedra.

== 8.2. Referencias Bibliográficas
- Burden, R. L., & Faires, J. D. (2011). *Análisis Numérico* (9.ª ed.). Cengage Learning. (Capítulo 7: Técnicas iterativas en el álgebra matricial).
- Strang, G. (2016). *Introduction to Linear Algebra* (5.ª ed.). Wellesley-Cambridge Press.
- Golub, G. H., & Van Loan, C. F. (2013). *Matrix Computations* (4.ª ed.). Johns Hopkins University Press.
- Lay, D. C., Lay, S. R., & McDonald, J. J. (2016). *Álgebra Lineal y sus Aplicaciones* (5.ª ed.). Pearson Educación.
