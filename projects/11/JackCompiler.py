import argparse
from pathlib import Path
import re
from typing import TextIO
from Constants import Text, Pattern
from JackTokenizer import JackTokenizer, TokenType
from SymbolTable import SymbolTable, Kind
from VMWriter import VMWriter, Segment, Command


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
                src_path.name.replace('.jack', '.vm'))
            with open(file=dst_path, mode='w', encoding='utf-8') as dst:
                engine = CompilationEngine(src=src, dst=dst)
                try:
                    engine.compile_class()
                except RuntimeError as e:
                    print(f'In {src_path.relative_to(cwd)} ' +
                          f'(line {engine.tokenizer.line_number()}): {e}')


class CompilationEngine():
    """
    Runs the compilation process.
    """

    def __init__(self, src: TextIO, dst: TextIO) -> None:
        """
        Creates a new compilation engine with the given input and output.

        The next routine called must be `compileClass`.
        """
        self.tokenizer = JackTokenizer(f=src)
        self.vm_writer = VMWriter(f=dst)
        self.symbol_table = SymbolTable()

        # Current class name
        self.class_name = None
        # Subroutine-level label index for `if` statements
        self.if_label_index = 0
        # Subroutine-level label index for `while` statements
        self.while_label_index = 0

        self._advance_token()

    def compile_class(self) -> None:
        """
        Compiles a complete class.
        """
        self.read(pattern=Text.CLASS)
        self.class_name = self.read(pattern=Pattern.IDENTIFIER)
        self.read(pattern=Text.LEFT_CURLY_BRACKET)
        while self.match(pattern=Pattern.CLASS_VAR_DEC_START):
            self.compile_class_var_dec()
        while self.match(pattern=Pattern.SUBROUTINE_DEC_START):
            self.compile_subroutine()
        self.read(pattern=Text.RIGHT_CURLY_BRACKET)

    def compile_class_var_dec(self) -> None:
        """
        Compiles a static variable declaration, or a field declaration.
        """
        kind = Kind.value_to_member(
            self.read(pattern=Pattern.CLASS_VAR_DEC_START))
        type = self.read(pattern=Pattern.TYPE)
        name = self.read(pattern=Pattern.VAR_NAME)
        self.symbol_table.define(name=name, type=type, kind=kind)
        while self.match(pattern=Text.COMMA):
            self.read(pattern=Text.COMMA)
            name = self.read(pattern=Pattern.VAR_NAME)
            self.symbol_table.define(name=name, type=type, kind=kind)
        self.read(pattern=Text.SEMICOLON)

    def compile_subroutine(self) -> None:
        """
        Compiles a complete method, function, or constructor.
        """
        subroutine = self.read(pattern=Pattern.SUBROUTINE_DEC_START)
        type = self.read(pattern=Pattern.SUBROUTINE_TYPE)
        name = self.read(pattern=Pattern.SUBROUTINE_NAME)

        # Reset subroutine-level symbol table
        if subroutine == Text.CONSTRUCTOR or subroutine == Text.METHOD:
            self.symbol_table.resetSubroutine(enable_fields=True)
        else:
            self.symbol_table.resetSubroutine(enable_fields=False)
        # Reset subroutine-level label indexes
        self.if_label_index = 0
        self.while_label_index = 0

        self.read(pattern=Text.LEFT_ROUND_BRACKET)
        if subroutine == Text.METHOD:
            self.symbol_table.define(
                name=Text.THIS, type=self.class_name, kind=Kind.ARG)
        self.compile_parameter_list()
        self.read(pattern=Text.RIGHT_ROUND_BRACKET)

        var_count = 0
        self.read(pattern=Text.LEFT_CURLY_BRACKET)
        while self.match(pattern=Text.VAR):
            var_count += self.compile_var_dec()
        self.vm_writer.write_function(
            name=f'{self.class_name}.{name}', n_vars=var_count)

        if subroutine == Text.CONSTRUCTOR:
            self.vm_writer.write_push(
                segment=Segment.CONSTANT, index=self.symbol_table.field_count())
            self.vm_writer.write_call(name='Memory.alloc', n_args=1)
            self.vm_writer.write_pop(segment=Segment.POINTER, index=0)
        elif subroutine == Text.METHOD:
            self.vm_writer.write_push(segment=Segment.ARGUMENT, index=0)
            self.vm_writer.write_pop(segment=Segment.POINTER, index=0)

        if self.match(pattern=Pattern.STATEMENT_START):
            self.compile_statements()

        self.read(pattern=Text.RIGHT_CURLY_BRACKET)

    def compile_parameter_list(self) -> None:
        """
        Compiles a (possibly empty) parameter list.
        """
        if self.match(pattern=Pattern.TYPE):
            type = self.read(pattern=Pattern.TYPE)
            name = self.read(pattern=Pattern.VAR_NAME)
            self.symbol_table.define(name=name, type=type, kind=Kind.ARG)
            while self.match(pattern=Text.COMMA):
                self.read(pattern=Text.COMMA)
                type = self.read(pattern=Pattern.TYPE)
                name = self.read(pattern=Pattern.VAR_NAME)
                self.symbol_table.define(
                    name=name, type=type, kind=Kind.ARG)

    def compile_var_dec(self) -> int:
        """
        Compiles a `var` declaration.
        Returns the number of declared variables in the statement.
        """
        count = 0
        self.read(pattern=Text.VAR)
        type = self.read(pattern=Pattern.TYPE)
        name = self.read(pattern=Pattern.VAR_NAME)
        self.symbol_table.define(name=name, type=type, kind=Kind.VAR)
        count += 1
        while self.match(pattern=Text.COMMA):
            self.read(pattern=Text.COMMA)
            name = self.read(pattern=Pattern.VAR_NAME)
            self.symbol_table.define(name=name, type=type, kind=Kind.VAR)
            count += 1
        self.read(pattern=Text.SEMICOLON)
        return count

    def compile_statements(self) -> None:
        """
        Compiles a sequence of statements.
        """
        while self.match(pattern=Pattern.STATEMENT_START):
            if self.match(pattern=Text.LET):
                self.compile_let()
            elif self.match(pattern=Text.IF):
                self.compile_if()
            elif self.match(pattern=Text.WHILE):
                self.compile_while()
            elif self.match(pattern=Text.DO):
                self.compile_do()
            elif self.match(pattern=Text.RETURN):
                self.compile_return()

    def compile_let(self) -> None:
        """
        Compiles a `let` statement.
        """
        self.read(pattern=Text.LET)

        var_name = self.read(pattern=Pattern.VAR_NAME)
        kind = self.symbol_table.kind_of(var_name)
        index = self.symbol_table.index_of(var_name)

        is_arr = False
        if self.match(pattern=Text.LEFT_SQUARE_BRACKET):
            is_arr = True
            self.read(pattern=Text.LEFT_SQUARE_BRACKET)
            self.compile_expression()
            self.vm_writer.write_push(
                segment=Segment.from_kind(kind=kind), index=index)
            self.vm_writer.write_arithmetic(command=Command.ADD)
            self.read(pattern=Text.RIGHT_SQUARE_BRACKET)
        self.read(pattern=Text.ASSIGNMENT)
        self.compile_expression()
        if not is_arr:
            self.vm_writer.write_pop(
                segment=Segment.from_kind(kind=kind), index=index)
        else:
            self.vm_writer.write_pop(segment=Segment.TEMP, index=0)
            self.vm_writer.write_pop(segment=Segment.POINTER, index=1)
            self.vm_writer.write_push(segment=Segment.TEMP, index=0)
            self.vm_writer.write_pop(segment=Segment.THAT, index=0)
        self.read(pattern=Text.SEMICOLON)

    def compile_if(self) -> None:
        """
        Compiles an `if` statement, possibly with a trailing `else` clause.
        """
        self.read(pattern=Text.IF)

        cur_label_index = self.if_label_index
        self.if_label_index += 1

        self.read(pattern=Text.LEFT_ROUND_BRACKET)
        self.compile_expression()
        self.vm_writer.write_if(f'IF_TRUE{cur_label_index}')
        self.vm_writer.write_goto(f'IF_FALSE{cur_label_index}')
        self.read(pattern=Text.RIGHT_ROUND_BRACKET)

        self.read(pattern=Text.LEFT_CURLY_BRACKET)
        self.vm_writer.write_label(f'IF_TRUE{cur_label_index}')
        self.compile_statements()
        self.read(pattern=Text.RIGHT_CURLY_BRACKET)

        if self.match(pattern=Text.ELSE):
            self.read(pattern=Text.ELSE)
            self.read(pattern=Text.LEFT_CURLY_BRACKET)
            self.vm_writer.write_goto(f'IF_END{cur_label_index}')
            self.vm_writer.write_label(f'IF_FALSE{cur_label_index}')
            self.compile_statements()
            self.vm_writer.write_label(f'IF_END{cur_label_index}')
            self.read(pattern=Text.RIGHT_CURLY_BRACKET)
        else:
            self.vm_writer.write_label(f'IF_FALSE{cur_label_index}')

    def compile_while(self) -> None:
        """
        Compiles a `while` statement.
        """
        self.read(pattern=Text.WHILE)

        cur_label_index = self.while_label_index
        self.while_label_index += 1

        self.read(pattern=Text.LEFT_ROUND_BRACKET)
        self.vm_writer.write_label(f'WHILE_EXP{cur_label_index}')
        self.compile_expression()
        self.vm_writer.write_arithmetic(Command.NOT)
        self.vm_writer.write_if(f'WHILE_END{cur_label_index}')
        self.read(pattern=Text.RIGHT_ROUND_BRACKET)

        self.read(pattern=Text.LEFT_CURLY_BRACKET)
        self.compile_statements()
        self.vm_writer.write_goto(f'WHILE_EXP{cur_label_index}')
        self.vm_writer.write_label(f'WHILE_END{cur_label_index}')
        self.read(pattern=Text.RIGHT_CURLY_BRACKET)

    def compile_do(self) -> None:
        """
        Compiles a `do` statement.
        """
        self.read(pattern=Text.DO)
        self.compile_expression()
        self.vm_writer.write_pop(segment=Segment.TEMP, index=0)
        self.read(Text.SEMICOLON)

    def compile_return(self) -> None:
        """
        Compiles a `return` statement.
        """
        self.read(pattern=Text.RETURN)
        if not self.match(pattern=Text.SEMICOLON):
            self.compile_expression()
        else:
            self.vm_writer.write_push(segment=Segment.CONSTANT, index=0)
        self.vm_writer.write_return()
        self.read(pattern=Text.SEMICOLON)

    def compile_expression(self) -> None:
        """
        Compiles an expression.
        """
        self.compile_term()
        if self.match(pattern=Pattern.OP):
            op = self.read(pattern=Pattern.OP)
            self.compile_term()
            if op == Text.ADDITION:
                self.vm_writer.write_arithmetic(Command.ADD)
            elif op == Text.SUBTRACTION:
                self.vm_writer.write_arithmetic(Command.SUB)
            elif op == Text.MULTIPLICATION:
                self.vm_writer.write_call(name='Math.multiply', n_args=2)
            elif op == Text.DIVISION:
                self.vm_writer.write_call(name='Math.divide', n_args=2)
            elif op == Text.ASSIGNMENT:
                self.vm_writer.write_arithmetic(Command.EQ)
            elif op == Text.GREATER_THAN:
                self.vm_writer.write_arithmetic(Command.GT)
            elif op == Text.LESS_THAN:
                self.vm_writer.write_arithmetic(Command.LT)
            elif op == Text.BITWISE_AND:
                self.vm_writer.write_arithmetic(Command.AND)
            elif op == Text.BITWISE_OR:
                self.vm_writer.write_arithmetic(Command.OR)

    def compile_term(self) -> None:
        """
        Compiles a `term`.
        """
        if self.match(pattern=Pattern.INTEGER_CONSTANT):
            int_const = self.read(pattern=Pattern.INTEGER_CONSTANT)
            self.vm_writer.write_push(
                segment=Segment.CONSTANT, index=int(int_const))
        elif self.match(pattern=TokenType.STR_CONST):
            str_const = self.read(pattern=TokenType.STR_CONST)
            self.vm_writer.write_push(
                segment=Segment.CONSTANT, index=len(str_const))
            self.vm_writer.write_call(name='String.new', n_args=1)
            for c in list(str_const):
                self.vm_writer.write_push(
                    segment=Segment.CONSTANT, index=ord(c))
                self.vm_writer.write_call(name='String.appendChar', n_args=2)
        elif self.match(pattern=Pattern.KEYWORD_CONSTANT):
            keyword_const = self.read(pattern=Pattern.KEYWORD_CONSTANT)
            if keyword_const == Text.FALSE or keyword_const == Text.NULL:
                self.vm_writer.write_push(segment=Segment.CONSTANT, index=0)
            elif keyword_const == Text.TRUE:
                self.vm_writer.write_push(segment=Segment.CONSTANT, index=0)
                self.vm_writer.write_arithmetic(command=Command.NOT)
            elif keyword_const == Text.THIS:
                self.vm_writer.write_push(segment=Segment.POINTER, index=0)
        elif self.match(pattern=Pattern.IDENTIFIER):
            identifier = self.read(pattern=Pattern.IDENTIFIER)
            if self.match(pattern=Text.LEFT_SQUARE_BRACKET):
                # varName'['expression']'
                var_name = identifier
                kind = self.symbol_table.kind_of(var_name)
                index = self.symbol_table.index_of(var_name)
                self.read(pattern=Text.LEFT_SQUARE_BRACKET)
                self.compile_expression()
                self.vm_writer.write_push(
                    segment=Segment.from_kind(kind=kind), index=index)
                self.vm_writer.write_arithmetic(command=Command.ADD)
                self.vm_writer.write_pop(segment=Segment.POINTER, index=1)
                self.vm_writer.write_push(segment=Segment.THAT, index=0)
                self.read(pattern=Text.RIGHT_SQUARE_BRACKET)
            elif self.match(pattern=Text.ELEMENT_SELECTION):
                # (className | varName)'.'subroutineName'('expressionList')'
                self.read(pattern=Text.ELEMENT_SELECTION)
                if self.symbol_table.contains(identifier):
                    # varName'.'methodName'('expressionList')'
                    var_name = identifier
                    kind = self.symbol_table.kind_of(var_name)
                    index = self.symbol_table.index_of(var_name)
                    type = self.symbol_table.type_of(var_name)
                    self.vm_writer.write_push(
                        segment=Segment.from_kind(kind=kind), index=index)
                    method_name = self.read(
                        pattern=Pattern.SUBROUTINE_NAME)
                    self.read(pattern=Text.LEFT_ROUND_BRACKET)
                    arg_count = self.compile_expression_list()
                    self.read(pattern=Text.RIGHT_ROUND_BRACKET)
                    self.vm_writer.write_call(
                        name=f'{type}.{method_name}', n_args=1 + arg_count)
                else:
                    # className'.'(constructorName | functionName)'('expressionList')'
                    class_name = identifier
                    subroutine_name = self.read(
                        pattern=Pattern.SUBROUTINE_NAME)
                    self.read(pattern=Text.LEFT_ROUND_BRACKET)
                    arg_count = self.compile_expression_list()
                    self.read(pattern=Text.RIGHT_ROUND_BRACKET)
                    self.vm_writer.write_call(
                        name=f'{class_name}.{subroutine_name}', n_args=arg_count)
            elif self.match(pattern=Text.LEFT_ROUND_BRACKET):
                # subroutineName'('expressionList')'
                method_name = identifier
                # Push `this` as first argument
                self.vm_writer.write_push(segment=Segment.POINTER, index=0)
                self.read(pattern=Text.LEFT_ROUND_BRACKET)
                arg_count = self.compile_expression_list()
                self.read(pattern=Text.RIGHT_ROUND_BRACKET)
                self.vm_writer.write_call(
                    name=f'{self.class_name}.{method_name}', n_args=1 + arg_count)
            else:
                # varName
                var_name = identifier
                kind = self.symbol_table.kind_of(var_name)
                index = self.symbol_table.index_of(var_name)
                self.vm_writer.write_push(
                    segment=Segment.from_kind(kind=kind), index=index)
        elif self.match(pattern=Text.LEFT_ROUND_BRACKET):
            # '('expression')'
            self.read(pattern=Text.LEFT_ROUND_BRACKET)
            self.compile_expression()
            self.read(pattern=Text.RIGHT_ROUND_BRACKET)
        elif self.match(pattern=Pattern.UNARYOP):
            # (unaryOp term)
            unaryop = self.read(pattern=Pattern.UNARYOP)
            self.compile_term()
            if unaryop == Text.UNARY_MINUS:
                self.vm_writer.write_arithmetic(command=Command.NEG)
            elif unaryop == Text.BITWISE_NOT:
                self.vm_writer.write_arithmetic(command=Command.NOT)

    def compile_expression_list(self) -> int:
        """
        Compiles a (possibly empty) comma-separated list of expressions.
        Returns the number of expressions in the list.
        """
        count = 0
        if self.match(pattern=Pattern.TERM_START_PART) or \
                self.match(pattern=TokenType.STR_CONST):
            self.compile_expression()
            count += 1
            while self.match(pattern=Text.COMMA):
                self.read(pattern=Text.COMMA)
                self.compile_expression()
                count += 1
        return count

    def read(self, pattern: str | re.Pattern | TokenType) -> str:
        """
        A helper routine that validates and gets current token, and advances 
        to get the next token. 
        """
        self.validate(pattern=pattern)
        cur_content = self._get_token_content()
        self._advance_token()
        return cur_content

    def match(self, pattern: str | re.Pattern | TokenType) -> bool:
        """
        A helper function that checks current token. Return whether current
        token matches the pattern of the expected token.
        """
        try:
            self.validate(pattern=pattern)
            return True
        except SyntaxError:
            return False

    def validate(self, pattern: str | re.Pattern | TokenType) -> None:
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
