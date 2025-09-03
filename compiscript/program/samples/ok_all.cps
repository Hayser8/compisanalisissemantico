// ----- Constantes y variables top-level -----
const PI: float = 3.1415926;

let a: integer = 3;
let b: float = a;              
let s: string = "hola";
let t: string = s + " mundo"; 

let xs: integer[] = [1, 2, 3, 4];
let ys: float[]   = [1.0, 2.0, 3.5];

let grid = [[1,2],[3,4]];
let g11: integer = grid[1][1]; // 4

// mezcla numérica con inferencia (float[])
function makeMix(): float[] {
  let mix = [1, 2.0, 3];
  return mix;
}

// índice y asignación de arreglo
function pokeArray() {
  xs[0] = 42;
  ys[1] = ys[1] + 0.5;
}

let sumNum: float = 1.0 + a;         
let prod: float = (a * 2) / 3.0;     
let rest: integer = 10 - 7;
let modOk: float = 5.0 % 2;          

let flag: boolean = (a < 10) && (s == "hola") || !(false);
let tern: integer = (a > 0) ? a : 0; // condicional

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

function outer(a0: integer): integer {
  let bias: integer = 10;
  function inner(b: integer): integer {
    return a0 + bias + b;
  }
  return inner(5);
}

function sumWithLoops(): integer {
  let acc: integer = 0;

  // while
  let i: integer = 0;
  while (i < 4) {
    acc = acc + xs[i];
    i = i + 1;
  }

  // do-while
  let j: integer = 0;
  do {
    acc = acc + j;
    j = j + 1;
  } while (j < 2);

  // "for" simulado con while para evitar asignación en la sección de actualización
  let k: integer = 0;
  while (k < 3) {
    if (k == 1) { 
      k = k + 1;
      continue; 
    }
    if (k > 1) { break; }
    acc = acc + k;
    k = k + 1;
  }

  // foreach: iterador predeclarado y tipado
  let it: integer = 0;
  foreach (it in xs) {
    acc = acc + it;
  }

  return acc;
}

// ----- switch (booleans) -----
function checkSwitch(v: integer): integer {
  switch (true) {
    case (v > 10): {
      return 1;
    }
    default: {
      return 0;
    }
  }
  return 0;
}

// ----- Clases, this, constructor, herencia, métodos -----
class Animal {
  let name: string;
  function constructor(n: string) { this.name = n; }
  function speak(): string { return this.name; }
}

class Dog : Animal {
  const SPECIES: string = "Canis";
  function constructor(n: string) { this.name = n; }
  function bark(): string { return this.speak() + " guau"; } 
}

class A {
  const K: integer = 7;      
  let v: integer;
  function constructor(v: integer) { this.v = v; }
  function get(): integer { return this.v + this.K - 7; }
}

// uso de clases y arrays de objetos
let d1: Dog = new Dog("Fido");
let d2: Dog = new Dog("Rex");
let pack: Dog[] = [d1, d2];
let firstVoice: string = pack[0].bark();

function sumFirstN(arr: integer[], n: integer): integer {
  let s: integer = 0;
  let i: integer = 0;
  while (i < n) {
    s = s + arr[i];
    i = i + 1;
  }
  return s;
}

function runAll(): integer {
  pokeArray();

  let r1: integer = sum2(a, 2);
  let r2: integer = factorial(6);
  let r3: integer = fib(8);
  let r4: integer = outer(3);
  let r5: integer = sumWithLoops();

  let o: A = new A(10);
  let got: integer = o.get();

  let sw: integer = checkSwitch(5);

  // prueba de arreglos devueltos
  let mm: float[] = makeMix();
  let m0: float = mm[0];

  // sumar primeros 3 de xs (sin usar .length)
  let sx: integer = sumFirstN(xs, 3);

  // uso de strings de clase
  let voice: string = d1.bark();

  // combinar todo en un resultado
  let total: integer = r1 + r2 + r3 + r4 + r5 + got + sw + sx;
  if (voice == "Fido guau") { total = total + 1; }
  return total;
}

// Ejecutar algo al cargar
let FINAL: integer = runAll();
