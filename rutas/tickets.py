from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from db import get_db
from seguridad import ROLES_ATENCION, organizacion_actual, rol_requerido
from servicios.clasificador import CATEGORIA_POR_CLASIFICAR
from servicios.notificaciones import enlace_whatsapp, enviar_correo
from servicios.sla import calcular_sla
from servicios.tickets import ESTADOS_CERRADOS, ESTADOS_VALIDOS, PRIORIDADES_VALIDAS

bp = Blueprint("tickets", __name__)

CANALES_EXTERNOS = ("WhatsApp", "Correo", "Verbal", "Otro")


def registrar_cambio(conexion, ticket_id, campo, valor_anterior, valor_nuevo):
    """Guarda en cambios_ticket la trazabilidad de un campo modificado."""
    conexion.execute("""
        INSERT INTO cambios_ticket (
            ticket_id,
            campo,
            valor_anterior,
            valor_nuevo
        )
        VALUES (?, ?, ?, ?)
    """, (ticket_id, campo, valor_anterior, valor_nuevo))


@bp.route("/panel")
@rol_requerido(*ROLES_ATENCION)
def inicio():
    conexion = get_db()
    organizacion_id = organizacion_actual()

    # Filtros RF-05
    estado = request.args.get("estado", "").strip()
    prioridad = request.args.get("prioridad", "").strip()
    categoria_id = request.args.get("categoria", "").strip()

    categorias = conexion.execute("""
        SELECT id, nombre
        FROM categorias
        ORDER BY nombre
    """).fetchall()

    consulta = """
        SELECT
            t.id,
            t.titulo,
            t.fecha_creacion,
            t.fecha_cierre,
            t.prioridad,
            t.estado,
            u.nombre AS solicitante,
            c.nombre AS categoria,
            r.nombre AS responsable,
            e.codigo AS equipo
        FROM tickets t
        JOIN usuarios u ON t.solicitante_id = u.id
        JOIN categorias c ON t.categoria_id = c.id
        LEFT JOIN usuarios r ON t.responsable_id = r.id
        LEFT JOIN equipos e ON t.equipo_id = e.id
        WHERE t.organizacion_id = ?
    """

    parametros = [organizacion_id]

    if estado:
        consulta += " AND t.estado = ?"
        parametros.append(estado)

    if prioridad:
        consulta += " AND t.prioridad = ?"
        parametros.append(prioridad)

    if categoria_id:
        consulta += " AND t.categoria_id = ?"
        parametros.append(categoria_id)

    consulta += " ORDER BY t.id DESC"

    tickets = conexion.execute(consulta, parametros).fetchall()

    # Resumen RF-06
    resumen = conexion.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN estado = 'Nuevo' THEN 1 ELSE 0 END) AS nuevos,
            SUM(CASE WHEN estado = 'En proceso' THEN 1 ELSE 0 END) AS en_proceso,
            SUM(CASE WHEN estado = 'Resuelto' THEN 1 ELSE 0 END) AS resueltos,
            SUM(CASE WHEN estado = 'Cerrado' THEN 1 ELSE 0 END) AS cerrados
        FROM tickets
        WHERE organizacion_id = ?
    """, (organizacion_id,)).fetchone()

    # Avisos al encargado: tickets abiertos cerca o fuera de su plazo (SLA)
    tickets_abiertos = conexion.execute("""
        SELECT fecha_creacion, fecha_cierre, prioridad, estado
        FROM tickets
        WHERE organizacion_id = ?
        AND estado IN ('Nuevo', 'En proceso')
    """, (organizacion_id,)).fetchall()

    estados_sla = [calcular_sla(ticket)["estado"] for ticket in tickets_abiertos]

    avisos = {
        "por_vencer": estados_sla.count("Por vencer"),
        "vencidos": estados_sla.count("Vencido"),
        "por_clasificar": conexion.execute("""
            SELECT COUNT(*) FROM tickets t
            JOIN categorias c ON t.categoria_id = c.id
            WHERE t.organizacion_id = ?
            AND c.nombre = ?
            AND t.estado IN ('Nuevo', 'En proceso')
        """, (organizacion_id, CATEGORIA_POR_CLASIFICAR)).fetchone()[0],
        "alertas_pendientes": conexion.execute("""
            SELECT COUNT(*) FROM alertas a
            JOIN equipos e ON a.equipo_id = e.id
            WHERE e.organizacion_id = ?
            AND a.estado = 'Pendiente'
        """, (organizacion_id,)).fetchone()[0],
    }

    return render_template(
        "tickets/lista.html",
        tickets=tickets,
        categorias=categorias,
        estados=ESTADOS_VALIDOS,
        prioridades=PRIORIDADES_VALIDAS,
        filtro_estado=estado,
        filtro_prioridad=prioridad,
        filtro_categoria=categoria_id,
        resumen=resumen,
        avisos=avisos
    )


@bp.route("/tickets/<int:ticket_id>", methods=["GET", "POST"])
@rol_requerido(*ROLES_ATENCION)
def detalle(ticket_id):
    conexion = get_db()

    ticket = conexion.execute("""
        SELECT
            t.*,
            u.nombre AS solicitante,
            u.email AS solicitante_email,
            u.telefono AS solicitante_telefono,
            c.nombre AS categoria,
            r.nombre AS responsable,
            cs.nombre AS categoria_sugerida,
            e.codigo AS equipo_codigo,
            e.nombre AS equipo_nombre
        FROM tickets t
        JOIN usuarios u ON t.solicitante_id = u.id
        JOIN categorias c ON t.categoria_id = c.id
        LEFT JOIN usuarios r ON t.responsable_id = r.id
        LEFT JOIN categorias cs ON t.categoria_sugerida_id = cs.id
        LEFT JOIN equipos e ON t.equipo_id = e.id
        WHERE t.id = ?
        AND t.organizacion_id = ?
    """, (ticket_id, organizacion_actual())).fetchone()

    if ticket is None:
        abort(404)

    responsables = conexion.execute("""
        SELECT id, nombre
        FROM usuarios
        WHERE organizacion_id = ?
        AND rol IN ('tecnico', 'encargado')
        ORDER BY nombre
    """, (organizacion_actual(),)).fetchall()

    categorias = conexion.execute(
        "SELECT id, nombre FROM categorias ORDER BY nombre"
    ).fetchall()

    error = None

    if request.method == "POST":
        responsable_id = request.form.get("responsable_id", "").strip()
        nuevo_estado = request.form.get("estado", "").strip()
        nueva_prioridad = request.form.get("prioridad", "").strip()
        nueva_categoria_id = request.form.get("categoria_id", "").strip()
        solucion = request.form.get("solucion", "").strip()
        guardar_en_base = request.form.get("guardar_solucion") == "si"

        nombres_categorias = {
            str(categoria["id"]): categoria["nombre"]
            for categoria in categorias
        }
        nombres_responsables = {
            str(responsable["id"]): responsable["nombre"]
            for responsable in responsables
        }

        if nuevo_estado not in ESTADOS_VALIDOS:
            error = "El estado seleccionado no es válido."
        elif nueva_prioridad not in PRIORIDADES_VALIDAS:
            error = "La prioridad seleccionada no es válida."
        elif nueva_categoria_id not in nombres_categorias:
            error = "La categoría seleccionada no es válida."
        elif responsable_id and responsable_id not in nombres_responsables:
            error = "El responsable seleccionado no es válido."
        elif nuevo_estado in ESTADOS_CERRADOS and nombres_categorias[nueva_categoria_id] == CATEGORIA_POR_CLASIFICAR:
            error = "Antes de cerrar el ticket debes asignarle una categoría."
        else:
            nuevo_responsable_id = int(responsable_id) if responsable_id else None

            if ticket["responsable_id"] != nuevo_responsable_id:
                registrar_cambio(
                    conexion, ticket_id, "responsable",
                    ticket["responsable"] or "Sin asignar",
                    nombres_responsables.get(responsable_id, "Sin asignar")
                )

            if ticket["estado"] != nuevo_estado:
                registrar_cambio(conexion, ticket_id, "estado", ticket["estado"], nuevo_estado)

            # Corrección manual de la clasificación (riesgo R2)
            if ticket["prioridad"] != nueva_prioridad:
                registrar_cambio(conexion, ticket_id, "prioridad", ticket["prioridad"], nueva_prioridad)

            if str(ticket["categoria_id"]) != nueva_categoria_id:
                registrar_cambio(
                    conexion, ticket_id, "categoria",
                    ticket["categoria"], nombres_categorias[nueva_categoria_id]
                )

            # fecha_cierre solo se guarda al cerrar por primera vez
            conexion.execute("""
                UPDATE tickets
                SET responsable_id = ?,
                    estado = ?,
                    prioridad = ?,
                    categoria_id = ?,
                    solucion = ?,
                    fecha_cierre = CASE
                        WHEN ? IN ('Resuelto', 'Cerrado')
                            THEN COALESCE(fecha_cierre, CURRENT_TIMESTAMP)
                        ELSE NULL
                    END,
                    aviso_sla_enviado = CASE WHEN prioridad = ? THEN aviso_sla_enviado ELSE 0 END
                WHERE id = ?
            """, (
                nuevo_responsable_id,
                nuevo_estado,
                nueva_prioridad,
                nueva_categoria_id,
                solucion or None,
                nuevo_estado,
                nueva_prioridad,
                ticket_id
            ))

            if guardar_en_base and solucion and g.usuario["rol"] == "encargado":
                conexion.execute("""
                    INSERT INTO soluciones (organizacion_id, categoria_id, titulo, pasos)
                    VALUES (?, ?, ?, ?)
                """, (organizacion_actual(), nueva_categoria_id, ticket["titulo"], solucion))

            conexion.commit()

            # Aviso al solicitante cuando su ticket se resuelve
            se_cerro_ahora = nuevo_estado in ESTADOS_CERRADOS and ticket["estado"] not in ESTADOS_CERRADOS
            if se_cerro_ahora and ticket["solicitante_email"]:
                enlace = url_for("publico.seguimiento", codigo=ticket["codigo_seguimiento"], _external=True)
                enviar_correo(
                    [ticket["solicitante_email"]],
                    f"Tu solicitud #{ticket_id} fue resuelta",
                    f"Tu solicitud '{ticket['titulo']}' fue resuelta.\n"
                    f"Revisa el detalle y evalúa la atención aquí: {enlace}"
                )

            flash("Ticket actualizado.")
            return redirect(url_for("tickets.detalle", ticket_id=ticket_id))

    cambios = conexion.execute("""
        SELECT *
        FROM cambios_ticket
        WHERE ticket_id = ?
        ORDER BY id DESC
    """, (ticket_id,)).fetchall()

    enlace_seguimiento = url_for("publico.seguimiento", codigo=ticket["codigo_seguimiento"], _external=True)
    whatsapp = enlace_whatsapp(
        ticket["solicitante_telefono"],
        f"Hola {ticket['solicitante']}, tu solicitud #{ticket['id']} está en estado "
        f"'{ticket['estado']}'. Puedes revisarla aquí: {enlace_seguimiento}"
    )

    return render_template(
        "tickets/detalle.html",
        ticket=ticket,
        responsables=responsables,
        categorias=categorias,
        estados=ESTADOS_VALIDOS,
        prioridades=PRIORIDADES_VALIDAS,
        cambios=cambios,
        enlace_seguimiento=enlace_seguimiento,
        whatsapp=whatsapp,
        error=error
    )


@bp.route("/incidencias", methods=["GET", "POST"])
@rol_requerido(*ROLES_ATENCION)
def incidencias():
    """Incidencias por otros medios (K3)."""
    conexion = get_db()
    error = None

    if request.method == "POST":
        canal = request.form.get("canal", "").strip()
        descripcion = request.form.get("descripcion", "").strip()

        if canal not in CANALES_EXTERNOS:
            error = "El canal seleccionado no es válido."
        elif not descripcion:
            error = "Debes escribir una breve descripción."
        else:
            conexion.execute(
                "INSERT INTO incidencias_externas (organizacion_id, canal, descripcion) VALUES (?, ?, ?)",
                (organizacion_actual(), canal, descripcion)
            )
            conexion.commit()
            flash("Incidencia registrada. Recuerda pedir que la próxima vez se use la plataforma.")
            return redirect(url_for("tickets.incidencias"))

    registros = conexion.execute(
        """
        SELECT *
        FROM incidencias_externas
        WHERE organizacion_id = ?
        ORDER BY fecha DESC
        LIMIT 100
        """,
        (organizacion_actual(),)
    ).fetchall()

    return render_template(
        "tickets/incidencias.html",
        registros=registros,
        canales=CANALES_EXTERNOS,
        error=error
    )
