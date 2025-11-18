// 05_switch.cps
// switch con condición booleana (switch(true)).

function checkSwitch(v: integer): integer {
  switch (true) {
    case (v < 0): {
      print("v < 0");
      return -1;
    }
    case (v == 0): {
      print("v == 0");
      return 0;
    }
    case (v > 10): {
      print("v > 10");
      return 2;
    }
    default: {
      print("0 < v <= 10");
      return 1;
    }
  }
  return 0;
}

function demo_switch(): integer {
  let r1: integer = checkSwitch(-5);
  let r2: integer = checkSwitch(0);
  let r3: integer = checkSwitch(5);
  let r4: integer = checkSwitch(20);

  // solo para tocar los valores
  if (r1 == -1 && r2 == 0 && r3 == 1 && r4 == 2) {
    print("switch OK");
  }

  return r1 + r2 + r3 + r4;
}

let EXIT_CODE: integer = demo_switch();
