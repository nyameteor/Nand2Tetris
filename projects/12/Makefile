SHELL = /usr/bin/env sh
COMPILER = $(SHELL) ../../tools/JackCompiler.sh

.PHONY: build clean

build: clean
	cp Math.jack MathTest/Math.jack \
		&& $(COMPILER) MathTest
	cp Memory.jack MemoryTest/Memory.jack \
		&& $(COMPILER) MemoryTest
	cp Memory.jack MemoryTest/MemoryDiag/Memory.jack \
		&& $(COMPILER) MemoryTest/MemoryDiag
	cp Screen.jack ScreenTest/Screen.jack \
		&& cp Math.jack ScreenTest/Math.jack \
		&& $(COMPILER) ScreenTest
	cp Output.jack OutputTest/Output.jack \
		&& cp Math.jack OutputTest/Math.jack \
		&& $(COMPILER) OutputTest
	cp Keyboard.jack KeyboardTest/Keyboard.jack \
		&& $(COMPILER) KeyboardTest
	cp String.jack StringTest/String.jack \
		&& $(COMPILER) StringTest
	cp Array.jack ArrayTest/Array.jack \
		&& $(COMPILER) ArrayTest
	cp Sys.jack SysTest/Sys.jack \
		&& $(COMPILER) SysTest
	cp Math.jack ../11/Pong/Math.jack \
		&& cp Memory.jack ../11/Pong/Memory.jack \
		&& cp Screen.jack ../11/Pong/Screen.jack \
		&& cp Output.jack ../11/Pong/Output.jack \
		&& cp Keyboard.jack ../11/Pong/Keyboard.jack \
		&& cp String.jack ../11/Pong/String.jack \
		&& cp Array.jack ../11/Pong/Array.jack \
		&& cp Sys.jack ../11/Pong/Sys.jack \
		&& $(COMPILER) ../11/Pong

clean:
	rm -f MathTest/Math.jack
	rm -f MemoryTest/Memory.jack
	rm -f MemoryTest/MemoryDiag/Memory.jack
	rm -f ScreenTest/Screen.jack \
		&& rm -f ScreenTest/Math.jack
	rm -f OutputTest/Output.jack \
		&& rm -f OutputTest/Math.jack
	rm -f KeyboardTest/Keyboard.jack
	rm -f StringTest/String.jack
	rm -f ArrayTest/Array.jack
	rm -f SysTest/Sys.jack
	rm -f ../11/Pong/Math.jack \
		&& rm -f ../11/Pong/Memory.jack \
		&& rm -f ../11/Pong/Screen.jack \
		&& rm -f ../11/Pong/Output.jack \
		&& rm -f ../11/Pong/Keyboard.jack \
		&& rm -f ../11/Pong/String.jack \
		&& rm -f ../11/Pong/Array.jack \
		&& rm -f ../11/Pong/Sys.jack
	find . -name '*.vm' -exec rm -f {} +
	find ../11/Pong -name '*.vm' -exec rm -f {} +
