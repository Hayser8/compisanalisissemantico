from src.runtime.frame import FrameLayout, WORD


def test_frame_offsets_basic():
    fr = FrameLayout("f")
    fr.add_param("a")
    fr.add_param("b")
    fr.add_local("x")
    fr.add_local("y")
    fr.add_local("z")
    fr.seal()

    # Params positivos: +8, +16
    assert fr.offset_of("a") == WORD
    assert fr.offset_of("b") == 2 * WORD

    # Locals negativos: -8, -16, -24 (en orden de declaración)
    assert fr.offset_of("x") == -WORD
    assert fr.offset_of("y") == -2 * WORD
    assert fr.offset_of("z") == -3 * WORD

    # Tamaño de frame para locals
    assert fr.frame_size_bytes() == 3 * WORD


def test_frame_no_redeclare_and_seal():
    fr = FrameLayout("g")
    fr.add_param("p")
    fr.add_local("v")
    try:
        fr.add_param("p")
        assert False, "debió fallar parámetro duplicado"
    except ValueError:
        pass
    try:
        fr.add_local("p")
        assert False, "debió fallar nombre ya usado como parámetro"
    except ValueError:
        pass

    fr.seal()
    assert fr.offset_of("p") == WORD
    assert fr.offset_of("v") == -WORD

    # Tras sellar, no permite cambios
    try:
        fr.add_local("otro")
        assert False, "no debió permitir modificar al estar sellado"
    except RuntimeError:
        pass
