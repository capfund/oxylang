from lexer.lexer import Lexer
from parser.parser import Parser
from preprocessor import Preprocessor
from semantic import SemanticAnalyzer
from compiler.x86_64_linux import x86_64_Linux
import os

with open("tests.oxy") as f:
    source = f.read()

pp = Preprocessor()
ast = pp.process("tests.oxy")
SemanticAnalyzer(ast).analyze()
print(ast)

asm = x86_64_Linux(ast).generate()
print(asm)

os.makedirs("build", exist_ok=True)
with open("build/out.asm", "w") as f:
    f.write(asm)

os.system("nasm -felf64 build/out.asm")
os.system("gcc build/out.o -no-pie")