from flask import Blueprint, flash, redirect, render_template, url_for

from db import get_db
from seguridad import ROLES_ATENCION, organizacion_actual, rol_requerido
from servicios.alertas import DIAS_PLAZO_REVISION, DIAS_VENTANA, FALLAS_PARA_ALERTA

bp = Blueprint("alertas", __name__, url_prefix="/alertas")


@bp.route("/")
@rol_requerido(*ROLES_ATENCION)
def lista():
    alertas = get_db().execute("""
        SELECT
            a.*,
            e.codigo AS equipo_codigo,
            e.nombre AS equipo_nombre,
            CASE
                WHEN a.estado = 'Pendiente' AND a.fecha_limite < CURRENT_TIMESTAMP
                THEN 1 ELSE 0
            END AS vencida
        FROM alertas a
        JOIN equipos e ON a.equipo_id = e.id
        WHERE e.organizacion_id = ?
        ORDER BY a.estado, a.fecha_limite
    """, (organizacion_actual(),)).fetchall()

    return render_template(
        "alertas/lista.html",
        alertas=alertas,
        fallas=FALLAS_PARA_ALERTA,
        dias_ventana=DIAS_VENTANA,
        dias_plazo=DIAS_PLAZO_REVISION
    )


@bp.route("/<int:alerta_id>/revisar", methods=["POST"])
@rol_requerido(*ROLES_ATENCION)
def revisar(alerta_id):
    conexion = get_db()

    # La subconsulta asegura que la alerta sea de la organización del usuario
    conexion.execute("""
        UPDATE alertas
        SET estado = 'Revisada',
            fecha_revision = CURRENT_TIMESTAMP
        WHERE id = ?
        AND estado = 'Pendiente'
        AND equipo_id IN (SELECT id FROM equipos WHERE organizacion_id = ?)
    """, (alerta_id, organizacion_actual()))

    conexion.commit()
    flash("Alerta marcada como revisada.")

    return redirect(url_for("alertas.lista"))
