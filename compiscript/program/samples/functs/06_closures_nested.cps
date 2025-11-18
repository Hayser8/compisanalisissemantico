// 06_closures_nested.cps
// Funciones anidadas y efecto de "closure" simple.

function outer(base: integer): integer {
  let bias: integer = 10;

  function inner(delta: integer): integer {
    return base + bias + delta;
  }

  let r1: integer = inner(0);
  let r2: integer = inner(5);

  if (r1 == base + 10) {
    print("inner(0) OK");
  }
  if (r2 == base + 15) {
    print("inner(5) OK");
  }

  return r1 + r2;
}

function demo_closures(): integer {
  let total: integer = outer(3); // (3+10) + (3+15) = 31
  if (total == 31) {
    print("outer(3) == 31");
  }
  return total;
}

let EXIT_CODE: integer = demo_closures();
