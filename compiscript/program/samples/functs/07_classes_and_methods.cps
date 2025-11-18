// 07_classes_and_methods.cps
// Clases, this, constructores y métodos.

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

function demo_classes(): integer {
  let d: Dog = new Dog("Fido");
  let voice: string = d.bark();

  if (voice == "Fido guau") {
    print("Dog.bark OK");
  } else {
    print("Dog.bark FAIL");
  }

  // solo para tener un entero de retorno
  return 0;
}

let EXIT_CODE: integer = demo_classes();
