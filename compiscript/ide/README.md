# Compiscript Desktop IDE – MVP (Zero‑Config)

## 1) Install
```
cd ide-desktop
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

## 2) Run
```
python main.py
```
No hay Settings: la app **autodetecta** `cli.py` y la carpeta de trabajo:
- busca `cli.py` en el **root del repo** o en `compiscript/program/cli.py`.
- si `cli.py` está en `program/`, toma esa carpeta como workspace; si no, usa un `program/` vecino si existe.

## 3) Uso
- **Open Folder** (opcional): cambia el workspace si quieres otra carpeta.
- **New / Save / Save As** desde la barra.
- **▶ Run** ejecuta `cli.py --json --symbols <archivo>` y muestra:
  - **Problems**: errores (click salta a la línea)
  - **Output**: salida cruda del CLI
  - **Outline**: globals/clases/funciones del JSON
- **🌓 Theme** alterna claro/oscuro (sin persistencia).

---
