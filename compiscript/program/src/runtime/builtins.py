# program/src/runtime/builtins.py

def __array__(*xs):
    # El lower ya llama ('call','__array__', [...]) para literales de arreglo
    return list(xs)

def __len__(arr):
    # Usado por el desazucarado de foreach
    return len(arr)
