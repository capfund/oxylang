from lexer.lexer import Lexer
from parser.parser import Parser, ASTNode

class Preprocessor:
    def __init__(self):
        self.included = set()

    def process(self, filename):
        if filename in self.included:
            return ASTNode("PROGRAM", children=[])

        self.included.add(filename)

        with open(filename) as f:
            text = f.read()

        tokens = Lexer(text).tokenize()
        ast = Parser(tokens).parse()

        new_nodes = []
        for node in ast.children:
            if node.type == "INCLUDE":
                sub = self.process(node.value)
                new_nodes.extend(sub.children)
            else:
                new_nodes.append(node)

        return ASTNode("PROGRAM", children=new_nodes)
