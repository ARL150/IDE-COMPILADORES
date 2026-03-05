# semantic.py
# Analizador semántico para un mini lenguaje tipo TINY

# --- EJEMPLO: árbol sintáctico de entrada (podría venir de parser.py) ---
# Formato simple para este ejemplo:
# Cada nodo es un diccionario: {'tipo': 'asignacion'/'operacion', 'var': 'x', 'valor': valor}
syntax_tree = [
    {'tipo': 'asignacion', 'var': 'x', 'valor': 5, 'linea': 1},
    {'tipo': 'asignacion', 'var': 'y', 'valor': 10, 'linea': 2},
    {'tipo': 'asignacion', 'var': 'z', 'valor': {'op': '+', 'izq': 'x', 'der': 'y'}, 'linea': 3},
    {'tipo': 'imprimir', 'var': 'z', 'linea': 4},
    {'tipo': 'asignacion', 'var': 'error_line', 'valor': 1, 'linea': 5},  # ejemplo de error
]

# --- TABLA DE SIMBOLOS Y ERRORES ---
tabla_simbolos = {}
errores = []

# Función para procesar cada nodo
def procesar_nodo(nodo):
    if nodo['tipo'] == 'asignacion':
        var = nodo['var']
        valor = nodo['valor']

        # Verifica si el valor es una operación
        if isinstance(valor, dict) and 'op' in valor:
            izq = valor['izq']
            der = valor['der']
            # Comprobamos si las variables usadas existen
            for v in [izq, der]:
                if v not in tabla_simbolos:
                    errores.append({'linea': nodo['linea'], 'descripcion': f"Variable '{v}' usada antes de declarar"})
            # Asumimos tipo int para operaciones
            tabla_simbolos[var] = 'int'
        else:
            # Si el valor es un número, lo agregamos a la tabla
            if isinstance(valor, int):
                tabla_simbolos[var] = 'int'
            else:
                errores.append({'linea': nodo['linea'], 'descripcion': f"Valor no permitido para '{var}'"})
    elif nodo['tipo'] == 'imprimir':
        var = nodo['var']
        if var not in tabla_simbolos:
            errores.append({'linea': nodo['linea'], 'descripcion': f"Variable '{var}' usada antes de declarar"})

# --- PROCESAR TODO EL ARBOL ---
for nodo in syntax_tree:
    procesar_nodo(nodo)

# --- IMPRIMIR TABLA DE SIMBOLOS ---
print("===TABLA_DE_SIMBOLOS===")
if tabla_simbolos:
    for nombre, tipo in tabla_simbolos.items():
        print(f"{nombre} : {tipo}")
else:
    print("Tabla vacía")

# --- IMPRIMIR ERRORES SEMÁNTICOS ---
print("===ERRORES_SEMANTICOS===")
if errores:
    for e in errores:
        print(f"Línea {e['linea']}: {e['descripcion']}")
else:
    print("Sin errores semánticos")