// === TIPOS / ASIGNACIONES ===
let i: integer = 1.5;          // E200: float -> integer no asignable
let f: float = "hola";         // E200: string -> float no asignable
let s: string = 10;            // E200: integer -> string no asignable
let n: integer = null;         // E200: null -> integer no asignable

// === OPERADORES ===
let x = "hola" + 1;            // E201: '+' tipos inválidos (string + int)
let y = true * 3;              // E201: '*' requiere numéricos
let z = (1 < "a");             // E201: relacional sólo numéricos
let eq = ("a" == 1);           // E201: igualdad tipos incompatibles
let lg = (1 && 2);             // E201/E301: lógico requiere boolean
let ng = !42;                  // E201: '!' requiere boolean

// === CONDICIONES / CONTROL DE FLUJO ===
if ("no-bool") { }             // E301: condición no boolean
while (123) { }                // E301
do { } while ("x");            // E301
switch (1) {                   // E301: switch debe ser boolean
  default: { }
}

// break/continue fuera de bucle
break;                         // E300
continue;                      // E300

// === IDENTIFICADORES / ÁMBITO ===
u = 3;                         // E100: 'u' no declarado
let a: integer; let a: float;  // E101: redeclaración en el mismo scope

function dupParams(p: integer, p: integer) { }   // E102: parámetro duplicado

// === RETURN / FLUJO DE RETORNO ===
function retOutside() { }
return 5;                      // E302: return fuera de función

function needInt(): integer {  // E303: faltan retornos en todos los caminos
  if (true) { return 1; }
  // no hay 'else' que garantice return
}

function wrongReturn(): integer {
  return "hola";               // E200: string no asignable a integer
}

function deadCode() {
  return;
  let k = 1;                   // E500: código inalcanzable
}

// === LLAMADAS / ARIDAD ===
function sum2(x: integer, y: integer): integer { return x + y; }
let c0 = sum2(1);              // E202: aridad inválida
let c1 = sum2(1, "a");         // E201/E200: tipo de arg incompatible
let notFn: integer = 3;
let c2 = notFn(10);            // E201: llamada sobre no-función

// === ARREGLOS ===
let xs: integer[] = [1, 2, "a"];   // E201: elementos incompatibles
let m = xs["0"];                   // E203: índice no integer
let q = 5[0];                      // E203: indexar algo que no es arreglo
xs[0] = "hola";                    // E200: string -> integer (elemento)

// Propiedad en no-objeto (arreglo no tiene miembros)
let len = xs.length;               // E204: acceso a miembro en no-objeto

// === CLASES / THIS / MIEMBROS ===
class C {
  let v: integer;
  const K: integer = 7;
  function setV(x: integer) { this.v = x; }
  function constructor(v: integer) { this.v = v; }
}
let cc: C = new C();               // E202: aridad de constructor (espera 1)
cc.nope = 1;                        // E204: miembro no existe
cc.v = "hola";                      // E200: string -> integer

// Asignar a const de clase
cc.K = 9;                           // E401: asignar a const de clase

// 'this' fuera de método
let tthis = this;                   // E205/E_OP_TYPES: this fuera de contexto

// === ASIGNACIÓN A LADO-IZQ NO ASIGNABLE ===
sum2(1,2) = 5;                      // E201: LHS no asignable (llamada)
(this) = 3;                         // E201/E205: no se puede asignar a `this`

// === FUNCIONES ANIDADAS/RETORNOS ===
function outerBad(a: integer): integer {
  function innerBad(b: float): integer { return a + b; } // ok semántico numérico pero probaremos llamada mal
  return innerBad("x");            // E201/E200: arg incompatible
}
