# Plantilla de Pull Request

Copia este texto en la descripción del pull request. El título va en la primera línea, fuera del cuerpo, con el formato `feat(sprint-N): [Entregable en una frase]`.

Sustituye cada campo entre corchetes. Borra las secciones que no apliquen al sprint y conserva los encabezados de las que sí.

---

feat(sprint-[N]): [Entregable en una frase]

## Resumen de Cambios

Este PR introduce la implementación completa del Sprint [N], correspondiente a [qué problema académico o de producto cierra], tanto en el motor (`prettycalc.core`) como en la interfaz de escritorio (`prettycalc.ui`).

## Objetivos Cumplidos

- **[Objetivo 1]:** [Qué queda calculable o visible, y con qué garantía: aritmética exacta, trazado, manejo de error].
- **[Objetivo 2]:** [Segunda capacidad, nombrando la función, la vista o el teorema que cubre].
- **[Objetivo 3]:** [Tercera capacidad].
- **Suite de Pruebas Automatizadas:** [Qué casos de clase cubren los tests nuevos y que la suite previa sigue pasando].

## Detalles de Implementación por Módulo

### 1. Motor Matemático (`prettycalc/core/`)

- **[Módulo nuevo o archivo] (`archivo.py`):** [Responsabilidad, entradas, salidas y excepciones de dominio].
- **[Módulo existente] (`archivo.py`):** [Qué se añadió y qué contratos previos se conservan].
- **Exposición pública (`__init__.py`):** [Símbolos que pasan a importarse desde `prettycalc.core`].

### 2. Capa de Presentación (`prettycalc/ui/`)

- **[Vista o widget] (`archivo.py`):** [Cómo lo usa el estudiante: botón, badge, carrusel, panel].
- **[Segundo cambio de interfaz]:** [Estados de error, casos vacíos y desplazamiento si el panel crece].

### 3. Pruebas Automatizadas (`tests/`)

- **[tests/core/test_....py]:** [Casos numéricos exactos y errores de dominio].
- **[tests/ui/test_....py]:** [Flujos de pytest-qt: cálculo correcto, entrada inválida y ausencia de regresión visual].

### 4. Documentación

- **[README.md / Docs/...]:** [Qué guía quedó actualizada].

## Casos de Prueba Verificados

| Caso | Tema | Comportamiento esperado | Estado |
| :--- | :--- | :--- | :--- |
| [Sesión X, diapositiva Y] | [Operación] | [Resultado exacto o excepción] | Aprobado |
| [Caso límite] | [Dimensión, singularidad u otro borde] | [Qué ve el usuario o qué lanza el motor] | Aprobado |

## Instrucciones de Ejecución

### Ejecutar la aplicación gráfica

```bash
pip install -r requirements.txt
python run.py
```

[Dónde está la función nueva en la ventana: módulo, botón y ejemplo de carga].

### Ejecutar la suite de pruebas

```bash
pytest
```

En un entorno sin pantalla:

```bash
QT_QPA_PLATFORM=offscreen pytest
```

## Checklist de Revisión

- [ ] El motor nuevo usa solo Python estándar y `fractions.Fraction`.
- [ ] Cada algoritmo pedagógico deja pasos en `StepTracer` cuando el sprint lo exige.
- [ ] La interfaz cubre el caso correcto y los errores de dominio sin cerrar la aplicación.
- [ ] Los casos numéricos de clase coinciden componente a componente.
- [ ] `pytest` pasa, incluida la suite que ya existía antes del sprint.
