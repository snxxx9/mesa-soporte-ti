from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "soporte.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "database", "schema.sql")


def get_db():
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def init_db():
    conexion = get_db()

    with open(SCHEMA_PATH, "r", encoding="utf-8") as archivo:
        conexion.executescript(archivo.read())

    conexion.commit()
    conexion.close()


@app.route("/")
def inicio():
    conexion = get_db()

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
            t.prioridad,
            t.estado,
            u.nombre AS solicitante,
            c.nombre AS categoria,
            r.nombre AS responsable
        FROM tickets t
        JOIN usuarios u ON t.solicitante_id = u.id
        JOIN categorias c ON t.categoria_id = c.id
        LEFT JOIN usuarios r ON t.responsable_id = r.id
        WHERE 1 = 1
    """

    parametros = []

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

    tickets = conexion.execute(
        consulta,
        parametros
    ).fetchall()

    # Resumen RF-06
    resumen = conexion.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN estado = 'Nuevo' THEN 1 ELSE 0 END) AS nuevos,
            SUM(CASE WHEN estado = 'En proceso' THEN 1 ELSE 0 END) AS en_proceso,
            SUM(CASE WHEN estado = 'Resuelto' THEN 1 ELSE 0 END) AS resueltos,
            SUM(CASE WHEN estado = 'Cerrado' THEN 1 ELSE 0 END) AS cerrados
        FROM tickets
    """).fetchone()

    conexion.close()

    return render_template(
        "index.html",
        tickets=tickets,
        categorias=categorias,
        filtro_estado=estado,
        filtro_prioridad=prioridad,
        filtro_categoria=categoria_id,
        resumen=resumen
    )


@app.route("/nuevo", methods=["GET", "POST"])
def nuevo_ticket():
    conexion = get_db()

    categorias = conexion.execute(
        "SELECT id, nombre FROM categorias ORDER BY nombre"
    ).fetchall()

    error = None

    if request.method == "POST":
        solicitante = request.form.get("solicitante", "").strip()
        titulo = request.form.get("titulo", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        categoria_id = request.form.get("categoria_id", "").strip()
        prioridad = request.form.get("prioridad", "").strip()

        if (
            not solicitante
            or not titulo
            or not descripcion
            or not categoria_id
            or not prioridad
        ):
            error = "Debes completar todos los campos."

        elif prioridad not in ("Baja", "Media", "Alta"):
            error = "La prioridad seleccionada no es válida."

        else:
            usuario = conexion.execute(
                """
                SELECT id
                FROM usuarios
                WHERE LOWER(nombre) = LOWER(?)
                AND puede_atender = 0
                LIMIT 1
                """,
                (solicitante,)
            ).fetchone()

            if usuario:
                solicitante_id = usuario["id"]

            else:
                cursor_usuario = conexion.execute(
                    """
                    INSERT INTO usuarios (nombre, puede_atender)
                    VALUES (?, 0)
                    """,
                    (solicitante,)
                )

                solicitante_id = cursor_usuario.lastrowid

            conexion.execute(
                """
                INSERT INTO tickets (
                    titulo,
                    descripcion,
                    prioridad,
                    solicitante_id,
                    categoria_id
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    titulo,
                    descripcion,
                    prioridad,
                    solicitante_id,
                    categoria_id
                )
            )

            conexion.commit()
            conexion.close()

            return redirect(url_for("inicio"))

    conexion.close()

    return render_template(
        "nuevo_ticket.html",
        categorias=categorias,
        error=error
    )


@app.route("/ticket/<int:ticket_id>", methods=["GET", "POST"])
def detalle_ticket(ticket_id):
    conexion = get_db()

    ticket = conexion.execute("""
        SELECT
            t.*,
            u.nombre AS solicitante,
            c.nombre AS categoria,
            r.nombre AS responsable
        FROM tickets t
        JOIN usuarios u ON t.solicitante_id = u.id
        JOIN categorias c ON t.categoria_id = c.id
        LEFT JOIN usuarios r ON t.responsable_id = r.id
        WHERE t.id = ?
    """, (ticket_id,)).fetchone()

    if ticket is None:
        conexion.close()
        return "Ticket no encontrado", 404

    responsables = conexion.execute("""
        SELECT id, nombre
        FROM usuarios
        WHERE puede_atender = 1
        ORDER BY nombre
    """).fetchall()

    error = None

    if request.method == "POST":
        responsable_id = request.form.get("responsable_id", "").strip()
        nuevo_estado = request.form.get("estado", "").strip()

        estados_validos = (
            "Nuevo",
            "En proceso",
            "Resuelto",
            "Cerrado"
        )

        if nuevo_estado not in estados_validos:
            error = "El estado seleccionado no es válido."

        else:
            nuevo_responsable_id = None

            if responsable_id:
                responsable = conexion.execute("""
                    SELECT id, nombre
                    FROM usuarios
                    WHERE id = ?
                    AND puede_atender = 1
                """, (responsable_id,)).fetchone()

                if responsable is None:
                    error = "El responsable seleccionado no es válido."
                else:
                    nuevo_responsable_id = responsable["id"]

            if error is None:
                if ticket["responsable_id"] != nuevo_responsable_id:
                    responsable_anterior = (
                        ticket["responsable"] or "Sin asignar"
                    )

                    if nuevo_responsable_id:
                        responsable_nuevo = conexion.execute(
                            """
                            SELECT nombre
                            FROM usuarios
                            WHERE id = ?
                            """,
                            (nuevo_responsable_id,)
                        ).fetchone()["nombre"]
                    else:
                        responsable_nuevo = "Sin asignar"

                    conexion.execute("""
                        INSERT INTO cambios_ticket (
                            ticket_id,
                            campo,
                            valor_anterior,
                            valor_nuevo
                        )
                        VALUES (?, 'responsable', ?, ?)
                    """, (
                        ticket_id,
                        responsable_anterior,
                        responsable_nuevo
                    ))

                if ticket["estado"] != nuevo_estado:
                    conexion.execute("""
                        INSERT INTO cambios_ticket (
                            ticket_id,
                            campo,
                            valor_anterior,
                            valor_nuevo
                        )
                        VALUES (?, 'estado', ?, ?)
                    """, (
                        ticket_id,
                        ticket["estado"],
                        nuevo_estado
                    ))

                conexion.execute("""
                    UPDATE tickets
                    SET responsable_id = ?, estado = ?
                    WHERE id = ?
                """, (
                    nuevo_responsable_id,
                    nuevo_estado,
                    ticket_id
                ))

                conexion.commit()
                conexion.close()

                return redirect(
                    url_for(
                        "detalle_ticket",
                        ticket_id=ticket_id
                    )
                )

    conexion.close()

    return render_template(
        "detalle_ticket.html",
        ticket=ticket,
        responsables=responsables,
        error=error
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)