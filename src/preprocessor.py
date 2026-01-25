from lexer.lexer import Lexer
from parser.parser import Parser, ASTNode
import os

class Preprocessor:
    def __init__(self):
        self.included = set()

    def process(self, filename):
        #prechecks and processing
        absdir = None

        if not filename.endswith(".oxy"):
            raise LookupError("Module must be a .oxy file")
        
        if filename in self.included:
            return ASTNode("PROGRAM", children=[])

        if filename in os.listdir(os.getcwd()):
            absdir = filename
        elif filename in os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "includes")):
            absdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "includes", filename)
        else:
            raise LookupError(f"Could not find module '{filename}'")
        
        #then ye
        self.included.add(filename)

        with open(absdir) as f:
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
