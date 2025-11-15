from __future__ import annotations

class GlobalsTable:
    """
    Tabla mínima de globales. emit_full_program inspecciona dicts en vars(self)
    buscando {str:int} para emitir '.word'.
    """
    def __init__(self) -> None:
        # Puedes usar 'words' para enteros globales si lo necesitas:
        #   gtab.words['X'] = 123
        self.words: dict[str, int] = {}

    def define(self, name: str, value: int) -> None:
        self.words[name] = int(value)
