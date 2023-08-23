#!/usr/bin/env python3

import io
from typing import TextIO
from Constants import TokenType, KeywordType


EOF = ''
WHITESPACES = {' ', '\t', '\n', '\r'}
KEYWORDS = {k.value for k in KeywordType}
SYMBOLS = {'{', '}', '(', ')', '[', ']', '.', ',', ';',
           '+', '-', '*', '/', '&', '|', '<', '>', '=', '~'}
DIGITS = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
LETTERS = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
           'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'} \
    | {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
       'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'}
WORDS = DIGITS | LETTERS | {"_"}
STRING_DELIMS = {'"'}
TOKENS = KEYWORDS | SYMBOLS | DIGITS | WORDS | STRING_DELIMS


class JackTokenizer():
    def __init__(self, f: TextIO) -> None:
        self.f = f                  # The file stream
        self.done = False           # Is stream already at EOF
        self.valid = False          # Is current token valid
        self.cur_type = None
        self.cur_keyword = None
        self.cur_symbol = None
        self.cur_identifier = None
        self.cur_int_val = None
        self.cur_str_val = None

    def has_more_tokens(self) -> bool:
        if self.done:
            return False
        if self.valid:
            return True
        else:
            self._read_next()
            return self.valid

    def advance(self) -> None:
        self.valid = False

    def token_type(self) -> TokenType:
        return self.cur_type

    def keyword(self) -> KeywordType:
        return self.cur_keyword

    def symbol(self) -> str:
        return self.cur_symbol

    def identifier(self) -> str:
        return self.cur_identifier

    def int_val(self) -> int:
        return self.cur_int_val

    def str_val(self) -> str:
        return self.cur_str_val

    def _read_next(self) -> None:
        self._ignore_whitespaces_and_comments()

        c = self._peek()
        if c in SYMBOLS:
            self._read_symbol()
        elif c in DIGITS:
            self._read_int_constant()
        elif c in STRING_DELIMS:
            self._read_str_constant()
        elif c in WORDS:
            self._read_keyword_or_identifier()
        elif c == EOF:
            self.done = True
            self.valid = False
        else:
            raise RuntimeError(f"Unkown Token: {c}")

    def _ignore_whitespaces_and_comments(self) -> None:
        c = self._peek()
        while c in WHITESPACES or c == '/':
            if c in WHITESPACES:
                self._ignore_whitespace()
            elif c == '/':
                c = self._peek(offset=1)
                if c == '/':
                    self._ignore_line_comment()
                elif c == '*':
                    self._ignore_block_comment()
                else:
                    break
            c = self._peek()

    def _ignore_whitespace(self) -> None:
        c = self._read()
        while c in WHITESPACES:
            c = self._read()
        self._unread()

    def _ignore_line_comment(self) -> None:
        c = self._read()
        while c != '\n':
            c = self._read()

    def _ignore_block_comment(self) -> None:
        pre = self._read()      # '/'
        cur = self._read()      # '*'
        while not (pre == '*' and cur == '/'):
            pre, cur = cur, self._read()

    def _read_symbol(self) -> None:
        c = self._read()
        self.cur_type = TokenType.SYMBOL
        self.cur_symbol = c
        self.valid = True

    def _read_int_constant(self) -> None:
        chars = []
        c = self._read()
        while c in DIGITS:
            chars.append(c)
            c = self._read()
        self._unread()
        self.cur_type = TokenType.INT_CONST
        self.cur_int_val = int(''.join(chars))
        self.valid = True

    def _read_str_constant(self) -> None:
        self._read()            # '"'
        chars = []
        c = self._read()
        while not c in STRING_DELIMS:
            chars.append(c)
            c = self._read()
        self.cur_type = TokenType.STR_CONST
        self.cur_str_val = ''.join(chars)
        self.valid = True

    def _read_keyword_or_identifier(self):
        chars = []
        c = self._read()
        while c in WORDS:
            chars.append(c)
            c = self._read()
        self._unread()
        text = ''.join(chars)
        if text in KEYWORDS:
            self.cur_type = TokenType.KEYWORD
            self.cur_keyword = KeywordType.value_to_member(text)
            self.valid = True
        else:
            self.cur_type = TokenType.IDENTIFIER
            self.cur_identifier = text
            self.valid = True

    def _peek(self, offset=0) -> str:
        self.last_pos = self.f.tell()
        i = 0
        c = self.f.read(1)
        while i < offset:
            c = self.f.read(1)
            i += 1
        self.f.seek(self.last_pos, io.SEEK_SET)
        return c

    def _read(self) -> str:
        self.last_pos = self.f.tell()
        return self.f.read(1)

    def _unread(self):
        self.f.seek(self.last_pos, io.SEEK_SET)
