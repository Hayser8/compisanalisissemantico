.data
__str_0: .asciiz "hola"
__str_1: .asciiz " mundo"
__str_2: .asciiz " guau"
__str_3: .asciiz "Fido guau"

.text
.globl main
main:
  addiu $sp, $sp, -256
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 256
main__L0:
  li $t4, 0x40490FDA
  sw $t4, -4($fp)
  li $t4, 3
  sw $t4, -8($fp)
  lw $t0, -8($fp)
  sw $t0, -12($fp)
  la $t4, __str_0
  sw $t4, -16($fp)
  lw $t0, -16($fp)
  la $t5, __str_1
  addu $t0, $t0, $t5
  move $t6, $t0
  sw $t6, -20($fp)
  li $t4, 4
  move $a0, $t4
  jal __new_array
  move $t7, $v0
  # caller-save spill t1
  li $t1, 0
  li $t4, 1
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  sw $t4, 0($t3)
  li $t1, 1
  li $t4, 2
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  sw $t4, 0($t3)
  li $t1, 2
  li $t4, 3
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  sw $t4, 0($t3)
  li $t1, 3
  li $t4, 4
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  sw $t4, 0($t3)
  sw $t7, -24($fp)
  li $t4, 3
  move $a0, $t4
  jal __new_array
  move $t8, $v0
  # caller-save spill t2
  li $t1, 0
  li $t4, 0x3F800000
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  sw $t4, 0($t3)
  li $t1, 1
  li $t4, 0x40000000
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  sw $t4, 0($t3)
  li $t1, 2
  li $t4, 0x40600000
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  sw $t4, 0($t3)
  sw $t8, -28($fp)
  li $t4, 2
  move $a0, $t4
  jal __new_array
  move $t9, $v0
  # caller-save spill t3
  li $t4, 2
  move $a0, $t4
  jal __new_array
  move $t9, $v0
  # caller-save spill t4
  li $t1, 0
  li $t4, 1
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  sw $t4, 0($t3)
  li $t1, 1
  li $t4, 2
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  sw $t4, 0($t3)
  li $t1, 0
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  sw $t9, 0($t3)
  li $t4, 2
  move $a0, $t4
  jal __new_array
  move $t9, $v0
  # caller-save spill t5
  li $t1, 0
  li $t4, 3
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  sw $t4, 0($t3)
  li $t1, 1
  li $t4, 4
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  sw $t4, 0($t3)
  li $t1, 1
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  sw $t9, 0($t3)
  sw $t9, -32($fp)
  lw $t0, -32($fp)
  li $t1, 1
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  lw $t0, 0($t3)
  move $t9, $t0
  li $t1, 1
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  lw $t0, 0($t3)
  move $t9, $t0
  sw $t9, -36($fp)
  li $t4, 0x3F800000
  lw $t0, -8($fp)
  mtc1 $t4, $f0
  mtc1 $t0, $f1
  add.s $f2, $f0, $f1
  mfc1 $t0, $f2
  move $t9, $t0
  sw $t9, -40($fp)
  lw $t0, -8($fp)
  li $t5, 2
  mtc1 $t0, $f0
  mtc1 $t5, $f1
  mul.s $f2, $f0, $f1
  mfc1 $t0, $f2
  move $t9, $t0
  li $t5, 0x40400000
  mtc1 $t9, $f0
  mtc1 $t5, $f1
  div.s $f2, $f0, $f1
  mfc1 $t0, $f2
  move $t9, $t0
  sw $t9, -44($fp)
  li $t4, 10
  li $t5, 7
  mtc1 $t4, $f0
  mtc1 $t5, $f1
  sub.s $f2, $f0, $f1
  mfc1 $t0, $f2
  move $t9, $t0
  sw $t9, -48($fp)
  li $t4, 0x40A00000
  li $t5, 2
  div $t4, $t5
  mfhi $t0
  move $t9, $t0
  sw $t9, -52($fp)
  lw $t0, -8($fp)
  li $t5, 10
  slt $t0, $t0, $t5
  move $t9, $t0
  lw $t0, -16($fp)
  la $t5, __str_0
  seq $t0, $t0, $t5
  move $t9, $t0
  and $t0, $t9, $t9
  move $t9, $t0
  li $t4, 0
  sltiu $t0, $t4, 1
  move $t9, $t0
  or $t0, $t9, $t9
  move $t9, $t0
  sw $t9, -56($fp)
  lw $t0, -8($fp)
  li $t5, 0
  slt $t0, $t5, $t0
  move $t9, $t0
  bne $t9, $zero, main__L1_then
  j main__L2_else
main__L1_then:
  lw $t0, -8($fp)
  move $t9, $t0
  j main__L3_end
main__L2_else:
  li $t4, 0
  move $t9, $t4
  j main__L3_end
main__L3_end:
  sw $t9, -60($fp)
  li $v0, 9
  li $a0, 4
  syscall
  move $t9, $v0
  sw $t9, -64($fp)
  li $v0, 9
  li $a0, 4
  syscall
  move $t9, $v0
  sw $t9, -68($fp)
  li $t4, 2
  move $a0, $t4
  jal __new_array
  move $t9, $v0
  # caller-save spill t22
  li $t1, 0
  lw $t2, -64($fp)
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  sw $t2, 0($t3)
  li $t1, 1
  lw $t2, -68($fp)
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  sw $t2, 0($t3)
  sw $t9, -72($fp)
  lw $t0, -72($fp)
  li $t1, 0
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  lw $t0, 0($t3)
  move $t9, $t0
  move $a0, $t9
  jal __mcall__bark
  move $t9, $v0
  # caller-save spill t24
  sw $t9, -76($fp)
  jal runAll
  move $t9, $v0
  # caller-save spill t25
  sw $t9, -80($fp)
main__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 256
  li $v0, 10
  syscall

makeMix:
  addiu $sp, $sp, -256
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 256
makeMix__L0:
  li $t4, 3
  move $a0, $t4
  jal __new_array
  move $t6, $v0
  # caller-save spill t0
  li $t1, 0
  li $t4, 1
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  sw $t4, 0($t3)
  li $t1, 1
  li $t4, 0x40000000
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  sw $t4, 0($t3)
  li $t1, 2
  li $t4, 3
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  sw $t4, 0($t3)
  sw $t6, -4($fp)
  lw $t0, -4($fp)
  move $v0, $t0
  j makeMix__epilogue
makeMix__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 256
  beq $ra, $zero, __cps_halt
  jr $ra

pokeArray:
  addiu $sp, $sp, -256
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 256
pokeArray__L0:
  lw $t0, -4($fp)
  li $t1, 0
  li $t4, 42
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  sw $t4, 0($t3)
  lw $t0, -8($fp)
  li $t1, 1
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  lw $t0, 0($t3)
  move $t6, $t0
  li $t5, 0x3F000000
  mtc1 $t6, $f0
  mtc1 $t5, $f1
  add.s $f2, $f0, $f1
  mfc1 $t0, $f2
  move $t7, $t0
  lw $t0, -8($fp)
  li $t1, 1
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  sw $t7, 0($t3)
pokeArray__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 256
  beq $ra, $zero, __cps_halt
  jr $ra

sum2:
  addiu $sp, $sp, -256
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 256
  sw $a0, -4($fp)
  sw $a1, -8($fp)
sum2__L0:
  lw $t0, -4($fp)
  lw $t1, -8($fp)
  addu $t0, $t0, $t1
  move $t6, $t0
  move $v0, $t6
  j sum2__epilogue
sum2__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 256
  beq $ra, $zero, __cps_halt
  jr $ra

factorial:
  addiu $sp, $sp, -256
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 256
  sw $a0, -4($fp)
factorial__L0:
  lw $t0, -4($fp)
  li $t5, 1
  slt $t0, $t5, $t0
  xori $t0, $t0, 1
  move $t6, $t0
  bne $t6, $zero, factorial__L1_then
  j factorial__L2_end
factorial__L1_then:
  li $t4, 1
  move $v0, $t4
  j factorial__epilogue
  j factorial__L2_end
factorial__L2_end:
  lw $t0, -4($fp)
  li $t5, 1
  subu $t0, $t0, $t5
  move $t7, $t0
  move $a0, $t7
  jal factorial
  move $t8, $v0
  # caller-save spill t2
  lw $t0, -4($fp)
  mul $t0, $t0, $t8
  move $t9, $t0
  move $v0, $t9
  j factorial__epilogue
factorial__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 256
  beq $ra, $zero, __cps_halt
  jr $ra

fib:
  addiu $sp, $sp, -256
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 256
  sw $a0, -4($fp)
fib__L0:
  lw $t0, -4($fp)
  li $t5, 1
  slt $t0, $t5, $t0
  xori $t0, $t0, 1
  move $t6, $t0
  bne $t6, $zero, fib__L1_then
  j fib__L2_end
fib__L1_then:
  lw $t0, -4($fp)
  move $v0, $t0
  j fib__epilogue
  j fib__L2_end
fib__L2_end:
  lw $t0, -4($fp)
  li $t5, 1
  subu $t0, $t0, $t5
  move $t7, $t0
  move $a0, $t7
  jal fib
  move $t8, $v0
  # caller-save spill t2
  lw $t0, -4($fp)
  li $t5, 2
  subu $t0, $t0, $t5
  move $t9, $t0
  move $a0, $t9
  jal fib
  move $t9, $v0
  # caller-save spill t4
  addu $t0, $t8, $t9
  move $t9, $t0
  move $v0, $t9
  j fib__epilogue
fib__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 256
  beq $ra, $zero, __cps_halt
  jr $ra

outer:
  addiu $sp, $sp, -256
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 256
  sw $a0, -4($fp)
outer__L0:
  li $t4, 10
  sw $t4, -8($fp)
  li $t4, 5
  sw $t4, -12($fp)
  lw $t0, -4($fp)
  lw $t1, -8($fp)
  addu $t0, $t0, $t1
  move $t6, $t0
  lw $t0, -12($fp)
  addu $t0, $t6, $t0
  move $t7, $t0
  move $v0, $t7
  j outer__epilogue
outer__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 256
  beq $ra, $zero, __cps_halt
  jr $ra

sumWithLoops:
  addiu $sp, $sp, -256
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 256
sumWithLoops__L0:
  li $t4, 0
  sw $t4, -4($fp)
  li $t4, 0
  sw $t4, -8($fp)
  j sumWithLoops__L1_while_head
sumWithLoops__L1_while_head:
  lw $t0, -8($fp)
  li $t5, 4
  slt $t0, $t0, $t5
  move $t6, $t0
  bne $t6, $zero, sumWithLoops__L2_while_body
  j sumWithLoops__L3_while_end
sumWithLoops__L2_while_body:
  lw $t0, -12($fp)
  lw $t1, -8($fp)
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  lw $t0, 0($t3)
  move $t7, $t0
  lw $t0, -4($fp)
  addu $t0, $t0, $t7
  move $t8, $t0
  sw $t8, -4($fp)
  lw $t0, -8($fp)
  li $t5, 1
  addu $t0, $t0, $t5
  move $t9, $t0
  sw $t9, -8($fp)
  j sumWithLoops__L1_while_head
sumWithLoops__L3_while_end:
  li $t4, 0
  sw $t4, -16($fp)
sumWithLoops__L4_do_body:
  lw $t0, -4($fp)
  lw $t1, -16($fp)
  addu $t0, $t0, $t1
  move $t9, $t0
  sw $t9, -4($fp)
  lw $t0, -16($fp)
  li $t5, 1
  addu $t0, $t0, $t5
  move $t9, $t0
  sw $t9, -16($fp)
sumWithLoops__L5_do_head:
  lw $t0, -16($fp)
  li $t5, 2
  slt $t0, $t0, $t5
  move $t9, $t0
  bne $t9, $zero, sumWithLoops__L4_do_body
  j sumWithLoops__L6_do_end
sumWithLoops__L6_do_end:
  li $t4, 0
  sw $t4, -20($fp)
  j sumWithLoops__L7_while_head
sumWithLoops__L7_while_head:
  lw $t0, -20($fp)
  li $t5, 3
  slt $t0, $t0, $t5
  move $t9, $t0
  bne $t9, $zero, sumWithLoops__L8_while_body
  j sumWithLoops__L9_while_end
sumWithLoops__L8_while_body:
  lw $t0, -20($fp)
  li $t5, 1
  seq $t0, $t0, $t5
  move $t9, $t0
  bne $t9, $zero, sumWithLoops__L10_then
  j sumWithLoops__L11_end
sumWithLoops__L10_then:
  lw $t0, -20($fp)
  li $t5, 1
  addu $t0, $t0, $t5
  move $t9, $t0
  sw $t9, -20($fp)
  j sumWithLoops__L7_while_head
  j sumWithLoops__L11_end
sumWithLoops__L11_end:
  lw $t0, -20($fp)
  li $t5, 1
  slt $t0, $t5, $t0
  move $t9, $t0
  bne $t9, $zero, sumWithLoops__L12_then
  j sumWithLoops__L13_end
sumWithLoops__L12_then:
  j sumWithLoops__L9_while_end
  j sumWithLoops__L13_end
sumWithLoops__L13_end:
  lw $t0, -4($fp)
  lw $t1, -20($fp)
  addu $t0, $t0, $t1
  move $t9, $t0
  sw $t9, -4($fp)
  lw $t0, -20($fp)
  li $t5, 1
  addu $t0, $t0, $t5
  move $t9, $t0
  sw $t9, -20($fp)
  j sumWithLoops__L7_while_head
sumWithLoops__L9_while_end:
  li $t4, 0
  sw $t4, -24($fp)
  j sumWithLoops__L14_while_head
sumWithLoops__L14_while_head:
  lw $t0, -24($fp)
  li $t5, 4
  slt $t0, $t0, $t5
  move $t9, $t0
  bne $t9, $zero, sumWithLoops__L15_while_body
  j sumWithLoops__L16_while_end
sumWithLoops__L15_while_body:
  lw $t0, -12($fp)
  lw $t1, -24($fp)
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  lw $t0, 0($t3)
  move $t9, $t0
  lw $t0, -4($fp)
  addu $t0, $t0, $t9
  move $t9, $t0
  sw $t9, -4($fp)
  lw $t0, -24($fp)
  li $t5, 1
  addu $t0, $t0, $t5
  move $t9, $t0
  sw $t9, -24($fp)
  j sumWithLoops__L14_while_head
sumWithLoops__L16_while_end:
  lw $t0, -4($fp)
  move $v0, $t0
  j sumWithLoops__epilogue
sumWithLoops__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 256
  beq $ra, $zero, __cps_halt
  jr $ra

checkSwitch:
  addiu $sp, $sp, -256
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 256
  sw $a0, -4($fp)
checkSwitch__L0:
  lw $t0, -4($fp)
  li $t5, 10
  slt $t0, $t5, $t0
  move $t6, $t0
  li $t4, 1
  seq $t0, $t4, $t6
  move $t7, $t0
  bne $t7, $zero, checkSwitch__L1_case
  j checkSwitch__L2_switch_default
checkSwitch__L1_case:
  li $t4, 1
  move $v0, $t4
  j checkSwitch__epilogue
  j checkSwitch__L3_switch_end
checkSwitch__L2_switch_default:
  li $t4, 0
  move $v0, $t4
  j checkSwitch__epilogue
  j checkSwitch__L3_switch_end
checkSwitch__L3_switch_end:
  li $t4, 0
  move $v0, $t4
  j checkSwitch__epilogue
checkSwitch__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 256
  beq $ra, $zero, __cps_halt
  jr $ra

Animal__constructor:
  addiu $sp, $sp, -256
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 256
  sw $a0, -4($fp)
  sw $a0, -8($fp)
Animal__constructor__L0:
  lw $t0, -8($fp)
  lw $t1, -4($fp)
  sw $t1, 0($t0)
Animal__constructor__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 256
  beq $ra, $zero, __cps_halt
  jr $ra

Animal__speak:
  addiu $sp, $sp, -256
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 256
  sw $a0, -4($fp)
Animal__speak__L0:
  lw $t0, -4($fp)
  lw $t0, 0($t0)
  move $t6, $t0
  move $v0, $t6
  j Animal__speak__epilogue
Animal__speak__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 256
  beq $ra, $zero, __cps_halt
  jr $ra

Dog__constructor:
  addiu $sp, $sp, -256
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 256
  sw $a0, -4($fp)
  sw $a0, -8($fp)
Dog__constructor__L0:
  lw $t0, -8($fp)
  lw $t1, -4($fp)
  sw $t1, 0($t0)
Dog__constructor__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 256
  beq $ra, $zero, __cps_halt
  jr $ra

Dog__bark:
  addiu $sp, $sp, -260
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  sw $s0, 8($sp)
  addiu $fp, $sp, 260
  sw $a0, -4($fp)
Dog__bark__L0:
  lw $s0, -4($fp)
  sw $s0, -4($fp)
  lw $s0, -4($fp)
  move $a0, $s0
  jal __mcall__speak
  move $t6, $v0
  # caller-save spill t0
  la $t5, __str_2
  addu $t0, $t6, $t5
  move $t7, $t0
  move $v0, $t7
  j Dog__bark__epilogue
Dog__bark__epilogue:
  lw $s0, 8($sp)
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 260
  beq $ra, $zero, __cps_halt
  jr $ra

A__constructor:
  addiu $sp, $sp, -256
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 256
  sw $a0, -4($fp)
  sw $a0, -8($fp)
A__constructor__L0:
  lw $t0, -8($fp)
  lw $t1, -4($fp)
  sw $t1, 4($t0)
A__constructor__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 256
  beq $ra, $zero, __cps_halt
  jr $ra

A__get:
  addiu $sp, $sp, -256
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 256
  sw $a0, -4($fp)
A__get__L0:
  lw $t0, -4($fp)
  lw $t0, 4($t0)
  move $t6, $t0
  lw $t0, -4($fp)
  lw $t0, 0($t0)
  move $t7, $t0
  addu $t0, $t6, $t7
  move $t8, $t0
  li $t5, 7
  subu $t0, $t8, $t5
  move $t9, $t0
  move $v0, $t9
  j A__get__epilogue
A__get__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 256
  beq $ra, $zero, __cps_halt
  jr $ra

sumFirstN:
  addiu $sp, $sp, -256
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 256
  sw $a0, -4($fp)
  sw $a1, -8($fp)
sumFirstN__L0:
  li $t4, 0
  sw $t4, -12($fp)
  li $t4, 0
  sw $t4, -16($fp)
  j sumFirstN__L1_while_head
sumFirstN__L1_while_head:
  lw $t0, -16($fp)
  lw $t1, -8($fp)
  slt $t0, $t0, $t1
  move $t6, $t0
  bne $t6, $zero, sumFirstN__L2_while_body
  j sumFirstN__L3_while_end
sumFirstN__L2_while_body:
  lw $t0, -4($fp)
  lw $t1, -16($fp)
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  lw $t0, 0($t3)
  move $t7, $t0
  lw $t0, -12($fp)
  addu $t0, $t0, $t7
  move $t8, $t0
  sw $t8, -12($fp)
  lw $t0, -16($fp)
  li $t5, 1
  addu $t0, $t0, $t5
  move $t9, $t0
  sw $t9, -16($fp)
  j sumFirstN__L1_while_head
sumFirstN__L3_while_end:
  lw $t0, -12($fp)
  move $v0, $t0
  j sumFirstN__epilogue
sumFirstN__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 256
  beq $ra, $zero, __cps_halt
  jr $ra

runAll:
  addiu $sp, $sp, -256
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 256
runAll__L0:
  jal pokeArray
  move $t6, $v0
  # caller-save spill t0
  lw $t0, -4($fp)
  move $a0, $t0
  li $t5, 2
  move $a1, $t5
  jal sum2
  move $t7, $v0
  # caller-save spill t1
  sw $t7, -8($fp)
  li $t4, 6
  move $a0, $t4
  jal factorial
  move $t8, $v0
  # caller-save spill t2
  sw $t8, -12($fp)
  li $t4, 8
  move $a0, $t4
  jal fib
  move $t9, $v0
  # caller-save spill t3
  sw $t9, -16($fp)
  li $t4, 3
  move $a0, $t4
  jal outer
  move $t9, $v0
  # caller-save spill t4
  sw $t9, -20($fp)
  jal sumWithLoops
  move $t9, $v0
  # caller-save spill t5
  sw $t9, -24($fp)
  li $v0, 9
  li $a0, 8
  syscall
  move $t9, $v0
  sw $t9, -28($fp)
  lw $t0, -28($fp)
  move $a0, $t0
  jal __mcall__get
  move $t9, $v0
  # caller-save spill t7
  sw $t9, -32($fp)
  li $t4, 5
  move $a0, $t4
  jal checkSwitch
  move $t9, $v0
  # caller-save spill t8
  sw $t9, -36($fp)
  jal makeMix
  move $t9, $v0
  # caller-save spill t9
  sw $t9, -40($fp)
  lw $t0, -40($fp)
  li $t1, 0
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  lw $t0, 0($t3)
  move $t9, $t0
  sw $t9, -44($fp)
  lw $t0, -48($fp)
  move $a0, $t0
  li $t5, 3
  move $a1, $t5
  jal sumFirstN
  move $t9, $v0
  # caller-save spill t11
  sw $t9, -52($fp)
  lw $t0, -56($fp)
  move $a0, $t0
  jal __mcall__bark
  move $t9, $v0
  # caller-save spill t12
  sw $t9, -60($fp)
  lw $t0, -8($fp)
  lw $t1, -12($fp)
  addu $t0, $t0, $t1
  move $t9, $t0
  lw $t0, -16($fp)
  addu $t0, $t9, $t0
  move $t9, $t0
  lw $t0, -20($fp)
  addu $t0, $t9, $t0
  move $t9, $t0
  lw $t0, -24($fp)
  addu $t0, $t9, $t0
  move $t9, $t0
  lw $t0, -32($fp)
  addu $t0, $t9, $t0
  move $t9, $t0
  lw $t0, -36($fp)
  addu $t0, $t9, $t0
  move $t9, $t0
  lw $t0, -52($fp)
  addu $t0, $t9, $t0
  move $t9, $t0
  sw $t9, -64($fp)
  lw $t0, -60($fp)
  la $t5, __str_3
  seq $t0, $t0, $t5
  move $t9, $t0
  bne $t9, $zero, runAll__L1_then
  j runAll__L2_end
runAll__L1_then:
  lw $t0, -64($fp)
  li $t5, 1
  addu $t0, $t0, $t5
  move $t9, $t0
  sw $t9, -64($fp)
  j runAll__L2_end
runAll__L2_end:
  lw $t0, -64($fp)
  move $v0, $t0
  j runAll__epilogue
runAll__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 256
  beq $ra, $zero, __cps_halt
  jr $ra


.globl __make_closure
.globl __closure_apply
.globl __cps_halt

__make_closure:
  move $t0, $a0          # t0 = codeptr
  move $t1, $a1          # t1 = envptr

  li   $v0, 9            # syscall sbrk
  li   $a0, 8            # 2 words: code + env
  syscall

  move $t2, $v0          # t2 = closure ptr
  sw   $t0, 0($t2)       # closure->code = codeptr
  sw   $t1, 4($t2)       # closure->env  = envptr
  move $v0, $t2          # devolver closure en $v0
  jr   $ra
  nop

__closure_apply:
  # Si closure es NULL, retorna 0
  beq  $a0, $zero, __closure_apply_null
  nop

  # Cargar codeptr y envptr desde el closure
  lw   $t9, 0($a0)       # t9 = closure->code
  beq  $t9, $zero, __closure_apply_null
  nop
  lw   $t0, 4($a0)       # t0 = closure->env
  move $a0, $t0          # a0 = env (a1..a3 quedan igual)

  # Trampolín / tail-call: saltar directamente al código del closure
  jr   $t9
  nop

__closure_apply_null:
  # Closure roto o codeptr nulo -> devolver 0
  move $v0, $zero
  jr   $ra
  nop

__cps_halt:
  li   $v0, 10    # exit
  syscall

__new_array:
  # $a0 = length (en elementos)
  sll  $a0, $a0, 2       # *4 bytes por elemento
  li   $v0, 9            # syscall sbrk
  syscall
  move $t0, $v0          # base del array también en $t0
  jr   $ra


# --- Runtime stubs para llamadas a métodos (__mcall__X) ---
__mcall__speak:
  # Stub simple: estáticamente llama a Animal__speak
  jal Animal__speak
  jr  $ra

__mcall__bark:
  # Stub simple: estáticamente llama a Dog__bark
  jal Dog__bark
  jr  $ra

__mcall__get:
  # Stub simple: estáticamente llama a A__get
  jal A__get
  jr  $ra
