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
print(ast)
SemanticAnalyzer(ast).analyze()

asm = x86_64_Linux(ast).generate()
print(asm)

with open("out.asm", "w") as f:
    f.write(asm)

os.system("nasm -felf64 out.asm")
os.system("gcc out.o -no-pie")