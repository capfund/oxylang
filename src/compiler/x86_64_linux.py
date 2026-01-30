class CodegenError(Exception):
    pass

class x86_64_Linux:
    """Linux codegen for x86_64 arch using NASM syntax"""

    ARG_REGS = ["rdi", "rsi", "rdx", "rcx", "r8", "r9"]
    FLOAT_REGS = [f"xmm{i}" for i in range(8)]

    def __init__(self, ast):
        self.ast = ast
        self.lines = []
        self.label_id = 0
        self.locals = {}
        self.stack_size = 0
        self.strings = {}
        self.rodata = []
        self.loop_stack = []
        self.globals = {}
        self.data = []

    def mangle(self, name, params):
        sig = "_".join(p.children[0].value for p in params)
        return f"{name}__{sig}"

    def emit(self, line=""):
        self.lines.append(line)

    def new_label(self, prefix="L"):
        self.label_id += 1
        return f"{prefix}{self.label_id}"

    def string_label(self, value):
        if value not in self.strings:
            lbl = f"LC{len(self.strings)}"
            self.strings[value] = lbl
            self.rodata.append((lbl, value))
        return self.strings[value]
    
    def sizeof(self, type_node):
        if type_node.value == "CHAR":
            return 1
        if type_node.value == "CHAR_PTR":
            return 8
        
        # array size
        if type_node.children and type_node.children[0].type == "ARRAY_SIZE":
            base_size = 8 if type_node.value.endswith("_PTR") else (1 if type_node.value == "CHAR" else 8)
            array_size = type_node.children[0].value
            return base_size * array_size
        return 8

    def alloc_local(self, name, size, typ):
        self.stack_size += size
        self.locals[name] = (-self.stack_size, size, typ)

    def collect_locals(self, node):
        if node.type == "VAR_DECL":
            if node.value not in self.locals:
                typ = node.children[0].value
                size = self.sizeof(node.children[0])
                self.alloc_local(node.value, size, typ)

        if node.type in ("IF", "WHILE", "FOR", "UNSAFE_BLOCK", "BODY", "THEN", "ELSE"):
            for child in node.children:
                if child:
                    self.collect_locals(child)

    def generate(self):
        self.emit("global main")
        self.emit("extern puts")
        #self.emit("extern itoa")
        #self.emit("extern atoi")
        self.emit()
        self.emit("section .text")

        for node in self.ast.children:
            if node.type == "VAR_DECL":
                self.gen_global(node)
            elif node.type == "FUNCTION":
                self.gen_function(node)
            elif node.type == "EXTERN":
                self.emit(f"extern {node.value}")
            else:
                self.gen_stmt(node)

        self.emit("display_number:")
        self.emit("    push rax")
        self.emit("    push rbx")
        self.emit("    push rcx")
        self.emit("    push rdx")

        self.emit("    mov rbx, rax")  
        self.emit("    cmp rbx, 0")
        self.emit("    jne .num_nonzero")

        self.emit("    mov word [buffer], '0'+0x0A")
        self.emit("    mov rax, 1")          
        self.emit("    mov rdi, 1")          
        self.emit("    lea rsi, [buffer]")   
        self.emit("    mov rdx, 2")          
        self.emit("    syscall")             
        self.emit("    jmp .end_display")

        self.emit(".num_nonzero:")
        self.emit("    lea rcx, [buffer+19]")  
        self.emit("    mov byte [rcx], 10")
        self.emit("    dec rcx")
        self.emit("    mov rax, rbx")

        self.emit(".convert_loop:")
        self.emit("    xor rdx, rdx") 
        self.emit("    mov rsi, 10")
        self.emit("    div rsi")   
        self.emit("    add dl, '0'")
        self.emit("    mov [rcx], dl")
        self.emit("    dec rcx")
        self.emit("    cmp rax, 0")
        self.emit("    jne .convert_loop")

        self.emit("    inc rcx")  
        self.emit("    mov rax, 1")
        self.emit("    mov rdi, 1")
        self.emit("    lea rsi, [rcx]")
        self.emit("    mov rdx, buffer+20")
        self.emit("    sub rdx, rcx") 
        self.emit("    syscall")

        self.emit(".end_display:")
        self.emit("    pop rdx")
        self.emit("    pop rcx")
        self.emit("    pop rbx")
        self.emit("    pop rax")
        self.emit("    ret")

        self.emit("display_number_nonl:")
        self.emit("    push rax")
        self.emit("    push rbx")
        self.emit("    push rcx")
        self.emit("    push rdx")

        self.emit("    mov rbx, rax")  
        self.emit("    cmp rbx, 0")
        self.emit("    jne .num_nonzero_nl")

        self.emit("    mov byte [buffer], '0'")
        self.emit("    mov rax, 1")          
        self.emit("    mov rdi, 1")          
        self.emit("    lea rsi, [buffer]")   
        self.emit("    mov rdx, 1")          
        self.emit("    syscall")             
        self.emit("    jmp .end_display_nl")

        self.emit(".num_nonzero_nl:")
        self.emit("    lea rcx, [buffer+19]")  
        self.emit("    mov byte [rcx], 0")
        self.emit("    dec rcx")
        self.emit("    mov rax, rbx")

        self.emit(".convert_loop_nl:")
        self.emit("    xor rdx, rdx") 
        self.emit("    mov rsi, 10")
        self.emit("    div rsi")   
        self.emit("    add dl, '0'")
        self.emit("    mov [rcx], dl")
        self.emit("    dec rcx")
        self.emit("    cmp rax, 0")
        self.emit("    jne .convert_loop_nl")

        self.emit("    inc rcx")  
        self.emit("    mov rax, 1")
        self.emit("    mov rdi, 1")
        self.emit("    lea rsi, [rcx]")
        self.emit("    mov rdx, buffer+20")
        self.emit("    sub rdx, rcx") 
        self.emit("    syscall")

        self.emit(".end_display_nl:")
        self.emit("    pop rdx")
        self.emit("    pop rcx")
        self.emit("    pop rbx")
        self.emit("    pop rax")
        self.emit("    ret")
        
        self.emit("print_char:")
        self.emit("    mov [buffer], al")
        self.emit("    mov rax, 1")
        self.emit("    mov rdi, 1")
        self.emit("    lea rsi, [buffer]")
        self.emit("    mov rdx, 1")
        self.emit("    syscall")
        self.emit("    ret")

        if self.rodata:
            self.emit()
            self.emit("section .rodata")
            for lbl, s in self.rodata:
                escaped = s.replace("\\", "\\\\").replace('"', '\\"')
                self.emit(f"{lbl}: db \"{escaped}\", 0")

        self.emit()
        self.emit("section .data")
        self.emit("    buffer times 20 db 0")

        for name, size, val in self.data:
            if size == 1:
                self.emit(f"{name}: db {val}")
            else:
                self.emit(f"{name}: dq {val}")
        
        peepholed = self.peephole(self.lines)
        self.lines = peepholed
        return "\n".join(self.lines)
    
    def gen_global(self, node):
        name = node.value
        size = self.sizeof(node.children[0])
        self.globals[name] = size

        if len(node.children) > 1:
            val = node.children[1].value
        else:
            val = 0

        self.data.append((name, size, val))

    def gen_function(self, fn):
        base = fn.value
        params = fn.children[1].children
        if base in ["main", "puts", "display_number", "display_number_nonl", "print_char"]:
            name = base
        else:
            name = self.mangle(base, params)
        #eoc
        body = fn.children[2].children

        self.locals = {}
        self.stack_size = 0

        for param in params:
            typ = param.children[0].value
            size = self.sizeof(param.children[0])
            self.alloc_local(param.value, size, typ)

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
            offset, size, typ = self.locals[param.value]
            if typ == "FLOAT":
                self.emit(f"    movsd [rbp{offset}], {self.FLOAT_REGS[i]}")
            else:
                self.emit(f"    mov [rbp{offset}], {self.ARG_REGS[i]}")

        for stmt in body:
            self.gen_stmt(stmt)

        self.emit("    mov rsp, rbp")
        self.emit("    pop rbp")
        self.emit("    ret")

    def gen_stmt(self, node):
        t = node.type

        if t == "INCLUDE":
            return
        
        if t == "EXTERN":
            return

        if t == "VAR_DECL":
            if len(node.children) > 1:
                val_type = self.gen_expr(node.children[1])
                offset, size, typ = self.locals[node.value]

                if typ == "FLOAT":
                    self.emit(f"    movsd [rbp{offset}], xmm0")
                elif val_type == "FLOAT" and typ == "INT":
                    self.emit("    cvttsd2si rax, xmm0")
                    self.emit(f"    mov [rbp{offset}], rax")
                elif size == 1:
                    self.emit(f"    mov byte [rbp{offset}], al")
                else:
                    self.emit(f"    mov [rbp{offset}], rax")

        elif t == "RETURN":
            if node.children:
                ret_type = self.gen_expr(node.children[0])
                # if FLOAT, value is already in xmm0 (SysV ABI)
                # if INT, value is in rax (as before)
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

        elif t == "BREAK":
            if not self.loop_stack:
                raise CodegenError("break outside loop")
            _, end = self.loop_stack[-1]
            self.emit(f"    jmp {end}")

        elif t == "CONTINUE":
            if not self.loop_stack:
                raise CodegenError("continue outside loop")
            start, _ = self.loop_stack[-1]
            self.emit(f"    jmp {start}")

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

        self.loop_stack.append((start, end))

        self.emit(f"{start}:")
        self.gen_expr(node.children[0])
        self.emit("    cmp rax, 0")
        self.emit(f"    je {end}")

        for s in node.children[1].children:
            self.gen_stmt(s)

        self.emit(f"    jmp {start}")
        self.emit(f"{end}:")

        self.loop_stack.pop()

    def gen_for(self, node):
        init, cond, step, body = node.children
        start = self.new_label("for")
        end = self.new_label("endfor")

        if init:
            self.gen_expr(init)

        self.loop_stack.append((start, end))

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

        self.loop_stack.pop()
    
    def gen_assign(self, node):
        op = node.value
        lhs, rhs = node.children

        if lhs.type == "IDENTIFIER":
            name = lhs.value
            if name in self.locals:
                offset, size, typ = self.locals[name]
                self.emit(f"    lea rdx, [rbp{offset}]")
            elif name in self.globals:
                size = self.globals[name]
                self.emit(f"    lea rdx, [{name}]")
            else:
                raise CodegenError(f"Undefined variable {name}")

        elif lhs.type == "DEREF":
            self.gen_expr(lhs.children[0])
            self.emit("    mov rdx, rax")
            size = 8 # by default

        elif lhs.type == "ARRAY_INDEX":
            #array[index] - compute address
            base = lhs.children[0]
            index_node = lhs.children[1]
            
            self.gen_expr(index_node)
            self.emit("    push rax")
            self.gen_expr(base)
            self.emit("    pop rcx")
            self.emit("    add rax, rcx")
            self.emit("    mov rdx, rax")
            size = 8

        else:
            raise CodegenError("error: invalid assignment target")

        #RHS
        rhs_type = self.gen_expr(rhs)

        if rhs_type == "FLOAT" and typ == "INT":
            self.emit("    cvttsd2si rax, xmm0")
            self.emit("    mov rcx, rax")
        else:
            self.emit("    mov rcx, rax")

        if op == "ASSIGN":
            self.emit("    mov rax, rcx")

        elif op == "PLUS_ASSIGN":
            if size == 1:
                self.emit("    movzx rax, byte [rdx]")
            else:
                self.emit("    mov rax, [rdx]")
            self.emit("    add rax, rcx")

        elif op == "MINUS_ASSIGN":
            if size == 1:
                self.emit("    movzx rax, byte [rdx]")
            else:
                self.emit("    mov rax, [rdx]")
            self.emit("    sub rax, rcx")

        elif op == "MULT_ASSIGN":
            if size == 1:
                self.emit("    movzx rax, byte [rdx]")
            else:
                self.emit("    mov rax, [rdx]")
            self.emit("    imul rax, rcx")

        elif op == "DIV_ASSIGN":
            if size == 1:
                self.emit("    movzx rax, byte [rdx]")
            else:
                self.emit("    mov rax, [rdx]")
            self.emit("    cqo")
            self.emit("    idiv rcx")

        else:
            raise CodegenError(f"error: unsupported assignment op {op}")

        if typ == "FLOAT":
            self.emit("    movsd [rdx], xmm0")
        elif size == 1:
            self.emit("    mov byte [rdx], al")
        else:
            self.emit("    mov [rdx], rax")

    def gen_expr(self, node):
        t = node.type

        if t == "INCLUDE":
            return
        
        if t == "EXTERN":
            return
        
        if t == "NUMBER":
            if isinstance(node.value, float):
                lbl = self.new_label("float")
                self.data.append((lbl, 8, f"__float64__({node.value})"))
                self.emit(f"    movsd xmm0, [{lbl}]")
                return "FLOAT"
            else:
                self.emit(f"    mov rax, {node.value}")
                return "INT"

        elif t == "DEREF":
            self.gen_expr(node.children[0])
            self.emit("    movzx rax, byte [rax]")

        elif t == "ADDROF":
            expr = node.children[0]
            if expr.type == "IDENTIFIER":
                name = expr.value
                if name in self.locals:
                    offset, _ = self.locals[name]
                    self.emit(f"    lea rax, [rbp{offset}]")
                elif name in self.globals:
                    self.emit(f"    lea rax, [{name}]")
                else:
                    raise CodegenError(f"Undefined variable {name}")
            elif expr.type == "ARRAY_INDEX":
                # &arr[i]; compute array base + index
                base = expr.children[0]
                index_node = expr.children[1]
                
                self.gen_expr(index_node)
                self.emit("    push rax")
                self.gen_expr(base)
                self.emit("    pop rcx")
                self.emit("    add rax, rcx")
            else:
                raise CodegenError("error: can only take address of identifiers and array elements")

        elif t == "ARRAY_INDEX":
            #array[index] = *(array + index)
            base = node.children[0]
            index_node = node.children[1]
            
            self.gen_expr(index_node)
            self.emit("    push rax")
            self.gen_expr(base)
            self.emit("    pop rcx")
            self.emit("    add rax, rcx")
            self.emit("    movzx rax, byte [rax]")

        elif t == "PRE_INC":
            if node.children[0].type == "IDENTIFIER":
                name = node.children[0].value
                offset, size, typ = self.locals[name]
                if size == 1:
                    self.emit(f"    movzx rax, byte [rbp{offset}]")
                    self.emit("    add al, 1")
                    self.emit(f"    mov byte [rbp{offset}], al")
                    self.emit(f"    movzx rax, byte [rbp{offset}]")
                else:
                    self.emit(f"    mov rax, [rbp{offset}]")
                    self.emit("    add rax, 1")
                    self.emit(f"    mov [rbp{offset}], rax")
            else:
                raise CodegenError("error: invalid increment target")

        elif t == "PRE_DEC":
            if node.children[0].type == "IDENTIFIER":
                name = node.children[0].value
                offset, size, typ = self.locals[name]
                if size == 1:
                    self.emit(f"    movzx rax, byte [rbp{offset}]")
                    self.emit("    sub al, 1")
                    self.emit(f"    mov byte [rbp{offset}], al")
                    self.emit(f"    movzx rax, byte [rbp{offset}]")
                else:
                    self.emit(f"    mov rax, [rbp{offset}]")
                    self.emit("    sub rax, 1")
                    self.emit(f"    mov [rbp{offset}], rax")
            else:
                raise CodegenError("error: invalid decrement target")

        elif t == "POST_INC":
            if node.children[0].type == "IDENTIFIER":
                name = node.children[0].value
                offset, size, typ = self.locals[name]
                if size == 1:
                    self.emit(f"    movzx rax, byte [rbp{offset}]")
                    self.emit("    push rax")
                    self.emit("    add al, 1")
                    self.emit(f"    mov byte [rbp{offset}], al")
                    self.emit("    pop rax")
                else:
                    self.emit(f"    mov rax, [rbp{offset}]")
                    self.emit("    push rax")
                    self.emit("    add rax, 1")
                    self.emit(f"    mov [rbp{offset}], rax")
                    self.emit("    pop rax")
            else:
                raise CodegenError("error: invalid increment target")

        elif t == "POST_DEC":
            if node.children[0].type == "IDENTIFIER":
                name = node.children[0].value
                offset, size, typ = self.locals[name]
                if size == 1:
                    self.emit(f"    movzx rax, byte [rbp{offset}]")
                    self.emit("    push rax")
                    self.emit("    sub al, 1")
                    self.emit(f"    mov byte [rbp{offset}], al")
                    self.emit("    pop rax")
                else:
                    self.emit(f"    mov rax, [rbp{offset}]")
                    self.emit("    push rax")
                    self.emit("    sub rax, 1")
                    self.emit(f"    mov [rbp{offset}], rax")
                    self.emit("    pop rax")
            else:
                raise CodegenError("error: invalid decrement target")

        elif t == "IDENTIFIER":
            if node.value in self.locals:
                offset, size, typ = self.locals[node.value]
                if typ == "FLOAT":
                    self.emit(f"    movsd xmm0, [rbp{offset}]")
                    return "FLOAT"
                elif size == 1:
                    self.emit(f"    movzx rax, byte [rbp{offset}]")
                    return "INT"
                else:
                    self.emit(f"    mov rax, [rbp{offset}]")
                    return "INT"
            elif node.value in self.globals:
                size = self.globals[node.value]
                if size == 1:
                    self.emit(f"    movzx rax, byte [{node.value}]")
                else:
                    self.emit(f"    mov rax, [{node.value}]")
            else:
                raise CodegenError(f"Undefined variable {node.value}")

        elif t == "BIN_OP" and (node.value == "ASSIGN" or node.value.endswith("_ASSIGN")):
            self.gen_assign(node)

        elif t == "BIN_OP":
            lt = self.gen_expr(node.children[0])

            if lt == "FLOAT":
                self.emit("    sub rsp, 8")
                self.emit("    movsd [rsp], xmm0")
            else:
                self.emit("    push rax")

            rt = self.gen_expr(node.children[1])

            if lt == "FLOAT" or rt == "FLOAT":
                if rt == "INT":
                    self.emit("    cvtsi2sd xmm0, rax")
                self.emit("    movsd xmm1, xmm0")

                if lt == "FLOAT":
                    self.emit("    movsd xmm0, [rsp]")
                    self.emit("    add rsp, 8")
                else:
                    self.emit("    pop rax")
                    self.emit("    cvtsi2sd xmm0, rax")

                if node.value in ("EQ", "NE", "LT", "LE", "GT", "GE"):
                    self.gen_float_cmp(node.value)
                    return "INT"
                else:
                    self.gen_float_binop(node.value)
                    return "FLOAT"
            else:
                self.emit("    mov rcx, rax")
                self.emit("    pop rax")
                self.gen_binop(node.value)
                return "INT"

        elif t == "CALL":
            self.gen_call(node)

        elif t == "STRING":
            lbl = self.string_label(node.value)
            self.emit(f"    lea rax, [{lbl}]")

        elif t == "CHAR_LIT":
            self.emit(f"    mov rax, {node.value}")

        elif t == "UNARY_MINUS":
            self.gen_expr(node.children[0])
            self.emit("    neg rax")

        else:
            raise CodegenError(f"error: unsupported expr {t}")
        
    def gen_float_binop(self, op):
        ops = {
            "PLUS": "addsd",
            "MINUS": "subsd",
            "MULTIPLY": "mulsd",
            "DIVIDE": "divsd",
        }

        if op in ops:
            self.emit(f"    {ops[op]} xmm0, xmm1")
            return

        raise CodegenError(f"unsupported float operator {op}")
    
    def gen_float_cmp(self, op):
        #xmm0 left, xmm1 right
        self.emit("    ucomisd xmm0, xmm1")

        setcc = {
            "EQ": "sete",
            "NE": "setne",
            "LT": "setb",   # <
            "LE": "setbe",  # <=
            "GT": "seta",   # >
            "GE": "setae",  # >=
        }[op]

        self.emit(f"    {setcc} al")
        self.emit("    movzx rax, al")

    def gen_binop(self, op):
        ops = {
            "PLUS": "add",
            "MINUS": "sub",
            "MULTIPLY": "imul",
        }

        if op in ops:
            self.emit(f"    {ops[op]} rax, rcx")
            return

        if op == "DIVIDE":
            self.emit("    cqo")
            self.emit("    idiv rcx")
            return

        if op == "MOD":
            self.emit("    cqo")
            self.emit("    idiv rcx")
            self.emit("    mov rax, rdx")
            return
        
        if op == "POW":
            self.emit("    mov rbx, rax")  # base
            # rcx = exponent already
            self.emit("    mov rax, 1")    # result

            pow_loop = self.new_label("pow_loop")
            end_pow = self.new_label("end_pow")

            self.emit(f"{pow_loop}:")
            self.emit("    cmp rcx, 0")
            self.emit(f"    je {end_pow}")
            self.emit("    imul rax, rbx")
            self.emit("    dec rcx")
            self.emit(f"    jmp {pow_loop}")
            self.emit(f"{end_pow}:")
            return

        if op in ("EQ", "NE", "LT", "LE", "GT", "GE"):
            self.emit("    cmp rax, rcx")
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

        raise CodegenError(f"error: unsupported operator {op}")

    def gen_call(self, node):
        argc = len(node.children)
        base = node.value
        if base in ["main", "puts", "display_number", "display_number_nonl", "print_char"]:
            func_name = base
            #eoc
        else:
            arg_types = []
            for arg in node.children:
                if arg.type == "STRING":
                    arg_types.append("CHAR_PTR")
                elif arg.type == "CHAR_LIT":
                    arg_types.append("CHAR")
                elif arg.type == "IDENTIFIER":
                    if arg.value in self.locals:
                        _, size, typ = self.locals[arg.value]
                        #arg_types.append("FLOAT" if typ == "FLOAT" else ("CHAR" if size == 1 else "INT"))
                        if typ == "FLOAT":
                            arg_types.append("FLOAT")
                        else:
                            arg_types.append(typ)
                    else:
                        arg_types.append("INT")
                elif arg.type == "NUMBER" and isinstance(arg.value, float):
                    arg_types.append("FLOAT")
                else:
                    arg_types.append("INT")

            func_name = base + "__" + "_".join(arg_types)

        int_i = 0
        float_i = 0

        #if argc > len(self.ARG_REGS):
        #    raise CodegenError("too many arguments")

        for arg in node.children:
            t = self.gen_expr(arg)

            if t == "FLOAT":
                self.emit(f"    movsd {self.FLOAT_REGS[float_i]}, xmm0")
                float_i += 1
            else:
                self.emit(f"    mov {self.ARG_REGS[int_i]}, rax")
                int_i += 1

        self.emit("    sub rsp, 16")
        self.emit(f"    call {func_name}")
        self.emit("    add rsp, 16")

    def peephole(self, lines):
        out = []
        i = 0
        while i < len(lines):
            if i+1 < len(lines) and lines[i] == "    push rax" and lines[i+1] == "    pop rax":
                i += 2
                continue
            if i+1 < len(lines) and lines[i].startswith("    mov rax, rax"):
                i += 1
                continue
            out.append(lines[i])
            i += 1
        return out