SHELL = /usr/bin/env sh
PYTHON = /usr/bin/env python3
ASSEMBLER = $(PYTHON) ./Assembler.py
SUPPLIED_ASSEMBLER = $(SHELL) ../../tools/Assembler.sh

.PHONY: build build_compare compare clean

build:
	$(ASSEMBLER) ./add/Add.asm --output ./add/Add.hack
	$(ASSEMBLER) ./max/Max.asm --output ./max/Max.hack
	$(ASSEMBLER) ./max/MaxL.asm --output ./max/MaxL.hack
	$(ASSEMBLER) ./pong/Pong.asm --output ./pong/Pong.hack
	$(ASSEMBLER) ./pong/PongL.asm --output ./pong/PongL.hack
	$(ASSEMBLER) ./rect/Rect.asm --output ./rect/Rect.hack
	$(ASSEMBLER) ./rect/RectL.asm --output ./rect/RectL.hack

build_compare:
	$(SUPPLIED_ASSEMBLER) add/Add.asm && mv ./add/Add.hack ./add/Add.cmp
	$(SUPPLIED_ASSEMBLER) max/Max.asm && mv ./max/Max.hack ./max/Max.cmp
	$(SUPPLIED_ASSEMBLER) max/MaxL.asm && mv ./max/MaxL.hack ./max/MaxL.cmp
	$(SUPPLIED_ASSEMBLER) pong/Pong.asm && mv ./pong/Pong.hack ./pong/Pong.cmp
	$(SUPPLIED_ASSEMBLER) pong/PongL.asm && mv ./pong/PongL.hack ./pong/PongL.cmp
	$(SUPPLIED_ASSEMBLER) rect/Rect.asm && mv ./rect/Rect.hack ./rect/Rect.cmp
	$(SUPPLIED_ASSEMBLER) rect/RectL.asm && mv ./rect/RectL.hack ./rect/RectL.cmp

compare: build_compare build
	cmp ./add/Add.hack ./add/Add.cmp
	cmp ./max/Max.hack ./max/Max.cmp
	cmp ./max/MaxL.hack ./max/MaxL.cmp
	cmp ./pong/Pong.hack ./pong/Pong.cmp
	cmp ./pong/PongL.hack ./pong/PongL.cmp
	cmp ./rect/Rect.hack ./rect/Rect.cmp
	cmp ./rect/RectL.hack ./rect/RectL.cmp

clean:
	find . -name '*.hack' -exec rm -f {} +
	find . -name '*.cmp' -exec rm -f {} +
