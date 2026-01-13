class CodegenError(Exception):
    pass


class x86_64_Linux:
    """Linux codegen for x86_64 arch using NASM syntax"""

    ARG_REGS = ["rdi", "rsi", "rdx", "rcx", "r8", "r9"]

    def __init__(self, ast):
        self.ast = ast
        self.lines = []
        self.label_id = 0
        self.locals = {}
        self.stack_size = 0

    def emit(self, line=""):
        self.lines.append(line)

    def new_label(self, prefix="L"):
        self.label_id += 1
        return f"{prefix}{self.label_id}"

    def alloc_local(self, name):
        self.stack_size += 8
        self.locals[name] = -self.stack_size

    def collect_locals(self, node):
        if node.type == "VAR_DECL":
            if node.value not in self.locals:
                self.alloc_local(node.value)

        for child in getattr(node, "children", []):
            if child:
                self.collect_locals(child)

    def generate(self):
        self.emit("global main")
        self.emit()
        self.emit("section .text")

        for node in self.ast.children:
            if node.type == "FUNCTION":
                self.gen_function(node)

        return "\n".join(self.lines)

    def gen_function(self, fn):
        name = fn.value
        params = fn.children[1].children
        body = fn.children[2].children

        self.locals = {}
        self.stack_size = 0

        for param in params:
            self.alloc_local(param.value)

        for stmt in body:
            self.collect_locals(stmt)
        aligned = ((self.stack_size + 15) // 16) * 16

        self.emit()
        self.emit(f"{name}:")
        self.emit("    push rbp")
        self.emit("    mov rbp, rsp")

        if aligned:
            self.emit(f"    sub rsp, {aligned}")
        for i, param in enumerate(params):
            self.emit(f"    mov [rbp{self.locals[param.value]}], {self.ARG_REGS[i]}")

        for stmt in body:
            self.gen_stmt(stmt)

        self.emit("    mov rsp, rbp")
        self.emit("    pop rbp")
        self.emit("    ret")

    def gen_stmt(self, node):
        t = node.type

        if t == "VAR_DECL":
            if len(node.children) > 1:
                self.gen_expr(node.children[1])
                self.emit(f"    mov [rbp{self.locals[node.value]}], rax")

        elif t == "RETURN":
            if node.children:
                self.gen_expr(node.children[0])
            self.emit("    mov rsp, rbp")
            self.emit("    pop rbp")
            self.emit("    ret")

        elif t == "IF":
            self.gen_if(node)

        elif t == "WHILE":
            self.gen_while(node)

        elif t == "FOR":
            self.gen_for(node)

        elif t == "UNSAFE_BLOCK":
            for s in node.children:
                self.gen_stmt(s)

        else:
            self.gen_expr(node)

    def gen_if(self, node):
        cond, then, els = node.children
        else_lbl = self.new_label("else")
        end_lbl = self.new_label("endif")

        self.gen_expr(cond)
        self.emit("    cmp rax, 0")
        self.emit(f"    je {else_lbl}")

        for s in then.children:
            self.gen_stmt(s)

        self.emit(f"    jmp {end_lbl}")
        self.emit(f"{else_lbl}:")

        for s in els.children:
            self.gen_stmt(s)

        self.emit(f"{end_lbl}:")

    def gen_while(self, node):
        start = self.new_label("while")
        end = self.new_label("endwhile")

        self.emit(f"{start}:")
        self.gen_expr(node.children[0])
        self.emit("    cmp rax, 0")
        self.emit(f"    je {end}")

        for s in node.children[1].children:
            self.gen_stmt(s)

        self.emit(f"    jmp {start}")
        self.emit(f"{end}:")

    def gen_for(self, node):
        init, cond, step, body = node.children
        start = self.new_label("for")
        end = self.new_label("endfor")

        if init:
            self.gen_expr(init)

        self.emit(f"{start}:")
        if cond:
            self.gen_expr(cond)
            self.emit("    cmp rax, 0")
            self.emit(f"    je {end}")

        for s in body.children:
            self.gen_stmt(s)

        if step:
            self.gen_expr(step)

        self.emit(f"    jmp {start}")
        self.emit(f"{end}:")

    def gen_expr(self, node):
        t = node.type

        if t == "NUMBER":
            self.emit(f"    mov rax, {node.value}")

        elif t == "IDENTIFIER":
            if node.value not in self.locals:
                raise CodegenError(f"Undefined variable {node.value}")
            self.emit(f"    mov rax, [rbp{self.locals[node.value]}]")

        elif t == "BIN_OP":
            self.gen_expr(node.children[0])
            self.emit("    push rax")
            self.gen_expr(node.children[1])
            self.emit("    mov rbx, rax")
            self.emit("    pop rax")

            self.gen_binop(node.value)

        elif t == "CALL":
            self.gen_call(node)

        else:
            raise CodegenError(f"Unsupported expr {t}")

    def gen_binop(self, op):
        ops = {
            "PLUS": "add",
            "MINUS": "sub",
            "MULTIPLY": "imul",
        }

        if op in ops:
            self.emit(f"    {ops[op]} rax, rbx")
            return

        if op == "DIVIDE":
            self.emit("    cqo")
            self.emit("    idiv rbx")
            return

        if op in ("EQ", "NE", "LT", "LE", "GT", "GE"):
            self.emit("    cmp rax, rbx")
            setcc = {
                "EQ": "sete",
                "NE": "setne",
                "LT": "setl",
                "LE": "setle",
                "GT": "setg",
                "GE": "setge",
            }[op]
            self.emit(f"    {setcc} al")
            self.emit("    movzx rax, al")
            return

        raise CodegenError(f"Unsupported operator {op}")
        
    def gen_call(self, node):
        for i, arg in enumerate(node.children):
            self.gen_expr(arg)
            self.emit(f"    mov {self.ARG_REGS[i]}, rax")

        self.emit(f"    call {node.value}")
