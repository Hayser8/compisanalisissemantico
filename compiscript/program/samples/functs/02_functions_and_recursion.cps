// 02_functions_and_recursion.cps
// Funciones simples y recursión.

function sum2(x: integer, y: integer): integer {
  return x + y;
}

function factorial(n: integer): integer {
  if (n <= 1) { return 1; }
  return n * factorial(n - 1);
}

function fib(n: integer): integer {
  if (n <= 1) { return n; }
  return fib(n - 1) + fib(n - 2);
}

function demo_functions_recursion(): integer {
  let s: integer = sum2(3, 4);      // 7
  let f: integer = factorial(5);    // 120
  let fb: integer = fib(6);         // 8

  if (s == 7) {
    print("sum2(3,4) == 7");
  }
  if (f == 120) {
    print("factorial(5) == 120");
  }
  if (fb == 8) {
    print("fib(6) == 8");
  }

  return s + f + fb;
}

let EXIT_CODE: integer = demo_functions_recursion();
