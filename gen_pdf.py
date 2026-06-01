"""
Genera el documento PDF de descripción técnica — Fase 2 Análisis Sintáctico.
Usa Arial Unicode MS para renderizar correctamente todos los caracteres especiales.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Registrar fuente Unicode ───────────────────────────────────
pdfmetrics.registerFont(TTFont("AU",   "/Library/Fonts/Arial Unicode.ttf"))
pdfmetrics.registerFont(TTFont("AUB",  "/Library/Fonts/Arial Unicode.ttf"))  # bold fallback
# Mono para código (Monaco viene con macOS y soporta ASCII que nos basta)
pdfmetrics.registerFont(TTFont("MON",  "/System/Library/Fonts/Monaco.ttf"))

OUTPUT = "Fase2_Analisis_Sintactico.pdf"
W, H = A4
BODY_W = W - 5*cm   # ancho útil

# ── Colores ────────────────────────────────────────────────────
C_DARK   = colors.HexColor("#1a3a5c")
C_MID    = colors.HexColor("#2563a8")
C_BG     = colors.HexColor("#f1f5f9")
C_GRID   = colors.HexColor("#cbd5e1")
C_HEAD   = colors.HexColor("#dbeafe")
C_TEXT   = colors.HexColor("#1e293b")
C_MUTED  = colors.HexColor("#64748b")
C_GREEN  = colors.HexColor("#15803d")
C_RED    = colors.HexColor("#b91c1c")
C_WHITE  = colors.white

# ── Estilos ────────────────────────────────────────────────────
def S(name, **kw):
    return ParagraphStyle(name, **kw)

sTitle    = S("sTitle",    fontName="AU", fontSize=24, textColor=C_DARK,
               leading=30, alignment=TA_CENTER, spaceAfter=4)
sSubtitle = S("sSubtitle", fontName="AU", fontSize=12, textColor=C_MID,
               leading=17, alignment=TA_CENTER, spaceAfter=2)
sMeta     = S("sMeta",     fontName="AU", fontSize=8.5, textColor=C_MUTED,
               leading=13, alignment=TA_CENTER, spaceAfter=14)
sH1       = S("sH1",       fontName="AU", fontSize=12, textColor=C_WHITE,
               leading=17, spaceAfter=8, spaceBefore=16,
               backColor=C_DARK, borderPadding=(6, 10, 6, 10))
sH2       = S("sH2",       fontName="AU", fontSize=10.5, textColor=C_DARK,
               leading=15, spaceAfter=5, spaceBefore=12)
sBody     = S("sBody",     fontName="AU", fontSize=9.5, textColor=C_TEXT,
               leading=14, spaceAfter=5)
sBullet   = S("sBullet",   fontName="AU", fontSize=9.5, textColor=C_TEXT,
               leading=14, spaceAfter=3, leftIndent=16, bulletIndent=4)
sCode     = S("sCode",     fontName="MON", fontSize=7.8, textColor=C_TEXT,
               leading=11.5, backColor=C_BG,
               leftIndent=10, rightIndent=10,
               borderPadding=(7, 8, 7, 8), spaceAfter=8, spaceBefore=4)
sCodeSm   = S("sCodeSm",   fontName="MON", fontSize=7.2, textColor=C_TEXT,
               leading=11, backColor=C_BG,
               leftIndent=10, rightIndent=10,
               borderPadding=(7, 8, 7, 8), spaceAfter=8, spaceBefore=4)
sResult   = S("sResult",   fontName="AU", fontSize=8.5, textColor=C_GREEN,
               leading=12, spaceAfter=8, leftIndent=8)
sErr      = S("sErr",      fontName="MON", fontSize=8, textColor=C_RED,
               leading=13, leftIndent=12)
sFooter   = S("sFooter",   fontName="AU", fontSize=8, textColor=C_MUTED,
               leading=11, alignment=TA_CENTER)

# ── Helpers ────────────────────────────────────────────────────
def hr(color=C_GRID, thick=0.5, sb=4, sa=4):
    return HRFlowable(width="100%", thickness=thick,
                      color=color, spaceBefore=sb, spaceAfter=sa)

def sp(h=8):
    return Spacer(1, h)

def h1(text):
    return Paragraph(f"  {text}", sH1)

def h2(text):
    return [hr(C_MID, 1.5, 12, 0), Paragraph(text, sH2)]

def body(text):
    return Paragraph(text, sBody)

def bullet(text):
    return Paragraph(f"•   {text}", sBullet)

def _esc_code(text):
    """Escapa solo los tags XML pero deja los caracteres Unicode tal cual."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def code(text):
    html = "<br/>".join(_esc_code(text).split("\n"))
    return Paragraph(html, sCode)

def code_sm(text):
    html = "<br/>".join(_esc_code(text).split("\n"))
    return Paragraph(html, sCodeSm)

def _cell(text, bold=False, center=False, color=None, size=9):
    align = TA_CENTER if center else TA_LEFT
    fn    = "AU"
    tc    = color or C_TEXT
    return Paragraph(text, S("_c", fontName=fn, fontSize=size, textColor=tc,
                              leading=13, alignment=align))

def make_table(data, col_widths, header_rows=1):
    t = Table(data, colWidths=col_widths, repeatRows=header_rows)
    n = len(data)
    style = [
        ("BACKGROUND",    (0, 0),  (-1, header_rows-1), C_HEAD),
        ("TEXTCOLOR",     (0, 0),  (-1, header_rows-1), C_DARK),
        ("FONTNAME",      (0, 0),  (-1, header_rows-1), "AU"),
        ("FONTSIZE",      (0, 0),  (-1, header_rows-1), 8.5),
        ("BOTTOMPADDING", (0, 0),  (-1, header_rows-1), 7),
        ("TOPPADDING",    (0, 0),  (-1, header_rows-1), 7),
        ("FONTNAME",      (0, header_rows), (-1, -1),   "AU"),
        ("FONTSIZE",      (0, header_rows), (-1, -1),   8.5),
        ("LEADING",       (0, 0),  (-1, -1), 12),
        ("TOPPADDING",    (0, header_rows), (-1, -1),   5),
        ("BOTTOMPADDING", (0, header_rows), (-1, -1),   5),
        ("LEFTPADDING",   (0, 0),  (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0),  (-1, -1), 8),
        ("VALIGN",        (0, 0),  (-1, -1), "MIDDLE"),
        ("GRID",          (0, 0),  (-1, -1), 0.5, C_GRID),
        # filas alternas
        *[("BACKGROUND",  (0, r),  (-1, r), colors.HexColor("#f8fafc"))
          for r in range(header_rows+1, n, 2)],
    ]
    t.setStyle(TableStyle(style))
    return t

# ══════════════════════════════════════════════════════════════
#  CONTENIDO
# ══════════════════════════════════════════════════════════════
story = []

# ── Portada ───────────────────────────────────────────────────
story += [sp(28),
          Paragraph("Fase 2 – Análisis Sintáctico", sTitle),
          sp(4),
          Paragraph("Proyecto de Compiladores I  ·  8° ISC", sSubtitle),
          sp(2),
          Paragraph("Docente: Dra. Blanca Guadalupe Estrada Rentería  "
                    "·  Fecha de entrega: 19-20 de Junio de 2025", sMeta),
          hr(C_DARK, 2, 10, 10),
          sp(12)]

integ_data = [
    [_cell("Integrantes del Equipo", bold=True, center=True, color=C_WHITE, size=10),
     _cell("Matrícula",         bold=True, center=True, color=C_WHITE, size=10)],
    ["Jesús Abraham Robledo López",     "284745"],
    ["Edgar Alejandro Cedeño Suárez",   "262728"],
]
t_int = Table(integ_data, colWidths=[11*cm, 5*cm])
t_int.setStyle(TableStyle([
    ("BACKGROUND",    (0,0), (-1,0),  C_DARK),
    ("TEXTCOLOR",     (0,1), (-1,-1), C_TEXT),
    ("FONTNAME",      (0,0), (-1,-1), "AU"),
    ("FONTSIZE",      (0,0), (-1,-1), 10),
    ("ALIGN",         (0,0), (-1,-1), "CENTER"),
    ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING",    (0,0), (-1,-1), 9),
    ("BOTTOMPADDING", (0,0), (-1,-1), 9),
    ("GRID",          (0,0), (-1,-1), 0.8, C_GRID),
    ("BACKGROUND",    (0,2), (-1,2),  colors.HexColor("#f1f5f9")),
]))
story += [t_int, PageBreak()]

# ── Sección 1 — Descripción ───────────────────────────────────
story += [h1("1.  Descripción General del Proyecto"), sp(6),
          body("El presente proyecto implementa la <b>Fase 2</b> del compilador: un "
               "analizador sintáctico descendente recursivo que procesa los tokens "
               "generados por el analizador léxico (Fase 1) y construye un "
               "<b>Árbol Sintáctico Abstracto (AST)</b>. El sistema está "
               "integrado en un IDE desarrollado en Python con PyQt6, con interfaz visual "
               "profesional, múltiples vistas del árbol y terminales de error "
               "enriquecidas."),
          sp(4)]
story += h2("Componentes principales")
for itm in [
    "<font name='MON' size='8.5'>compiler/lexer.py</font>  —  Analizador léxico (Fase 1): tokenización con línea y columna",
    "<font name='MON' size='8.5'>compiler/parser.py</font> —  Analizador sintáctico descendente recursivo",
    "<font name='MON' size='8.5'>compiler/ast_nodes.py</font> —  Definición de nodos del AST",
    "<font name='MON' size='8.5'>ui/main_window.py</font>  —  IDE con interfaz gráfica PyQt6",
    "<font name='MON' size='8.5'>ui/syntax_tree.py</font>  —  Vista gráfica y colapsable del AST",
    "<font name='MON' size='8.5'>ui/console.py</font>      —  Terminales de salida con HTML enriquecido",
]:
    story.append(bullet(itm))
story.append(sp(4))

# ── Sección 2 — Gramática ─────────────────────────────────────
story += [h1("2.  Gramática Implementada"), sp(6),
          body("La siguiente gramática libre de contexto fue implementada mediante "
               "análisis descendente recursivo sin backtracking. "
               "Cada producción corresponde directamente a un método del parser."),
          sp(4)]

story.append(code(
"programa         ->  main { lista_declaracion }\n"
"lista_declaracion->  lista_declaracion declaracion | declaracion\n"
"declaracion      ->  declaracion_variable | lista_sentencias\n"
"declaracion_var  ->  tipo identificador ;\n"
"identificador    ->  id | identificador , id\n"
"tipo             ->  int | float | bool\n"
"lista_sentencias ->  lista_sentencias sentencia | (vacio)\n"
"sentencia        ->  seleccion | iteracion | repeticion | sent_in | sent_out | asignacion\n"
"asignacion       ->  id = sent_expresion\n"
"sent_expresion   ->  expresion ; | ;\n"
"seleccion        ->  if expresion then lista_sentencias [ else lista_sentencias ] end\n"
"iteracion        ->  while expresion lista_sentencias end\n"
"repeticion       ->  do lista_sentencias while expresion\n"
"sent_in          ->  cin >> id ;\n"
"sent_out         ->  cout << salida\n"
"salida           ->  cadena | expresion | cadena << expresion | expresion << cadena\n"
"expresion        ->  expresion_simple [ rel_op expresion_simple ]\n"
"rel_op           ->  < | <= | > | >= | == | !=\n"
"expresion_simple ->  expresion_simple suma_op termino | termino\n"
"suma_op          ->  + | - | ++ | --\n"
"termino          ->  termino mult_op factor | factor\n"
"mult_op          ->  * | / | %\n"
"factor           ->  factor pot_op componente | componente\n"
"pot_op           ->  ^\n"
"componente       ->  ( expresion ) | numero | id | bool | op_logico componente\n"
"op_logico        ->  && | || | !\n"
'cadena           ->  "cualquier texto"'
))
story.append(sp(4))

story += h2("Correspondencia Métodos del Parser ↔ Gramática")
pm_data = [
    [_cell("Método",                bold=True, color=C_DARK),
     _cell("Producción gramatical", bold=True, color=C_DARK)],
]
rows_pm = [
    ("parse() / program()",       "programa -> main { lista_declaracion }"),
    ("variable_declaration()",    "declaracion_variable -> tipo identificador ;"),
    ("statement()",               "sentencia -> seleccion | iteracion | repeticion | ..."),
    ("assignment()",              "asignacion -> id = sent_expresion"),
    ("if_statement()",            "seleccion -> if expresion then ... end"),
    ("while_statement()",         "iteracion -> while expresion lista_sentencias end"),
    ("do_while_statement()",      "repeticion -> do lista_sentencias while expresion"),
    ("input_statement()",         "sent_in -> cin >> id ;"),
    ("output_statement()",        "sent_out -> cout << salida"),
    ("expression()",              "expresion -> expresion_simple [ rel_op expresion_simple ]"),
    ("simple_expression()",       "expresion_simple -> expresion_simple suma_op termino | termino"),
    ("term()",                    "termino -> termino mult_op factor | factor"),
    ("factor()",                  "factor -> factor pot_op componente | componente"),
    ("component()",               "componente -> ( expresion ) | numero | id | bool | op_logico"),
]
for m, g in rows_pm:
    pm_data.append([
        Paragraph(f"<font name='MON' size='8'>{m}</font>",
                  S("pm", fontName="AU", fontSize=8.5, leading=12)),
        Paragraph(f"<font name='MON' size='8'>{g}</font>",
                  S("pg", fontName="AU", fontSize=8.5, leading=12)),
    ])
story.append(make_table(pm_data, col_widths=[6.5*cm, 10.5*cm]))
story.append(PageBreak())

# ── Sección 3 — Requisitos ────────────────────────────────────
story += [h1("3.  Requisitos Técnicos Cumplidos"), sp(6)]

def req(num, titulo, desc):
    return [
        _cell(str(num), center=True, color=C_DARK, size=9),
        Paragraph(titulo, S(f"rt{num}", fontName="AU", fontSize=9,
                             textColor=C_TEXT, leading=13)),
        Paragraph("✔ Cumplido", S(f"rs{num}", fontName="AU", fontSize=9,
                                        textColor=C_GREEN, alignment=TA_CENTER, leading=13)),
        Paragraph(desc, S(f"rd{num}", fontName="AU", fontSize=8.5,
                           textColor=C_TEXT, leading=12)),
    ]

rq_data = [
    [_cell("#",              bold=True, center=True, color=C_DARK, size=9),
     _cell("Requisito",     bold=True, color=C_DARK, size=9),
     _cell("Estado",        bold=True, center=True, color=C_DARK, size=9),
     _cell("Descripción", bold=True, color=C_DARK, size=9)],
    req(1, "Entrada desde archivo de tokens",
        "load_tokens_from_file() lee tokens.txt con tipo, lexema, línea y columna"),
    req(2, "Análisis sintáctico y construcción del AST",
        "Parser descendente recursivo, genera AST con nodos tipados"),
    req(3, "Visualización gráfica del árbol",
        "GraphicalASTView: nodos circulares conectados por líneas (QGraphicsView), zoom y pan"),
    req(4, "Visualización colapsable del árbol",
        "ASTTableView: tabla HTML con ramas unicode (╠═ ╚═ │), colores por tipo"),
    req(5, "Reporte de errores con línea y columna",
        '"Error sintáctico: mensaje (línea X, columna Y)"'),
    req(6, "Continuación tras errores no fatales",
        "synchronize() avanza hasta SEMICOLON / END / RBRACE y retoma el análisis"),
    req(7, "Archivo errores_sintacticos.txt",
        "save_errors() genera el archivo al finalizar cada análisis"),
    req(8, "2 archivos válidos + 1 con errores",
        "test_valido1.txt, test_valido2.txt, test_errores.txt"),
]
story.append(make_table(rq_data, col_widths=[1.0*cm, 4.8*cm, 2.4*cm, 8.8*cm]))
story.append(sp(10))

# ── Sección 4 — Archivos de Prueba ───────────────────────────
story += [h1("4.  Archivos de Prueba"), sp(6)]

story += h2("test_valido1.txt — Declaraciones, if/else, cout")
story.append(code(
"main {\n"
"  int x, y;\n"
"  float z;\n"
"  bool bandera;\n"
"\n"
"  x = 10;\n"
"  y = x + 5;\n"
"  z = y * 2.5;\n"
"  bandera = true;\n"
"\n"
"  if x < y then\n"
'    cout << "x es menor que y" << x;\n'
"  else\n"
'    cout << "x no es menor";\n'
"  end\n"
"\n"
'  cout << "z vale" << z;\n'
"}"
))
story.append(Paragraph(
    "✔  57 tokens reconocidos  |  0 errores léxicos  |  0 errores sintácticos",
    sResult))
story.append(sp(6))

story += h2("test_valido2.txt — while, do-while, cin, if sin else")
story.append(code(
"main {\n"
"  int contador;\n"
"  bool activo;\n"
"\n"
"  contador = 0;\n"
"  activo = true;\n"
"\n"
"  while contador < 10\n"
'    cout << "Iteracion" << contador;\n'
"    contador = contador + 1;\n"
"  end\n"
"\n"
"  do\n"
"    cin >> contador;\n"
'    cout << "Leiste" << contador;\n'
"  while contador != 0\n"
"\n"
"  if contador == 0 then\n"
'    cout << "Contador es cero";\n'
"  end\n"
"}"
))
story.append(Paragraph(
    "✔  AST generado correctamente  |  0 errores sintácticos",
    sResult))
story.append(PageBreak())

story += h2("test_errores.txt — Errores sintácticos intencionales")
story.append(code(
"main {\n"
"  int x y;        /* Error 1: falta coma/; entre x e y */\n"
"  float ;         /* Error 2: falta identificador      */\n"
"  x = 10          /* Error 3: falta ;                  */\n"
"  if x < then     /* Error 4: falta operando derecho   */\n"
'    cout << "error sin operando derecho";\n'
"  end\n"
"  while x > 0\n"
"    x = x - 1;\n"
"}               /* Error 5+: falta end en while      */"
))
story.append(body("Errores detectados (7):"))
for e in [
    "Se esperaba 'SEMICOLON' — encontrado 'y'     (línea 2, columna 9)",
    "Se esperaba 'ID' — encontrado ';'            (línea 3, columna 9)",
    "Se esperaba 'SEMICOLON' — encontrado 'x'     (línea 4, columna 3)",
    "Factor inválido — encontrado 'then'         (línea 5, columna 10)",
    "Se esperaba 'THEN' — encontrado 'cout'        (línea 6, columna 5)",
    "Se esperaba 'END' — encontrado '}'            (línea 10, columna 1)",
    "Se esperaba 'end' para cerrar el while         (línea 10, columna 1)",
]:
    story.append(Paragraph(f"✖  {e}", sErr))
story.append(sp(10))

# ── Sección 5 — AST ───────────────────────────────────────────
story += [h1("5.  Árbol Sintáctico Abstracto (AST)"), sp(6)]

story += h2("AST — test_valido1.txt")
story.append(code_sm(
"PROGRAMA [1:1]\n"
"  MAIN: main [1:1]\n"
"  DECLARACIONES [1:1]\n"
"    DECL_VAR [2:3]  ->  TIPO:int | ID:x | ID:y\n"
"    DECL_VAR [3:3]  ->  TIPO:float | ID:z\n"
"    DECL_VAR [4:3]  ->  TIPO:bool | ID:bandera\n"
"  SENTENCIAS [1:1]\n"
"    ASIGNACION: x [6:3]      ->  ID:x | NUMERO:10\n"
"    ASIGNACION: y [7:3]      ->  ID:y | OP_SUMA:+ (ID:x, NUMERO:5)\n"
"    ASIGNACION: z [8:3]      ->  ID:z | OP_MULT:* (ID:y, REAL:2.5)\n"
"    ASIGNACION: bandera [9:3]->  ID:bandera | BOOL:true\n"
"    IF [11:3]\n"
"      CONDICION  ->  OP_REL:< (ID:x, ID:y)\n"
'      ENTONCES   ->  SALIDA (CADENA:"x es menor que y", ID:x)\n'
'      SINO       ->  SALIDA (CADENA:"x no es menor")\n'
'    SALIDA [17:3]   ->  CADENA:"z vale" | ID:z'
))

story += h2("AST — test_valido2.txt")
story.append(code_sm(
"PROGRAMA [1:1]\n"
"  MAIN: main [1:1]\n"
"  DECLARACIONES [1:1]\n"
"    DECL_VAR [2:3]  ->  TIPO:int  | ID:contador\n"
"    DECL_VAR [3:3]  ->  TIPO:bool | ID:activo\n"
"  SENTENCIAS [1:1]\n"
"    ASIGNACION: contador [5:3]  ->  NUMERO:0\n"
"    ASIGNACION: activo   [6:3]  ->  BOOL:true\n"
"    MIENTRAS [8:3]\n"
"      CONDICION  ->  OP_REL:< (ID:contador, NUMERO:10)\n"
"      CUERPO     ->  SALIDA | ASIGNACION:contador+1\n"
"    HACER_MIENTRAS [13:3]\n"
"      CUERPO     ->  ENTRADA(ID:contador) | SALIDA\n"
"      CONDICION  ->  OP_REL:!= (ID:contador, NUMERO:0)\n"
"    IF [18:3]\n"
"      CONDICION  ->  OP_REL:== (ID:contador, NUMERO:0)\n"
'      ENTONCES   ->  SALIDA (CADENA:"Contador es cero")'
))
story.append(PageBreak())

# ── Sección 6 — Manejo de Errores ────────────────────────────
story += [h1("6.  Manejo de Errores"), sp(6),
          body("El parser implementa <b>recuperación de errores</b> mediante el método "
               "<font name='MON' size='9'>synchronize()</font>:")]
for itm in [
    "Registra el error con tipo, mensaje, línea y columna exactos",
    "Avanza tokens hasta encontrar un punto de sincronización: "
    "<font name='MON' size='8.5'>SEMICOLON</font>, "
    "<font name='MON' size='8.5'>END</font> o "
    "<font name='MON' size='8.5'>RBRACE</font>",
    "Retoma el análisis desde ese punto — permite detectar <b>múltiples errores en una sola pasada</b>",
    "Al finalizar, genera <font name='MON' size='8.5'>errores_sintacticos.txt</font> con todos los errores encontrados",
]:
    story.append(bullet(itm))
story += [sp(6),
          body("Los errores se visualizan en la terminal <b>Err. Sint.</b> del IDE: "
               "tarjetas con borde naranja sobre fondo negro, mostrando "
               "descripción del error y posición línea:columna."),
          sp(10)]

# ── Sección 7 — IDE ───────────────────────────────────────────
story += [h1("7.  Descripción del IDE"), sp(6),
          body("El analizador sintáctico está integrado en un IDE completo "
               "desarrollado en <b>Python 3 + PyQt6</b>:"),
          sp(4)]

ide_rows = [
    ("Editor de código",
     "Resaltado de sintaxis, números de línea, auto-indentación, Ctrl+D / Ctrl+/"),
    ("Vista gráfica del AST",
     "Nodos circulares conectados por líneas, zoom Ctrl+rueda, pan con mouse"),
    ("Vista colapsable del AST",
     "Tabla HTML con ramas unicode, colores por tipo de nodo, fondo oscuro"),
    ("Terminal de Tokens",
     "Tabla HTML: tipo coloreado por categoría, lexema, línea y columna"),
    ("Terminal Err. Léxicos",
     "Tarjetas con borde rojo: símbolo no reconocido y posición exacta"),
    ("Terminal Err. Sint.",
     "Tarjetas con borde naranja: descripción del error y posición línea:col"),
    ("Consola principal",
     "Salida con badges de estado (info, ok, warning, error)"),
    ("15 temas visuales",
     "dark_pro, pure_black, tokyo_night, catppuccin, dracula, nord, monokai…"),
    ("Paleta de comandos",
     "Ctrl+Shift+P — búsqueda y ejecución de cualquier acción del IDE"),
    ("Drag & Drop",
     "Arrastrar archivos .txt / .c / .cpp directamente al editor"),
]
ide_data = [
    [_cell("Característica", bold=True, color=C_DARK, size=9),
     _cell("Descripción",    bold=True, color=C_DARK, size=9)],
]
for c1, c2 in ide_rows:
    ide_data.append([
        Paragraph(f"<b>{c1}</b>",
                  S("id1", fontName="AU", fontSize=9, textColor=C_MID, leading=13)),
        Paragraph(c2,
                  S("id2", fontName="AU", fontSize=8.5, textColor=C_TEXT, leading=12)),
    ])
story.append(make_table(ide_data, col_widths=[5.5*cm, 11.5*cm]))
story.append(sp(10))

story += h2("Tecnologías utilizadas")
for itm in [
    "Python 3.11",
    "PyQt6 6.x — interfaz gráfica multiplataforma",
    "Analizador léxico propio — <font name='MON' size='8.5'>compiler/lexer.py</font>",
    "Analizador sintáctico propio — descendente recursivo — <font name='MON' size='8.5'>compiler/parser.py</font>",
    "Sin dependencias externas para el análisis (solo stdlib + PyQt6)",
]:
    story.append(bullet(itm))

story += [sp(24), hr(C_DARK, 1.5), sp(4),
          Paragraph("IDE Compilador — Fase 2: Análisis Sintáctico  "
                    "·  Compiladores I  ·  8° ISC  ·  2025",
                    sFooter)]

# ── Build ──────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=A4,
    leftMargin=2.5*cm, rightMargin=2.5*cm,
    topMargin=2.2*cm,  bottomMargin=2.2*cm,
    title="Fase 2 – Análisis Sintáctico",
    author="Jesús Abraham Robledo López / Edgar Alejandro Cedeño Suárez",
    subject="Compiladores I — 8° ISC",
)
doc.build(story)
print(f"PDF generado: {OUTPUT}")
