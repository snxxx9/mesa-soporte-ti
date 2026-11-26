from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db
from seguridad import rol_requerido

bp = Blueprint("auth", __name__)

LARGO_MINIMO_CLAVE = 8


def pagina_inicio_segun_rol(rol):
    if rol == "admin":
        return url_for("admin.organizaciones")
    return url_for("tickets.inicio")


@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        clave = request.form.get("clave", "")

        cuenta = get_db().execute(
            "SELECT * FROM usuarios WHERE usuario = ? AND clave_hash IS NOT NULL",
            (usuario,)
        ).fetchone()

        if cuenta is None or not check_password_hash(cuenta["clave_hash"], clave):
            error = "Usuario o clave incorrectos."
        else:
            session.clear()
            session["usuario_id"] = cuenta["id"]

            siguiente = request.args.get("siguiente", "")

            # Solo se permite redirigir a rutas internas
            if siguiente.startswith("/") and not siguiente.startswith("//"):
                return redirect(siguiente)

            return redirect(pagina_inicio_segun_rol(cuenta["rol"]))

    return render_template("auth/login.html", error=error)


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("publico.inicio"))


@bp.route("/cuenta/clave", methods=["GET", "POST"])
@rol_requerido("tecnico", "encargado", "admin")
def cambiar_clave():
    error = None

    if request.method == "POST":
        actual = request.form.get("actual", "")
        nueva = request.form.get("nueva", "")
        repetir = request.form.get("repetir", "")

        if not check_password_hash(g.usuario["clave_hash"], actual):
            error = "La clave actual no es correcta."
        elif len(nueva) < LARGO_MINIMO_CLAVE:
            error = f"La nueva clave debe tener al menos {LARGO_MINIMO_CLAVE} caracteres."
        elif nueva != repetir:
            error = "Las claves nuevas no coinciden."
        else:
            conexion = get_db()
            conexion.execute(
                "UPDATE usuarios SET clave_hash = ? WHERE id = ?",
                (generate_password_hash(nueva), g.usuario["id"])
            )
            conexion.commit()

            flash("Clave actualizada correctamente.")
            return redirect(pagina_inicio_segun_rol(g.usuario["rol"]))

    return render_template("auth/cambiar_clave.html", error=error)
