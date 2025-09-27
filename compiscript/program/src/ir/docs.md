# Compiscript IR (TAC)

Este IR es de **tres direcciones** (TAC), estructurado en **funciones** que contienen
**bloques básicos** (BasicBlocks) con una etiqueta y una lista lineal de instrucciones.

## Unidades

- **Program**: conjunto de funciones.
- **Function**: nombre, parámetros (identificadores), lista de `BasicBlock`s.
- **BasicBlock**: `Label` + lista de instrucciones.

## Operandos

- **Temp**: temporal (`t0`, `t1`, …) – producido por el generador.
- **Name**: nombre estable (variable local/global/campo) para referenciar valores existentes.
- **Const**: literal (`123`, `"hola"`, `true`, `null`).
- **Label**: destino de saltos (`L0`, `L1`, …).

> Los tipos (cuando se necesiten) se almacenan como strings (e.g., `"integer"`, `"string"`).

## Instrucciones (forma textual)

- Asignación / movimiento:
  - `x = y`
  - `x = 3`
- Unarias / Binarias:
  - `t = - a`
  - `t = ! a`
  - `t = a + b`
  - `t = a - b`
  - `t = a * b`
  - `t = a / b`
  - `t = a % b`
  - `t = a == b` `t = a != b`
  - `t = a < b`  `t = a <= b` `t = a > b` `t = a >= b`
  - `t = a && b` `t = a || b`
- Control de flujo:
  - `if t goto Lk`
  - `goto Lk`
  - `Lk:` (etiqueta)
- Llamadas y retorno:
  - `t = call f, a, b, c`
  - `return t`
  - `return` (void)
- Arreglos:
  - `t = load a[i]`
  - `store a[i], v`
- Objetos / campos:
  - `t = get obj.p`
  - `set obj.p, v`
  - `t = new Clase(a, b, c)`

## Notas de diseño

- Las comparaciones y lógicas producen un **boolean** en un `Temp`.
- `if t goto L` asume que `t` es boolean.
- `switch` (cuando se emita) se descompone en secuencia de comparaciones + saltos.
- La convención de llamada se modela en el IR con `call` + `return`. El detalle de
  activación (AR) queda para el backend.

## Ejemplo

function suma(a, b):
L0:
t0 = a + b
return t0