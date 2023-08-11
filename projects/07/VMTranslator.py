#!/usr/bin/env python3

import argparse
import re
from enum import Enum
from pathlib import Path
from typing import TextIO


def main() -> None:
    argparser = argparse.ArgumentParser(
        description='The VM-to-Hack translator'
    )
    argparser.add_argument('file', metavar='FILE')
    argparser.add_argument('-o', '--output',
                           dest='output_file', metavar='FILE',
                           help='write output to FILE')
    argparser.add_argument('-d', '--debug',
                           dest='debug', action='store_true',
                           help='enable debugging output')
    args = argparser.parse_args()

    cwd = Path.cwd()
    src_file = cwd.joinpath(args.file)
    if args.output_file:
        dst_file = cwd.joinpath(args.output_file)
    else:
        dst_file = cwd.joinpath(src_file.name.replace('.vm', '.asm'))
    with open(file=src_file, mode='r', encoding='utf-8') as src, \
            open(file=dst_file, mode='w', encoding='utf-8') as dst:
        translator = VMTranslator(src=src, dst=dst, namespace=src_file.stem,
                                  debug=args.debug)
        translator.translate()


class VMTranslator():
    def __init__(self, src: TextIO, dst: TextIO, namespace: str, debug: bool) -> None:
        self.parser = Parser(f=src)
        self.writer = CodeWriter(f=dst, namespace=namespace, debug=debug)

    def translate(self) -> None:
        while self.parser.has_more_cmds():
            self.parser.advance()
            cmd_type = self.parser.cmd_type()
            if cmd_type == CmdType.C_ARITHMETIC:
                self.writer.write_arithmetic(cmd=self.parser.arg1())
            elif cmd_type == CmdType.C_PUSH or cmd_type == CmdType.C_POP:
                self.writer.write_push_pop(cmd_type=cmd_type,
                                           segment=self.parser.arg1(),
                                           index=self.parser.arg2())


class CmdType(Enum):
    C_ARITHMETIC = 0
    C_PUSH = 1
    C_POP = 2


class Parser():
    c_arithmetic_p = re.compile(
        r'^(?P<command>add|sub|neg|eq|gt|lt|and|or|not)$')
    c_push_p = re.compile(
        r'^push\s+(?P<segment>argument|local|static|constant|this|that|pointer|temp)\s+(?P<index>\d+)$')
    c_pop_p = re.compile(
        r'^pop\s+(?P<segment>argument|local|static|this|that|pointer|temp)\s+(?P<index>\d+)$')

    def __init__(self, f: TextIO) -> None:
        self.f = f
        self.cur_cmd = None
        self.cur_type = None
        self.cur_arg1 = None
        self.cur_arg2 = None

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
        match = re.match(Parser.c_arithmetic_p, self.cur_cmd)
        if match is not None:
            self.cur_type = CmdType.C_ARITHMETIC
            self.cur_arg1 = match.group('command')
            return
        match = re.match(Parser.c_push_p, self.cur_cmd)
        if match is not None:
            self.cur_type = CmdType.C_PUSH
            self.cur_arg1 = match.group('segment')
            self.cur_arg2 = match.group('index')
            return
        match = re.match(Parser.c_pop_p, self.cur_cmd)
        if match is not None:
            self.cur_type = CmdType.C_POP
            self.cur_arg1 = match.group('segment')
            self.cur_arg2 = match.group('index')
            return
        raise RuntimeError(f"Failed to parse command: {self.cur_cmd}")

    def cmd_type(self) -> CmdType:
        return self.cur_type

    def arg1(self) -> str:
        return self.cur_arg1

    def arg2(self) -> int:
        return int(self.cur_arg2)


class CodeWriter():
    def __init__(self, f: TextIO, namespace: str, debug: bool) -> None:
        self.f = f
        self.namespace = namespace
        self.debug = debug
        self.cmp_jump_i = 0

    def write_arithmetic(self, cmd: str) -> None:
        lines = []
        if self.debug:
            lines.append(f'// {cmd}')
        if cmd in ['add', 'sub', 'and', 'or']:
            if cmd == 'add':
                comp = 'D+M'
            elif cmd == 'sub':
                comp = 'M-D'
            elif cmd == 'and':
                comp = 'D&M'
            elif cmd == 'or':
                comp = 'D|M'
            lines.extend(['@SP', 'AM=M-1', 'D=M', 'A=A-1', f'M={comp}'])
        elif cmd in ['neg', 'not']:
            if cmd == 'neg':
                comp = '-M'
            elif cmd == 'not':
                comp = '!M'
            lines.extend(['@SP', 'A=M-1', f'M={comp}'])
        elif cmd in ['eq', 'gt', 'lt']:
            if cmd == 'eq':
                jump = 'JEQ'
            elif cmd == 'gt':
                jump = 'JGT'
            elif cmd == 'lt':
                jump = 'JLT'
            cur_jump_i = self.cmp_jump_i
            lines.extend(['@SP', 'AM=M-1', 'D=M', 'A=A-1', 'D=M-D',
                          f'@cmp{cur_jump_i}', f'D;{jump}'])
            # compare test failed
            lines.extend(['@SP', 'A=M-1', 'M=0',
                          f'@cmp{cur_jump_i}end', '0;JMP'])
            # compare test success
            lines.extend([f'(cmp{cur_jump_i})',
                          '@SP', 'A=M-1', 'M=-1'])
            # end of compare
            lines.extend([f'(cmp{cur_jump_i}end)'])
            self.cmp_jump_i += 1
        self._write_lines(lines)

    def write_push_pop(self, cmd_type: CmdType, segment: str, index: int) -> None:
        lines = []
        if self.debug:
            if cmd_type == CmdType.C_PUSH:
                lines.append(f'// push {segment} {index}')
            elif cmd_type == CmdType.C_POP:
                lines.append(f'// pop {segment} {index}')
        if segment in ['local', 'argument', 'this', 'that']:
            if segment == 'local':
                pointer = 'LCL'
            elif segment == 'argument':
                pointer = 'ARG'
            elif segment == 'this':
                pointer = 'THIS'
            elif segment == 'that':
                pointer = 'THAT'
            if cmd_type == CmdType.C_PUSH:
                # `push segment i` -> `addr = segmentPointer + i, *SP = *addr, SP++`
                lines.extend([f'@{pointer}', 'D=M', f'@{index}', 'D=D+A', 'A=D', 'D=M',
                              '@SP', 'AM=M+1', 'A=A-1', 'M=D'])
            elif cmd_type == CmdType.C_POP:
                # `pop segment i`  -> `addr = segmentPointer + i, SP--, *addr = *SP`
                lines.extend([f'@{pointer}', 'D=M', f'@{index}', 'D=D+A', '@R13', 'M=D',
                              '@SP', 'AM=M-1', 'D=M', '@R13', 'A=M', 'M=D'])
        elif segment == 'constant':
            # `push constant i` -> `*SP = i, SP++`
            lines.extend([f'@{index}', 'D=A',
                          '@SP', 'AM=M+1', 'A=A-1', 'M=D'])
        elif segment == 'static':
            if cmd_type == CmdType.C_PUSH:
                # `push static i` -> `addr = namespace.i, *SP = *addr, SP++`
                lines.extend([f'@{self.namespace}.{index}', 'D=M',
                              '@SP', 'AM=M+1', 'A=A-1', 'M=D'])
            elif cmd_type == CmdType.C_POP:
                # `pop static i`  -> `addr = namespace.i, SP--, *addr = *SP`
                lines.extend(['@SP', 'AM=M-1', 'D=M',
                              f'@{self.namespace}.{index}', 'M=D'])
        elif segment == 'temp':
            if cmd_type == CmdType.C_PUSH:
                # `push temp i` -> `*SP = tempAddr, SP++`
                lines.extend([f'@{5 + index}', 'D=M',
                              '@SP', 'AM=M+1', 'A=A-1', 'M=D'])
            elif cmd_type == CmdType.C_POP:
                # `pop temp i`  -> `SP--, tempAddr = *SP`
                lines.extend(['@SP', 'AM=M-1', 'D=M',
                              f'@{5 + index}', 'M=D'])
        elif segment == 'pointer':
            if index == 0:
                pointer = 'THIS'
            elif index == 1:
                pointer = 'THAT'
            if cmd_type == CmdType.C_PUSH:
                # `push pointer 0/1` -> `*SP = THIS/THAT, SP++`
                lines.extend([f'@{pointer}', 'D=M',
                              '@SP', 'AM=M+1', 'A=A-1', 'M=D'])
            elif cmd_type == CmdType.C_POP:
                # `pop pointer 0/1`  -> `SP--, THIS/THAT = *SP`
                lines.extend(['@SP', 'AM=M-1', 'D=M',
                              f'@{pointer}', 'M=D'])
        self._write_lines(lines)

    def _write_lines(self, lines: list[str]):
        for line in lines:
            self.f.write(f"{line}\n")


if __name__ == '__main__':
    main()
