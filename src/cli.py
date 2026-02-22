import os
import sys
import argparse
import compiler.x86_64_linux
import lexer, parser, preprocessor, semantic # core

def parse_args():
    parser = argparse.ArgumentParser(description="Oxylang Compiler CLI")
    parser.add_argument("--v", "--version", "-v", "-version",
                        action="version",
                        version="Oxylang Compiler release candidate (indev)",
                        help="Show Oxylang version")
    

    subparsers = parser.add_subparsers(dest="command")
    compile_parser = subparsers.add_parser("compile", help="Compile Oxylang source file")

    compile_parser.add_argument("-f", type=str, help="Oxylang source file to compile")
    compile_parser.add_argument("-o", type=str, help="Output file name for the compiled assembly code")

    return parser.parse_args()

def main():
    args = parse_args()
    if args.command == "compile":
        if not args.f:
            print("Error: No source file specified. Use -f to specify the source file.")
            sys.exit(1)
        if not args.o:
            print("Error: No output file name specified. Use -o to specify the output file name.")
            sys.exit(1)

        pp = preprocessor.Preprocessor()
        ast = pp.process(args.f)
        semantic.SemanticAnalyzer(ast).analyze()
        asm = compiler.x86_64_linux.x86_64_Linux(ast).generate()
        with open(args.o, "w") as f:
            f.write(asm)

if __name__ == "__main__":
    main()