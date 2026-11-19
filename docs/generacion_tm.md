# Generación de código TM — reales, cadenas y alcance

Pipeline: `lexer → parser → semantic_analyzer → intermediate.py (.ci)` y, en paralelo
desde el **mismo árbol anotado**, `codegen.py (.tm) → tm_simulator.py`.
El simulador sólo recibe el texto `.tm` (nunca el fuente ni el `.ci`).

## Modo TM estándar y modo extendido

`CodeGenerator(symbol_table, standard=None)` elige el modo solo:

| | **Estándar** (por defecto) | **Extendido** |
|---|---|---|
| Cuándo | el programa NO usa reales ni cadenas | usa `float`/`real` o `cout "texto"` (o `standard=False`) |
| Instrucciones | solo las del `tm.c` de Louden: `HALT IN OUT ADD SUB MUL DIV LD ST LDA LDC JLT JLE JGT JGE JEQ JNE` | las anteriores + `INF OUTF OUTC OUTNL MOD` |
| `a % b` | `a - (a/b)*b` con `DIV`/`MUL`/`SUB` (usa `r2`) | `MOD` |
| Fin de `cout` | nada: cada `OUT` es su renglón (como Louden) | `OUTNL` |
| Dónde corre | simulador del IDE **y** `tm.c` de Louden | solo el simulador del IDE |

Ambos modos empiezan con el prólogo de Louden `LD 6,0(0)` / `ST 0,0(0)` (el simulador del IDE
arranca igual que `tm.c`: registros en 0 y `dMem[0] = 1023`). El simulador del IDE ejecuta los dos
modos con los mismos resultados (`run_ejercicios.py` lo comprueba). `CodeGenerator.extensions_used`
lista las instrucciones no estándar del `.tm`; la UI las usa para avisar en consola y con un
banner en las pestañas Cód. TM y Ejecución TM: *"Este programa usa extensiones (…): solo corre en el
simulador del IDE, no en el tm.c de Louden."* Con `tm.c`, el límite es de 1024 instrucciones.

## Reales (`float` / `real`): punto fijo con factor 10 000

La TM sólo opera con enteros, así que un real se guarda como `valor × 10000`
(`1.5 → 15000`, `3.1416 → 31416`). Módulo único: `compiler/fixed_point.py`.

| Operación | Código TM |
|---|---|
| constante real `3.1416` | `LDC 0,31416(0)` (se redondea al 4.º decimal) |
| `int → float` (anotado por el semántico: `conversion = int_to_float`) | `n * 10000` (`LDC` directo en literales, `MUL` en el resto) |
| `a + b`, `a - b`, comparaciones | directo (ambos operandos ya escalados) |
| `a * b` | `MUL` y luego `DIV` entre 10000 |
| `a / b` | `a * 10000` y luego `DIV` entre `b` |
| `a ^ n` | multiplicaciones sucesivas con reescalado; el exponente real se trunca a entero |
| `cin x` (x real) | `INF` (lee decimales: `1.5`) |
| `cout x` (x real) | `OUTF` |

Formato de salida de un real: hasta **4 decimales**, sin ceros finales y con al menos un
decimal: `100.0`, `3.048`, `45.4545`, `-0.5`. `*` y `/` truncan hacia cero (precisión 1e-4).
Las entradas con más de 4 decimales se redondean al 4.º.

`int / int` sigue siendo división **entera** (trunca hacia cero, igual que el plegado de
constantes del semántico); `%` también usa el signo del dividendo. `x / 0` y `x % 0`
detienen la ejecución con el error `División por cero …`.

## Texto en `cout`

`cout "aprobado=1";` genera `LDC 0,<código>` + `OUTC` por cada carácter (el `.tm` es
autocontenido: el texto va dentro de las instrucciones, no en una tabla aparte).
`\n` dentro de la cadena genera `OUTNL`.

Cada sentencia `cout` termina con `OUTNL` (una línea por `cout`). Dentro de un mismo
`cout` los elementos se escriben seguidos (`cout "x=" << x;` → `x=5`); sólo entre **dos
números** consecutivos se inserta un espacio (`cout a << b;` → `1 2`).

## Extensiones del simulador (no existen en la TM original)

Documentadas en el encabezado de `compiler/tm_simulator.py`; sólo estas cuatro (más `MOD` en modo extendido):

| Instrucción | Efecto |
|---|---|
| `INF r,0,0` | lee la siguiente entrada como real y la guarda en punto fijo |
| `OUTF r,0,0` | imprime `reg[r]` como real |
| `OUTC r,0,0` | imprime el carácter de código `reg[r]` |
| `OUTNL 0,0,0` | cierra el renglón de salida en curso |

El resto (`IN, OUT, ADD…, LD, ST, LDA, LDC, J**`, `HALT`) es la TM estándar. Los enteros del
simulador no desbordan (Python); una TM real usaría 32 bits. Límite de seguridad: 5 000 000
pasos.

## Estructuras soportadas

`main{}`, `int/float(real)/bool`, `cin`/`cout` (con `>>` y `<<` opcionales), asignación,
`++`/`--` como sentencia, `+ - * / % ^`, menos unario, `< <= > >= == !=`, `&& || !`,
`if … then … else … end`, `while(c){…}` / `while c … end`, `do{…}while(c)`,
`do{…}until(c)` (repite mientras `c` sea falsa), bloques con ámbito propio
(una variable interna puede ocultar a una externa, incluso con otro tipo).

## No soportado (no se presenta como implementado)

* **Arreglos y `for`**: el lenguaje no los tiene. Implementarlos exige tocar lexer, parser,
  semántico, tabla de símbolos, vistas del árbol y codegen; los ejercicios de vinos, lluvias,
  fábricas y estadio se resuelven con variables escalares + `while` (ver `tests/ejercicios_pdf/`).
* **Funciones**, `<<`/`>>` como operadores de bits, cast explícito `float → int`.
* `^` con exponente negativo: da 1 (el semántico sólo pliega constantes con exponente ≥ 0).
* `a - -b` / `a + +b` escritos con espacio: el lexer los une como `--` / `++`
  (comportamiento previo del lexer; usar paréntesis: `a - (-b)`).
* Programas con reales o cadenas no corren en el `tm.c` de Louden (modo extendido).

## Pruebas

```
python tests/run_ejercicios.py        # compila + ejecuta en TM + compara contra la salida esperada
                                      # + 2.ª pasada en tm.c de Louden (si hay gcc y tm.c)
python tests/run_ejercicios.py -v g04 # filtra por nombre; -v muestra el .tm de los que fallan
python tests/test_semantica_extra.py  # pruebas del analizador semántico
```

`tests/ejercicios_pdf/` tiene un `.txt` por ejercicio de `EjericiosFinalesCompisII.pdf`
(los ejercicios repetidos entre grupos se prueban una sola vez; el encabezado de cada archivo
indica a qué grupos corresponde). Donde el PDF no fija el formato de entrada o un caso
límite, el encabezado lo declara como `ENTRADA`/`SUPUESTO`. `tests/codegen_extra/` cubre
operadores y casos límite del generador.

### Segunda pasada con el `tm.c` de Louden

Los programas en modo estándar se ejecutan también en el `tm.c` real (`gcc -std=c11 tm.c -o tm`;
stdin: `g`, las entradas, `q`; se lee `Resultado del programa (OUT): N`). `tm.c` se busca en la
variable de entorno `TM_C`, en `tests/tm_ref/tm.c` y en la carpeta del curso; si falta `gcc` o
`tm.c`, la pasada se omite con un aviso (no cuenta como fallo). Además, sin necesidad de `gcc`,
se exige que un programa estándar no contenga ningún opcode fuera del conjunto de Louden.
