// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Put your code here.
(LOOP)
    @KBD
    D=M
    @DRAW_WHITE
    D;JEQ       // If RAM[KBD] == 0, goto DRAW_WHITE
    @DRAW_BLACK
    0;JMP       // Else, goto DRAW_BLACK

(DRAW_WHITE)
    @i
    M=0         // i = 0

(LOOP_WHITE)
    @i
    D=M
    @8192
    D=D-A
    @LOOP
    D;JGE       // If i >= 8192, goto LOOP

    @i
    D=M
    @SCREEN
    A=A+D
    M=0         // Set to white

    @i
    M=M+1       // i = i + 1
    @LOOP_WHITE
    0;JMP

(DRAW_BLACK)
    @i
    M=0         // i = 0

(LOOP_BLACK)
    @i
    D=M
    @8192
    D=D-A
    @LOOP
    D;JGE       // If i >= 8192, goto LOOP

    @i
    D=M
    @SCREEN
    A=A+D
    M=-1        // Set to black

    @i
    M=M+1       // i = i + 1
    @LOOP_BLACK
    0;JMP