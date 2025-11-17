OK ✅  (sin errores)
[IR-DBG] pokeArray params (lower_from_ast): []
[IR-DBG] runAll -> pokeArray calls (lower_from_ast):
  [IR-DBG]   ('call', 'pokeArray', [])
[EMITTER] fn=main frame_size(plan)=8 has_calls=True
[EMITTER]   s_regs_in_use=[]
[EMITTER]   params=[]
[EMITTER]   local_off={}
[EMITTER]   param_home_off={}
[EMITTER]   need_param_homes=0
[EMITTER]   most_neg_offset=0
[EMITTER]   frame_bytes(final)=256
[EMITTER]   call in main -> __str_concat (argc=2)
[EMITTER]     flushing names: []
[EMITTER]   call in main -> __new_array (argc=1)
[EMITTER]     flushing names: []
[EMITTER]   call in main -> __new_array (argc=1)
[EMITTER]     flushing names: []
[EMITTER]   call in main -> __new_array (argc=1)
[EMITTER]     flushing names: []
[EMITTER]   call in main -> __new_array (argc=1)
[EMITTER]     flushing names: []
[EMITTER]   call in main -> __new_array (argc=1)
[EMITTER]     flushing names: []
[EMITTER]   call in main -> __str_eq (argc=2)
[EMITTER]     flushing names: []
[EMITTER]   call in main -> __new_array (argc=1)
[EMITTER]     flushing names: []
[EMITTER]   call in main -> __mcall__bark (argc=1)
[EMITTER]     flushing names: []
[EMITTER]   call in main -> runAll (argc=0)
[EMITTER]     flushing names: []
[EMITTER] ===== ASM for main (frame(plan)=8) =====
    main:
      addiu $sp, $sp, -256
      sw $fp, 0($sp)
      sw $ra, 4($sp)
      addiu $fp, $sp, 256
    main__L0:
      li $t4, 0x40490FDA
      # store global PI
      la $at, PI
      sw $t4, 0($at)
      li $t4, 3
      # store global a
      la $at, a
      sw $t4, 0($at)
      # load global a
      la $at, a
      lw $t0, 0($at)
      # store global b
      la $at, b
      sw $t0, 0($at)
      la $t4, __str_0
      # store global s
      la $at, s
      sw $t4, 0($at)
      # load global s
      la $at, s
      lw $t0, 0($at)
      move $a0, $t0
      la $t5, __str_1
      move $a1, $t5
      jal __str_concat
      move $t6, $v0
      # caller-save spill t0
      # store global t
      la $at, t
      sw $t6, 0($at)
      li $t4, 4
      move $a0, $t4
      jal __new_array
      move $t7, $v0
      # caller-save spill t1
      li $t5, 0
      li $t4, 1
      sll $t3, $t5, 2
      addu $t3, $t7, $t3
      sw $t4, 0($t3)
      li $t5, 1
      li $t4, 2
      sll $t3, $t5, 2
      addu $t3, $t7, $t3
      sw $t4, 0($t3)
      li $t5, 2
      li $t4, 3
      sll $t3, $t5, 2
      addu $t3, $t7, $t3
      sw $t4, 0($t3)
      li $t5, 3
      li $t4, 4
      sll $t3, $t5, 2
      addu $t3, $t7, $t3
      sw $t4, 0($t3)
      # store global xs
      la $at, xs
      sw $t7, 0($at)
      li $t4, 3
      move $a0, $t4
      jal __new_array
      move $t8, $v0
      # caller-save spill t2
      li $t5, 0
      li $t4, 0x3F800000
      sll $t3, $t5, 2
      addu $t3, $t8, $t3
      sw $t4, 0($t3)
      li $t5, 1
      li $t4, 0x40000000
      sll $t3, $t5, 2
      addu $t3, $t8, $t3
      sw $t4, 0($t3)
      li $t5, 2
      li $t4, 0x40600000
      sll $t3, $t5, 2
      addu $t3, $t8, $t3
      sw $t4, 0($t3)
      # store global ys
      la $at, ys
      sw $t8, 0($at)
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
      li $t5, 0
      li $t4, 1
      sll $t3, $t5, 2
      addu $t3, $t9, $t3
      sw $t4, 0($t3)
      li $t5, 1
      li $t4, 2
      sll $t3, $t5, 2
      addu $t3, $t9, $t3
      sw $t4, 0($t3)
      li $t5, 0
      sll $t3, $t5, 2
      addu $t3, $t9, $t3
      sw $t9, 0($t3)
      li $t4, 2
      move $a0, $t4
      jal __new_array
      move $t9, $v0
      # caller-save spill t5
      li $t5, 0
      li $t4, 3
      sll $t3, $t5, 2
      addu $t3, $t9, $t3
[EMITTER]   ... <truncated> ...
[EMITTER] ===== END ASM for main =====
[EMITTER] fn=makeMix frame_size(plan)=8 has_calls=True
[EMITTER]   s_regs_in_use=[]
[EMITTER]   params=[]
[EMITTER]   local_off={}
[EMITTER]   param_home_off={}
[EMITTER]   need_param_homes=0
[EMITTER]   most_neg_offset=0
[EMITTER]   frame_bytes(final)=256
[EMITTER]   call in makeMix -> __new_array (argc=1)
[EMITTER]     flushing names: []
[EMITTER] ===== ASM for makeMix (frame(plan)=8) =====
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
      li $t5, 0
      li $t4, 1
      sll $t3, $t5, 2
      addu $t3, $t6, $t3
      sw $t4, 0($t3)
      li $t5, 1
      li $t4, 0x40000000
      sll $t3, $t5, 2
      addu $t3, $t6, $t3
      sw $t4, 0($t3)
      li $t5, 2
      li $t4, 3
      sll $t3, $t5, 2
      addu $t3, $t6, $t3
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
      nop
      jr $ra
[EMITTER] ===== END ASM for makeMix =====
[EMITTER] fn=pokeArray frame_size(plan)=8 has_calls=False
[EMITTER]   s_regs_in_use=[]
[EMITTER]   params=[]
[EMITTER]   local_off={}
[EMITTER]   param_home_off={}
[EMITTER]   need_param_homes=0
[EMITTER]   most_neg_offset=0
[EMITTER]   frame_bytes(final)=256
[EMITTER] ===== ASM for pokeArray (frame(plan)=8) =====
    pokeArray:
      addiu $sp, $sp, -256
      sw $fp, 0($sp)
      sw $ra, 4($sp)
      addiu $fp, $sp, 256
    pokeArray__L0:
      # load global xs
      la $at, xs
      lw $t0, 0($at)
      li $t5, 0
      li $t4, 42
      sll $t3, $t5, 2
      addu $t3, $t0, $t3
      sw $t4, 0($t3)
      # load global ys
      la $at, ys
      lw $t0, 0($at)
      li $t5, 1
      sll $t3, $t5, 2
      addu $t3, $t0, $t3
      lw $t0, 0($t3)
      move $t6, $t0
      li $t5, 0x3F000000
      mtc1 $t6, $f0
      mtc1 $t5, $f1
      add.s $f2, $f0, $f1
      mfc1 $t0, $f2
      move $t7, $t0
      # load global ys
      la $at, ys
      lw $t0, 0($at)
      li $t5, 1
      sll $t3, $t5, 2
      addu $t3, $t0, $t3
      sw $t7, 0($t3)
    pokeArray__epilogue:
      lw $fp, 0($sp)
      lw $ra, 4($sp)
      addiu $sp, $sp, 256
      beq $ra, $zero, __cps_halt
      nop
      jr $ra
[EMITTER] ===== END ASM for pokeArray =====
[EMITTER] fn=sum2 frame_size(plan)=16 has_calls=False
[EMITTER]   s_regs_in_use=[]
[EMITTER]   params=['x', 'y']
[EMITTER]   local_off={}
[EMITTER]   param_home_off={0: -4, 1: -8}
[EMITTER]   need_param_homes=2
[EMITTER]   most_neg_offset=-8
[EMITTER]   frame_bytes(final)=256
[EMITTER] ===== ASM for sum2 (frame(plan)=16) =====
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
      nop
      jr $ra
[EMITTER] ===== END ASM for sum2 =====
[EMITTER] fn=factorial frame_size(plan)=16 has_calls=True
[EMITTER]   s_regs_in_use=[]
[EMITTER]   params=['n']
[EMITTER]   local_off={}
[EMITTER]   param_home_off={0: -4}
[EMITTER]   need_param_homes=1
[EMITTER]   most_neg_offset=-4
[EMITTER]   frame_bytes(final)=256
[EMITTER]   call in factorial -> factorial (argc=1)
[EMITTER]     flushing names: []
[EMITTER] ===== ASM for factorial (frame(plan)=16) =====
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
      nop
      jr $ra
[EMITTER] ===== END ASM for factorial =====
[EMITTER] fn=fib frame_size(plan)=16 has_calls=True
[EMITTER]   s_regs_in_use=[]
[EMITTER]   params=['n']
[EMITTER]   local_off={}
[EMITTER]   param_home_off={0: -4}
[EMITTER]   need_param_homes=1
[EMITTER]   most_neg_offset=-4
[EMITTER]   frame_bytes(final)=256
[EMITTER]   call in fib -> fib (argc=1)
[EMITTER]     flushing names: []
[EMITTER]   call in fib -> fib (argc=1)
[EMITTER]     flushing names: []
[EMITTER] ===== ASM for fib (frame(plan)=16) =====
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
      nop
      jr $ra
[EMITTER] ===== END ASM for fib =====
[EMITTER] fn=outer frame_size(plan)=16 has_calls=True
[EMITTER]   s_regs_in_use=[]
[EMITTER]   params=['a0']
[EMITTER]   local_off={}
[EMITTER]   param_home_off={0: -4}
[EMITTER]   need_param_homes=1
[EMITTER]   most_neg_offset=-4
[EMITTER]   frame_bytes(final)=256
[EMITTER]   call in outer -> inner (argc=1)
[EMITTER]     flushing names: []
[EMITTER] ===== ASM for outer (frame(plan)=16) =====
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
      move $a0, $t4
      jal inner
      move $t6, $v0
      # caller-save spill t0
      move $v0, $t6
      j outer__epilogue
    outer__epilogue:
      lw $fp, 0($sp)
      lw $ra, 4($sp)
      addiu $sp, $sp, 256
      beq $ra, $zero, __cps_halt
      nop
      jr $ra
[EMITTER] ===== END ASM for outer =====
[EMITTER] fn=sumWithLoops frame_size(plan)=8 has_calls=False
[EMITTER]   s_regs_in_use=[]
[EMITTER]   params=[]
[EMITTER]   local_off={}
[EMITTER]   param_home_off={}
[EMITTER]   need_param_homes=0
[EMITTER]   most_neg_offset=0
[EMITTER]   frame_bytes(final)=256
[EMITTER] ===== ASM for sumWithLoops (frame(plan)=8) =====
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
      # load global xs
      la $at, xs
      lw $t0, 0($at)
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
      sw $t4, -12($fp)
    sumWithLoops__L4_do_body:
      lw $t0, -4($fp)
      lw $t1, -12($fp)
      addu $t0, $t0, $t1
      move $t9, $t0
      sw $t9, -4($fp)
      lw $t0, -12($fp)
      li $t5, 1
      addu $t0, $t0, $t5
      move $t9, $t0
      sw $t9, -12($fp)
    sumWithLoops__L5_do_head:
      lw $t0, -12($fp)
      li $t5, 2
      slt $t0, $t0, $t5
      move $t9, $t0
      bne $t9, $zero, sumWithLoops__L4_do_body
      j sumWithLoops__L6_do_end
    sumWithLoops__L6_do_end:
      li $t4, 0
      sw $t4, -16($fp)
      j sumWithLoops__L7_while_head
    sumWithLoops__L7_while_head:
      lw $t0, -16($fp)
      li $t5, 3
      slt $t0, $t0, $t5
      move $t9, $t0
      bne $t9, $zero, sumWithLoops__L8_while_body
      j sumWithLoops__L9_while_end
    sumWithLoops__L8_while_body:
      lw $t0, -16($fp)
      li $t5, 1
      seq $t0, $t0, $t5
      move $t9, $t0
      bne $t9, $zero, sumWithLoops__L10_then
      j sumWithLoops__L11_end
    sumWithLoops__L10_then:
      lw $t0, -16($fp)
      li $t5, 1
      addu $t0, $t0, $t5
      move $t9, $t0
      sw $t9, -16($fp)
      j sumWithLoops__L7_while_head
      j sumWithLoops__L11_end
    sumWithLoops__L11_end:
      lw $t0, -16($fp)
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
      lw $t1, -16($fp)
      addu $t0, $t0, $t1
      move $t9, $t0
      sw $t9, -4($fp)
      lw $t0, -16($fp)
      li $t5, 1
      addu $t0, $t0, $t5
      move $t9, $t0
      sw $t9, -16($fp)
      j sumWithLoops__L7_while_head
    sumWithLoops__L9_while_end:
      li $t4, 0
      sw $t4, -20($fp)
      j sumWithLoops__L14_while_head
    sumWithLoops__L14_while_head:
      lw $t0, -20($fp)
      li $t5, 4
      slt $t0, $t0, $t5
      move $t9, $t0
      bne $t9, $zero, sumWithLoops__L15_while_body
      j sumWithLoops__L16_while_end
    sumWithLoops__L15_while_body:
      # load global xs
      la $at, xs
[EMITTER]   ... <truncated> ...
[EMITTER] ===== END ASM for sumWithLoops =====
[EMITTER] fn=checkSwitch frame_size(plan)=16 has_calls=False
[EMITTER]   s_regs_in_use=[]
[EMITTER]   params=['v']
[EMITTER]   local_off={}
[EMITTER]   param_home_off={0: -4}
[EMITTER]   need_param_homes=1
[EMITTER]   most_neg_offset=-4
[EMITTER]   frame_bytes(final)=256
[EMITTER] ===== ASM for checkSwitch (frame(plan)=16) =====
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
      nop
      jr $ra
[EMITTER] ===== END ASM for checkSwitch =====
[EMITTER] fn=Animal::constructor frame_size(plan)=16 has_calls=False
[EMITTER]   s_regs_in_use=[]
[EMITTER]   params=['this', 'n']
[EMITTER]   local_off={}
[EMITTER]   param_home_off={0: -4, 1: -8}
[EMITTER]   need_param_homes=2
[EMITTER]   most_neg_offset=-8
[EMITTER]   frame_bytes(final)=256
[EMITTER] ===== ASM for Animal::constructor (frame(plan)=16) =====
    Animal__constructor:
      addiu $sp, $sp, -256
      sw $fp, 0($sp)
      sw $ra, 4($sp)
      addiu $fp, $sp, 256
      sw $a0, -4($fp)
      sw $a1, -8($fp)
    Animal__constructor__L0:
      lw $t0, -4($fp)
      lw $t1, -8($fp)
      sw $t1, 0($t0)
    Animal__constructor__epilogue:
      lw $fp, 0($sp)
      lw $ra, 4($sp)
      addiu $sp, $sp, 256
      beq $ra, $zero, __cps_halt
      nop
      jr $ra
[EMITTER] ===== END ASM for Animal::constructor =====
[EMITTER] fn=Animal::speak frame_size(plan)=16 has_calls=False
[EMITTER]   s_regs_in_use=[]
[EMITTER]   params=['this']
[EMITTER]   local_off={}
[EMITTER]   param_home_off={0: -4}
[EMITTER]   need_param_homes=1
[EMITTER]   most_neg_offset=-4
[EMITTER]   frame_bytes(final)=256
[EMITTER] ===== ASM for Animal::speak (frame(plan)=16) =====
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
      nop
      jr $ra
[EMITTER] ===== END ASM for Animal::speak =====
[EMITTER] fn=Dog::constructor frame_size(plan)=16 has_calls=False
[EMITTER]   s_regs_in_use=[]
[EMITTER]   params=['this', 'n']
[EMITTER]   local_off={}
[EMITTER]   param_home_off={0: -4, 1: -8}
[EMITTER]   need_param_homes=2
[EMITTER]   most_neg_offset=-8
[EMITTER]   frame_bytes(final)=256
[EMITTER] ===== ASM for Dog::constructor (frame(plan)=16) =====
    Dog__constructor:
      addiu $sp, $sp, -256
      sw $fp, 0($sp)
      sw $ra, 4($sp)
      addiu $fp, $sp, 256
      sw $a0, -4($fp)
      sw $a1, -8($fp)
    Dog__constructor__L0:
      lw $t0, -4($fp)
      lw $t1, -8($fp)
      sw $t1, 0($t0)
    Dog__constructor__epilogue:
      lw $fp, 0($sp)
      lw $ra, 4($sp)
      addiu $sp, $sp, 256
      beq $ra, $zero, __cps_halt
      nop
      jr $ra
[EMITTER] ===== END ASM for Dog::constructor =====
[EMITTER] fn=Dog::bark frame_size(plan)=16 has_calls=True
[EMITTER]   s_regs_in_use=[]
[EMITTER]   params=['this']
[EMITTER]   local_off={}
[EMITTER]   param_home_off={0: -4}
[EMITTER]   need_param_homes=1
[EMITTER]   most_neg_offset=-4
[EMITTER]   frame_bytes(final)=256
[EMITTER]   call in Dog::bark -> __mcall__speak (argc=1)
[EMITTER]     flushing names: []
[EMITTER]   call in Dog::bark -> __str_concat (argc=2)
[EMITTER]     flushing names: []
[EMITTER] ===== ASM for Dog::bark (frame(plan)=16) =====
    Dog__bark:
      addiu $sp, $sp, -256
      sw $fp, 0($sp)
      sw $ra, 4($sp)
      addiu $fp, $sp, 256
      sw $a0, -4($fp)
    Dog__bark__L0:
      lw $t0, -4($fp)
      move $a0, $t0
      jal __mcall__speak
      move $t6, $v0
      # caller-save spill t0
      move $a0, $t6
      la $t5, __str_2
      move $a1, $t5
      jal __str_concat
      move $t7, $v0
      # caller-save spill t1
      move $v0, $t7
      j Dog__bark__epilogue
    Dog__bark__epilogue:
      lw $fp, 0($sp)
      lw $ra, 4($sp)
      addiu $sp, $sp, 256
      beq $ra, $zero, __cps_halt
      nop
      jr $ra
[EMITTER] ===== END ASM for Dog::bark =====
[EMITTER] fn=A::constructor frame_size(plan)=16 has_calls=False
[EMITTER]   s_regs_in_use=[]
[EMITTER]   params=['this', 'v']
[EMITTER]   local_off={}
[EMITTER]   param_home_off={0: -4, 1: -8}
[EMITTER]   need_param_homes=2
[EMITTER]   most_neg_offset=-8
[EMITTER]   frame_bytes(final)=256
[EMITTER] ===== ASM for A::constructor (frame(plan)=16) =====
    A__constructor:
      addiu $sp, $sp, -256
      sw $fp, 0($sp)
      sw $ra, 4($sp)
      addiu $fp, $sp, 256
      sw $a0, -4($fp)
      sw $a1, -8($fp)
    A__constructor__L0:
      lw $t0, -4($fp)
      lw $t1, -8($fp)
      sw $t1, 4($t0)
    A__constructor__epilogue:
      lw $fp, 0($sp)
      lw $ra, 4($sp)
      addiu $sp, $sp, 256
      beq $ra, $zero, __cps_halt
      nop
      jr $ra
[EMITTER] ===== END ASM for A::constructor =====
[EMITTER] fn=A::get frame_size(plan)=16 has_calls=False
[EMITTER]   s_regs_in_use=[]
[EMITTER]   params=['this']
[EMITTER]   local_off={}
[EMITTER]   param_home_off={0: -4}
[EMITTER]   need_param_homes=1
[EMITTER]   most_neg_offset=-4
[EMITTER]   frame_bytes(final)=256
[EMITTER] ===== ASM for A::get (frame(plan)=16) =====
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
      nop
      jr $ra
[EMITTER] ===== END ASM for A::get =====
[EMITTER] fn=sumFirstN frame_size(plan)=16 has_calls=False
[EMITTER]   s_regs_in_use=[]
[EMITTER]   params=['arr', 'n']
[EMITTER]   local_off={}
[EMITTER]   param_home_off={0: -4, 1: -8}
[EMITTER]   need_param_homes=2
[EMITTER]   most_neg_offset=-8
[EMITTER]   frame_bytes(final)=256
[EMITTER] ===== ASM for sumFirstN (frame(plan)=16) =====
    sumFirstN:
      addiu $sp, $sp, -256
      sw $fp, 0($sp)
      sw $ra, 4($sp)
      addiu $fp, $sp, 256
      sw $a0, -4($fp)
      sw $a1, -8($fp)
    sumFirstN__L0:
      li $t4, 0
      # store global s
      la $at, s
      sw $t4, 0($at)
      li $t4, 0
      sw $t4, -12($fp)
      j sumFirstN__L1_while_head
    sumFirstN__L1_while_head:
      lw $t0, -12($fp)
      lw $t1, -8($fp)
      slt $t0, $t0, $t1
      move $t6, $t0
      bne $t6, $zero, sumFirstN__L2_while_body
      j sumFirstN__L3_while_end
    sumFirstN__L2_while_body:
      lw $t0, -4($fp)
      lw $t1, -12($fp)
      sll $t3, $t1, 2
      addu $t3, $t0, $t3
      lw $t0, 0($t3)
      move $t7, $t0
      # load global s
      la $at, s
      lw $t0, 0($at)
      addu $t0, $t0, $t7
      move $t8, $t0
      # store global s
      la $at, s
      sw $t8, 0($at)
      lw $t0, -12($fp)
      li $t5, 1
      addu $t0, $t0, $t5
      move $t9, $t0
      sw $t9, -12($fp)
      j sumFirstN__L1_while_head
    sumFirstN__L3_while_end:
      # load global s
      la $at, s
      lw $t0, 0($at)
      move $v0, $t0
      j sumFirstN__epilogue
    sumFirstN__epilogue:
      lw $fp, 0($sp)
      lw $ra, 4($sp)
      addiu $sp, $sp, 256
      beq $ra, $zero, __cps_halt
      nop
      jr $ra
[EMITTER] ===== END ASM for sumFirstN =====
[EMITTER] fn=runAll frame_size(plan)=8 has_calls=True
[EMITTER]   s_regs_in_use=[]
[EMITTER]   params=[]
[EMITTER]   local_off={}
[EMITTER]   param_home_off={}
[EMITTER]   need_param_homes=0
[EMITTER]   most_neg_offset=0
[EMITTER]   frame_bytes(final)=256
[EMITTER]   call in runAll -> pokeArray (argc=0)
[EMITTER]     flushing names: []
[EMITTER]   call in runAll -> sum2 (argc=2)
[EMITTER]     flushing names: []
[EMITTER]   call in runAll -> factorial (argc=1)
[EMITTER]     flushing names: []
[EMITTER]   call in runAll -> fib (argc=1)
[EMITTER]     flushing names: []
[EMITTER]   call in runAll -> outer (argc=1)
[EMITTER]     flushing names: []
[EMITTER]   call in runAll -> sumWithLoops (argc=0)
[EMITTER]     flushing names: []
[EMITTER]   call in runAll -> __mcall__get (argc=1)
[EMITTER]     flushing names: []
[EMITTER]   call in runAll -> checkSwitch (argc=1)
[EMITTER]     flushing names: []
[EMITTER]   call in runAll -> makeMix (argc=0)
[EMITTER]     flushing names: []
[EMITTER]   call in runAll -> sumFirstN (argc=2)
[EMITTER]     flushing names: []
[EMITTER]   call in runAll -> __mcall__bark (argc=1)
[EMITTER]     flushing names: []
[EMITTER]   call in runAll -> __str_eq (argc=2)
[EMITTER]     flushing names: []
[EMITTER] ===== ASM for runAll (frame(plan)=8) =====
    runAll:
      addiu $sp, $sp, -256
      sw $fp, 0($sp)
      sw $ra, 4($sp)
      addiu $fp, $sp, 256
    runAll__L0:
      jal pokeArray
      move $t6, $v0
      # caller-save spill t0
      # load global a
      la $at, a
      lw $t0, 0($at)
      move $a0, $t0
      li $t5, 2
      move $a1, $t5
      jal sum2
      move $t7, $v0
      # caller-save spill t1
      sw $t7, -4($fp)
      li $t4, 6
      move $a0, $t4
      jal factorial
      move $t8, $v0
      # caller-save spill t2
      sw $t8, -8($fp)
      li $t4, 8
      move $a0, $t4
      jal fib
      move $t9, $v0
      # caller-save spill t3
      sw $t9, -12($fp)
      li $t4, 3
      move $a0, $t4
      jal outer
      move $t9, $v0
      # caller-save spill t4
      sw $t9, -16($fp)
      jal sumWithLoops
      move $t9, $v0
      # caller-save spill t5
      sw $t9, -20($fp)
      li $v0, 9
      li $a0, 8
      syscall
      move $t9, $v0
      sw $t9, -24($fp)
      lw $t0, -24($fp)
      move $a0, $t0
      jal __mcall__get
      move $t9, $v0
      # caller-save spill t7
      sw $t9, -28($fp)
      li $t4, 5
      move $a0, $t4
      jal checkSwitch
      move $t9, $v0
      # caller-save spill t8
      sw $t9, -32($fp)
      jal makeMix
      move $t9, $v0
      # caller-save spill t9
      sw $t9, -36($fp)
      lw $t0, -36($fp)
      li $t5, 0
      sll $t3, $t5, 2
      addu $t3, $t0, $t3
      lw $t0, 0($t3)
      move $t9, $t0
      sw $t9, -40($fp)
      # load global xs
      la $at, xs
      lw $t0, 0($at)
      move $a0, $t0
      li $t5, 3
      move $a1, $t5
      jal sumFirstN
      move $t9, $v0
      # caller-save spill t11
      sw $t9, -44($fp)
      # load global d1
      la $at, d1
      lw $t0, 0($at)
      move $a0, $t0
      jal __mcall__bark
      move $t9, $v0
      # caller-save spill t12
      sw $t9, -48($fp)
      lw $t0, -4($fp)
      lw $t1, -8($fp)
      addu $t0, $t0, $t1
      move $t9, $t0
      lw $t0, -12($fp)
      addu $t0, $t9, $t0
      move $t9, $t0
      lw $t0, -16($fp)
      addu $t0, $t9, $t0
      move $t9, $t0
      lw $t0, -20($fp)
      addu $t0, $t9, $t0
      move $t9, $t0
      lw $t0, -28($fp)
      addu $t0, $t9, $t0
      move $t9, $t0
      lw $t0, -32($fp)
      addu $t0, $t9, $t0
      move $t9, $t0
      lw $t0, -44($fp)
      addu $t0, $t9, $t0
      move $t9, $t0
      sw $t9, -52($fp)
      lw $t0, -48($fp)
      move $a0, $t0
      la $t5, __str_3
      move $a1, $t5
      jal __str_eq
      move $t9, $v0
      # caller-save spill t20
      bne $t9, $zero, runAll__L1_then
      j runAll__L2_end
    runAll__L1_then:
[EMITTER]   ... <truncated> ...
[EMITTER] ===== END ASM for runAll =====

--- MIPS ASM ---
.data
PI: .word 0
a: .word 0
b: .word 0
s: .word 0
t: .word 0
xs: .word 0
ys: .word 0
grid: .word 0
g11: .word 0
sumNum: .word 0
prod: .word 0
rest: .word 0
modOk: .word 0
flag: .word 0
tern: .word 0
d1: .word 0
d2: .word 0
pack: .word 0
firstVoice: .word 0
FINAL: .word 0
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
  # store global PI
  la $at, PI
  sw $t4, 0($at)
  li $t4, 3
  # store global a
  la $at, a
  sw $t4, 0($at)
  # load global a
  la $at, a
  lw $t0, 0($at)
  # store global b
  la $at, b
  sw $t0, 0($at)
  la $t4, __str_0
  # store global s
  la $at, s
  sw $t4, 0($at)
  # load global s
  la $at, s
  lw $t0, 0($at)
  move $a0, $t0
  la $t5, __str_1
  move $a1, $t5
  jal __str_concat
  move $t6, $v0
  # caller-save spill t0
  # store global t
  la $at, t
  sw $t6, 0($at)
  li $t4, 4
  move $a0, $t4
  jal __new_array
  move $t7, $v0
  # caller-save spill t1
  li $t5, 0
  li $t4, 1
  sll $t3, $t5, 2
  addu $t3, $t7, $t3
  sw $t4, 0($t3)
  li $t5, 1
  li $t4, 2
  sll $t3, $t5, 2
  addu $t3, $t7, $t3
  sw $t4, 0($t3)
  li $t5, 2
  li $t4, 3
  sll $t3, $t5, 2
  addu $t3, $t7, $t3
  sw $t4, 0($t3)
  li $t5, 3
  li $t4, 4
  sll $t3, $t5, 2
  addu $t3, $t7, $t3
  sw $t4, 0($t3)
  # store global xs
  la $at, xs
  sw $t7, 0($at)
  li $t4, 3
  move $a0, $t4
  jal __new_array
  move $t8, $v0
  # caller-save spill t2
  li $t5, 0
  li $t4, 0x3F800000
  sll $t3, $t5, 2
  addu $t3, $t8, $t3
  sw $t4, 0($t3)
  li $t5, 1
  li $t4, 0x40000000
  sll $t3, $t5, 2
  addu $t3, $t8, $t3
  sw $t4, 0($t3)
  li $t5, 2
  li $t4, 0x40600000
  sll $t3, $t5, 2
  addu $t3, $t8, $t3
  sw $t4, 0($t3)
  # store global ys
  la $at, ys
  sw $t8, 0($at)
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
  li $t5, 0
  li $t4, 1
  sll $t3, $t5, 2
  addu $t3, $t9, $t3
  sw $t4, 0($t3)
  li $t5, 1
  li $t4, 2
  sll $t3, $t5, 2
  addu $t3, $t9, $t3
  sw $t4, 0($t3)
  li $t5, 0
  sll $t3, $t5, 2
  addu $t3, $t9, $t3
  sw $t9, 0($t3)
  li $t4, 2
  move $a0, $t4
  jal __new_array
  move $t9, $v0
  # caller-save spill t5
  li $t5, 0
  li $t4, 3
  sll $t3, $t5, 2
  addu $t3, $t9, $t3
  sw $t4, 0($t3)
  li $t5, 1
  li $t4, 4
  sll $t3, $t5, 2
  addu $t3, $t9, $t3
  sw $t4, 0($t3)
  li $t5, 1
  sll $t3, $t5, 2
  addu $t3, $t9, $t3
  sw $t9, 0($t3)
  # store global grid
  la $at, grid
  sw $t9, 0($at)
  # load global grid
  la $at, grid
  lw $t0, 0($at)
  li $t5, 1
  sll $t3, $t5, 2
  addu $t3, $t0, $t3
  lw $t0, 0($t3)
  move $t9, $t0
  li $t5, 1
  sll $t3, $t5, 2
  addu $t3, $t9, $t3
  lw $t0, 0($t3)
  move $t9, $t0
  # store global g11
  la $at, g11
  sw $t9, 0($at)
  li $t4, 0x3F800000
  # load global a
  la $at, a
  lw $t0, 0($at)
  mtc1 $t4, $f0
  mtc1 $t0, $f1
  add.s $f2, $f0, $f1
  mfc1 $t0, $f2
  move $t9, $t0
  # store global sumNum
  la $at, sumNum
  sw $t9, 0($at)
  # load global a
  la $at, a
  lw $t0, 0($at)
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
  # store global prod
  la $at, prod
  sw $t9, 0($at)
  li $t4, 10
  li $t5, 7
  mtc1 $t4, $f0
  mtc1 $t5, $f1
  sub.s $f2, $f0, $f1
  mfc1 $t0, $f2
  move $t9, $t0
  # store global rest
  la $at, rest
  sw $t9, 0($at)
  li $t4, 0x40A00000
  li $t5, 2
  div $t4, $t5
  mfhi $t0
  move $t9, $t0
  # store global modOk
  la $at, modOk
  sw $t9, 0($at)
  # load global a
  la $at, a
  lw $t0, 0($at)
  li $t5, 10
  slt $t0, $t0, $t5
  move $t9, $t0
  # load global s
  la $at, s
  lw $t0, 0($at)
  move $a0, $t0
  la $t5, __str_0
  move $a1, $t5
  jal __str_eq
  move $t9, $v0
  # caller-save spill t14
  and $t0, $t9, $t9
  move $t9, $t0
  li $t4, 0
  sltiu $t0, $t4, 1
  move $t9, $t0
  or $t0, $t9, $t9
  move $t9, $t0
  # store global flag
  la $at, flag
  sw $t9, 0($at)
  # load global a
  la $at, a
  lw $t0, 0($at)
  li $t5, 0
  slt $t0, $t5, $t0
  move $t9, $t0
  bne $t9, $zero, main__L1_then
  j main__L2_else
main__L1_then:
  # load global a
  la $at, a
  lw $t0, 0($at)
  move $t9, $t0
  j main__L3_end
main__L2_else:
  li $t4, 0
  move $t9, $t4
  j main__L3_end
main__L3_end:
  # store global tern
  la $at, tern
  sw $t9, 0($at)
  li $v0, 9
  li $a0, 4
  syscall
  move $t9, $v0
  # store global d1
  la $at, d1
  sw $t9, 0($at)
  li $v0, 9
  li $a0, 4
  syscall
  move $t9, $v0
  # store global d2
  la $at, d2
  sw $t9, 0($at)
  li $t4, 2
  move $a0, $t4
  jal __new_array
  move $t9, $v0
  # caller-save spill t22
  li $t5, 0
  # load global d1
  la $at, d1
  lw $t0, 0($at)
  sll $t3, $t5, 2
  addu $t3, $t9, $t3
  sw $t0, 0($t3)
  li $t5, 1
  # load global d2
  la $at, d2
  lw $t0, 0($at)
  sll $t3, $t5, 2
  addu $t3, $t9, $t3
  sw $t0, 0($t3)
  # store global pack
  la $at, pack
  sw $t9, 0($at)
  # load global pack
  la $at, pack
  lw $t0, 0($at)
  li $t5, 0
  sll $t3, $t5, 2
  addu $t3, $t0, $t3
  lw $t0, 0($t3)
  move $t9, $t0
  move $a0, $t9
  jal __mcall__bark
  move $t9, $v0
  # caller-save spill t24
  # store global firstVoice
  la $at, firstVoice
  sw $t9, 0($at)
  jal runAll
  move $t9, $v0
  # caller-save spill t25
  # store global FINAL
  la $at, FINAL
  sw $t9, 0($at)
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
  li $t5, 0
  li $t4, 1
  sll $t3, $t5, 2
  addu $t3, $t6, $t3
  sw $t4, 0($t3)
  li $t5, 1
  li $t4, 0x40000000
  sll $t3, $t5, 2
  addu $t3, $t6, $t3
  sw $t4, 0($t3)
  li $t5, 2
  li $t4, 3
  sll $t3, $t5, 2
  addu $t3, $t6, $t3
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
  nop
  jr $ra

pokeArray:
  addiu $sp, $sp, -256
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 256
pokeArray__L0:
  # load global xs
  la $at, xs
  lw $t0, 0($at)
  li $t5, 0
  li $t4, 42
  sll $t3, $t5, 2
  addu $t3, $t0, $t3
  sw $t4, 0($t3)
  # load global ys
  la $at, ys
  lw $t0, 0($at)
  li $t5, 1
  sll $t3, $t5, 2
  addu $t3, $t0, $t3
  lw $t0, 0($t3)
  move $t6, $t0
  li $t5, 0x3F000000
  mtc1 $t6, $f0
  mtc1 $t5, $f1
  add.s $f2, $f0, $f1
  mfc1 $t0, $f2
  move $t7, $t0
  # load global ys
  la $at, ys
  lw $t0, 0($at)
  li $t5, 1
  sll $t3, $t5, 2
  addu $t3, $t0, $t3
  sw $t7, 0($t3)
pokeArray__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 256
  beq $ra, $zero, __cps_halt
  nop
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
  nop
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
  nop
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
  nop
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
  move $a0, $t4
  jal inner
  move $t6, $v0
  # caller-save spill t0
  move $v0, $t6
  j outer__epilogue
outer__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 256
  beq $ra, $zero, __cps_halt
  nop
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
  # load global xs
  la $at, xs
  lw $t0, 0($at)
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
  sw $t4, -12($fp)
sumWithLoops__L4_do_body:
  lw $t0, -4($fp)
  lw $t1, -12($fp)
  addu $t0, $t0, $t1
  move $t9, $t0
  sw $t9, -4($fp)
  lw $t0, -12($fp)
  li $t5, 1
  addu $t0, $t0, $t5
  move $t9, $t0
  sw $t9, -12($fp)
sumWithLoops__L5_do_head:
  lw $t0, -12($fp)
  li $t5, 2
  slt $t0, $t0, $t5
  move $t9, $t0
  bne $t9, $zero, sumWithLoops__L4_do_body
  j sumWithLoops__L6_do_end
sumWithLoops__L6_do_end:
  li $t4, 0
  sw $t4, -16($fp)
  j sumWithLoops__L7_while_head
sumWithLoops__L7_while_head:
  lw $t0, -16($fp)
  li $t5, 3
  slt $t0, $t0, $t5
  move $t9, $t0
  bne $t9, $zero, sumWithLoops__L8_while_body
  j sumWithLoops__L9_while_end
sumWithLoops__L8_while_body:
  lw $t0, -16($fp)
  li $t5, 1
  seq $t0, $t0, $t5
  move $t9, $t0
  bne $t9, $zero, sumWithLoops__L10_then
  j sumWithLoops__L11_end
sumWithLoops__L10_then:
  lw $t0, -16($fp)
  li $t5, 1
  addu $t0, $t0, $t5
  move $t9, $t0
  sw $t9, -16($fp)
  j sumWithLoops__L7_while_head
  j sumWithLoops__L11_end
sumWithLoops__L11_end:
  lw $t0, -16($fp)
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
  lw $t1, -16($fp)
  addu $t0, $t0, $t1
  move $t9, $t0
  sw $t9, -4($fp)
  lw $t0, -16($fp)
  li $t5, 1
  addu $t0, $t0, $t5
  move $t9, $t0
  sw $t9, -16($fp)
  j sumWithLoops__L7_while_head
sumWithLoops__L9_while_end:
  li $t4, 0
  sw $t4, -20($fp)
  j sumWithLoops__L14_while_head
sumWithLoops__L14_while_head:
  lw $t0, -20($fp)
  li $t5, 4
  slt $t0, $t0, $t5
  move $t9, $t0
  bne $t9, $zero, sumWithLoops__L15_while_body
  j sumWithLoops__L16_while_end
sumWithLoops__L15_while_body:
  # load global xs
  la $at, xs
  lw $t0, 0($at)
  lw $t1, -20($fp)
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  lw $t0, 0($t3)
  move $t9, $t0
  lw $t0, -4($fp)
  addu $t0, $t0, $t9
  move $t9, $t0
  sw $t9, -4($fp)
  lw $t0, -20($fp)
  li $t5, 1
  addu $t0, $t0, $t5
  move $t9, $t0
  sw $t9, -20($fp)
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
  nop
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
  nop
  jr $ra

Animal__constructor:
  addiu $sp, $sp, -256
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 256
  sw $a0, -4($fp)
  sw $a1, -8($fp)
Animal__constructor__L0:
  lw $t0, -4($fp)
  lw $t1, -8($fp)
  sw $t1, 0($t0)
Animal__constructor__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 256
  beq $ra, $zero, __cps_halt
  nop
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
  nop
  jr $ra

Dog__constructor:
  addiu $sp, $sp, -256
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 256
  sw $a0, -4($fp)
  sw $a1, -8($fp)
Dog__constructor__L0:
  lw $t0, -4($fp)
  lw $t1, -8($fp)
  sw $t1, 0($t0)
Dog__constructor__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 256
  beq $ra, $zero, __cps_halt
  nop
  jr $ra

Dog__bark:
  addiu $sp, $sp, -256
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 256
  sw $a0, -4($fp)
Dog__bark__L0:
  lw $t0, -4($fp)
  move $a0, $t0
  jal __mcall__speak
  move $t6, $v0
  # caller-save spill t0
  move $a0, $t6
  la $t5, __str_2
  move $a1, $t5
  jal __str_concat
  move $t7, $v0
  # caller-save spill t1
  move $v0, $t7
  j Dog__bark__epilogue
Dog__bark__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 256
  beq $ra, $zero, __cps_halt
  nop
  jr $ra

A__constructor:
  addiu $sp, $sp, -256
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 256
  sw $a0, -4($fp)
  sw $a1, -8($fp)
A__constructor__L0:
  lw $t0, -4($fp)
  lw $t1, -8($fp)
  sw $t1, 4($t0)
A__constructor__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 256
  beq $ra, $zero, __cps_halt
  nop
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
  nop
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
  # store global s
  la $at, s
  sw $t4, 0($at)
  li $t4, 0
  sw $t4, -12($fp)
  j sumFirstN__L1_while_head
sumFirstN__L1_while_head:
  lw $t0, -12($fp)
  lw $t1, -8($fp)
  slt $t0, $t0, $t1
  move $t6, $t0
  bne $t6, $zero, sumFirstN__L2_while_body
  j sumFirstN__L3_while_end
sumFirstN__L2_while_body:
  lw $t0, -4($fp)
  lw $t1, -12($fp)
  sll $t3, $t1, 2
  addu $t3, $t0, $t3
  lw $t0, 0($t3)
  move $t7, $t0
  # load global s
  la $at, s
  lw $t0, 0($at)
  addu $t0, $t0, $t7
  move $t8, $t0
  # store global s
  la $at, s
  sw $t8, 0($at)
  lw $t0, -12($fp)
  li $t5, 1
  addu $t0, $t0, $t5
  move $t9, $t0
  sw $t9, -12($fp)
  j sumFirstN__L1_while_head
sumFirstN__L3_while_end:
  # load global s
  la $at, s
  lw $t0, 0($at)
  move $v0, $t0
  j sumFirstN__epilogue
sumFirstN__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 256
  beq $ra, $zero, __cps_halt
  nop
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
  # load global a
  la $at, a
  lw $t0, 0($at)
  move $a0, $t0
  li $t5, 2
  move $a1, $t5
  jal sum2
  move $t7, $v0
  # caller-save spill t1
  sw $t7, -4($fp)
  li $t4, 6
  move $a0, $t4
  jal factorial
  move $t8, $v0
  # caller-save spill t2
  sw $t8, -8($fp)
  li $t4, 8
  move $a0, $t4
  jal fib
  move $t9, $v0
  # caller-save spill t3
  sw $t9, -12($fp)
  li $t4, 3
  move $a0, $t4
  jal outer
  move $t9, $v0
  # caller-save spill t4
  sw $t9, -16($fp)
  jal sumWithLoops
  move $t9, $v0
  # caller-save spill t5
  sw $t9, -20($fp)
  li $v0, 9
  li $a0, 8
  syscall
  move $t9, $v0
  sw $t9, -24($fp)
  lw $t0, -24($fp)
  move $a0, $t0
  jal __mcall__get
  move $t9, $v0
  # caller-save spill t7
  sw $t9, -28($fp)
  li $t4, 5
  move $a0, $t4
  jal checkSwitch
  move $t9, $v0
  # caller-save spill t8
  sw $t9, -32($fp)
  jal makeMix
  move $t9, $v0
  # caller-save spill t9
  sw $t9, -36($fp)
  lw $t0, -36($fp)
  li $t5, 0
  sll $t3, $t5, 2
  addu $t3, $t0, $t3
  lw $t0, 0($t3)
  move $t9, $t0
  sw $t9, -40($fp)
  # load global xs
  la $at, xs
  lw $t0, 0($at)
  move $a0, $t0
  li $t5, 3
  move $a1, $t5
  jal sumFirstN
  move $t9, $v0
  # caller-save spill t11
  sw $t9, -44($fp)
  # load global d1
  la $at, d1
  lw $t0, 0($at)
  move $a0, $t0
  jal __mcall__bark
  move $t9, $v0
  # caller-save spill t12
  sw $t9, -48($fp)
  lw $t0, -4($fp)
  lw $t1, -8($fp)
  addu $t0, $t0, $t1
  move $t9, $t0
  lw $t0, -12($fp)
  addu $t0, $t9, $t0
  move $t9, $t0
  lw $t0, -16($fp)
  addu $t0, $t9, $t0
  move $t9, $t0
  lw $t0, -20($fp)
  addu $t0, $t9, $t0
  move $t9, $t0
  lw $t0, -28($fp)
  addu $t0, $t9, $t0
  move $t9, $t0
  lw $t0, -32($fp)
  addu $t0, $t9, $t0
  move $t9, $t0
  lw $t0, -44($fp)
  addu $t0, $t9, $t0
  move $t9, $t0
  sw $t9, -52($fp)
  lw $t0, -48($fp)
  move $a0, $t0
  la $t5, __str_3
  move $a1, $t5
  jal __str_eq
  move $t9, $v0
  # caller-save spill t20
  bne $t9, $zero, runAll__L1_then
  j runAll__L2_end
runAll__L1_then:
  lw $t0, -52($fp)
  li $t5, 1
  addu $t0, $t0, $t5
  move $t9, $t0
  sw $t9, -52($fp)
  j runAll__L2_end
runAll__L2_end:
  lw $t0, -52($fp)
  move $v0, $t0
  j runAll__epilogue
runAll__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 256
  beq $ra, $zero, __cps_halt
  nop
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


# --- Runtime de strings ---
__str_eq:
  # a0 = s1, a1 = s2
  move $t0, $a0          # ptr s1
  move $t1, $a1          # ptr s2
__str_eq_loop:
  lbu  $t2, 0($t0)
  lbu  $t3, 0($t1)
  bne  $t2, $t3, __str_eq_not
  beq  $t2, $zero, __str_eq_yes   # ambos son '\0'
  addiu $t0, $t0, 1
  addiu $t1, $t1, 1
  j    __str_eq_loop
__str_eq_yes:
  li   $v0, 1
  jr   $ra
__str_eq_not:
  li   $v0, 0
  jr   $ra

__str_concat:
  # a0 = s1, a1 = s2
  move $t0, $a0          # s1
  move $t1, $a1          # s2
  # len(s1) en t2
  move $t4, $t0
  li   $t2, 0
__str_len1_loop:
  lbu  $t5, 0($t4)
  beq  $t5, $zero, __str_len1_done
  addiu $t2, $t2, 1
  addiu $t4, $t4, 1
  j    __str_len1_loop
__str_len1_done:
  # len(s2) en t3
  move $t4, $t1
  li   $t3, 0
__str_len2_loop:
  lbu  $t5, 0($t4)
  beq  $t5, $zero, __str_len2_done
  addiu $t3, $t3, 1
  addiu $t4, $t4, 1
  j    __str_len2_loop
__str_len2_done:
  # total = len1 + len2 + 1 (para '\0') en t6
  addu $t6, $t2, $t3
  addiu $t6, $t6, 1
  # pedir memoria con sbrk
  li   $v0, 9
  move $a0, $t6
  syscall
  move $t7, $v0          # dst
  move $t4, $t7          # cursor de escritura
  # copiar s1
  move $t8, $t0
__str_copy1_loop:
  lbu  $t5, 0($t8)
  beq  $t5, $zero, __str_copy1_done
  sb   $t5, 0($t4)
  addiu $t8, $t8, 1
  addiu $t4, $t4, 1
  j    __str_copy1_loop
__str_copy1_done:
  # copiar s2
  move $t8, $t1
__str_copy2_loop:
  lbu  $t5, 0($t8)
  beq  $t5, $zero, __str_copy2_done
  sb   $t5, 0($t4)
  addiu $t8, $t8, 1
  addiu $t4, $t4, 1
  j    __str_copy2_loop
__str_copy2_done:
  # terminador nulo
  sb   $zero, 0($t4)
  move $v0, $t7
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


# --- Auto-generated stubs for missing functions ---
inner:
  # Auto-generated stub: returns its first argument (a0) unchanged
  addiu $sp, $sp, -16
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 16
  sw $a0, -4($fp)
inner__L0:
  lw $t0, -4($fp)
  move $v0, $t0
  j inner__epilogue
inner__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 16
  beq $ra, $zero, __cps_halt
  nop
  jr $ra
MARS 4.5  Copyright 2003-2014 Pete Sanderson and Kenneth Vollmar

