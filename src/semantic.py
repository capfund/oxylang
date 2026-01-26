class SemanticError(Exception):
    pass

class SemanticAnalyzer:
    def __init__(self, ast):
        self.ast = ast
        self.functions = {}

    def analyze(self):
        self._collect_globals()
        self._check_main()

    def _collect_globals(self):
        for node in self.ast.children:
            #if node.type == "FUNCTION":
                #if node.value in self.functions:
                    #raise SemanticError(f"Duplicate function '{node.value}'")
                #self.functions[node.value] = node

            if node.type == "VAR_DECL":
                continue
                
            elif node.type == "FUNCTION":
                self.functions[node.value] = node

            else:
                if node.type == "INCLUDE" or node.type == "EXTERN":
                    continue
                
                raise SemanticError(
                    f"Illegal top-level statement: {node.type}"
                )

    def _check_main(self):
        if "main" not in self.functions:
            raise SemanticError("Missing 'main' entrypoint")

        main = self.functions["main"]

        ret_type = main.children[0].value
        params = main.children[1].children

        if ret_type not in ("INT", "INT32"):
            raise SemanticError(
                f"'main' must return int or int32, not {ret_type}"
            )

        if params:
            raise SemanticError(
                "'main' must take no parameters"
            )
