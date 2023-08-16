SHELL = /usr/bin/env sh
PYTHON = /usr/bin/env python3
CPUEMULATOR = $(SHELL) ../../tools/CPUEmulator.sh
VMTRANSLATOR = $(PYTHON) ./VMTranslator.py

.PHONY: build test clean

build:
	$(VMTRANSLATOR) ./ProgramFlow/BasicLoop/ --debug
	$(VMTRANSLATOR) ./ProgramFlow/FibonacciSeries/ --debug
	$(VMTRANSLATOR) ./FunctionCalls/SimpleFunction/ --debug
	$(VMTRANSLATOR) ./FunctionCalls/NestedCall/ --debug
	$(VMTRANSLATOR) ./FunctionCalls/FibonacciElement/ --bootstrap --debug
	$(VMTRANSLATOR) ./FunctionCalls/StaticsTest/ --bootstrap --debug

test: build
	$(CPUEMULATOR) ./ProgramFlow/BasicLoop/BasicLoop.tst
	$(CPUEMULATOR) ./ProgramFlow/FibonacciSeries/FibonacciSeries.tst
	$(CPUEMULATOR) ./FunctionCalls/SimpleFunction/SimpleFunction.tst
	$(CPUEMULATOR) ./FunctionCalls/NestedCall/NestedCall.tst
	$(CPUEMULATOR) ./FunctionCalls/FibonacciElement/FibonacciElement.tst
	$(CPUEMULATOR) ./FunctionCalls/StaticsTest/StaticsTest.tst

clean:
	find . -name '*.asm' -exec rm -f {} +
