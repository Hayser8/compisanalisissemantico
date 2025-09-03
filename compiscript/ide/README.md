# Compiscript IDE (Desktop · PySide6)

IDE minimalista para trabajar con **Compiscript** sobre el *checker/CLI* del repositorio.  
Permite **abrir/probar** archivos `.cps`, ver **errores** y **símbolos** del análisis, con **tema claro/oscuro**, pestañas con cierre, y panel de resultados.

---

## Características

- **Explorador de archivos**: abre carpetas y navega `.cps`.
- **Editor** con resaltado (syntax highlighting).
- **Pestañas** con “X” y **autoguardado** al cerrar.
- **Botón ▶ Run**: ejecuta el **CLI** y muestra resultados.
- Panel inferior con:
  - **Problems**: errores con salto a línea/columna (doble-click).
  - **Output**: logs + **JSON** crudo del CLI.
  - **Reporte**: resumen **legible** (OK/errores y símbolos).
- **Outline**: variables, funciones y clases detectadas.
- **Theme**: claro (blanco/negro) y oscuro.

> El IDE actual por la fase **no ejecuta programas**; invoca el **análisis** del proyecto vía `cli.py --json --symbols`.


## Requisitos

- **Python 3.10+** (recomendado 3.10 o 3.11)
- **pip** actualizado
- **Windows / macOS / Linux**
- **(Opcional)** Docker, porque lo tenemos de backup por si falla el antlr, venv de python 

**Dependencias clave**

- `PySide6==6.7.x`
- `antlr4-python3-runtime==4.13.1` 

---

## Instalación

### Opción A — venv del IDE (rápida)

**Windows (PowerShell)**

```powershell
cd compiscript\ide
py -3.10 -m venv .venv
.\.venv\Scripts\activate
pip install --upgrade pip
pip install PySide6==6.7.2 antlr4-python3-runtime==4.13.1
```

**macOS / Linux**

```bash
cd compiscript/ide
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install "PySide6==6.7.2" "antlr4-python3-runtime==4.13.1"
```

### Opción B — venv del compilador en `program/` (recomendada para equipos)

```bash
cd compiscript/program
python3 -m venv .venv 
pip install --upgrade pip
pip install "antlr4-python3-runtime==4.13.1"
```

> El `runner.py` **prefiere automáticamente** `program/.venv` si existe.  
> Si no, usará el venv del IDE (`ide/.venv`); como última opción, el Python del sistema.

---

## Ejecutar el IDE

Con el venv activado:

```bash
cd compiscript/ide
.\.venv\Scripts\activate
python main.py
```

### Primeros pasos

1. **Open Folder** → selecciona `compiscript/program`.
2. Abre un `.cps` (ej: `samples/ok_all.cps`).
3. **Save** si editas.
4. **▶ Run** para analizar.
   - **Problems**: errores (doble-click salta a la línea).
   - **Output**: logs + JSON crudo del CLI.
   - **Reporte**: resumen legible (OK/errores y símbolos).
   - **Outline**: símbolos navegables.
5. **Theme** alterna claro/oscuro.

---

## Samples

- `program/samples/ok_all.cps` → **OK** sin errores.
- `program/samples/bad_types.cps` → errores de tipos esperados.


## Cómo decide el Python el `runner.py`

Orden de preferencia:
1. `compiscript/program/.venv` (si existe)
2. `compiscript/ide/.venv`
3. `sys.executable` (Python del sistema)

Si el análisis **no produce JSON** y parece error real (p. ej., `No module named antlr4`, `Traceback`, exit-code ≠ 0), el `runner.py` puede intentar **Docker** como respaldo (si está instalado).

> Si quieres **desactivar Docker** permanentemente, abre `runner.py` y deshabilita el fallback (por bandera o comentando el bloque correspondiente).

---

## Notas

- El IDE consume el JSON de `cli.py --json --symbols`.
- Si se cambia el formato del CLI, ajusta `on_run_finished()` y `update_pretty_report()` en `app.py`.
- El proyecto fue probado principalmente en Windows; la UI es **cross-platform**.

---