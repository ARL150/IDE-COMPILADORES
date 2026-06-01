# compiler/parser.py

from compiler.ast_nodes import ASTNode


def load_tokens_from_file(filepath: str) -> list:
    """
    Carga tokens desde tokens.txt generado por el lexer.

    Soporta dos formatos:
      - Con tabs:   TIPO\\tLEXEMA\\tLINEA\\tCOLUMNA
      - Con tabs+espacios (formato de la UI): columnas alineadas con tabs

    Cumple el requisito de la rúbrica:
      'El analizador debe leer un archivo de texto con los tokens
       generados por el analizador léxico.'
    """
    tokens = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.rstrip("\n")
                # Saltar líneas vacías, encabezado y separadores
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith(("TIPO", "─", "-", "=")):
                    continue

                # Intentar separación por TAB primero
                parts = line.split("\t")
                parts = [p.strip() for p in parts if p.strip()]

                if len(parts) >= 4:
                    try:
                        tipo    = parts[0]
                        lexema  = parts[1]
                        linea   = int(parts[2])
                        columna = int(parts[3])
                        tokens.append((tipo, lexema, linea, columna))
                    except (ValueError, IndexError):
                        pass
    except FileNotFoundError:
        pass
    return tokens


class Parser:

    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0
        self.errors = []

        self.current_token = tokens[0] if tokens else None

    @classmethod
    def from_file(cls, filepath: str) -> "Parser":
        """
        Crea un Parser cargando los tokens directamente desde tokens.txt.
        Uso: parser = Parser.from_file('tokens.txt')
        """
        tokens = load_tokens_from_file(filepath)
        return cls(tokens)

    # =====================================================
    # AVANZAR
    # =====================================================

    def advance(self):
        self.position += 1
        if self.position < len(self.tokens):
            self.current_token = self.tokens[self.position]
        else:
            self.current_token = None

    # =====================================================
    # TOKEN ACTUAL (helpers)
    # =====================================================

    def _type(self):
        return self.current_token[0] if self.current_token else None

    def _line(self):
        return self.current_token[2] if self.current_token else None

    def _col(self):
        return self.current_token[3] if self.current_token else None

    # =====================================================
    # MATCH
    # =====================================================

    def match(self, expected_type):
        if self.current_token and self.current_token[0] == expected_type:
            token = self.current_token
            self.advance()
            return token

        self.syntax_error(f"Se esperaba '{expected_type}'")
        self.synchronize()
        return None

    # =====================================================
    # ERROR
    # =====================================================

    def syntax_error(self, message):
        if self.current_token:
            lexeme = self.current_token[1]
            line   = self.current_token[2]
            col    = self.current_token[3]
            error  = (
                f"Error sintáctico: {message} "
                f"— encontrado '{lexeme}' "
                f"(línea {line}, columna {col})"
            )
        else:
            error = f"Error sintáctico al final del archivo: {message}"

        self.errors.append(error)
        print(error)

    # =====================================================
    # RECUPERACIÓN DE ERRORES
    # =====================================================

    def synchronize(self):
        sync_tokens = {
            "SEMICOLON",
            "IF", "WHILE", "DO",
            "CIN", "COUT",
            "INT", "FLOAT", "BOOL",
            "END", "ELSE",
            "RBRACE",
        }

        while self.current_token and self.current_token[0] not in sync_tokens:
            self.advance()

        # Consumir el punto y coma de sincronización si es eso
        if self.current_token and self.current_token[0] == "SEMICOLON":
            self.advance()

    # =====================================================
    # GUARDAR ERRORES
    # =====================================================

    def save_errors(self):
        with open("errores_sintacticos.txt", "w", encoding="utf-8") as f:
            if self.errors:
                for error in self.errors:
                    f.write(error + "\n")
            else:
                f.write("Sin errores sintácticos\n")

    # =====================================================
    # PARSE PRINCIPAL
    # programa → main { lista_declaracion }
    # =====================================================

    def parse(self):
        return self.program()

    def program(self):
        line, col = self._line(), self._col()
        node = ASTNode("PROGRAMA", line=line, column=col)

        main_tok = self.match("MAIN")
        if main_tok:
            node.add_child(ASTNode("MAIN", "main", main_tok[2], main_tok[3]))

        self.match("LBRACE")

        decls = ASTNode("DECLARACIONES", line=line, column=col)
        stmts = ASTNode("SENTENCIAS",    line=line, column=col)

        while self.current_token and self._type() != "RBRACE":
            if self._type() in ("INT", "FLOAT", "BOOL"):
                decls.add_child(self.variable_declaration())
            else:
                stmt = self.statement()
                if stmt:
                    stmts.add_child(stmt)

        self.match("RBRACE")

        node.add_child(decls)
        node.add_child(stmts)

        return node

    # =====================================================
    # DECLARACIÓN DE VARIABLE
    # declaracion_variable → tipo identificador ;
    # identificador → id | identificador , id
    # =====================================================

    def variable_declaration(self):
        type_tok = self.current_token
        self.advance()

        node = ASTNode("DECL_VAR", line=type_tok[2], column=type_tok[3])
        node.add_child(ASTNode("TIPO", type_tok[1], type_tok[2], type_tok[3]))

        while True:
            id_tok = self.match("ID")
            if id_tok:
                node.add_child(ASTNode("ID", id_tok[1], id_tok[2], id_tok[3]))

            if self._type() == "COMMA":
                self.match("COMMA")
            else:
                break

        self.match("SEMICOLON")
        return node

    # =====================================================
    # SENTENCIA (dispatch)
    # sentencia → seleccion | iteracion | repeticion |
    #             sent_in | sent_out | asignacion
    # =====================================================

    def statement(self):
        if not self.current_token:
            return None

        t = self._type()

        if t == "ID":
            return self.assignment()
        elif t == "IF":
            return self.if_statement()
        elif t == "WHILE":
            return self.while_statement()
        elif t == "DO":
            return self.do_while_statement()
        elif t == "CIN":
            return self.input_statement()
        elif t == "COUT":
            return self.output_statement()
        elif t in ("INT", "FLOAT", "BOOL"):
            # Declaración de variable fuera del bloque inicial — aceptar igualmente
            return self.variable_declaration()
        else:
            self.syntax_error(f"Sentencia inválida")
            self.advance()
            return None

    # =====================================================
    # ASIGNACIÓN
    # asignacion → id = sent_expresion
    # sent_expresion → expresion ; | ;
    # =====================================================

    def assignment(self):
        id_tok = self.match("ID")
        eq_tok = self.match("EQUAL")

        node = ASTNode(
            "ASIGNACION",
            id_tok[1] if id_tok else "?",
            id_tok[2] if id_tok else None,
            id_tok[3] if id_tok else None,
        )

        if id_tok:
            node.add_child(ASTNode("ID", id_tok[1], id_tok[2], id_tok[3]))

        # sent_expresion → expresion ; | ;
        if self._type() == "SEMICOLON":
            self.advance()  # asignación sin expresión: x = ;
        else:
            expr = self.expression()
            if expr:
                node.add_child(expr)
            self.match("SEMICOLON")

        return node

    # =====================================================
    # IF
    # seleccion → if expresion then lista_sentencias
    #             [ else lista_sentencias ] end
    # =====================================================

    def if_statement(self):
        if_tok = self.match("IF")
        line, col = (if_tok[2], if_tok[3]) if if_tok else (None, None)

        condition = self.expression()

        then_tok = self.match("THEN")
        if not then_tok:
            self.syntax_error("Se esperaba 'then' después de la condición del if")

        node = ASTNode("IF", line=line, column=col)
        node.add_child(ASTNode("CONDICION", line=line, column=col))
        node.children[-1].add_child(condition)

        then_block = ASTNode("ENTONCES", line=line, column=col)
        while self.current_token and self._type() not in ("ELSE", "END", "RBRACE"):
            stmt = self.statement()
            if stmt:
                then_block.add_child(stmt)
        node.add_child(then_block)

        if self._type() == "ELSE":
            self.match("ELSE")
            else_block = ASTNode("SINO", line=line, column=col)
            while self.current_token and self._type() not in ("END", "RBRACE"):
                stmt = self.statement()
                if stmt:
                    else_block.add_child(stmt)
            node.add_child(else_block)

        if not self.match("END"):
            self.syntax_error("Se esperaba 'end' para cerrar el if")

        return node

    # =====================================================
    # WHILE
    # iteracion → while expresion lista_sentencias end
    # =====================================================

    def while_statement(self):
        w_tok = self.match("WHILE")
        line, col = (w_tok[2], w_tok[3]) if w_tok else (None, None)

        condition = self.expression()

        node = ASTNode("MIENTRAS", line=line, column=col)
        node.add_child(ASTNode("CONDICION", line=line, column=col))
        node.children[-1].add_child(condition)

        body = ASTNode("CUERPO", line=line, column=col)
        while self.current_token and self._type() not in ("END", "RBRACE"):
            stmt = self.statement()
            if stmt:
                body.add_child(stmt)
        node.add_child(body)

        if not self.match("END"):
            self.syntax_error("Se esperaba 'end' para cerrar el while")

        return node

    # =====================================================
    # DO WHILE
    # repeticion → do lista_sentencias while expresion
    # =====================================================

    def do_while_statement(self):
        do_tok = self.match("DO")
        line, col = (do_tok[2], do_tok[3]) if do_tok else (None, None)

        node = ASTNode("HACER_MIENTRAS", line=line, column=col)

        body = ASTNode("CUERPO", line=line, column=col)
        while self.current_token and self._type() != "WHILE":
            stmt = self.statement()
            if stmt:
                body.add_child(stmt)
        node.add_child(body)

        self.match("WHILE")
        condition = self.expression()
        node.add_child(ASTNode("CONDICION", line=line, column=col))
        node.children[-1].add_child(condition)

        return node

    # =====================================================
    # CIN
    # sent_in → cin >> id ;
    # =====================================================

    def input_statement(self):
        cin_tok = self.match("CIN")
        line, col = (cin_tok[2], cin_tok[3]) if cin_tok else (None, None)

        if not self.match("SHIFT_RIGHT"):
            self.syntax_error("Se esperaba '>>' después de cin")

        id_tok = self.match("ID")
        if not id_tok:
            self.syntax_error("Se esperaba un identificador después de '>>'")

        self.match("SEMICOLON")

        node = ASTNode("ENTRADA", line=line, column=col)
        if id_tok:
            node.add_child(ASTNode("ID", id_tok[1], id_tok[2], id_tok[3]))

        return node

    # =====================================================
    # COUT
    # sent_out → cout << salida
    # salida → cadena | expresion | cadena << expresion
    #        | expresion << cadena
    # =====================================================

    def output_statement(self):
        cout_tok = self.match("COUT")
        line, col = (cout_tok[2], cout_tok[3]) if cout_tok else (None, None)

        if not self.match("SHIFT_LEFT"):
            self.syntax_error("Se esperaba '<<' después de cout")

        node = ASTNode("SALIDA", line=line, column=col)
        node.add_child(self.output_value())

        # Encadenamiento: salida << cadena / expresion
        while self._type() == "SHIFT_LEFT":
            self.advance()
            node.add_child(self.output_value())

        self.match("SEMICOLON")
        return node

    def output_value(self):
        if not self.current_token:
            return None

        if self._type() == "STRING":
            tok = self.current_token
            self.advance()
            return ASTNode("CADENA", tok[1], tok[2], tok[3])

        return self.expression()

    # =====================================================
    # EXPRESIÓN
    # expresion → expresion_simple [ rel_op expresion_simple ]
    # rel_op → < | <= | > | >= | == | !=
    # =====================================================

    def expression(self):
        left = self.simple_expression()

        while self._type() in ("LT", "LE", "GT", "GE", "EQ", "NE", "AND", "OR"):
            op_tok = self.current_token
            self.advance()
            right = self.simple_expression()

            node = ASTNode("OP_REL", op_tok[1], op_tok[2], op_tok[3])
            node.add_child(left)
            node.add_child(right)
            left = node

        return left

    # =====================================================
    # EXPRESIÓN SIMPLE
    # expresion_simple → termino { suma_op termino }
    # suma_op → + | - | ++ | --
    # =====================================================

    def simple_expression(self):
        node = self.term()

        while self._type() in ("PLUS", "MINUS", "INCREMENT", "DECREMENT"):
            op_tok = self.current_token
            self.advance()
            right = self.term()

            new_node = ASTNode("OP_SUMA", op_tok[1], op_tok[2], op_tok[3])
            new_node.add_child(node)
            new_node.add_child(right)
            node = new_node

        return node

    # =====================================================
    # TÉRMINO
    # termino → factor { mult_op factor }
    # mult_op → * | / | %
    # =====================================================

    def term(self):
        node = self.factor()

        while self._type() in ("MULT", "DIV", "MOD"):
            op_tok = self.current_token
            self.advance()
            right = self.factor()

            new_node = ASTNode("OP_MULT", op_tok[1], op_tok[2], op_tok[3])
            new_node.add_child(node)
            new_node.add_child(right)
            node = new_node

        return node

    # =====================================================
    # FACTOR
    # factor → componente { pot_op componente }
    # pot_op → ^
    # componente → ( expresion ) | número | id | bool
    #            | op_logico componente
    # =====================================================

    def factor(self):
        node = self.component()

        while self._type() == "POWER":
            op_tok = self.current_token
            self.advance()
            right = self.component()

            new_node = ASTNode("OP_POT", op_tok[1], op_tok[2], op_tok[3])
            new_node.add_child(node)
            new_node.add_child(right)
            node = new_node

        return node

    def component(self):
        tok = self.current_token

        if not tok:
            self.syntax_error("Se esperaba un componente")
            return None

        # Número entero
        if tok[0] == "NUMBER":
            self.advance()
            return ASTNode("NUMERO", tok[1], tok[2], tok[3])

        # Número real
        if tok[0] == "REAL":
            self.advance()
            return ASTNode("REAL", tok[1], tok[2], tok[3])

        # Booleano
        if tok[0] in ("TRUE", "FALSE"):
            self.advance()
            return ASTNode("BOOL", tok[1], tok[2], tok[3])

        # Identificador
        if tok[0] == "ID":
            self.advance()
            return ASTNode("ID", tok[1], tok[2], tok[3])

        # Operador lógico unario: ! componente
        if tok[0] == "NOT":
            self.advance()
            child = self.component()
            node = ASTNode("OP_LOGICO", tok[1], tok[2], tok[3])
            node.add_child(child)
            return node

        # Paréntesis: ( expresion )
        if tok[0] == "LPAREN":
            self.advance()
            node = self.expression()
            if not self.match("RPAREN"):
                self.syntax_error("Paréntesis sin cerrar")
            return node

        self.syntax_error(f"Factor inválido")
        self.advance()
        return None
