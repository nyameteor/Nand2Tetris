#!/usr/bin/env python3

import argparse
from pathlib import Path
import re
from typing import Self
from JackTokenizer import JackTokenizer
from Constants import TokenType, Pattern, Text


def main() -> None:
    argparser = argparse.ArgumentParser(
        description='A syntax analyzer for the Jack language'
    )
    argparser.add_argument(
        'source',
        metavar='SOURCE',
        help='SOURCE is either a file name of the form Xxx.jack \
            or the name of a folder containing one or more .jack files'
    )
    args = argparser.parse_args()

    cwd = Path.cwd()
    source = cwd.joinpath(args.source)
    if source.is_file():
        src_paths = [source]
    elif source.is_dir():
        src_paths = list(source.glob('*.jack'))
    else:
        return
    for src_path in src_paths:
        with open(file=src_path, mode='r', encoding='utf-8') as src:
            dst_path = src_path.parent.joinpath(
                src_path.name.replace('.jack', '.xml'))
            with open(file=dst_path, mode='w', encoding='utf-8') as dst:
                engine = CompilationEngine(tokenizer=JackTokenizer(f=src))
                dst.write(engine.compile_class().to_xml())


class Node:
    def __init__(self, name: str, content: str | list[Self]) -> None:
        self.name = name
        self.content = content

    @classmethod
    def new_tree(cls, name: str) -> Self:
        return cls(name=name, content=[])

    @classmethod
    def new_leaf(cls, name: str, content: str) -> Self:
        return cls(name=name, content=content)

    def is_leaf(self) -> bool:
        return isinstance(self.content, str)

    def has_child(self) -> bool:
        if self.is_leaf():
            return False
        return len(self.content) > 0

    def append_child(self, node: Self) -> Self:
        """
        Append the child NODE to this node at the end of the list of children.
        """
        if self.is_leaf():
            raise RuntimeError(
                f"Node {self.name}: can not append child to a leaf node")
        self.content.append(node)
        return self

    def to_xml(self, indent=0) -> str:

        def escape(s: str) -> str:
            s = s.replace('&', '&amp;')
            s = s.replace('<', '&lt;')
            s = s.replace('>', '&gt;')
            s = s.replace('"', '&quot;')
            return s

        whitespace = ' ' * 2 * indent
        if self.is_leaf():
            return f'{whitespace}<{self.name}> {escape(self.content)} </{self.name}>\n'
        else:
            content = ''.join([
                Node.to_xml(self=child, indent=indent+1) for child in self.content
            ])
            return f'{whitespace}<{self.name}>\n{content}{whitespace}</{self.name}>\n'


class CompilationEngine():
    def __init__(self, tokenizer: JackTokenizer) -> None:
        self.tokenizer = tokenizer
        self._advance_token()

    def compile_class(self) -> Node:
        root = Node.new_tree(name="class")
        root.append_child(
            node=self.process(
                pattern=Text.CLASS
            )
        )
        root.append_child(
            node=self.process(
                pattern=Pattern.IDENTIFIER
            )
        )
        root.append_child(
            node=self.process(
                pattern=Text.LEFT_CURLY_BRACKET
            )
        )
        while self._check(pattern=Pattern.CLASS_VAR_DEC_START):
            root.append_child(
                node=self.compile_class_var_dec()
            )
        while self._check(pattern=Pattern.SUBROUTINE_DEC_START):
            root.append_child(
                node=self.compile_subroutine_dec()
            )
        root.append_child(
            node=self.process(
                pattern=Text.RIGHT_CURLY_BRACKET
            )
        )
        return root

    def compile_class_var_dec(self) -> Node:
        root = Node.new_tree(name="classVarDec")
        root.append_child(
            node=self.process(
                pattern=Pattern.CLASS_VAR_DEC_START
            )
        )
        root.append_child(
            node=self.process(
                pattern=Pattern.TYPE
            )
        )
        root.append_child(
            node=self.process(
                pattern=Pattern.VAR_NAME
            )
        )
        while self._check(pattern=Text.COMMA):
            root.append_child(
                node=self.process(
                    pattern=Text.COMMA
                )
            )
            root.append_child(
                node=self.process(
                    pattern=Pattern.VAR_NAME
                )
            )
        root.append_child(
            node=self.process(
                pattern=Text.SEMICOLON
            )
        )
        return root

    def compile_subroutine_dec(self) -> Node:
        root = Node.new_tree(name="subroutineDec")
        root.append_child(
            node=self.process(
                pattern=Pattern.SUBROUTINE_DEC_START
            )
        )
        root.append_child(
            node=self.process(
                pattern=Pattern.SUBROUTINE_TYPE
            )
        )
        root.append_child(
            node=self.process(
                pattern=Pattern.SUBROUTINE_NAME
            )
        )
        root.append_child(
            node=self.process(
                pattern=Text.LEFT_ROUND_BRACKET
            )
        )
        root.append_child(
            node=self.compile_parameter_list()
        )
        root.append_child(
            node=self.process(
                pattern=Text.RIGHT_ROUND_BRACKET
            )
        )
        root.append_child(
            node=self.compile_subroutine_body()
        )
        return root

    def compile_parameter_list(self) -> Node:
        root = Node.new_tree(name="parameterList")
        if self._check(pattern=Pattern.TYPE):
            root.append_child(
                node=self.process(
                    pattern=Pattern.TYPE
                )
            )
            root.append_child(
                node=self.process(
                    pattern=Pattern.VAR_NAME
                )
            )
            while self._check(pattern=Text.COMMA):
                root.append_child(
                    node=self.process(
                        pattern=Text.COMMA
                    )
                )
                root.append_child(
                    node=self.process(
                        pattern=Pattern.TYPE
                    )
                )
                root.append_child(
                    node=self.process(
                        pattern=Pattern.VAR_NAME
                    )
                )
        return root

    def compile_subroutine_body(self) -> Node:
        root = Node.new_tree(name="subroutineBody")
        root.append_child(
            node=self.process(
                pattern=Text.LEFT_CURLY_BRACKET
            )
        )
        while self._check(pattern=Text.VAR):
            root.append_child(
                node=self.compile_var_dec()
            )
        if self._check(pattern=Pattern.STATEMENT_START):
            root.append_child(
                node=self.compile_statements()
            )
        root.append_child(
            node=self.process(
                pattern=Text.RIGHT_CURLY_BRACKET
            )
        )
        return root

    def compile_var_dec(self) -> Node:
        root = Node.new_tree(name="varDec")
        root.append_child(
            node=self.process(
                pattern=Text.VAR
            )
        )
        root.append_child(
            node=self.process(
                pattern=Pattern.TYPE
            )
        )
        root.append_child(
            node=self.process(
                pattern=Pattern.VAR_NAME
            )
        )
        while self._check(pattern=Text.COMMA):
            root.append_child(
                node=self.process(
                    pattern=Text.COMMA
                )
            )
            root.append_child(
                node=self.process(
                    pattern=Pattern.VAR_NAME
                )
            )
        root.append_child(
            node=self.process(
                pattern=Text.SEMICOLON
            )
        )
        return root

    def compile_statements(self) -> Node:
        root = Node.new_tree(name="statements")
        while self._check(pattern=Pattern.STATEMENT_START):
            if self._check(pattern=Text.LET):
                root.append_child(
                    node=self.compile_let()
                )
            elif self._check(pattern=Text.IF):
                root.append_child(
                    node=self.compile_if()
                )
            elif self._check(pattern=Text.WHILE):
                root.append_child(
                    node=self.compile_while()
                )
            elif self._check(pattern=Text.DO):
                root.append_child(
                    node=self.compile_do()
                )
            elif self._check(pattern=Text.RETURN):
                root.append_child(
                    node=self.compile_return()
                )
        return root

    def compile_let(self) -> Node:
        root = Node.new_tree(name="letStatement")
        root.append_child(
            node=self.process(
                pattern=Text.LET
            )
        )
        root.append_child(
            node=self.process(
                pattern=Pattern.VAR_NAME
            )
        )
        if self._check(pattern=Text.LEFT_SQUARE_BRACKET):
            root.append_child(
                node=self.process(
                    pattern=Text.LEFT_SQUARE_BRACKET
                )
            )
            root.append_child(
                node=self.compile_expression()
            )
            root.append_child(
                node=self.process(
                    pattern=Text.RIGHT_SQUARE_BRACKET
                )
            )
        root.append_child(
            node=self.process(
                pattern=Text.ASSIGNMENT
            )
        )
        root.append_child(
            node=self.compile_expression()
        )
        root.append_child(
            node=self.process(
                pattern=Text.SEMICOLON
            )
        )
        return root

    def compile_if(self) -> Node:
        root = Node.new_tree(name="ifStatement")
        root.append_child(
            node=self.process(
                pattern=Text.IF
            )
        )
        root.append_child(
            node=self.process(
                pattern=Text.LEFT_ROUND_BRACKET
            )
        )
        root.append_child(
            node=self.compile_expression()
        )
        root.append_child(
            node=self.process(
                pattern=Text.RIGHT_ROUND_BRACKET
            )
        )
        root.append_child(
            node=self.process(
                pattern=Text.LEFT_CURLY_BRACKET
            )
        )
        root.append_child(
            node=self.compile_statements()
        )
        root.append_child(
            node=self.process(
                pattern=Text.RIGHT_CURLY_BRACKET
            )
        )
        if self._check(Text.ELSE):
            root.append_child(
                node=self.process(
                    pattern=Text.ELSE
                )
            )
            root.append_child(
                node=self.process(
                    pattern=Text.LEFT_CURLY_BRACKET
                )
            )
            root.append_child(
                node=self.compile_statements()
            )
            root.append_child(
                node=self.process(
                    pattern=Text.RIGHT_CURLY_BRACKET
                )
            )
        return root

    def compile_while(self) -> Node:
        root = Node.new_tree(name="whileStatement")
        root.append_child(
            node=self.process(
                pattern=Text.WHILE
            )
        )
        root.append_child(
            node=self.process(
                pattern=Text.LEFT_ROUND_BRACKET
            )
        )
        root.append_child(
            node=self.compile_expression()
        )
        root.append_child(
            node=self.process(
                pattern=Text.RIGHT_ROUND_BRACKET
            )
        )
        root.append_child(
            node=self.process(
                pattern=Text.LEFT_CURLY_BRACKET
            )
        )
        root.append_child(
            node=self.compile_statements()
        )
        root.append_child(
            node=self.process(
                pattern=Text.RIGHT_CURLY_BRACKET
            )
        )
        return root

    def compile_do(self) -> Node:
        root = Node.new_tree(name="doStatement")
        root.append_child(
            node=self.process(
                pattern=Text.DO
            )
        )
        root.append_child(
            node=self.process(
                pattern=Pattern.SUBROUTINE_CALL_START
            )
        )
        if self._check(pattern=Text.ELEMENT_SELECTION):
            root.append_child(
                node=self.process(
                    pattern=Text.ELEMENT_SELECTION
                )
            )
            root.append_child(
                node=self.process(
                    pattern=Pattern.SUBROUTINE_NAME
                )
            )
        root.append_child(
            node=self.process(
                pattern=Text.LEFT_ROUND_BRACKET
            )
        )
        root.append_child(
            node=self.compile_expression_list()
        )
        root.append_child(
            node=self.process(
                pattern=Text.RIGHT_ROUND_BRACKET
            )
        )
        root.append_child(
            node=self.process(
                pattern=Text.SEMICOLON
            )
        )
        return root

    def compile_return(self) -> Node:
        root = Node.new_tree(name="returnStatement")
        root.append_child(
            node=self.process(
                pattern=Text.RETURN
            )
        )
        if not self._check(pattern=Text.SEMICOLON):
            root.append_child(
                node=self.compile_expression()
            )
        root.append_child(
            node=self.process(
                pattern=Text.SEMICOLON
            )
        )
        return root

    def compile_expression(self) -> Node:
        root = Node.new_tree(name="expression")
        root.append_child(
            node=self.compile_term()
        )
        if self._check(pattern=Pattern.OP):
            root.append_child(
                node=self.process(
                    pattern=Pattern.OP
                )
            )
            root.append_child(
                node=self.compile_term()
            )
        return root

    def compile_term(self) -> Node:
        root = Node.new_tree(name="term")
        if self._check(pattern=Pattern.INTEGER_CONSTANT):
            root.append_child(
                node=self.process(
                    pattern=Pattern.INTEGER_CONSTANT
                )
            )
        elif self._check(pattern=TokenType.STR_CONST):
            root.append_child(
                node=self.process(
                    pattern=TokenType.STR_CONST
                )
            )
        elif self._check(pattern=Pattern.KEYWORD_CONSTANT):
            root.append_child(
                node=self.process(
                    pattern=Pattern.KEYWORD_CONSTANT
                )
            )
        elif self._check(pattern=Pattern.IDENTIFIER):
            root.append_child(
                node=self.process(
                    pattern=Pattern.IDENTIFIER
                )
            )
            if self._check(pattern=Text.LEFT_SQUARE_BRACKET):
                # varName'['expression']'
                root.append_child(
                    node=self.process(
                        pattern=Text.LEFT_SQUARE_BRACKET
                    )
                )
                root.append_child(
                    node=self.compile_expression()
                )
                root.append_child(
                    node=self.process(
                        pattern=Text.RIGHT_SQUARE_BRACKET
                    )
                )
            elif self._check(pattern=Text.ELEMENT_SELECTION):
                # (className | varName)'.'subroutineName'('expressionList')'
                root.append_child(
                    node=self.process(
                        pattern=Text.ELEMENT_SELECTION
                    )
                )
                root.append_child(
                    node=self.process(
                        pattern=Pattern.SUBROUTINE_NAME
                    )
                )
                root.append_child(
                    node=self.process(
                        pattern=Text.LEFT_ROUND_BRACKET
                    )
                )
                root.append_child(
                    node=self.compile_expression_list()
                )
                root.append_child(
                    node=self.process(
                        pattern=Text.RIGHT_ROUND_BRACKET
                    )
                )
            elif self._check(pattern=Text.LEFT_ROUND_BRACKET):
                # subroutineName'('expressionList')'
                root.append_child(
                    node=self.process(
                        pattern=Text.LEFT_ROUND_BRACKET
                    )
                )
                root.append_child(
                    node=self.compile_expression_list()
                )
                root.append_child(
                    node=self.process(
                        pattern=Text.RIGHT_ROUND_BRACKET
                    )
                )
        elif self._check(pattern=Text.LEFT_ROUND_BRACKET):
            # '('expression')'
            root.append_child(
                node=self.process(
                    pattern=Text.LEFT_ROUND_BRACKET
                )
            )
            root.append_child(
                node=self.compile_expression()
            )
            root.append_child(
                node=self.process(
                    pattern=Text.RIGHT_ROUND_BRACKET
                )
            )
        elif self._check(pattern=Pattern.UNARYOP):
            # (unaryOp term)
            root.append_child(
                node=self.process(
                    pattern=Pattern.UNARYOP
                )
            )
            root.append_child(
                node=self.compile_term()
            )
        return root

    def compile_expression_list(self) -> Node:
        root = Node.new_tree(name="expressionList")
        if self._check(pattern=Pattern.TERM_START_PART) or \
                self._check(pattern=TokenType.STR_CONST):
            root.append_child(
                node=self.compile_expression()
            )
            while self._check(pattern=Text.COMMA):
                root.append_child(
                    node=self.process(
                        pattern=Text.COMMA
                    )
                )
                root.append_child(
                    node=self.compile_expression()
                )
        return root

    def process(self, pattern: str | re.Pattern | TokenType) -> Node:
        """
        A helper routine that handles the current token, and advances to get 
        the next token. 
        """
        self._validate(pattern=pattern)

        cur_type = self._get_token_type()
        cur_content = self._get_token_content()

        node = Node(
            name=cur_type.value,
            content=cur_content
        )

        self._advance_token()

        return node

    def _check(self, pattern: str | re.Pattern | TokenType) -> bool:
        """
        A helper function that checks current token. Return whether current
        token is the expected token.
        """
        try:
            self._validate(pattern=pattern)
            return True
        except SyntaxError:
            return False

    def _validate(self, pattern: str | re.Pattern | TokenType) -> None:
        """
        A helper function that validates current token. Raise error if current 
        token is not the expected token.

        If PATTERN is an instance of str: 
            Validate PATTERN equals current token content.
        If PATTERN is an instance of re.Pattern: 
            Validate current token content matches the PATTERN.
        If PATTERN is an instance of TokenType: 
            Validate PATTERN equals current token type.
        """
        cur_type = self._get_token_type()
        cur_content = self._get_token_content()
        if isinstance(pattern, str):
            if pattern != cur_content:
                raise SyntaxError(
                    f"\nExpected: {pattern}" +
                    f"\nActual:   {cur_content}"
                )
        elif isinstance(pattern, re.Pattern):
            if not re.match(pattern, cur_content):
                raise SyntaxError(
                    f"\nExpected: {pattern}" +
                    f"\nActual:   {cur_content}"
                )
        elif isinstance(pattern, TokenType):
            if pattern != cur_type:
                raise SyntaxError(
                    f"\nExpected: {pattern}" +
                    f"\nActual:   {cur_type}"
                )

    def _get_token_type(self) -> TokenType:
        return self.tokenizer.token_type()

    def _get_token_content(self) -> str:
        type = self._get_token_type()
        if type == TokenType.KEYWORD:
            return self.tokenizer.keyword().value
        elif type == TokenType.SYMBOL:
            return self.tokenizer.symbol()
        elif type == TokenType.IDENTIFIER:
            return self.tokenizer.identifier()
        elif type == TokenType.INT_CONST:
            return str(self.tokenizer.int_val())
        elif type == TokenType.STR_CONST:
            return self.tokenizer.str_val()

    def _advance_token(self) -> None:
        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()


class SyntaxError(RuntimeError):
    pass


if __name__ == '__main__':
    main()
