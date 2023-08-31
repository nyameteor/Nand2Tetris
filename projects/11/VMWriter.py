from enum import Enum
from typing import Self, TextIO
from SymbolTable import Kind


class Segment(Enum):
    CONSTANT = "constant"
    ARGUMENT = "argument"
    LOCAL = "local"
    STATIC = "static"
    THIS = "this"
    THAT = "that"
    POINTER = "pointer"
    TEMP = "temp"

    @classmethod
    def from_kind(cls, kind: Kind) -> Self:
        if kind == Kind.STATIC:
            return Segment.STATIC
        elif kind == Kind.FIELD:
            return Segment.THIS
        elif kind == Kind.VAR:
            return Segment.LOCAL
        elif kind == Kind.ARG:
            return Segment.ARGUMENT


class Command(Enum):
    ADD = "add"
    SUB = "sub"
    NEG = "neg"
    EQ = "eq"
    GT = "gt"
    LT = "lt"
    AND = "and"
    OR = "or"
    NOT = "not"


class VMWriter():
    """
    Features a set of simple routines for writing VM commands into the output 
    file.
    """

    def __init__(self, f: TextIO) -> None:
        """
        Creates a new output `.vm` file stream, and prepares it for writing.
        """
        self.f = f

    def write_push(self, segment: Segment, index: int) -> None:
        """
        Writes a VM `push` command.
        """
        self.f.write(f'push {segment.value} {index}\n')

    def write_pop(self, segment: Segment, index: int) -> None:
        """
        Writes a VM `pop` command.
        """
        self.f.write(f'pop {segment.value} {index}\n')

    def write_arithmetic(self, command: Command) -> None:
        """
        Writes a VM arithmetic-logical command.
        """
        self.f.write(f'{command.value}\n')

    def write_label(self, label: str) -> None:
        """
        Writes a VM `label` command.
        """
        self.f.write(f'label {label}\n')

    def write_goto(self, label: str) -> None:
        """
        Writes a VM `goto` command.
        """
        self.f.write(f'goto {label}\n')

    def write_if(self, label: str) -> None:
        """
        Writes a VM `if-goto` command.
        """
        self.f.write(f'if-goto {label}\n')

    def write_call(self, name: str, n_args: int) -> None:
        """
        Writes a VM `call` command.
        """
        self.f.write(f'call {name} {n_args}\n')

    def write_function(self, name: str, n_vars: int) -> None:
        """
        Writes a VM `function` command.
        """
        self.f.write(f'function {name} {n_vars}\n')

    def write_return(self) -> None:
        """
        Writes a VM `return` command.
        """
        self.f.write('return\n')
