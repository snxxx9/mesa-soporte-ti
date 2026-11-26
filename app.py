"""
SoporTI · Tu soporte TI, ordenado y preventivo.

Archivo principal: crea la aplicación Flask y registra las rutas,
que están separadas por área dentro de la carpeta rutas/.
"""

import os
import secrets

from flask import Flask, render_template

from db import close_db, init_db
from rutas import admin, alertas, auth, equipos, indicadores, publico, soluciones, tickets
from seguridad import cargar_usuario, obtener_token_csrf, validar_csrf
from servicios.sla import calcular_sla


def crear_app():
    app = Flask(__name__)

    # La clave secreta firma la sesión. En producción se define con la
    # variable de entorno SECRET_KEY para que no cambie al reiniciar.
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))

    # Funciones disponibles en todas las plantillas
    app.jinja_env.globals["calcular_sla"] = calcular_sla
    app.jinja_env.globals["csrf_token"] = obtener_token_csrf

    # Antes de cada petición: usuario conectado y validación del formulario
    app.before_request(cargar_usuario)
    app.before_request(validar_csrf)
    app.teardown_appcontext(close_db)

    for modulo in (publico, auth, tickets, equipos, alertas, indicadores, soluciones, admin):
        app.register_blueprint(modulo.bp)

    @app.errorhandler(403)
    def sin_permiso(error):
        return render_template("error.html", mensaje="No tienes permiso para ver esta página."), 403

    @app.errorhandler(404)
    def no_encontrado(error):
        return render_template("error.html", mensaje="La página que buscas no existe."), 404

    return app


app = crear_app()


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
