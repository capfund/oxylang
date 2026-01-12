
class ASTNode:
    def __init__(self, type_, value=None, children=None):
        self.type = type_
        self.value = value
        self.children = children or []

    def __repr__(self):
        if self.children:
            return f"{self.type}({self.value}, {self.children})"
        return f"{self.type}({self.value})"


class Parser:
    PRECEDENCE = {
        'ASSIGN': 0, 'PLUS_ASSIGN': 0, 'MINUS_ASSIGN': 0,
        'MULT_ASSIGN': 0, 'DIV_ASSIGN': 0, 'MOD_ASSIGN': 0,

        'OR': 1,
        'AND': 2,
        'EQ': 3, 'NE': 3,
        'LT': 4, 'LE': 4, 'GT': 4, 'GE': 4,
        'PLUS': 5, 'MINUS': 5,
        'MULTIPLY': 6, 'DIVIDE': 6, 'MOD': 6,
    }

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def peek(self, offset=1):
        return self.tokens[self.pos + offset] if self.pos + offset < len(self.tokens) else None

    def advance(self):
        self.pos += 1

    def eat(self, token_type):
        tok = self.current()
        if tok and tok.type == token_type:
            self.advance()
            return tok
        raise SyntaxError(f"Expected {token_type}, got {tok}")

    # ==========================
    # Program
    # ==========================
    def parse(self):
        nodes = []
        while self.current() and self.current().type != "EOF":
            node = self.parse_declaration_or_function()
            if node:
                nodes.append(node)
        return ASTNode("PROGRAM", children=nodes)

    # ==========================
    # Declarations / Functions
    # ==========================
    def parse_declaration_or_function(self):
        tok = self.current()
        if tok.type in ["CHAR", "INT", "FLOAT", "VOID"]:
            type_tok = tok
            self.advance()
            id_tok = self.eat("IDENTIFIER")

            if self.current().type == "LPAREN":
                return self.parse_function(type_tok, id_tok)

            if self.current().type in self.PRECEDENCE:
                expr = self.parse_expression()
                self.eat("SEMICOLON")
                return ASTNode("VAR_DECL", id_tok.value, [
                    ASTNode("TYPE", type_tok.type),
                    expr
                ])

            self.eat("SEMICOLON")
            return ASTNode("VAR_DECL", id_tok.value, [
                ASTNode("TYPE", type_tok.type)
            ])
        return self.parse_statement()

    def parse_function(self, type_tok, id_tok):
        self.eat("LPAREN")
        params = self.parse_parameters()
        self.eat("RPAREN")
        self.eat("LBRACE")
        body = self.parse_block()
        self.eat("RBRACE")
        return ASTNode("FUNCTION_DEF", id_tok.value, [
            ASTNode("TYPE", type_tok.type),
            ASTNode("PARAMS", children=params),
            ASTNode("BODY", children=body)
        ])

    def parse_parameters(self):
        params = []
        while self.current().type != "RPAREN":
            type_tok = self.current()
            self.advance()
            id_tok = self.eat("IDENTIFIER")
            params.append(ASTNode("PARAM", id_tok.value, [
                ASTNode("TYPE", type_tok.type)
            ]))
            if self.current().type == "COMMA":
                self.advance()
        return params

    # ==========================
    # Blocks & Statements
    # ==========================
    def parse_block(self):
        stmts = []
        while self.current() and self.current().type != "RBRACE":
            stmt = self.parse_statement()
            if stmt:
                stmts.append(stmt)
        return stmts

    def parse_statement(self):
        tok = self.current()

        if tok.type == "SEMICOLON":
            self.advance()
            return None

        if tok.type == "RETURN":
            self.advance()
            expr = self.parse_expression()
            self.eat("SEMICOLON")
            return ASTNode("RETURN", children=[expr])

        if tok.type == "IF":
            return self.parse_if()

        if tok.type == "WHILE":
            return self.parse_while()

        if tok.type == "FOR":
            return self.parse_for()

        if tok.type == "BREAK":
            self.advance()
            self.eat("SEMICOLON")
            return ASTNode("BREAK")

        if tok.type == "CONTINUE":
            self.advance()
            self.eat("SEMICOLON")
            return ASTNode("CONTINUE")

        expr = self.parse_expression()
        self.eat("SEMICOLON")
        return expr

    # ==========================
    # Control Structures
    # ==========================
    def parse_if(self):
        self.eat("IF")
        self.eat("LPAREN")
        cond = self.parse_expression()
        self.eat("RPAREN")
        self.eat("LBRACE")
        then_body = self.parse_block()
        self.eat("RBRACE")

        else_body = []
        if self.current().type == "ELSE":
            self.advance()
            self.eat("LBRACE")
            else_body = self.parse_block()
            self.eat("RBRACE")

        return ASTNode("IF", children=[
            cond,
            ASTNode("THEN", children=then_body),
            ASTNode("ELSE", children=else_body)
        ])

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

        init = None
        if self.current().type != "SEMICOLON":
            init = self.parse_expression()
        self.eat("SEMICOLON")

        cond = None
        if self.current().type != "SEMICOLON":
            cond = self.parse_expression()
        self.eat("SEMICOLON")

        update = None
        if self.current().type != "RPAREN":
            update = self.parse_expression()
        self.eat("RPAREN")

        self.eat("LBRACE")
        body = self.parse_block()
        self.eat("RBRACE")

        return ASTNode("FOR", children=[init, cond, update, ASTNode("BODY", children=body)])

    # ==========================
    # Expressions
    # ==========================
    def parse_expression(self, min_prec=0):
        left = self.parse_primary()

        while self.current() and self.current().type in self.PRECEDENCE:
            prec = self.PRECEDENCE[self.current().type]
            if prec < min_prec:
                break

            op = self.current()
            self.advance()

            right = self.parse_expression(
                prec + (0 if op.type in ["ASSIGN", "PLUS_ASSIGN", "MINUS_ASSIGN",
                                         "MULT_ASSIGN", "DIV_ASSIGN", "MOD_ASSIGN"] else 1)
            )

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
                return self.parse_function_call()
            self.advance()
            return ASTNode("IDENTIFIER", tok.value)

        if tok.type == "LPAREN":
            self.advance()
            expr = self.parse_expression()
            self.eat("RPAREN")
            return expr

        if tok.type in ["PLUS", "MINUS", "NOT"]:
            self.advance()
            expr = self.parse_primary()
            return ASTNode("UNARY_OP", tok.type, [expr])

        raise SyntaxError(f"Unexpected token {tok}")

    def parse_function_call(self):
        name = self.eat("IDENTIFIER").value
        self.eat("LPAREN")
        args = []
        while self.current().type != "RPAREN":
            args.append(self.parse_expression())
            if self.current().type == "COMMA":
                self.advance()
        self.eat("RPAREN")
        return ASTNode("CALL", name, args)
