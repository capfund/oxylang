class CodegenError(Exception):
    pass


class x86_64_Linux:
    """Linux codegen for x86_64 arch using NASM syntax"""
    def __init__(self, ast):
        self.ast = ast
        self.lines = []

    def emit(self, line=""):
        self.lines.append(line)

    def generate(self):
        self.emit("global main")
        #self.emit("extern exit")
        self.emit()
        self.emit("section .text")

        for node in self.ast.children:
            if node.type == "FUNCTION":
                self.gen_function(node)

        return "\n".join(self.lines)

    def gen_function(self, fn):
        name = fn.value
        body = fn.children[2]

        self.emit()
        self.emit(f"{name}:")
        self.emit("    push rbp")
        self.emit("    mov rbp, rsp")

        for stmt in body.children:
            if stmt.type == "RETURN":
                self.gen_return(stmt)

        self.emit("    pop rbp")
        self.emit("    ret")

    def gen_return(self, stmt):
        expr = stmt.children[0]

        if expr.type == "NUMBER":
            self.emit(f"    mov eax, {expr.value}")
        else:
            raise CodegenError("error: only return of integer literal supported")
