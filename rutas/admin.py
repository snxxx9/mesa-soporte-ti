import re
import sqlite3

from flask import Blueprint, flash, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash

from db import get_db
from rutas.auth import LARGO_MINIMO_CLAVE
from seguridad import rol_requerido
from servicios.clasificador import normalizar
from servicios.indicadores import cuadro_de_mando

bp = Blueprint("admin", __name__, url_prefix="/admin")

TIPOS_ORGANIZACION = ("Pyme", "Colegio", "Servicio TI")
ROLES_CON_CUENTA = ("tecnico", "encargado")


def crear_slug(nombre):
    """'Colegio San José' -> 'colegio-san-jose' (se usa en los enlaces)."""
    return re.sub(r"[^a-z0-9]+", "-", normalizar(nombre)).strip("-")


def validar_cuenta(nombre, usuario, clave):
    if not nombre or not usuario:
        return "El nombre y el usuario de la cuenta son obligatorios."
    if len(clave) < LARGO_MINIMO_CLAVE:
        return f"La clave debe tener al menos {LARGO_MINIMO_CLAVE} caracteres."
    return None


@bp.route("/organizaciones", methods=["GET", "POST"])
@rol_requerido("admin")
def organizaciones():
    conexion = get_db()
    error = None

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        tipo = request.form.get("tipo", "").strip()
        encargado = request.form.get("encargado", "").strip()
        usuario = request.form.get("usuario", "").strip()
        clave = request.form.get("clave", "")
        email = request.form.get("email", "").strip()

        if not nombre:
            error = "El nombre de la organización es obligatorio."
        elif tipo not in TIPOS_ORGANIZACION:
            error = "El tipo de organización no es válido."
        else:
            error = validar_cuenta(encargado, usuario, clave)

        if error is None:
            try:
                cursor = conexion.execute(
                    "INSERT INTO organizaciones (nombre, slug, tipo) VALUES (?, ?, ?)",
                    (nombre, crear_slug(nombre), tipo)
                )
                conexion.execute(
                    """
                    INSERT INTO usuarios (organizacion_id, nombre, rol, usuario, clave_hash, email)
                    VALUES (?, ?, 'encargado', ?, ?, ?)
                    """,
                    (cursor.lastrowid, encargado, usuario, generate_password_hash(clave), email or None)
                )
                conexion.commit()

                flash(f"Organización {nombre} creada con su encargado TI.")
                return redirect(url_for("admin.organizaciones"))

            except sqlite3.IntegrityError:
                conexion.rollback()
                error = "Ya existe una organización con ese nombre o el usuario ya está en uso."

    lista = conexion.execute("""
        SELECT
            o.*,
            (SELECT COUNT(*) FROM equipos e WHERE e.organizacion_id = o.id) AS equipos,
            (SELECT COUNT(*) FROM tickets t WHERE t.organizacion_id = o.id) AS tickets,
            (SELECT COUNT(*) FROM usuarios u WHERE u.organizacion_id = o.id) AS usuarios
        FROM organizaciones o
        ORDER BY o.nombre
    """).fetchall()

    return render_template(
        "admin/organizaciones.html",
        organizaciones=lista,
        tipos=TIPOS_ORGANIZACION,
        error=error
    )


@bp.route("/usuarios", methods=["GET", "POST"])
@rol_requerido("admin")
def usuarios():
    conexion = get_db()
    error = None

    organizaciones = conexion.execute(
        "SELECT id, nombre FROM organizaciones ORDER BY nombre"
    ).fetchall()

    if request.method == "POST":
        organizacion_id = request.form.get("organizacion_id", "").strip()
        rol = request.form.get("rol", "").strip()
        nombre = request.form.get("nombre", "").strip()
        usuario = request.form.get("usuario", "").strip()
        clave = request.form.get("clave", "")
        email = request.form.get("email", "").strip()

        if organizacion_id not in [str(organizacion["id"]) for organizacion in organizaciones]:
            error = "La organización seleccionada no es válida."
        elif rol not in ROLES_CON_CUENTA:
            error = "El rol seleccionado no es válido."
        else:
            error = validar_cuenta(nombre, usuario, clave)

        if error is None:
            try:
                conexion.execute(
                    """
                    INSERT INTO usuarios (organizacion_id, nombre, rol, usuario, clave_hash, email)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (organizacion_id, nombre, rol, usuario, generate_password_hash(clave), email or None)
                )
                conexion.commit()
                flash(f"Cuenta '{usuario}' creada.")
                return redirect(url_for("admin.usuarios"))

            except sqlite3.IntegrityError:
                conexion.rollback()
                error = "Ese nombre de usuario ya está en uso."

    cuentas = conexion.execute("""
        SELECT u.id, u.nombre, u.rol, u.usuario, u.email, o.nombre AS organizacion
        FROM usuarios u
        LEFT JOIN organizaciones o ON u.organizacion_id = o.id
        WHERE u.usuario IS NOT NULL
        ORDER BY o.nombre, u.rol, u.nombre
    """).fetchall()

    return render_template(
        "admin/usuarios.html",
        cuentas=cuentas,
        organizaciones=organizaciones,
        roles=ROLES_CON_CUENTA,
        error=error
    )


@bp.route("/usuarios/<int:usuario_id>/clave", methods=["POST"])
@rol_requerido("admin")
def restablecer_clave(usuario_id):
    clave = request.form.get("clave", "")

    if len(clave) < LARGO_MINIMO_CLAVE:
        flash(f"La clave debe tener al menos {LARGO_MINIMO_CLAVE} caracteres.")
    else:
        conexion = get_db()
        conexion.execute(
            "UPDATE usuarios SET clave_hash = ? WHERE id = ? AND usuario IS NOT NULL",
            (generate_password_hash(clave), usuario_id)
        )
        conexion.commit()
        flash("Clave restablecida.")

    return redirect(url_for("admin.usuarios"))


@bp.route("/proyecto", methods=["GET", "POST"])
@rol_requerido("admin")
def proyecto():
    """Registro semanal de K1, K2 y K9."""
    conexion = get_db()
    error = None

    campos = (
        "tareas_planificadas", "tareas_terminadas", "costo_presupuestado",
        "costo_real", "horas_totales", "horas_en_linea",
    )

    if request.method == "POST":
        semana_inicio = request.form.get("semana_inicio", "").strip()

        try:
            valores = [float(request.form.get(campo, "")) for campo in campos]
        except ValueError:
            valores = None

        if not semana_inicio or valores is None:
            error = "Completa todos los campos con números."
        elif any(valor < 0 for valor in valores):
            error = "Los valores no pueden ser negativos."
        else:
            # Si ya existe la semana, se reemplaza
            conexion.execute(
                """
                INSERT OR REPLACE INTO mediciones_semanales (
                    semana_inicio, tareas_planificadas, tareas_terminadas,
                    costo_presupuestado, costo_real, horas_totales, horas_en_linea
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [semana_inicio] + valores
            )
            conexion.commit()
            flash("Medición semanal guardada.")
            return redirect(url_for("admin.proyecto"))

    mediciones = conexion.execute(
        "SELECT * FROM mediciones_semanales ORDER BY semana_inicio DESC"
    ).fetchall()

    cuadro = cuadro_de_mando(conexion, organizacion_id=None, incluir_proyecto=True)

    return render_template(
        "admin/proyecto.html",
        mediciones=mediciones,
        cuadro=cuadro,
        error=error
    )
