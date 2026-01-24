from lexer.lexer import Lexer
from parser.parser import Parser
from semantic import SemanticAnalyzer
from compiler.x86_64_linux import x86_64_Linux
import os

source = """
include minlib;

fn factorial(int n) -> int {
    if (n <= 1) {
        ret 1;
    }
    ret n * factorial(n-1);
}

fn wrapper(char* str) -> void {
    puts(str);
    int n = 5;
    while (1) {
        n += 1;
        if (n >= 5) {
            break;
        }
        continue;
    }
    puts("done loop");
}

fn atoi(char* s) -> int {
    int result = 0;
    int i = 0;
    while (s[i] != 0) {
        result = result * 10 + (s[i] - '0');
        i += 1;
    }
    ret result;
}

fn main() -> int {
    int n = atoi("15");
    puts("String converted to integer");
    int result = factorial(5);
    puts("Factorial computed");
    result++;

    int x = 10 % 3;
    puts("Modulo computed");
    x = -x;
    puts("Negation computed");
    x = -x;

    ret n;
}
"""

tok = Lexer(source).tokenize()
ast = Parser(tok).parse()
print(ast)
SemanticAnalyzer(ast).analyze()

asm = x86_64_Linux(ast).generate()
print(asm)

with open("out.asm", "w") as f:
    f.write(asm)

os.system("nasm -felf64 out.asm")
os.system("gcc out.o -no-pie")