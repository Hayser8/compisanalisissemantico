// 09_strings_and_concat.cps
// Strings, concatenación e igualdad.

function greet(name: string): string {
  let base: string = "Hola, ";
  let ex: string = "!";
  let tmp: string = base + name;
  let full: string = tmp + ex;
  return full;
}

function demo_strings(): integer {
  let g: string = greet("Compiscript");

  if (g == "Hola, Compiscript!") {
    print("greet OK");
  } else {
    print("greet FAIL");
  }

  return 0;
}

let EXIT_CODE: integer = demo_strings();
