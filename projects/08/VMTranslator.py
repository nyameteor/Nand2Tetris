#!/usr/bin/env python3

import argparse
import functools
import re
from enum import Enum
from pathlib import Path
from typing import TextIO


def main() -> None:
    argparser = argparse.ArgumentParser(
        description='The VM-to-Hack translator'
    )
    argparser.add_argument(
        'source',
        metavar='SOURCE',
        help='SOURCE is either a file name of the form Xxx.vm \
            or the name of a folder containing one or more .vm files'
    )
    argparser.add_argument(
        '-o', '--output',
        dest='output_file', metavar='FILE',
        help='write output to FILE'
    )
    argparser.add_argument(
        '-b', '--bootstrap',
        dest='bootstrap', action='store_true',
        help='enable writing the bootstrap code that initializes the VM'
    )
    argparser.add_argument(
        '-d', '--debug',
        dest='debug', action='store_true',
        help='enable writing debug output'
    )
    args = argparser.parse_args()

    cwd = Path.cwd()
    source = cwd.joinpath(args.source)
    if source.is_file():
        src_paths = [source]
    elif source.is_dir():
        src_paths = list(source.glob('*.vm'))
    if args.output_file:
        dst_path = cwd.joinpath(args.output_file)
    elif source.is_file():
        dst_path = cwd.joinpath(source.name.replace('.vm', '.asm'))
    elif source.is_dir():
        dst_path = source.joinpath(f"{source.name}.asm")

    translator = VMTranslator(
        src_paths=src_paths,
        dst_path=dst_path,
        bootstrap=args.bootstrap,
        debug=args.debug
    )
    translator.translate()


class VMTranslator():
    def __init__(self, src_paths: list[Path], dst_path: Path,
                 bootstrap: bool, debug: bool) -> None:
        self.src_paths = src_paths
        self.dst_path = dst_path
        self.bootstrap = bootstrap
        self.debug = debug
        self.parser = None
        self.writer = None

    def translate(self) -> None:
        self._sort_src_paths()
        dst_path = self.dst_path
        if dst_path.exists():
            dst_path.unlink()
        with dst_path.open(mode='a', encoding='utf-8') as dst:
            self.writer = CodeWriter(f=dst, debug=self.debug)
            if self.bootstrap:
                self.writer.write_init()
            for src_path in self.src_paths:
                with src_path.open(mode='r', encoding='utf-8') as src:
                    self.parser = Parser(f=src)
                    self.writer.set_namespace(src_path.stem)
                    self._translate_single_file()

    def _sort_src_paths(self) -> None:
        def cmp(p1: Path, p2: Path) -> int:
            if p1.stem == 'Sys':
                return -1
            if p1.stem == 'Main' and p2.stem != 'Sys':
                return -1
            else:
                return 0
        self.src_paths.sort(key=functools.cmp_to_key(cmp))

    def _translate_single_file(self) -> None:
        while self.parser.has_more_cmds():
            self.parser.advance()
            cmd_type = self.parser.cmd_type()
            if cmd_type == CmdType.C_ARITHMETIC:
                self.writer.write_arithmetic(
                    cmd=self.parser.arg1()
                )
            elif cmd_type == CmdType.C_PUSH:
                self.writer.write_push(
                    segment=self.parser.arg1(),
                    index=self.parser.arg2()
                )
            elif cmd_type == CmdType.C_POP:
                self.writer.write_pop(
                    segment=self.parser.arg1(),
                    index=self.parser.arg2()
                )
            elif cmd_type == CmdType.C_LABEL:
                self.writer.write_label(
                    label=self.parser.arg1()
                )
            elif cmd_type == CmdType.C_GOTO:
                self.writer.write_goto(
                    label=self.parser.arg1()
                )
            elif cmd_type == CmdType.C_IF:
                self.writer.write_if(
                    label=self.parser.arg1()
                )
            elif cmd_type == CmdType.C_FUNCTION:
                self.writer.write_function(
                    function_name=self.parser.arg1(),
                    n_vars=self.parser.arg2()
                )
            elif cmd_type == CmdType.C_RETURN:
                self.writer.write_return()
            elif cmd_type == CmdType.C_CALL:
                self.writer.write_call(
                    function_name=self.parser.arg1(),
                    n_vars=self.parser.arg2()
                )


class CmdType(Enum):
    C_ARITHMETIC = 0
    C_PUSH = 1
    C_POP = 2
    C_LABEL = 3
    C_GOTO = 4
    C_IF = 5
    C_FUNCTION = 6
    C_RETURN = 7
    C_CALL = 8


class Parser():
    C_ARITHMETIC_P = re.compile(
        r'^(?P<command>add|sub|neg|eq|gt|lt|and|or|not)$'
    )

    C_PUSH_P = re.compile(
        r'^push\s+(?P<segment>argument|local|static|constant|this|that|pointer|temp)\s+(?P<index>\d+)$'
    )

    C_POP_P = re.compile(
        r'^pop\s+(?P<segment>argument|local|static|this|that|pointer|temp)\s+(?P<index>\d+)$'
    )

    C_LABEL_P = re.compile(
        r'label\s+(?P<label>[\w\.\:]+)'
    )

    C_GOTO_P = re.compile(
        r'goto\s+(?P<label>[\w\.\:]+)'
    )

    C_IF_P = re.compile(
        r'if-goto\s+(?P<label>[\w\.\:]+)'
    )

    C_FUNCTION_P = re.compile(
        r'function\s+(?P<function_name>[\w\.]+)\s+(?P<n_vars>\d+)'
    )

    C_RETURN_P = re.compile(
        r'return'
    )

    C_CALL_P = re.compile(
        r'call\s+(?P<function_name>[\w\.]+)\s+(?P<n_vars>\d+)'
    )

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
        match = re.match(Parser.C_LABEL_P, cmd)
        if match is not None:
            self.cur_type = CmdType.C_LABEL
            self.cur_arg1 = match.group('label')
            return
        match = re.match(Parser.C_GOTO_P, cmd)
        if match is not None:
            self.cur_type = CmdType.C_GOTO
            self.cur_arg1 = match.group('label')
            return
        match = re.match(Parser.C_IF_P, cmd)
        if match is not None:
            self.cur_type = CmdType.C_IF
            self.cur_arg1 = match.group('label')
            return
        match = re.match(Parser.C_FUNCTION_P, cmd)
        if match is not None:
            self.cur_type = CmdType.C_FUNCTION
            self.cur_arg1 = match.group('function_name')
            self.cur_arg2 = match.group('n_vars')
            return
        match = re.match(Parser.C_RETURN_P, cmd)
        if match is not None:
            self.cur_type = CmdType.C_RETURN
            return
        match = re.match(Parser.C_CALL_P, cmd)
        if match is not None:
            self.cur_type = CmdType.C_CALL
            self.cur_arg1 = match.group('function_name')
            self.cur_arg2 = match.group('n_vars')
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

    def __init__(self, f: TextIO, debug: bool) -> None:
        self.f = f
        self.debug = debug
        self.cur_namespace = None
        self.cur_scope = None
        self.cur_ret_i = 0
        self.cur_jump_i = 0

    def set_namespace(self, namespace: str) -> None:
        """
        Informs that the translation of a new VM file has started.
        """
        self.cur_namespace = namespace

    def write_init(self) -> None:
        lines = []
        if self.debug:
            lines.append(
                '// Bootstrap code'
            )
        lines.extend([
            # SP = 256
            '@256',
            'D=A',
            '@SP',
            'M=D',
            # LCL = -1
            'D=-1',
            '@LCL',
            'M=D',
            # ARG = -2
            'D=D-1',
            '@ARG',
            'M=D',
            # THIS = -3
            'D=D-1',
            '@THIS',
            'M=D',
            # THAT = -4
            'D=D-1',
            '@THAT',
            'M=D'
        ])
        self._write_lines(lines)
        # call Sys.init
        self.write_call(function_name='Sys.init', n_vars=0)

    def write_arithmetic(self, cmd: str) -> None:
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
            cur_jump_i = self.cur_jump_i
            lines.extend([
                '@SP',
                'AM=M-1',
                'D=M',
                'A=A-1',
                'D=M-D',
                f'@cmp{cur_jump_i}',
                f'D;{jump}'
            ])
            # Compare test failed
            lines.extend([
                '@SP',
                'A=M-1',
                'M=0',
                f'@cmp{cur_jump_i}end',
                '0;JMP'
            ])
            # Compare test success
            lines.extend([
                f'(cmp{cur_jump_i})',
                '@SP',
                'A=M-1',
                'M=-1'
            ])
            # End of compare
            lines.extend([
                f'(cmp{cur_jump_i}end)'
            ])
            self.cur_jump_i += 1
        self._write_lines(lines)

    def write_push(self, segment: str, index: int) -> None:
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
                f'@{self.cur_namespace}.{index}',
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
        self._write_lines(lines)

    def write_pop(self, segment: str, index: int) -> None:
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
                f'@{self.cur_namespace}.{index}',
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
        self._write_lines(lines)

    def write_label(self, label: str) -> None:
        lines = []
        if self.debug:
            lines.append(
                f'// label {label}'
            )
        lines.extend([
            f'({self.cur_scope}${label})'
        ])
        self._write_lines(lines)

    def write_goto(self, label: str) -> None:
        lines = []
        if self.debug:
            lines.append(
                f'// goto {label}'
            )
        lines.extend([
            f'@{self.cur_scope}${label}',
            '0;JMP'
        ])
        self._write_lines(lines)

    def write_if(self, label: str) -> None:
        lines = []
        if self.debug:
            lines.append(
                f'// if-goto {label}'
            )
        lines.extend([
            '@SP',
            'AM=M-1',
            'D=M',
            f'@{self.cur_scope}${label}',
            'D;JNE'
        ])
        self._write_lines(lines)

    def write_function(self, function_name: str, n_vars: int) -> None:
        lines = []
        if self.debug:
            lines.append(
                f'// function {function_name} {n_vars}'
            )
        self.cur_scope = function_name
        self.cur_ret_i = 0
        # Injects a function entry label into the code
        lines.extend([
            f'({function_name})'
        ])
        # Repeat nVars times: initializes the local variables to 0
        for _ in range(n_vars):
            lines.extend([
                '@SP',
                'AM=M+1',
                'A=A-1',
                'M=0'
            ])
        self._write_lines(lines)

    def write_call(self, function_name: str, n_vars: int) -> None:
        lines = []
        if self.debug:
            lines.append(
                f'// call {function_name} {n_vars}'
            )
        push_d_to_stack = [
            '@SP',
            'AM=M+1',
            'A=A-1',
            'M=D'
        ]
        push_m_to_stack = [
            'D=M',
            *push_d_to_stack
        ]
        push_a_to_stack = [
            'D=A',
            *push_d_to_stack
        ]
        lines.extend([
            # Generates a label and pushes it to the stack
            f'@{self.cur_scope}$ret.{self.cur_ret_i}',
            *push_a_to_stack,
            # Saves LCL, ARG, THIS, THAT of the caller
            '@LCL',
            *push_m_to_stack,
            '@ARG',
            *push_m_to_stack,
            '@THIS',
            *push_m_to_stack,
            '@THAT',
            *push_m_to_stack,
            # Repositions ARG = SP - 5 - nVars
            '@SP',
            'D=M',
            f'@{5 + n_vars}',
            'D=D-A',
            '@ARG',
            'M=D',
            # Repositions LCL = SP
            '@SP',
            'D=M',
            '@LCL',
            'M=D',
            # Transfers control to the callee
            f'@{function_name}',
            '0;JMP',
            # Injects the return address label into the code
            f'({self.cur_scope}$ret.{self.cur_ret_i})'
        ])
        self.cur_ret_i += 1
        self._write_lines(lines)

    def write_return(self) -> None:
        lines = []
        if self.debug:
            lines.append(
                f'// return'
            )

        store_m_to_frame = [
            'D=M',
            '@R15',
            'M=D'
        ]

        def deref_frame_minus_i_to_d(i) -> list[str]:
            """
            D = *(frame-i)
            """
            return [
                '@R15',
                'D=M',
                f'@{i}',
                'D=D-A',
                'A=D',
                'D=M',
            ]

        lines.extend([
            # frame is a temporary variable, frame = LCL
            '@LCL',
            *store_m_to_frame,
            # Puts the return address in a temporary variable,
            # retAddr = *(frame-5)
            *deref_frame_minus_i_to_d(i=5),
            '@R14',
            'M=D',
            # Repositions the return value for the caller, *ARG = pop()
            '@ARG',
            'D=M',
            '@R13',
            'M=D',
            '@SP',
            'AM=M-1',
            'D=M',
            '@R13',
            'A=M',
            'M=D',
            # Repositions SP for the caller, SP = ARG+1
            '@ARG',
            'D=M',
            'D=D+1',
            '@SP',
            'M=D',
            # Restores THAT, THIS, ARG, LCL for the caller
            # THAT = *(frame-1)
            *deref_frame_minus_i_to_d(i=1),
            '@THAT',
            'M=D',
            # THIS = *(frame-2)
            *deref_frame_minus_i_to_d(i=2),
            '@THIS',
            'M=D',
            # ARG = *(frame-3)
            *deref_frame_minus_i_to_d(i=3),
            '@ARG',
            'M=D',
            # LCL = *(frame-4)
            *deref_frame_minus_i_to_d(i=4),
            '@LCL',
            'M=D',
            # Go to the return address, goto retAddr
            '@R14',
            'A=M',
            '0;JMP',
        ])
        self._write_lines(lines)

    def _write_lines(self, lines: list[str]):
        for line in lines:
            self.f.write(f"{line}\n")


if __name__ == '__main__':
    main()
