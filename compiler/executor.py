import sys
import subprocess

if __name__ == "__main__":
    file_path = sys.argv[1]

    try:
        # Ejecuta el archivo Python
        result = subprocess.run(["python", file_path], capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)  # dock Consola
        if result.stderr:
            print(result.stderr, file=sys.stderr)  # dock Errores
    except Exception as e:
        print(e, file=sys.stderr)