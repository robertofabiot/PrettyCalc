# Fuentes empaquetadas

PrettyCalc trae sus propias fuentes para verse igual en Windows, Linux y macOS
(ver `prettycalc/ui/platform_setup.py`). Ninguna depende de lo que tenga
instalado el sistema.

| Archivo | Uso | Origen | Licencia |
|---|---|---|---|
| `Inter-*.ttf` | Texto de la interfaz | [rsms/inter](https://github.com/rsms/inter) v4.1 | SIL OFL 1.1 (`LICENSE-Inter.txt`) |
| `FiraCode-*.ttf` | Números, celdas y matrices | [tonsky/FiraCode](https://github.com/tonsky/FiraCode) 6.2 | SIL OFL 1.1 (`LICENSE-FiraCode.txt`) |
| `DejaVuSans*.ttf` | Símbolos que las anteriores no traen (ℝ, ᵀ, ∘, ≟, ✓, ✕) | [DejaVu Fonts](https://dejavu-fonts.github.io) 2.37 | Bitstream Vera + dominio público (`LICENSE-DejaVu.txt`) |

## Modificación

En `Inter-Medium.ttf`, `Inter-SemiBold.ttf` y `FiraCode-SemiBold.ttf` se
cambiaron solo los registros 1 y 2 de la tabla `name` (familia «Inter» o «Fira
Code» y estilo «Medium» o «SemiBold»). Los archivos originales los declaran
como familias aparte («Inter SemiBold»), y Windows y Linux agrupan esas
familias de forma distinta: un `font-weight: 600` podía salir en SemiBold en
un sistema y en negrita sintética en el otro. Ninguna de estas fuentes declara
un nombre reservado, y los archivos modificados siguen bajo la SIL OFL 1.1.
