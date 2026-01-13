from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.semantic import SemanticAnalyzer
from src.compiler.x86_64_linux import x86_64_Linux

source = """
int32 main() {
    return 42;
}
"""

ast = Parser(Lexer(source).tokenize()).parse()
SemanticAnalyzer(ast).analyze()

asm = x86_64_Linux(ast).generate()
print(asm)

with open("out.asm", "w") as f:
    f.write(asm)