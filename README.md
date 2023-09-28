# Nand2Tetris

This is my coursework for self-studying Nand2Tetris.
For an overview of the course, please see the [course website](https://www.nand2tetris.org/).

## Course Resources

- Course Website:
  https://www.nand2tetris.org/

- Nand2Tetris Part I:
  https://www.coursera.org/learn/build-a-computer

- Nand2Tetris Part II:
  https://www.coursera.org/learn/nand2tetris2

## Coursework Progress

| Name                                     | Status    |
| ---------------------------------------- | --------- |
| Project 1: Boolean Logic                 | Completed |
| Project 2: Boolean Arithmetic            | Completed |
| Project 3: Sequential Logic              | Completed |
| Project 4: Machine Language              | Completed |
| Project 5: Computer Architecture         | Completed |
| Project 6: Assembler                     | Completed |
| Project 7: VM I: Stack Arithmetic        | Completed |
| Project 8: VM II: Program Control        | Completed |
| Project 9: High-Level Language           | Completed |
| Project 10: Compiler I: Syntax Analysis  | Completed |
| Project 11: Compiler II: Code Generation | Completed |
| Project 12: Operating System             | Completed |

## Usage

For simplicity, I didn't upload the software tools (the `tools` directory) to this repository,
which contains emulators for the Hack computer and many useful tools.
If you want to run simulations on the Hack computer, please download the necessary tools from [the software page](https://www.nand2tetris.org/software).

### The Hack Assembler

Source code: [projects/06/Assembler.py](projects/06/Assembler.py)

```sh
cd projects/06

# Translate the examples.
make build

# Compare the translated results with the supplied assembler.
make compare

# Clean files.
make clean
```

### The VM-to-Hack Translator

Source code: [projects/08/VMTranslator.py](projects/08/VMTranslator.py)

```sh
cd projects/08

# Translate the examples.
make build

# Run tests on CPU Emulator.
make test

# Clean files.
make clean
```

### The Jack Compiler

Source code: [projects/11/JackCompiler.py](projects/11/JackCompiler.py)

This compiler implementation is intended to be fully compatible with the supplied Jack compiler,
which means it will generate the same VM code as the supplied compiler for the same source code.
But now, it only gives the similar error messages during lexical analysis,
and lacks user-friendly error messages during syntactic analysis.

```sh
cd projects/11

# Compile the examples.
make build

# This project has no test scripts, so we need to do manual testing.
# To test the compiler implementation, we can execute the Pong game in the
# supplied VM Emulator:
# 1. Start the VM Emulator:
sh ../../tools/VMEmulator.sh
# 2. Load the program "projects/11/Pong".
# 3. change the "Animate" setting to "No animation".
# 4. Run the game to see if it works.

# Clean files.
make clean
```

### The Jack OS

Source code: [projects/12](projects/12)

```sh
cd projects/12

# Build Jack OS and compile the examples.
make build

# This project has no test scripts, so we need to do manual testing.
# To test the entire OS implementation, we can execute the Pong game in the
# supplied VM Emulator, just like how we tested the Jack compiler.

# Clean files.
make clean
```
