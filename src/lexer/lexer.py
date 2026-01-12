import re

class Token:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value
    def __repr__(self):
        return f"{self.type}" if self.value is None else f"({self.type}, {self.value})"

class Lexer:
    KEYWORDS = {"char", "int", "float", "void", "return", "if", "else", "while", "for", "break", "continue"}
    
    SYMBOLS = {
        '=': "ASSIGN", ';': "SEMICOLON", ',': "COMMA",
        '(': "LPAREN", ')': "RPAREN", '{': "LBRACE", '}': "RBRACE"
    }
    
    OPERATORS = {
        '+': "PLUS", '-': "MINUS", '*': "MULTIPLY", '/': "DIVIDE", '%': "MOD",
        '==': "EQ", '!=': "NE", '<=': "LE", '>=': "GE", '<': "LT", '>': "GT",
        '&&': "AND", '||': "OR", '!': "NOT",
        '+=': "PLUS_ASSIGN", '-=': "MINUS_ASSIGN",
        '*=': "MULT_ASSIGN", '/=': "DIV_ASSIGN", '%=': "MOD_ASSIGN"
    }

    def __init__(self, text):
        self.text = text
        self.ln = 1
        self.pos = 0

    def current_char(self):
        return self.text[self.pos] if self.pos < len(self.text) else None

    def peek(self, offset=1):
        return self.text[self.pos + offset] if self.pos + offset < len(self.text) else None

    def advance(self, steps=1):
        self.pos += steps

    def skip_whitespace(self):
        while self.current_char() and self.current_char().isspace():
            self.advance()

    def skip_comment(self):
        if self.current_char() == '/' and self.peek() == '/':
            self.advance(2)
            while self.current_char() and self.current_char() != '\n':
                self.advance()
            if self.current_char() == '\n':
                self.ln += 1
            self.advance()
        elif self.current_char() == '/' and self.peek() == '*':
            self.advance(2)
            while self.current_char() and not (self.current_char() == '*' and self.peek() == '/'):
                self.advance()
            self.advance(2)

    def lex_number(self):
        start = self.pos
        has_dot = False
        while self.current_char() and (self.current_char().isdigit() or (self.current_char() == '.' and not has_dot)):
            if self.current_char() == '.':
                has_dot = True
            self.advance()
        num_str = self.text[start:self.pos]
        return Token("NUMBER", float(num_str) if '.' in num_str else int(num_str))

    def lex_string(self):
        quote_char = self.current_char()
        self.advance()
        start = self.pos
        while self.current_char() != quote_char:
            self.advance()
        if not self.current_char():
            raise SyntaxError(f"Unterminated string @ line {self.ln}")
        value = self.text[start:self.pos]
        self.advance()
        return Token("STRING", value)

    def lex_identifier_or_keyword(self):
        start = self.pos
        while self.current_char() and (self.current_char().isalnum() or self.current_char() == '_'):
            self.advance()
        word = self.text[start:self.pos]
        if word in self.KEYWORDS:
            return Token(word.upper())
        return Token("IDENTIFIER", word)

    def lex_operator_or_symbol(self):
        two_chars = self.current_char() + (self.peek() or '')
        if two_chars in self.OPERATORS:
            self.advance(2)
            return Token(self.OPERATORS[two_chars])
        if self.current_char() in self.OPERATORS:
            op = self.current_char()
            self.advance()
            return Token(self.OPERATORS[op])
        if self.current_char() in self.SYMBOLS:
            sym = self.current_char()
            self.advance()
            return Token(self.SYMBOLS[sym])
        #self.advance()
        raise SyntaxError(f"Unknown character: {self.current_char()} @ line {self.ln}")

    def tokenize(self):
        tokens = []
        while self.current_char():
            if self.current_char() == "\n":
                self.ln += 1
                self.advance()
                continue
            if self.current_char().isspace():
                self.skip_whitespace()
                continue
            if self.current_char() == '/' and self.peek() in ('/', '*'):
                self.skip_comment()
                continue
            char = self.current_char()
            if char.isdigit():
                tokens.append(self.lex_number())
            elif char in ('"', "'"):
                tokens.append(self.lex_string())
            elif char.isalpha() or char == '_':
                tokens.append(self.lex_identifier_or_keyword())
            else:
                tok = self.lex_operator_or_symbol()
                if tok:
                    tokens.append(tok)
        # add EOF...
        tokens.append(Token("EOF"))
        
        return tokens
    