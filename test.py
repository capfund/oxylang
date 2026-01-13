from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.semantic import SemanticAnalyzer

l = Lexer("""
int32 add(int32 a, int32 b) {
    unsafe {
        char buffer[32];
    }
    return a + b;
}
          
int main() {
    int32 result = add(10, 20);
    return result;
}
""")


t = l.tokenize()
p = Parser(t)
ast = p.parse()

analyzer = SemanticAnalyzer(ast)
analyzer.analyze()

print(ast)
