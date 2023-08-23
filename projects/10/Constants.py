from enum import Enum
import re
from typing import Self


class Text():
    # TokenTypes
    KEYWORD = "keyword"
    SYMBOL = "symbol"
    IDENTIFIER = "identifier"
    INT_CONST = "integerConstant"
    STR_CONST = "stringConstant"
    # Keywords
    CLASS = "class"
    METHOD = "method"
    FUNCTION = "function"
    CONSTRUCTOR = "constructor"
    INT = "int"
    BOOLEAN = "boolean"
    CHAR = "char"
    VOID = "void"
    VAR = "var"
    STATIC = "static"
    FIELD = "field"
    LET = "let"
    DO = "do"
    IF = "if"
    ELSE = "else"
    WHILE = "while"
    RETURN = "return"
    TRUE = "true"
    FALSE = "false"
    NULL = "null"
    THIS = "this"
    # Symbols
    LEFT_ROUND_BRACKET = '('
    RIGHT_ROUND_BRACKET = ')'
    LEFT_SQUARE_BRACKET = '['
    RIGHT_SQUARE_BRACKET = ']'
    LEFT_CURLY_BRACKET = '{'
    RIGHT_CURLY_BRACKET = '}'
    ELEMENT_SELECTION = '.'
    COMMA = ','
    SEMICOLON = ';'
    DOUBLE_QUOTATION_MARK = '"'
    # Operators
    ADDITION = '+'
    SUBTRACTION = '-'
    MULTIPLICATION = '*'
    DIVISION = '/'
    BITWISE_AND = '&'
    BITWISE_OR = '|'
    LESS_THAN = '<'
    GREATER_THAN = '>'
    ASSIGNMENT = '='
    # Unary operators
    UNARY_MINUS = '-'
    BITWISE_NOT = '~'


class TokenType(Enum):
    KEYWORD = Text.KEYWORD
    SYMBOL = Text.SYMBOL
    IDENTIFIER = Text.IDENTIFIER
    INT_CONST = Text.INT_CONST
    STR_CONST = Text.STR_CONST


class KeywordType(Enum):
    CLASS = Text.CLASS
    METHOD = Text.METHOD
    FUNCTION = Text.FUNCTION
    CONSTRUCTOR = Text.CONSTRUCTOR
    INT = Text.INT
    BOOLEAN = Text.BOOLEAN
    CHAR = Text.CHAR
    VOID = Text.VOID
    VAR = Text.VAR
    STATIC = Text.STATIC
    FIELD = Text.FIELD
    LET = Text.LET
    DO = Text.DO
    IF = Text.IF
    ELSE = Text.ELSE
    WHILE = Text.WHILE
    RETURN = Text.RETURN
    TRUE = Text.TRUE
    FALSE = Text.FALSE
    NULL = Text.NULL
    THIS = Text.THIS

    @classmethod
    def value_to_member(cls, value: str) -> Self:
        if not hasattr(cls, 'VALUE_TO_MEMBER'):
            cls.VALUE_TO_MEMBER = {k.value: k for k in cls}
        return cls.VALUE_TO_MEMBER.get(value)


class Regex():
    # Lexical elements
    KEYWORD = rf'^{"|".join([keyword.value for keyword in KeywordType])}$'
    INTEGER_CONSTANT = r'^\d+$'
    STRING_CONSTANT = rf'^.+$'
    _NOT_KEYWORD = "".join([f"(?!{keyword.value})" for keyword in KeywordType])
    IDENTIFIER = rf'^{_NOT_KEYWORD}\w+$'

    # Program structure
    CLASS_NAME = IDENTIFIER
    SUBROUTINE_NAME = IDENTIFIER
    VAR_NAME = IDENTIFIER
    TYPE = rf'^{Text.INT}|{Text.CHAR}|{Text.BOOLEAN}|{CLASS_NAME}$'
    SUBROUTINE_TYPE = rf'^{Text.VOID}|{TYPE}$'
    CLASS_VAR_DEC_START = rf'^{Text.STATIC}|{Text.FIELD}$'
    SUBROUTINE_DEC_START = rf'^{Text.CONSTRUCTOR}|{Text.FUNCTION}|{Text.METHOD}$'
    SUBROUTINE_CALL_START = rf'^{SUBROUTINE_NAME}|{CLASS_NAME}|{VAR_NAME}$'

    # Statements
    STATEMENT_START = rf'^{Text.LET}|{Text.IF}|{Text.WHILE}|{Text.DO}|{Text.RETURN}$'

    # Expressions
    OP = rf'^\{Text.ADDITION}|\{Text.SUBTRACTION}|\{Text.MULTIPLICATION}|\{Text.DIVISION}' + \
        rf'|\{Text.BITWISE_AND}|\{Text.BITWISE_OR}|\{Text.LESS_THAN}|\{Text.GREATER_THAN}|\{Text.ASSIGNMENT}$'
    UNARYOP = rf'^\{Text.UNARY_MINUS}|\{Text.BITWISE_NOT}$'
    KEYWORD_CONSTANT = rf'^{Text.TRUE}|{Text.FALSE}|{Text.NULL}|{Text.THIS}$'
    # TERM_START_PART does not contain STRING_CONSTANT because it may incorrectly match other patterns.
    TERM_START_PART = rf'^{INTEGER_CONSTANT}|{KEYWORD_CONSTANT}|{IDENTIFIER}' + \
        rf'|\{Text.LEFT_ROUND_BRACKET}|{UNARYOP}|{SUBROUTINE_NAME}|{CLASS_NAME}|{VAR_NAME}$'


class Pattern():
    # Lexical elements
    KEYWORD = re.compile(Regex.KEYWORD)
    INTEGER_CONSTANT = re.compile(Regex.INTEGER_CONSTANT)
    STRING_CONSTANT = re.compile(Regex.STRING_CONSTANT)
    IDENTIFIER = re.compile(Regex.IDENTIFIER)

    # Program structure
    CLASS_NAME = re.compile(Regex.CLASS_NAME)
    SUBROUTINE_NAME = re.compile(Regex.SUBROUTINE_NAME)
    VAR_NAME = re.compile(Regex.VAR_NAME)
    TYPE = re.compile(Regex.TYPE)
    SUBROUTINE_TYPE = re.compile(Regex.SUBROUTINE_TYPE)
    CLASS_VAR_DEC_START = re.compile(Regex.CLASS_VAR_DEC_START)
    SUBROUTINE_DEC_START = re.compile(Regex.SUBROUTINE_DEC_START)
    SUBROUTINE_CALL_START = re.compile(Regex.SUBROUTINE_CALL_START)

    # Statements
    STATEMENT_START = re.compile(Regex.STATEMENT_START)

    # Expressions
    OP = re.compile(Regex.OP)
    UNARYOP = re.compile(Regex.UNARYOP)
    KEYWORD_CONSTANT = re.compile(Regex.KEYWORD_CONSTANT)
    TERM_START_PART = re.compile(Regex.TERM_START_PART)
