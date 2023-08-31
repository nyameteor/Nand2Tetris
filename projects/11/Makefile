SHELL = /usr/bin/env sh
PYTHON = /usr/bin/env python3
COMPILER = $(PYTHON) JackCompiler.py

.PHONY: build clean

build:
	$(COMPILER) Seven
	$(COMPILER) ConvertToBin
	$(COMPILER) Square
	$(COMPILER) Average
	$(COMPILER) Pong
	$(COMPILER) ComplexArrays

clean:
	find . -name '*.vm' -exec rm -f {} +
	find . -name '*.cmp' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +
