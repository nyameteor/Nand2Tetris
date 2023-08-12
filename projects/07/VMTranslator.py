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
    argparser.add_argument(
        'file', metavar='FILE'
    )
    argparser.add_argument(
        '-o', '--output',
        dest='output_file', metavar='FILE',
        help='write output to FILE'
    )
    argparser.add_argument(
        '-d', '--debug',
        dest='debug', action='store_true',
        help='enable debugging output'
    )
    args = argparser.parse_args()

    cwd = Path.cwd()
    src_file = cwd.joinpath(args.file)
    if args.output_file:
        dst_file = cwd.joinpath(args.output_file)
    else:
        dst_file = cwd.joinpath(src_file.name.replace('.vm', '.asm'))
    with open(file=src_file, mode='r', encoding='utf-8') as src, \
            open(file=dst_file, mode='w', encoding='utf-8') as dst:
        translator = VMTranslator(
            src=src, dst=dst, namespace=src_file.stem, debug=args.debug)
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
                self.writer.write_push_pop(
                    cmd_type=cmd_type,
                    segment=self.parser.arg1(),
                    index=self.parser.arg2()
                )


class CmdType(Enum):
    C_ARITHMETIC = 0
    C_PUSH = 1
    C_POP = 2


class Parser():
    C_ARITHMETIC_P = re.compile(
        r'^(?P<command>add|sub|neg|eq|gt|lt|and|or|not)$')
    C_PUSH_P = re.compile(
        r'^push\s+(?P<segment>argument|local|static|constant|this|that|pointer|temp)\s+(?P<index>\d+)$')
    C_POP_P = re.compile(
        r'^pop\s+(?P<segment>argument|local|static|this|that|pointer|temp)\s+(?P<index>\d+)$')

    def __init__(self, f: TextIO) -> None:
        self.f = f
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
        text = text.split("//")[0].strip()
        self._parse_cmd(cmd=text)

    def cmd_type(self) -> CmdType:
        return self.cur_type

    def arg1(self) -> str:
        return self.cur_arg1

    def arg2(self) -> int:
        return int(self.cur_arg2)

    def _parse_cmd(self, cmd: str) -> None:
        match = re.match(Parser.C_ARITHMETIC_P, cmd)
        if match is not None:
            self.cur_type = CmdType.C_ARITHMETIC
            self.cur_arg1 = match.group('command')
            return
        match = re.match(Parser.C_PUSH_P, cmd)
        if match is not None:
            self.cur_type = CmdType.C_PUSH
            self.cur_arg1 = match.group('segment')
            self.cur_arg2 = match.group('index')
            return
        match = re.match(Parser.C_POP_P, cmd)
        if match is not None:
            self.cur_type = CmdType.C_POP
            self.cur_arg1 = match.group('segment')
            self.cur_arg2 = match.group('index')
            return
        raise RuntimeError(f"Failed to parse command: {cmd}")


class CodeWriter():
    ARITHMETIC_TO_OP = {
        'add': '+',
        'sub': '-',
        'and': '&',
        'or': '|',
        'neg': '-',
        'not': '!'
    }

    COMPARISON_TO_JUMP = {
        'eq': 'JEQ',
        'gt': 'JGT',
        'lt': 'JLT'
    }

    SEGMENT_TO_ADDR = {
        'local': 'LCL',
        'argument': 'ARG',
        'this': 'THIS',
        'that': 'THAT'
    }

    POINTER_TO_ADDR = {
        '0': 'THIS',
        '1': 'THAT'
    }

    def __init__(self, f: TextIO, namespace: str, debug: bool) -> None:
        self.f = f
        self.namespace = namespace
        self.debug = debug
        self.cmp_jump_i = 0

    def write_arithmetic(self, cmd: str) -> None:
        lines = self._gen_arithmetic_lines(cmd=cmd)
        self._write_lines(lines)

    def write_push_pop(self, cmd_type: CmdType, segment: str, index: int) -> None:
        if cmd_type == CmdType.C_PUSH:
            lines = self._gen_push_lines(segment, index)
        elif cmd_type == CmdType.C_POP:
            lines = self._gen_pop_lines(segment, index)
        self._write_lines(lines)

    def _gen_arithmetic_lines(self, cmd: str) -> list[str]:
        lines = []
        if self.debug:
            lines.append(
                f'// {cmd}'
            )
        if cmd in ['add', 'sub', 'and', 'or']:
            op = CodeWriter.ARITHMETIC_TO_OP.get(cmd)
            lines.extend([
                '@SP',
                'AM=M-1',
                'D=M',
                'A=A-1',
                f'M=M{op}D'
            ])
        elif cmd in ['neg', 'not']:
            op = CodeWriter.ARITHMETIC_TO_OP.get(cmd)
            lines.extend([
                '@SP',
                'A=M-1',
                f'M={op}M'
            ])
        elif cmd in ['eq', 'gt', 'lt']:
            jump = CodeWriter.COMPARISON_TO_JUMP.get(cmd)
            cur_jump_i = self.cmp_jump_i
            lines.extend([
                '@SP',
                'AM=M-1',
                'D=M',
                'A=A-1',
                'D=M-D',
                f'@cmp{cur_jump_i}',
                f'D;{jump}'
            ])
            # compare test failed
            lines.extend([
                '@SP',
                'A=M-1',
                'M=0',
                f'@cmp{cur_jump_i}end',
                '0;JMP'
            ])
            # compare test success
            lines.extend([
                f'(cmp{cur_jump_i})',
                '@SP',
                'A=M-1',
                'M=-1'
            ])
            # end of compare
            lines.extend([
                f'(cmp{cur_jump_i}end)'
            ])
            self.cmp_jump_i += 1
        return lines

    def _gen_push_lines(self, segment: str, index: int) -> list[str]:
        lines = []
        if self.debug:
            lines.append(
                f'// push {segment} {index}'
            )
        push_d_to_stack = [
            '@SP',
            'AM=M+1',
            'A=A-1',
            'M=D'
        ]
        if segment in ['local', 'argument', 'this', 'that']:
            # `push segment i` -> `addr = segmentPointer + i, *SP = *addr, SP++`
            base_addr = CodeWriter.SEGMENT_TO_ADDR.get(segment)
            lines.extend([
                f'@{base_addr}',
                'D=M',
                f'@{index}',
                'D=D+A',
                'A=D',
                'D=M',
                *push_d_to_stack
            ])
        elif segment == 'constant':
            # `push constant i` -> `*SP = i, SP++`
            lines.extend([
                f'@{index}',
                'D=A',
                *push_d_to_stack
            ])
        elif segment == 'static':
            # `push static i` -> `addr = namespace.i, *SP = *addr, SP++`
            lines.extend([
                f'@{self.namespace}.{index}',
                'D=M',
                *push_d_to_stack
            ])
        elif segment == 'temp':
            # `push temp i` -> `*SP = tempAddr, SP++`
            lines.extend([
                f'@{5 + index}',
                'D=M',
                *push_d_to_stack
            ])
        elif segment == 'pointer':
            # `push pointer 0/1` -> `*SP = THIS/THAT, SP++`
            base_addr = CodeWriter.POINTER_TO_ADDR.get(str(index))
            lines.extend([
                f'@{base_addr}',
                'D=M',
                *push_d_to_stack
            ])
        return lines

    def _gen_pop_lines(self, segment: str, index: int) -> list[str]:
        lines = []
        if self.debug:
            lines.append(
                f'// pop {segment} {index}'
            )
        pop_stack_to_d = [
            '@SP',
            'AM=M-1',
            'D=M'
        ]
        if segment in ['local', 'argument', 'this', 'that']:
            # `pop segment i`  -> `addr = segmentPointer + i, SP--, *addr = *SP`
            base_addr = CodeWriter.SEGMENT_TO_ADDR.get(segment)
            lines.extend([
                f'@{base_addr}',
                'D=M',
                f'@{index}',
                'D=D+A',
                '@R13',
                'M=D',
                *pop_stack_to_d,
                '@R13',
                'A=M',
                'M=D'
            ])
        elif segment == 'static':
            # `pop static i`  -> `addr = namespace.i, SP--, *addr = *SP`
            lines.extend([
                *pop_stack_to_d,
                f'@{self.namespace}.{index}',
                'M=D'
            ])
        elif segment == 'temp':
            # `pop temp i`  -> `SP--, tempAddr = *SP`
            lines.extend([
                *pop_stack_to_d,
                f'@{5 + index}',
                'M=D'
            ])
        elif segment == 'pointer':
            # `pop pointer 0/1`  -> `SP--, THIS/THAT = *SP`
            base_addr = CodeWriter.POINTER_TO_ADDR.get(str(index))
            lines.extend([
                *pop_stack_to_d,
                f'@{base_addr}',
                'M=D'
            ])
        return lines

    def _write_lines(self, lines: list[str]):
        for line in lines:
            self.f.write(f"{line}\n")


if __name__ == '__main__':
    main()
