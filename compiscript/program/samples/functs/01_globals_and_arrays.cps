// 01_globals_and_arrays.cps
// Prueba de globales, arrays y acceso por índice.

let a: integer = 3;
let b: float   = 1.5;
let msg: string = "hola";

let xs: integer[] = [1, 2, 3, 4];
let ys: float[]   = [1.0, 2.5, 3.5];

function sumFirstN(arr: integer[], n: integer): integer {
  let acc: integer = 0;
  let i: integer = 0;
  while (i < n) {
    acc = acc + arr[i];
    i = i + 1;
  }
  return acc;
}

function demo_globals_arrays(): integer {
  let s3: integer = sumFirstN(xs, 3); // 1+2+3 = 6
  if (s3 == 6) {
    print("sumFirstN OK (6)");
  }

  // tocar globals b y msg
  if (b > 1.0) {
    print("b > 1.0");
  }
  if (msg == "hola") {
    print("msg == hola");
  }

  return s3;
}

let EXIT_CODE: integer = demo_globals_arrays();
