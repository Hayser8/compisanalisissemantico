// mini_ok.cps — prueba pequeña para el backend MIPS

let a: integer = 3;

function sum2(x: integer, y: integer): integer {
  return x + y;
}

function factorial(n: integer): integer {
  if (n <= 1) {
    return 1;
  }
  return n * factorial(n - 1);
}

function runAll(): integer {
  let r1: integer = sum2(a, 4);   // 3 + 4 = 7
  let r2: integer = factorial(5); // 120
  let total: integer = r1 + r2;   // 127
  return total;
}

// Ejecutar algo al cargar (igual patrón que ok_all_post.cps)
let FINAL: integer = runAll();
