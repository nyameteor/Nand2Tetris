#!/usr/bin/env python3

import argparse
import re
from enum import Enum
from pathlib import Path
from typing import TextIO


def main():
    argparser = argparse.ArgumentParser(
        description='The Hack assembler'
    )
    argparser.add_argument('file', metavar='FILE')
    argparser.add_argument('-o',  metavar='FILE',
                           dest='output_file', help='write output to FILE')
    args = argparser.parse_args()

    cwd = Path.cwd()
    src_file = cwd.joinpath(args.file)
    if args.output_file:
        dst_file = cwd.joinpath(args.output_file)
    else:
        dst_file = cwd.joinpath(src_file.name.replace('.asm', '.hack'))
    with open(file=src_file, mode='r', encoding='utf-8') as src, \
            open(file=dst_file, mode='w', encoding='utf-8') as dst:
        assembler = Assembler(src=src)
        assembler.translate(dst=dst)


class Assembler():
    def __init__(self, src: TextIO) -> None:
        self.symbolTable = SymbolTable()
        self.parser = Parser(f=src)

    def translate(self, dst: TextIO) -> None:
        self._add_label_symbols()
        n = 16
        while self.parser.has_more_cmds():
            self.parser.advance()
            cmd_type = self.parser.cmd_type()
            if cmd_type == CmdType.A_COMMAND:
                symbol = self.parser.symbol()
                if symbol.isdigit():
                    value = symbol
                else:
                    if not self.symbolTable.contains(symbol):
                        self.symbolTable.add_entry(symbol, n)
                        n += 1
                    value = self.symbolTable.get_address(symbol)
                code = f'0{int(value):015b}\n'
            elif cmd_type == CmdType.C_COMMAND:
                dest = Code.dest(self.parser.dest())
                comp = Code.comp(self.parser.comp())
                jump = Code.jump(self.parser.jump())
                code = f'111{comp}{dest}{jump}\n'
            else:
                continue
            dst.write(code)

    def _add_label_symbols(self) -> None:
        line = 0
        while self.parser.has_more_cmds():
            self.parser.advance()
            if self.parser.cmd_type() == CmdType.L_COMMAND:
                self.symbolTable.add_entry(self.parser.symbol(), line)
            else:
                line += 1
        self.parser.reset()


class CmdType(Enum):
    A_COMMAND = 0
    C_COMMAND = 1
    L_COMMAND = 2


class Parser():
    """Encapsulates access to the input code. 
    Reads an assembly language command, parses it, and provides convenient 
    access to the components (fields and symbols) of the command. In addition, 
    removes all white space and comments.
    """

    a_cmd_p = re.compile(r'@(?P<value>[\w\.\$]+)')
    l_cmd_p = re.compile(r'\((?P<label>[\w\.\$]+)\)')
    c_cmd_p = re.compile(
        r'((?P<dest>\w+)=){0,1}(?P<comp>[\w\+\-\!\|\&]+)(;(?P<jump>\w+)){0,1}')

    def __init__(self, f: TextIO) -> None:
        self.f = f
        self.cur_cmd = None
        self.cur_type = None
        self.cur_symbol = None
        self.cur_dest = None
        self.cur_comp = None
        self.cur_jump = None

    def has_more_cmds(self) -> bool:
        last_pos = self.f.tell()
        text = self.f.readline()
        while text.isspace() or text.startswith("//"):
            text = self.f.readline()
        self.f.seek(last_pos)
        return text != ""

    def advance(self) -> None:
        text = self.f.readline()
        while text.isspace() or text.startswith("//"):
            text = self.f.readline()
        self.cur_cmd = text.split("//")[0].strip()
        match = re.match(self.a_cmd_p, self.cur_cmd)
        if match is not None:
            self.cur_type = CmdType.A_COMMAND
            self.cur_symbol = match.group('value')
            return
        match = re.match(self.l_cmd_p, self.cur_cmd)
        if match is not None:
            self.cur_type = CmdType.L_COMMAND
            self.cur_symbol = match.group('label')
            return
        match = re.match(self.c_cmd_p, self.cur_cmd)
        if match is not None:
            self.cur_type = CmdType.C_COMMAND
            self.cur_dest = match.group('dest')
            self.cur_comp = match.group('comp')
            self.cur_jump = match.group('jump')
            return
        raise RuntimeError(f"Failed to parse command: {self.cur_cmd}")

    def reset(self) -> None:
        """Change the stream position to the start of the stream."""
        self.f.seek(0)

    def cmd_type(self) -> CmdType:
        return self.cur_type

    def symbol(self) -> str:
        return self.cur_symbol

    def dest(self) -> str:
        return self.cur_dest

    def comp(self) -> str:
        return self.cur_comp

    def jump(self) -> str:
        return self.cur_jump


class SymbolTable():
    """Keeps a correspondence between symbolic labels and numeric addresses."""

    predefined_table = {
        'SP': 0,
        'LCL': 1,
        'ARG': 2,
        'THIS': 3,
        'THAT': 4,
        'R0': 0,
        'R1': 1,
        'R2': 2,
        'R3': 3,
        'R4': 4,
        'R5': 5,
        'R6': 6,
        'R7': 7,
        'R8': 8,
        'R9': 9,
        'R10': 10,
        'R11': 11,
        'R12': 12,
        'R13': 13,
        'R14': 14,
        'R15': 15,
        'SCREEN': 16384,
        'KBD': 24576,
    }

    def __init__(self) -> None:
        self.table = {**SymbolTable.predefined_table}

    def add_entry(self, symbol: str, address: int) -> None:
        self.table[symbol] = address

    def contains(self, symbol: str) -> bool:
        return symbol in self.table

    def get_address(self, symbol: str) -> int:
        return self.table.get(symbol)


class Code():
    """Translates Hack assembly language mnemonics into binary codes."""

    dest_table = {
        'null': '000',
        'M': '001',
        'D': '010',
        'MD': '011',
        'A': '100',
        'AM': '101',
        'AD': '110',
        'AMD': '111',
    }

    comp_table = {
        # a = 0
        '0': '0101010',
        '1': '0111111',
        '-1': '0111010',
        'D': '0001100',
        'A': '0110000',
        '!D': '0001101',
        '!A': '0110001',
        '-D': '0001111',
        '-A': '0110011',
        'D+1': '0011111',
        'A+1': '0110111',
        'D-1': '0001110',
        'A-1': '0110010',
        'D+A': '0000010',
        'D-A': '0010011',
        'A-D': '0000111',
        'D&A': '0000000',
        'D|A': '0010101',
        # a = 1
        'M': '1110000',
        '!M': '1110001',
        '-M': '1110011',
        'M+1': '1110111',
        'M-1': '1110010',
        'D+M': '1000010',
        'D-M': '1010011',
        'M-D': '1000111',
        'D&M': '1000000',
        'D|M': '1010101',
    }

    jump_table = {
        'null': '000',
        'JGT': '001',
        'JEQ': '010',
        'JGE': '011',
        'JLT': '100',
        'JNE': '101',
        'JLE': '110',
        'JMP': '111',
    }

    @staticmethod
    def dest(mnemonic: str) -> str:
        """Returns the binary code of the dest mnemonic."""
        return Code._get_code(mnemonic=mnemonic, table=Code.dest_table)

    @staticmethod
    def comp(mnemonic: str) -> str:
        """Returns the binary code of the comp mnemonic."""
        return Code._get_code(mnemonic=mnemonic, table=Code.comp_table)

    @staticmethod
    def jump(mnemonic: str) -> str:
        """Returns the binary code of the jump mnemonic."""
        return Code._get_code(mnemonic=mnemonic, table=Code.jump_table)

    @staticmethod
    def _get_code(mnemonic: str, table: dict) -> str:
        if mnemonic is None:
            mnemonic = 'null'
        if mnemonic in table:
            return table.get(mnemonic)
        else:
            raise RuntimeError(f"Failed to translate mnemonic: {mnemonic}")


if __name__ == '__main__':
    main()
