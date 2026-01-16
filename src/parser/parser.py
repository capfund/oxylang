class ASTNode:
    def __init__(self, type_, value=None, children=None):
        self.type = type_
        self.value = value
        self.children = children or []

    def __repr__(self):
        return f"{self.type}({self.value}, {self.children})"


class Parser:
    TYPE_TOKENS = {
        "INT", "INT16", "INT32", "INT64",
        "CHAR", "FLOAT", "VOID", "FN"
    }

    PRECEDENCE = {
        'ASSIGN': 0, 'PLUS_ASSIGN': 0, 'MINUS_ASSIGN': 0,
        'MULT_ASSIGN': 0, 'DIV_ASSIGN': 0, 'MOD_ASSIGN': 0,
        'OR': 1, 'AND': 2,
        'EQ': 3, 'NE': 3,
        'LT': 4, 'LE': 4, 'GT': 4, 'GE': 4,
        'PLUS': 5, 'MINUS': 5,
        'MULTIPLY': 6, 'DIVIDE': 6, 'MOD': 6,
    }

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos]

    def peek(self, offset=1):
        return self.tokens[self.pos + offset]

    def advance(self):
        self.pos += 1

    def eat(self, t):
        tok = self.current()
        if tok.type != t:
            raise SyntaxError(f"error: expected {t}, got {tok}")
        self.advance()
        return tok
    
    def eat_type(self):
        if self.current().type not in self.TYPE_TOKENS:
            raise SyntaxError(f"error: expected type, got {self.current()}")
        return self.eat(self.current().type)

    def parse(self):
        nodes = []
        while self.current().type != "EOF":
            nodes.append(self.parse_declaration_or_statement())
        return ASTNode("PROGRAM", children=nodes)

    def parse_declaration_or_statement(self):
        tok = self.current()

        if tok.type in self.TYPE_TOKENS:
            return self.parse_declaration_or_function()

        return self.parse_statement()

    def parse_declaration_or_function(self):
        tok = self.current()
        
        if tok.type == "FN":
            self.eat("FN")
            name = self.eat("IDENTIFIER").value

            self.eat("LPAREN")
            params = self.parse_parameters()
            self.eat("RPAREN")

            self.eat("ARROW")
            return_type_tok = self.eat_type()
            return_type = ASTNode("TYPE", return_type_tok.type)

            self.eat("LBRACE")
            body = self.parse_block()
            self.eat("RBRACE")

            return ASTNode("FUNCTION", name, [return_type, ASTNode("PARAMS", children=params), ASTNode("BODY", children=body)])

        if tok.type in self.TYPE_TOKENS:
            type_tok = self.current()
            self.advance()
            is_ptr = False
            if self.current().type == "MULTIPLY":
                is_ptr = True
                self.advance()
            name = self.eat("IDENTIFIER").value

            array_size = None
            if self.current().type == "LBRACKET":
                self.advance()
                array_size = self.eat("NUMBER").value
                self.eat("RBRACKET")

            type_name = type_tok.type + ("_PTR" if is_ptr else "")
            type_node = ASTNode("TYPE", type_name,
                                [ASTNode("ARRAY_SIZE", array_size)] if array_size else [])

            if self.current().type == "LPAREN":
                self.advance()
                params = self.parse_parameters()
                self.eat("RPAREN")
                self.eat("LBRACE")
                body = self.parse_block()
                self.eat("RBRACE")
                return ASTNode("FUNCTION", name, [type_node, ASTNode("PARAMS", children=params), ASTNode("BODY", children=body)])

            init = None
            if self.current().type == "ASSIGN":
                self.advance()
                init = self.parse_expression()

            self.eat("SEMICOLON")
            return ASTNode("VAR_DECL", name, [type_node, init] if init else [type_node])

    def parse_parameters(self):
        params = []
        while self.current().type != "RPAREN":
            t = self.current()
            self.advance()
            name = self.eat("IDENTIFIER").value
            params.append(ASTNode("PARAM", name, [ASTNode("TYPE", t.type)]))
            if self.current().type == "COMMA":
                self.advance()
        return params

    def parse_block(self):
        stmts = []
        while self.current().type != "RBRACE":
            stmts.append(self.parse_declaration_or_statement())
        return stmts


    def parse_statement(self):
        tok = self.current()

        if tok.type == "UNSAFE":
            return self.parse_unsafe()

        if tok.type == "RET":
            self.advance()
            expr = None
            if self.current().type != "SEMICOLON":
                expr = self.parse_expression()
            self.eat("SEMICOLON")
            return ASTNode("RETURN", children=[expr] if expr else [])

        if tok.type == "IF":
            return self.parse_if()

        if tok.type == "WHILE":
            return self.parse_while()

        if tok.type == "FOR":
            return self.parse_for()

        expr = self.parse_expression()
        self.eat("SEMICOLON")
        return expr

    def parse_unsafe(self):
        self.eat("UNSAFE")
        self.eat("LBRACE")
        body = self.parse_block()
        self.eat("RBRACE")
        return ASTNode("UNSAFE_BLOCK", children=body)

    def parse_if(self):
        self.eat("IF")
        self.eat("LPAREN")
        cond = self.parse_expression()
        self.eat("RPAREN")
        self.eat("LBRACE")
        then = self.parse_block()
        self.eat("RBRACE")

        else_block = []
        if self.current().type == "ELSE":
            self.advance()
            self.eat("LBRACE")
            else_block = self.parse_block()
            self.eat("RBRACE")

        return ASTNode("IF", children=[cond, ASTNode("THEN", children=then), ASTNode("ELSE", children=else_block)])

    def parse_while(self):
        self.eat("WHILE")
        self.eat("LPAREN")
        cond = self.parse_expression()
        self.eat("RPAREN")
        self.eat("LBRACE")
        body = self.parse_block()
        self.eat("RBRACE")
        return ASTNode("WHILE", children=[cond, ASTNode("BODY", children=body)])

    def parse_for(self):
        self.eat("FOR")
        self.eat("LPAREN")
        init = self.parse_expression() if self.current().type != "SEMICOLON" else None
        self.eat("SEMICOLON")
        cond = self.parse_expression() if self.current().type != "SEMICOLON" else None
        self.eat("SEMICOLON")
        step = self.parse_expression() if self.current().type != "RPAREN" else None
        self.eat("RPAREN")
        self.eat("LBRACE")
        body = self.parse_block()
        self.eat("RBRACE")
        return ASTNode("FOR", children=[init, cond, step, ASTNode("BODY", children=body)])

    def parse_expression(self, min_prec=0):
        left = self.parse_primary()

        while self.current().type in self.PRECEDENCE:
            prec = self.PRECEDENCE[self.current().type]
            if prec < min_prec:
                break
            op = self.current()
            self.advance()
            right = self.parse_expression(prec + 1)
            left = ASTNode("BIN_OP", op.type, [left, right])

        return left

    def parse_primary(self):
        tok = self.current()

        if tok.type == "NUMBER":
            self.advance()
            return ASTNode("NUMBER", tok.value)

        if tok.type == "STRING":
            self.advance()
            return ASTNode("STRING", tok.value)

        if tok.type == "IDENTIFIER":
            if self.peek().type == "LPAREN":
                return self.parse_call()
            self.advance()
            return ASTNode("IDENTIFIER", tok.value)

        if tok.type == "LPAREN":
            self.advance()
            expr = self.parse_expression()
            self.eat("RPAREN")
            return expr

        raise SyntaxError(f"Unexpected token {tok}")

    def parse_call(self):
        name = self.eat("IDENTIFIER").value
        self.eat("LPAREN")
        args = []
        while self.current().type != "RPAREN":
            args.append(self.parse_expression())
            if self.current().type == "COMMA":
                self.advance()
        self.eat("RPAREN")
        return ASTNode("CALL", name, args)
