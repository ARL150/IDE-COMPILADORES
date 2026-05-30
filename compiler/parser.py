# compiler/parser.py

from compiler.ast_nodes import ASTNode


class Parser:

    def __init__(self, tokens):

        self.tokens = tokens
        self.position = 0
        self.errors = []

        if tokens:
            self.current_token = tokens[0]
        else:
            self.current_token = None

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
    # MATCH
    # =====================================================

    def match(self, expected_type):

        if (
            self.current_token and
            self.current_token[0] == expected_type
        ):

            token = self.current_token

            self.advance()

            return token

        else:

            self.syntax_error(
                f"Se esperaba {expected_type}"
            )

            # recuperación
            self.synchronize()

            return None
        
    def save_errors(self):

        with open(
            "errores_sintacticos.txt",
            "w",
            encoding="utf-8"
        ) as file:

            for error in self.errors:

                file.write(error + "\n")

    # =====================================================
    # ERROR
    # =====================================================

    def syntax_error(self, message):

        if self.current_token:

            lexeme = self.current_token[1]
            line = self.current_token[2]
            column = self.current_token[3]

            error = (
                f"Error sintáctico: {message} "
                f"en '{lexeme}' "
                f"(línea {line}, columna {column})"
            )

        else:

            error = "Error sintáctico al final del archivo"

        self.errors.append(error)

        print(error)

    # =========================================
    # RECUPERACION DE ERRORES
    # =========================================

    def synchronize(self):

        sync_tokens = [

            "SEMICOLON",

            "IF",
            "WHILE",
            "DO",

            "CIN",
            "COUT",

            "INT",
            "FLOAT",
            "BOOL",

            "END",

            "RBRACE"
        ]

        while (
            self.current_token and
            self.current_token[0] not in sync_tokens
        ):

            self.advance()

        # avanzar ;
        if (
            self.current_token and
            self.current_token[0] == "SEMICOLON"
        ):

            self.advance()

    # =====================================================
    # PARSE PRINCIPAL
    # =====================================================

    def parse(self):

        return self.program()

    # =====================================================
    # programa → main { lista_declaracion }
    # =====================================================

    def program(self):

        root = ASTNode("PROGRAM")

        self.match("MAIN")

        self.match("LBRACE")

        while (
            self.current_token and
            self.current_token[0] != "RBRACE"
        ):

            node = self.declaration()

            if node:
                root.add_child(node)

        self.match("RBRACE")

        return root

    # =====================================================
    # DECLARACIONES
    # =====================================================

    def declaration(self):

        if not self.current_token:
            return None

        # variables
        if self.current_token[0] in [
            "INT",
            "FLOAT",
            "BOOL"
        ]:

            return self.variable_declaration()

        # asignacion
        elif self.current_token[0] == "ID":

            return self.assignment()

        # if
        elif self.current_token[0] == "IF":

            return self.if_statement()

        # while
        elif self.current_token[0] == "WHILE":

            return self.while_statement()

        # do while
        elif self.current_token[0] == "DO":

            return self.do_while_statement()

        # cin
        elif self.current_token[0] == "CIN":

            return self.input_statement()

        # cout
        elif self.current_token[0] == "COUT":

            return self.output_statement()

        else:

            self.syntax_error(
                "Declaracion invalida"
            )

            self.advance()

    # =====================================================
    # DECLARACION VARIABLE
    # int x, y, z;
    # =====================================================

    def variable_declaration(self):

        type_token = self.current_token

        self.advance()

        node = ASTNode("VAR_DECL")

        node.add_child(
            ASTNode(
                "TYPE",
                type_token[1]
            )
        )

        while True:

            id_token = self.match("ID")

            if id_token:

                node.add_child(
                    ASTNode(
                        "ID",
                        id_token[1]
                    )
                )

            if (
                self.current_token and
                self.current_token[0] == "COMMA"
            ):

                self.match("COMMA")

            else:
                break

        self.match("SEMICOLON")

        return node

    # =====================================================
    # ASIGNACION
    # x = 5;
    # =====================================================

    def assignment(self):

        id_token = self.match("ID")

        self.match("EQUAL")

        expr = self.expression()

        self.match("SEMICOLON")

        node = ASTNode("ASSIGN")

        if id_token:

            node.add_child(
                ASTNode(
                    "ID",
                    id_token[1]
                )
            )

        node.add_child(expr)

        return node

    # =====================================================
    # IF
    # =====================================================

    def if_statement(self):

        self.match("IF")

        condition = self.expression()

        self.match("THEN")

        node = ASTNode("IF")

        node.add_child(condition)

        # THEN
        then_block = ASTNode("THEN")

        while (
            self.current_token and
            self.current_token[0] not in [
                "ELSE",
                "END"
            ]
        ):

            stmt = self.declaration()

            if stmt:
                then_block.add_child(stmt)

        node.add_child(then_block)

        # ELSE
        if (
            self.current_token and
            self.current_token[0] == "ELSE"
        ):

            self.match("ELSE")

            else_block = ASTNode("ELSE")

            while (
                self.current_token and
                self.current_token[0] != "END"
            ):

                stmt = self.declaration()

                if stmt:
                    else_block.add_child(stmt)

            node.add_child(else_block)

        self.match("END")

        return node

    # =====================================================
    # WHILE
    # =====================================================

    def while_statement(self):

        self.match("WHILE")

        condition = self.expression()

        node = ASTNode("WHILE")

        node.add_child(condition)

        body = ASTNode("BODY")

        while (
            self.current_token and
            self.current_token[0] != "END"
        ):

            stmt = self.declaration()

            if stmt:
                body.add_child(stmt)

        node.add_child(body)

        self.match("END")

        return node

    # =====================================================
    # DO WHILE
    # =====================================================

    def do_while_statement(self):

        self.match("DO")

        node = ASTNode("DO_WHILE")

        body = ASTNode("BODY")

        while (
            self.current_token and
            self.current_token[0] != "WHILE"
        ):

            stmt = self.declaration()

            if stmt:
                body.add_child(stmt)

        node.add_child(body)

        self.match("WHILE")

        condition = self.expression()

        node.add_child(condition)

        return node

    # =====================================================
    # CIN
    # =====================================================

    def input_statement(self):

        self.match("CIN")

        self.match("SHIFT_RIGHT")

        id_token = self.match("ID")

        self.match("SEMICOLON")

        node = ASTNode("INPUT")

        if id_token:

            node.add_child(
                ASTNode(
                    "ID",
                    id_token[1]
                )
            )

        return node

    # =====================================================
    # COUT
    # =====================================================

    def output_statement(self):

        self.match("COUT")

        self.match("SHIFT_LEFT")

        expr = self.output_value()

        self.match("SEMICOLON")

        node = ASTNode("OUTPUT")

        node.add_child(expr)

        return node

    # =====================================================
    # SALIDA
    # =====================================================

    def output_value(self):

        token = self.current_token

        # string
        if token[0] == "STRING":

            self.advance()

            return ASTNode(
                "STRING",
                token[1]
            )

        # expresion
        return self.expression()

    # =====================================================
    # EXPRESION
    # =====================================================

    def expression(self):

        left = self.simple_expression()

        while (
            self.current_token and
            self.current_token[0] in [

                "LT",
                "LE",
                "GT",
                "GE",
                "EQ",
                "NE",

                "AND",
                "OR"
            ]
        ):

            op = self.current_token

            self.advance()

            right = self.simple_expression()

            node = ASTNode(
                "EXPR_OP",
                op[1]
            )

            node.add_child(left)

            node.add_child(right)

            left = node

        return left

    # =====================================================
    # EXPRESION SIMPLE
    # =====================================================

    def simple_expression(self):

        node = self.term()

        while (
            self.current_token and
            self.current_token[0] in [

                "PLUS",
                "MINUS",

                "INCREMENT",
                "DECREMENT"
            ]
        ):

            op = self.current_token

            self.advance()

            right = self.term()

            new_node = ASTNode(
                "ADD_OP",
                op[1]
            )

            new_node.add_child(node)

            new_node.add_child(right)

            node = new_node

        return node

    # =====================================================
    # TERMINO
    # =====================================================

    def term(self):

        node = self.factor()

        while (
            self.current_token and
            self.current_token[0] in [

                "MULT",
                "DIV",
                "MOD",

                "POWER"
            ]
        ):

            op = self.current_token

            self.advance()

            right = self.factor()

            new_node = ASTNode(
                "MULT_OP",
                op[1]
            )

            new_node.add_child(node)

            new_node.add_child(right)

            node = new_node

        return node

    # =====================================================
    # FACTOR
    # =====================================================

    def factor(self):

        token = self.current_token

        if not token:
            return None

        # numero
        if token[0] == "NUMBER":

            self.advance()

            return ASTNode(
                "NUMBER",
                token[1]
            )

        # real
        elif token[0] == "REAL":

            self.advance()

            return ASTNode(
                "REAL",
                token[1]
            )

        # bool
        elif token[0] in [
            "TRUE",
            "FALSE"
        ]:

            self.advance()

            return ASTNode(
                "BOOL",
                token[1]
            )

        # identificador
        elif token[0] == "ID":

            self.advance()

            return ASTNode(
                "ID",
                token[1]
            )

        # !
        elif token[0] == "NOT":

            op = token

            self.advance()

            child = self.factor()

            node = ASTNode(
                "LOGIC_OP",
                op[1]
            )

            node.add_child(child)

            return node

        # parentesis
        elif token[0] == "LPAREN":

            self.advance()

            node = self.expression()

            self.match("RPAREN")

            return node

        else:

            self.syntax_error(
                "Factor invalido"
            )

            self.advance()

            return None