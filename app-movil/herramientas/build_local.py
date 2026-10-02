# Arma una página completa (con doctype y head) a partir de index.html, para abrirla fuera del Artifact.
import sys, pathlib
APP = pathlib.Path(__file__).resolve().parent.parent
src = (APP / "index.html").read_text(encoding="utf-8")
out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else APP / "local.html"
page = ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<meta name="theme-color" content="#FF5E08">\n<link rel="icon" href="img/icono.png">\n'
        '<link rel="apple-touch-icon" href="img/icono.png">\n</head>\n<body>\n' + src + '\n</body>\n</html>\n')
out.write_text(page, encoding="utf-8")
print("escrito", out)
