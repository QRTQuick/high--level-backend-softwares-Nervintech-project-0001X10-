    .text
    .global asm_jitter
    .type asm_jitter, @function

asm_jitter:
    movq %rdi, %rax
    movabsq $0x9e3779b97f4a7c15, %rcx
    xorq %rcx, %rax
    rolq $13, %rax
    xorq %rdi, %rax
    ret
