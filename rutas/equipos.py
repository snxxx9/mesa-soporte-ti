"""
Inventario de equipos: códigos QR, historial, mantenimiento predictivo
y reporte de equipos dados de baja para reciclaje (Ley REP).
"""

import csv
import io

from flask import Blueprint, Response, abort, flash, redirect, render_template, request, url_for

from db import get_db
from seguridad import ROLES_ATENCION, organizacion_actual, rol_requerido
from servicios.prediccion import riesgo_de_equipos

bp = Blueprint("equipos", __name__, url_prefix="/equipos")

TIPOS_EQUIPO = ("Computador", "Notebook", "Impresora", "Proyector", "Red", "Otro")
ESTADOS_EQUIPO = ("Activo", "En reparación", "Dado de baja")

CAMPOS_EQUIPO = (
    "codigo", "nombre", "tipo", "marca", "modelo", "numero_serie",
    "ubicacion", "fecha_compra", "estado", "motivo_baja",
)


def obtener_equipo_o_404(codigo):
    equipo = get_db().execute(
        "SELECT * FROM equipos WHERE codigo = ? AND organizacion_id = ?",
        (codigo, organizacion_actual())
    ).fetchone()

    if equipo is None:
        abort(404)

    return equipo


def validar_equipo(datos, codigo_actual=None):
    """Devuelve un mensaje de error o None si los datos son válidos."""
    if not datos["codigo"] or not datos["nombre"]:
        return "El código y el nombre son obligatorios."

    if datos["tipo"] not in TIPOS_EQUIPO:
        return "El tipo de equipo no es válido."

    if datos["estado"] not in ESTADOS_EQUIPO:
        return "El estado del equipo no es válido."

    if datos["estado"] == "Dado de baja" and not datos["motivo_baja"]:
        return "Indica el motivo de la baja."

    if datos["codigo"] != codigo_actual:
        repetido = get_db().execute(
            "SELECT id FROM equipos WHERE codigo = ?",
            (datos["codigo"],)
        ).fetchone()
        if repetido:
            return "Ya existe un equipo con ese código."

    return None


def leer_formulario_equipo():
    datos = {campo: request.form.get(campo, "").strip() for campo in CAMPOS_EQUIPO}
    datos["codigo"] = datos["codigo"].upper()
    return datos


@bp.route("/")
@rol_requerido(*ROLES_ATENCION)
def lista():
    conexion = get_db()

    equipos = conexion.execute("""
        SELECT
            e.*,
            COUNT(t.id) AS total_tickets
        FROM equipos e
        LEFT JOIN tickets t ON t.equipo_id = e.id
        WHERE e.organizacion_id = ?
        GROUP BY e.id
        ORDER BY e.estado = 'Dado de baja', e.codigo
    """, (organizacion_actual(),)).fetchall()

    riesgos = riesgo_de_equipos(conexion, organizacion_actual())

    return render_template("equipos/lista.html", equipos=equipos, riesgos=riesgos)


@bp.route("/nuevo", methods=["GET", "POST"])
@rol_requerido("encargado")
def nuevo():
    datos = {"tipo": "Computador", "estado": "Activo"}
    error = None

    if request.method == "POST":
        datos = leer_formulario_equipo()
        error = validar_equipo(datos)

        if error is None:
            conexion = get_db()
            conexion.execute("""
                INSERT INTO equipos (
                    organizacion_id, codigo, nombre, tipo, marca, modelo,
                    numero_serie, ubicacion, fecha_compra, estado, motivo_baja,
                    fecha_baja
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        CASE WHEN ? = 'Dado de baja' THEN date('now') END)
            """, (
                organizacion_actual(), datos["codigo"], datos["nombre"], datos["tipo"],
                datos["marca"] or None, datos["modelo"] or None, datos["numero_serie"] or None,
                datos["ubicacion"] or None, datos["fecha_compra"] or None, datos["estado"],
                datos["motivo_baja"] or None, datos["estado"]
            ))
            conexion.commit()

            flash(f"Equipo {datos['codigo']} registrado.")
            return redirect(url_for("equipos.lista"))

    return render_template(
        "equipos/formulario.html",
        datos=datos, tipos=TIPOS_EQUIPO, estados=ESTADOS_EQUIPO, error=error, editando=False
    )


@bp.route("/<codigo>/editar", methods=["GET", "POST"])
@rol_requerido("encargado")
def editar(codigo):
    equipo = obtener_equipo_o_404(codigo)
    datos = dict(equipo)
    error = None

    if request.method == "POST":
        datos = leer_formulario_equipo()
        error = validar_equipo(datos, codigo_actual=equipo["codigo"])

        if error is None:
            conexion = get_db()
            conexion.execute("""
                UPDATE equipos
                SET codigo = ?, nombre = ?, tipo = ?, marca = ?, modelo = ?,
                    numero_serie = ?, ubicacion = ?, fecha_compra = ?, estado = ?,
                    motivo_baja = ?,
                    fecha_baja = CASE
                        WHEN ? = 'Dado de baja' THEN COALESCE(fecha_baja, date('now'))
                        ELSE NULL
                    END
                WHERE id = ?
            """, (
                datos["codigo"], datos["nombre"], datos["tipo"], datos["marca"] or None,
                datos["modelo"] or None, datos["numero_serie"] or None, datos["ubicacion"] or None,
                datos["fecha_compra"] or None, datos["estado"], datos["motivo_baja"] or None,
                datos["estado"], equipo["id"]
            ))
            conexion.commit()

            flash(f"Equipo {datos['codigo']} actualizado.")
            return redirect(url_for("equipos.historial", codigo=datos["codigo"]))

    return render_template(
        "equipos/formulario.html",
        datos=datos, tipos=TIPOS_EQUIPO, estados=ESTADOS_EQUIPO, error=error, editando=True
    )


@bp.route("/<codigo>")
@rol_requerido(*ROLES_ATENCION)
def historial(codigo):
    conexion = get_db()
    equipo = obtener_equipo_o_404(codigo)

    tickets = conexion.execute("""
        SELECT
            t.id, t.titulo, t.fecha_creacion, t.fecha_cierre,
            t.prioridad, t.estado, t.solucion,
            c.nombre AS categoria
        FROM tickets t
        JOIN categorias c ON t.categoria_id = c.id
        WHERE t.equipo_id = ?
        ORDER BY t.id DESC
    """, (equipo["id"],)).fetchall()

    alertas = conexion.execute("""
        SELECT *
        FROM alertas
        WHERE equipo_id = ?
        ORDER BY id DESC
    """, (equipo["id"],)).fetchall()

    riesgo = riesgo_de_equipos(conexion, organizacion_actual()).get(equipo["id"])

    return render_template(
        "equipos/historial.html",
        equipo=equipo,
        tickets=tickets,
        alertas=alertas,
        riesgo=riesgo
    )


@bp.route("/etiquetas")
@rol_requerido(*ROLES_ATENCION)
def etiquetas():
    """Página para imprimir las etiquetas QR de todos los equipos activos."""
    equipos = get_db().execute("""
        SELECT codigo, nombre, ubicacion
        FROM equipos
        WHERE organizacion_id = ?
        AND estado <> 'Dado de baja'
        ORDER BY codigo
    """, (organizacion_actual(),)).fetchall()

    return render_template("equipos/etiquetas.html", equipos=equipos)


@bp.route("/afiche")
@rol_requerido(*ROLES_ATENCION)
def afiche():
    """Afiche con el QR general de la organización (ajuste del piloto, K3)."""
    return render_template("equipos/afiche.html")


@bp.route("/reciclaje")
@rol_requerido("encargado")
def reciclaje():
    """Reporte de equipos dados de baja para reciclaje responsable (Ley REP)."""
    equipos = get_db().execute("""
        SELECT codigo, nombre, tipo, marca, modelo, numero_serie,
               fecha_compra, fecha_baja, motivo_baja
        FROM equipos
        WHERE organizacion_id = ?
        AND estado = 'Dado de baja'
        ORDER BY fecha_baja DESC
    """, (organizacion_actual(),)).fetchall()

    if request.args.get("formato") == "csv":
        salida = io.StringIO()
        escritor = csv.writer(salida, delimiter=";")
        escritor.writerow(equipos[0].keys() if equipos else ["codigo"])
        for equipo in equipos:
            escritor.writerow(list(equipo))

        # El BOM (﻿) permite que Excel muestre bien los tildes
        return Response(
            "﻿" + salida.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=equipos_dados_de_baja.csv"}
        )

    return render_template("equipos/reciclaje.html", equipos=equipos)
