// 08_arrays_of_objects.cps
// Arrays de objetos y acceso a métodos.

class A {
  const K: integer = 7;
  let v: integer;

  function constructor(v: integer) {
    this.v = v;
  }

  function get(): integer {
    return this.v + this.K - 7;
  }
}

function sumFirstTwo(objs: A[]): integer {
  let i: integer = 0;
  let acc: integer = 0;
  while (i < 2) {
    acc = acc + objs[i].get();
    i = i + 1;
  }
  return acc;
}

function demo_arrays_objects(): integer {
  let a1: A = new A(10);
  let a2: A = new A(20);
  let arr: A[] = [a1, a2];

  let s: integer = sumFirstTwo(arr); // 10 + 20 = 30
  if (s == 30) {
    print("sumFirstTwo == 30");
  }

  return s;
}

let EXIT_CODE: integer = demo_arrays_objects();
