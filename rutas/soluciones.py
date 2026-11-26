"""
Base de soluciones frecuentes de la organización.
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from db import get_db
from seguridad import organizacion_actual, rol_requerido
from servicios.clasificador import CATEGORIA_POR_CLASIFICAR

bp = Blueprint("soluciones", __name__, url_prefix="/soluciones")


@bp.route("/", methods=["GET", "POST"])
@rol_requerido("encargado")
def lista():
    conexion = get_db()

    categorias = conexion.execute(
        "SELECT id, nombre FROM categorias WHERE nombre <> ? ORDER BY nombre",
        (CATEGORIA_POR_CLASIFICAR,)
    ).fetchall()

    error = None

    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        pasos = request.form.get("pasos", "").strip()
        categoria_id = request.form.get("categoria_id", "").strip()

        if not titulo or not pasos:
            error = "Debes completar el título y los pasos."
        elif categoria_id not in [str(categoria["id"]) for categoria in categorias]:
            error = "La categoría seleccionada no es válida."
        else:
            conexion.execute(
                "INSERT INTO soluciones (organizacion_id, categoria_id, titulo, pasos) VALUES (?, ?, ?, ?)",
                (organizacion_actual(), categoria_id, titulo, pasos)
            )
            conexion.commit()
            flash("Solución agregada.")
            return redirect(url_for("soluciones.lista"))

    soluciones = conexion.execute("""
        SELECT s.*, c.nombre AS categoria
        FROM soluciones s
        JOIN categorias c ON s.categoria_id = c.id
        WHERE s.organizacion_id = ?
        ORDER BY c.nombre, s.titulo
    """, (organizacion_actual(),)).fetchall()

    return render_template(
        "soluciones/lista.html",
        soluciones=soluciones,
        categorias=categorias,
        error=error
    )


@bp.route("/<int:solucion_id>/eliminar", methods=["POST"])
@rol_requerido("encargado")
def eliminar(solucion_id):
    conexion = get_db()
    conexion.execute(
        "DELETE FROM soluciones WHERE id = ? AND organizacion_id = ?",
        (solucion_id, organizacion_actual())
    )
    conexion.commit()
    flash("Solución eliminada.")
    return redirect(url_for("soluciones.lista"))
