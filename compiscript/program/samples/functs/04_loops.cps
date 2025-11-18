// 04_loops.cps
// while, do-while y "for" emulado con while.

let xs: integer[] = [1, 2, 3, 4];

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

  // "for" -> while + continue/break
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

  return acc;
}

function demo_loops(): integer {
  let total: integer = sumWithLoops(); // debería ser 1+2+3+4 + 0+1 + 0+2 = 13
  if (total == 13) {
    print("sumWithLoops == 13");
  } else {
    print("sumWithLoops != 13");
  }
  return total;
}

let EXIT_CODE: integer = demo_loops();
