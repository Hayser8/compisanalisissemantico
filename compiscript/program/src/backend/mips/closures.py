# src/backend/mips/closures.py
from __future__ import annotations


def emit_runtime_closures() -> str:
    """
    Runtime de closures (MIPS32 / MARS / SPIM):

      __make_closure(a0 = codeptr, a1 = envptr) -> v0 = closure_ptr
      __closure_apply(a0 = closure_ptr, a1..a3 = args) -> v0 = ret

    Layout en memoria del closure (8 bytes):
      [0] codeptr
      [4] envptr

    Notas:
      - Aquí SOLO definimos el runtime de closures y __cps_halt.
      - __new_array y los __mcall__* se definen en el emitter principal.
      - Se asume que el entorno (envptr) fue alocado en heap (sbrk) por MakeClosure,
        no en el stack de algún frame que pueda destruirse.
    """
    lines = [
        "",
        # Marcar símbolos globales del runtime de closures
        ".globl __make_closure",
        ".globl __closure_apply",
        ".globl __cps_halt",
        "",
        # -------------------------------------------------
        # __make_closure
        #   a0 = puntero a código
        #   a1 = puntero a entorno (o $zero si no hay)
        #   v0 = puntero a struct { codeptr, envptr }
        #
        #   struct Closure {
        #     void (*code)(Env*, ...);
        #     Env* env;
        #   };
        #
        #   Se aloca en heap usando syscall 9 (sbrk).
        # -------------------------------------------------
        "__make_closure:",
        "  move $t0, $a0          # t0 = codeptr",
        "  move $t1, $a1          # t1 = envptr",
        "",
        "  li   $v0, 9            # syscall sbrk",
        "  li   $a0, 8            # 2 words: code + env",
        "  syscall",
        "",
        "  move $t2, $v0          # t2 = closure ptr",
        "  sw   $t0, 0($t2)       # closure->code = codeptr",
        "  sw   $t1, 4($t2)       # closure->env  = envptr",
        "  move $v0, $t2          # devolver closure en $v0",
        "  jr   $ra",
        "  nop",
        "",
        # -------------------------------------------------
        # __closure_apply
        #   a0 = closure*
        #   a1..a3 = argumentos lógicos del usuario
        #
        #   Hace:
        #     codeptr = closure->code
        #     envptr  = closure->env
        #     a0 = envptr
        #     jr codeptr   (trampolín; el $ra del caller se preserva)
        #
        #   Protección:
        #     - si closure == NULL -> retorna 0
        #     - si codeptr == NULL -> retorna 0
        #
        #   Importante:
        #     - No toca $ra, así que la función del closure hará jr $ra y
        #       regresará directamente al caller original de __closure_apply.
        # -------------------------------------------------
        "__closure_apply:",
        "  # Si closure es NULL, retorna 0",
        "  beq  $a0, $zero, __closure_apply_null",
        "  nop",
        "",
        "  # Cargar codeptr y envptr desde el closure",
        "  lw   $t9, 0($a0)       # t9 = closure->code",
        "  beq  $t9, $zero, __closure_apply_null",
        "  nop",
        "  lw   $t0, 4($a0)       # t0 = closure->env",
        "  move $a0, $t0          # a0 = env (a1..a3 quedan igual)",
        "",
        "  # Trampolín / tail-call: saltar directamente al código del closure",
        "  jr   $t9",
        "  nop",
        "",
        "__closure_apply_null:",
        "  # Closure roto o codeptr nulo -> devolver 0",
        "  move $v0, $zero",
        "  jr   $ra",
        "  nop",
        "",
        # -------------------------------------------------
        # __cps_halt:
        #   Punto de “no retorno” genérico para el compilador.
        #   Termina el programa con syscall 10.
        #
        #   El epílogo usa:
        #     beq $ra, $zero, __cps_halt
        #     jr  $ra
        # -------------------------------------------------
        "__cps_halt:",
        "  li   $v0, 10    # exit",
        "  syscall",
        ""
    ]
    return "\n".join(lines)
