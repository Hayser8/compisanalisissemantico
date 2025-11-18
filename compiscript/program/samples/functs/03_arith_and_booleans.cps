// 03_arith_and_booleans.cps
// Aritmética y expresiones booleanas.

let a: integer = 3;

let sumNum: float = 1.0 + a;
let prod: float   = (a * 2) / 3.0;
let rest: integer = 10 - 7;
let modOk: float  = 5.0 % 2;

let s: string = "hola";

// (a < 10) && (s == "hola") || !(false)
let flag: boolean = (a < 10) && (s == "hola") || !(false);

// condicional ternario
let tern: integer = (a > 0) ? a : 0;

function demo_arith(): integer {
  if (flag) {
    print("flag es verdadera");
  }

  if (tern == 3) {
    print("tern es 3");
  }

  if (rest == 3) {
    print("rest = 3");
  }

  if (sumNum > 3.0) {
    print("sumNum > 3.0");
  }
  if (prod > 1.0) {
    print("prod > 1.0");
  }
  if (modOk > 0.0) {
    print("modOk > 0.0");
  }

  return 0;
}

let EXIT_CODE: integer = demo_arith();
