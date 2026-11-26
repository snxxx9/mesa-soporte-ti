"""
Inicio de sesión, permisos por rol y protección CSRF (riesgo R5).

- cargar_usuario(): deja en g.usuario al usuario conectado (o None).
- rol_requerido(...): decorador que limita una ruta a ciertos roles.
- validar_csrf(): rechaza formularios POST que no traen el token correcto,
  así otra página no puede enviar formularios en nombre del usuario.
"""

import secrets
from functools import wraps

from flask import abort, flash, g, redirect, request, session, url_for

from db import get_db

# Roles que atienden tickets dentro de una organización
ROLES_ATENCION = ("tecnico", "encargado")


def cargar_usuario():
    usuario_id = session.get("usuario_id")

    if usuario_id is None:
        g.usuario = None
    else:
        g.usuario = get_db().execute(
            """
            SELECT u.*, o.nombre AS organizacion, o.slug AS organizacion_slug
            FROM usuarios u
            LEFT JOIN organizaciones o ON u.organizacion_id = o.id
            WHERE u.id = ?
            """,
            (usuario_id,)
        ).fetchone()


def rol_requerido(*roles):
    """Uso: @rol_requerido("encargado") sobre una función de ruta."""
    def decorador(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            if g.usuario is None:
                flash("Debes iniciar sesión para continuar.")
                return redirect(url_for("auth.login", siguiente=request.path))

            if g.usuario["rol"] not in roles:
                abort(403)

            return vista(*args, **kwargs)
        return envoltura
    return decorador


def organizacion_actual():
    """Id de la organización del usuario conectado."""
    return g.usuario["organizacion_id"]


def obtener_token_csrf():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return session["csrf_token"]


def validar_csrf():
    if request.method == "POST":
        token = request.form.get("csrf_token", "")
        if not secrets.compare_digest(token, session.get("csrf_token", "")):
            abort(400, "El formulario expiró. Vuelve a cargar la página.")
