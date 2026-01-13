from lexer.lexer import Lexer
from parser.parser import Parser
from semantic import SemanticAnalyzer
from compiler.x86_64_linux import x86_64_Linux

source = """
int factorial(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

int main() {
    int n = 5;
    int result = factorial(n);

    return result;
}
"""

ast = Parser(Lexer(source).tokenize()).parse()
SemanticAnalyzer(ast).analyze()

asm = x86_64_Linux(ast).generate()
print(asm)

with open("out.asm", "w") as f:
    f.write(asm)