// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)
//
// This program only needs to handle arguments that satisfy
// R0 >= 0, R1 >= 0, and R0*R1 < 32768.

// Put your code here.
    @res
    M=0     // res = 0

    @i
    M=0     // i = 0

(LOOP)
    @i
    D=M
    @R1
    D=D-M
    @STOP
    D;JGE   // If (i-R1) >= 0 goto STOP

    @R0
    D=M
    @res
    M=M+D   // res = res + R0

    @i
    M=M+1   // i = i + 1
    @LOOP
    0;JMP   // Goto LOOP

(STOP)
    @res
    D=M
    @R2
    M=D     // R2 = res

(END)
    @END
    0;JMP   // Infinite loop