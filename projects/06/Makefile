SHELL = /usr/bin/env sh
PYTHON = /usr/bin/env python3
MV = /usr/bin/env mv
CMP = /usr/bin/env cmp
ASSEMBLER = $(PYTHON) ./Assembler.py
SUPPLIED_ASSEMBLER = $(SHELL) ../../tools/Assembler.sh

.PHONY: build build_cmp test clean

build:
	$(ASSEMBLER) ./add/Add.asm --output ./add/Add.hack
	$(ASSEMBLER) ./max/Max.asm --output ./max/Max.hack
	$(ASSEMBLER) ./max/MaxL.asm --output ./max/MaxL.hack
	$(ASSEMBLER) ./pong/Pong.asm --output ./pong/Pong.hack
	$(ASSEMBLER) ./pong/PongL.asm --output ./pong/PongL.hack
	$(ASSEMBLER) ./rect/Rect.asm --output ./rect/Rect.hack
	$(ASSEMBLER) ./rect/RectL.asm --output ./rect/RectL.hack

build_cmp:
	$(SUPPLIED_ASSEMBLER) add/Add.asm && $(MV) ./add/Add.hack ./add/Add.cmp
	$(SUPPLIED_ASSEMBLER) max/Max.asm && $(MV) ./max/Max.hack ./max/Max.cmp
	$(SUPPLIED_ASSEMBLER) max/MaxL.asm && $(MV) ./max/MaxL.hack ./max/MaxL.cmp
	$(SUPPLIED_ASSEMBLER) pong/Pong.asm && $(MV) ./pong/Pong.hack ./pong/Pong.cmp
	$(SUPPLIED_ASSEMBLER) pong/PongL.asm && $(MV) ./pong/PongL.hack ./pong/PongL.cmp
	$(SUPPLIED_ASSEMBLER) rect/Rect.asm && $(MV) ./rect/Rect.hack ./rect/Rect.cmp
	$(SUPPLIED_ASSEMBLER) rect/RectL.asm && $(MV) ./rect/RectL.hack ./rect/RectL.cmp

test: build_cmp build
	$(CMP) ./add/Add.hack ./add/Add.cmp
	$(CMP) ./max/Max.hack ./max/Max.cmp
	$(CMP) ./max/MaxL.hack ./max/MaxL.cmp
	$(CMP) ./pong/Pong.hack ./pong/Pong.cmp
	$(CMP) ./pong/PongL.hack ./pong/PongL.cmp
	$(CMP) ./rect/Rect.hack ./rect/Rect.cmp
	$(CMP) ./rect/RectL.hack ./rect/RectL.cmp

clean:
	find . -name '*.hack' -exec rm -f {} +
	find . -name '*.cmp' -exec rm -f {} +
