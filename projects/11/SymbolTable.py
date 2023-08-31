from dataclasses import dataclass
from enum import Enum
from typing import Self
from Constants import Text


class Kind(Enum):
    STATIC = Text.STATIC
    FIELD = Text.FIELD
    VAR = Text.VAR
    ARG = ""

    @classmethod
    def value_to_member(cls, value: str) -> Self:
        if not hasattr(cls, 'VALUE_TO_MEMBER'):
            cls.VALUE_TO_MEMBER = {k.value: k for k in cls}
        return cls.VALUE_TO_MEMBER.get(value)


@dataclass
class TableEntry:
    name: str
    type: str
    kind: Kind
    index: int


class SymbolTable():
    """
    Provides services for building, populating, and using symbol tables that 
    keep track of the symbol properties `name`, `type`, `kind`, and a running 
    `index` for each kind.
    """

    def __init__(self) -> None:
        """
        Creates a new symbol table.
        """
        # Class-level symbol table
        self.class_table: dict[str, TableEntry] = {}
        self.static_index = 0
        self.field_index = 0

        # Subroutine-level symbol table
        self.subroutine_table: dict[str, TableEntry] = {}
        self.arg_index = 0
        self.var_index = 0

        # Whether to look for `fields` symbols
        self.enable_fields = True

    def resetSubroutine(self, enable_fields: bool) -> None:
        """
        Empties the subroutine-level symbol table, resets the `arg` and `var` 
        indexes to 0, and enables or disables `fields`.
        Should be called when starting to compile a subroutine declaration.
        """
        self.subroutine_table.clear()
        self.arg_index = 0
        self.var_index = 0
        self.enable_fields = enable_fields

    def define(self, name: str, type: str, kind: Kind) -> None:
        """
        Defines (adds to the table) a new variable of the given `name`, `type`, 
        and `kind`. Assigns to it the index value of that `kind`, and adds 1 to
        the index.
        """
        entry = TableEntry(
            name=name, type=type,
            kind=kind, index=self.var_count(kind)
        )
        if kind == Kind.STATIC:
            self.class_table[name] = entry
            self.static_index += 1
        elif kind == Kind.FIELD:
            self.class_table[name] = entry
            self.field_index += 1
        elif kind == Kind.ARG:
            self.subroutine_table[name] = entry
            self.arg_index += 1
        elif kind == Kind.VAR:
            self.subroutine_table[name] = entry
            self.var_index += 1

    def var_count(self, kind: Kind) -> int:
        """
        Returns the number of variables of the given `kind` already defined 
        in the table.
        """
        if kind == Kind.STATIC:
            return self.static_index
        elif kind == Kind.FIELD:
            return self.field_index
        elif kind == Kind.ARG:
            return self.arg_index
        elif kind == Kind.VAR:
            return self.var_index

    def field_count(self) -> int:
        """
        Returns the number of fields in the table.
        """
        return self.field_index

    def kind_of(self, name: str) -> Kind:
        """
        Returns the `kind` of the named identifier. 
        """
        return self._get_entry(name).kind

    def type_of(self, name: str) -> str:
        """
        Returns the `type` of the named variable.
        """
        return self._get_entry(name).type

    def index_of(self, name: str) -> int:
        """
        Returns the `index` of the named variable.
        """
        return self._get_entry(name).index

    def contains(self, name: str) -> bool:
        """
        Returns whether the table contains the named variable.
        """
        try:
            self._get_entry(name=name)
            return True
        except RuntimeError:
            return False

    def _get_entry(self, name) -> TableEntry:
        if name in self.subroutine_table:
            return self.subroutine_table.get(name)
        elif name in self.class_table:
            entry = self.class_table.get(name)
            if not (entry.kind == Kind.FIELD and not self.enable_fields):
                return entry
        raise RuntimeError(f'{name} is not defined as a variable')
