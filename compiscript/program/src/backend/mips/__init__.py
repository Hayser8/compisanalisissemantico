# program/src/backend/mips/__init__.py
from .frame_plan import FramePlan
from .emitter import (
    emit_program_stub,
    emit_function_skeleton,
    emit_function,
    emit_full_program,
)
from .emit_utils import emit_prologue, emit_epilogue, emit_copy_params_to_homes
from .abi import mangle_method_label

__all__ = [
    "FramePlan",
    "emit_program_stub",
    "emit_function_skeleton",
    "emit_prologue",
    "emit_epilogue",
    "emit_copy_params_to_homes",
    "mangle_method_label",
]
