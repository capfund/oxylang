class Token:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"{self.type}" if self.value is None else f"({self.type}, {self.value})"


class Lexer:
    KEYWORDS = {
        "char", "int", "int16", "int32", "int64",
        "float", "void",
        "ret", "fn", "if", "else", "while", "for",
        "break", "continue", "unsafe", "include", "extern"
    }

    SYMBOLS = {
        '=': "ASSIGN", ';': "SEMICOLON", ',': "COMMA",
        '(': "LPAREN", ')': "RPAREN",
        '{': "LBRACE", '}': "RBRACE",
        '[': "LBRACKET", ']': "RBRACKET"
    }

    OPERATORS = {
        '+': "PLUS", '-': "MINUS", '*': "MULTIPLY", '/': "DIVIDE", '%': "MOD",
        '==': "EQ", '!=': "NE", '<=': "LE", '>=': "GE", '<': "LT", '>': "GT",
        '&&': "AND", '||': "OR", '!': "NOT",
        '+=': "PLUS_ASSIGN", '-=': "MINUS_ASSIGN",
        '*=': "MULT_ASSIGN", '/=': "DIV_ASSIGN", '%=': "MOD_ASSIGN",
        '&': "AMPERSAND", '++': "INCREMENT", '--': "DECREMENT", "%": "MOD", "^": "POW"
    }

    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.ln = 1

    def current_char(self):
        return self.text[self.pos] if self.pos < len(self.text) else None

    def peek(self, offset=1):
        return self.text[self.pos + offset] if self.pos + offset < len(self.text) else None

    def advance(self, steps=1):
        self.pos += steps

    def skip_whitespace(self):
        while self.current_char() and self.current_char().isspace():
            if self.current_char() == '\n':
                self.ln += 1
            self.advance()

    def skip_comment(self):
        if self.current_char() == '/' and self.peek() == '/':
            self.advance(2)
            while self.current_char() and self.current_char() != '\n':
                self.advance()
        elif self.current_char() == '/' and self.peek() == '*':
            self.advance(2)
            while self.current_char() and not (self.current_char() == '*' and self.peek() == '/'):
                self.advance()
            self.advance(2)

    def lex_number(self):
        start = self.pos
        has_dot = False
        while self.current_char() and (self.current_char().isdigit() or self.current_char() == '.'):
            if self.current_char() == '.':
                has_dot = True
            self.advance()
        val = self.text[start:self.pos]
        return Token("NUMBER", float(val) if has_dot else int(val))

    def lex_string(self):
        quote = self.current_char()
        self.advance()
        start = self.pos
        value = ""

        while self.current_char() and self.current_char() != quote:
            if self.current_char() == '\\':
                self.advance()
                if self.current_char() == 'n':
                    #value += ' 10'
                    value += '\n'
                elif self.current_char() == 't':
                    value += '    '
                # Add more escape sequences as needed
                else:
                    value += self.current_char()
            else:
                value += self.current_char()
            self.advance()

        self.advance()  # Skip the closing quote
        return Token("STRING", value)

    def lex_char(self):
        self.advance()
        ch = self.current_char()

        if ch is None:
            raise SyntaxError(f"error: unterminated character literal (line {self.ln}, col {self.pos})")

        value = ord(ch)
        self.advance()

        if self.current_char() != "'":
            raise SyntaxError(f"error: character literal must be one character (line {self.ln}, col {self.pos})")

        self.advance()
        return Token("CHAR_LIT", value)

    def lex_identifier_or_keyword(self):
        start = self.pos
        while self.current_char() and (self.current_char().isalnum() or self.current_char() == '_'):
            self.advance()
        word = self.text[start:self.pos]
        if word in self.KEYWORDS:
            return Token(word.upper())
        return Token("IDENTIFIER", word)

    def lex_operator_or_symbol(self):
        two = (self.current_char() or '') + (self.peek() or '')
        if two == "->":
            self.advance(2)
            return Token("ARROW")
        if two in self.OPERATORS:
            self.advance(2)
            return Token(self.OPERATORS[two])
        if self.current_char() in self.OPERATORS:
            ch = self.current_char()
            self.advance()
            return Token(self.OPERATORS[ch])
        if self.current_char() in self.SYMBOLS:
            ch = self.current_char()
            self.advance()
            return Token(self.SYMBOLS[ch])
        raise SyntaxError(f"Unknown character {self.current_char()}")

    def tokenize(self):
        tokens = []
        while self.current_char():
            if self.current_char().isspace():
                self.skip_whitespace()
            elif self.current_char() == '/' and self.peek() in ('/', '*'):
                self.skip_comment()
            elif self.current_char().isdigit():
                tokens.append(self.lex_number())
            elif self.current_char() == '"':
                tokens.append(self.lex_string())
            elif self.current_char() == "'":
                tokens.append(self.lex_char())
            elif self.current_char().isalpha() or self.current_char() == '_':
                tokens.append(self.lex_identifier_or_keyword())
            else:
                tokens.append(self.lex_operator_or_symbol())
        tokens.append(Token("EOF"))
        return tokens