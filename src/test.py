from lexer.lexer import Lexer
from parser.parser import Parser
from semantic import SemanticAnalyzer
from compiler.x86_64_linux import x86_64_Linux
import os

source = """
fn factorial(int n) -> int {
    if (n <= 1) {
        ret 1;
    }
    ret n * factorial(n-1);
}

fn main() -> int {
    int n = 5;
    int result = factorial(n);
    int a = 5;
    char* test = "Hello world!";

    puts(test);
    ret result;
}
"""

ast = Parser(Lexer(source).tokenize()).parse()
SemanticAnalyzer(ast).analyze()

asm = x86_64_Linux(ast).generate()
print(asm)

with open("out.asm", "w") as f:
    f.write(asm)

os.system("nasm -felf64 out.asm")
os.system("gcc out.o -no-pie")