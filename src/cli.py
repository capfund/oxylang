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
    compile_parser.add_argument("-arch", type=str, default="x86_64-linux", help="Target architecture (default: x86_64-linux)")

    return parser.parse_args()

def main():
    args = parse_args()
    if args.command == "compile":
        if not args.f:
            print("error: no source file specified")
            sys.exit(1)
        if not args.o:
            print("error: no output file specified")
            sys.exit(1)

        pp = preprocessor.Preprocessor()
        ast = pp.process(args.f)
        semantic.SemanticAnalyzer(ast).analyze()
        if args.arch == "x86_64-linux":
            asm = compiler.x86_64_linux.x86_64_Linux(ast).generate()
        else:
            print(f"error: unsupported architecture or does not exist '{args.arch}'")
            sys.exit(1)

        with open(args.o.replace(".out", ".asm").replace(".o", ".asm"), "w") as f:
            f.write(asm)

        if args.o.endswith(".o"):
            os.system(f"nasm -felf64 {args.o.replace('.o', '.asm')} -o {args.o}")
        elif args.o.endswith(".out"):
            os.system(f"nasm -felf64 {args.o.replace('.out', '.asm')} -o {args.o.replace('.out', '.o')}")
            os.system(f"gcc {args.o.replace('.out', '.o')} -no-pie -o {args.o}")

if __name__ == "__main__":
    main()