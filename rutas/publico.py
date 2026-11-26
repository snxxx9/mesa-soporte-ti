from flask import Blueprint, Response, abort, flash, g, jsonify, redirect, render_template, request, url_for
import qrcode
import qrcode.image.svg

from db import get_db
from servicios.clasificador import CATEGORIA_POR_CLASIFICAR
from servicios.tickets import PRIORIDADES_VALIDAS, obtener_solicitante, registrar_ticket

bp = Blueprint("publico", __name__)


def obtener_organizacion_o_404(slug):
    organizacion = get_db().execute(
        "SELECT * FROM organizaciones WHERE slug = ?",
        (slug,)
    ).fetchone()

    if organizacion is None:
        abort(404)

    return organizacion


def respuesta_qr(texto):
    imagen = qrcode.make(texto, image_factory=qrcode.image.svg.SvgPathImage)
    return Response(imagen.to_string(), mimetype="image/svg+xml")


@bp.route("/")
def inicio():
    if g.usuario is not None:
        if g.usuario["rol"] == "admin":
            return redirect(url_for("admin.organizaciones"))
        return redirect(url_for("tickets.inicio"))

    return render_template("publico/inicio.html")


@bp.route("/e/<codigo>")
def escanear_equipo(codigo):
    """Destino del QR pegado en cada equipo (enlace corto)."""
    equipo = get_db().execute(
        """
        SELECT e.codigo, o.slug
        FROM equipos e
        JOIN organizaciones o ON e.organizacion_id = o.id
        WHERE e.codigo = ?
        """,
        (codigo,)
    ).fetchone()

    if equipo is None:
        abort(404)

    return redirect(url_for("publico.reportar", slug=equipo["slug"], equipo=equipo["codigo"]))


@bp.route("/qr/equipo/<codigo>.svg")
def qr_equipo(codigo):
    return respuesta_qr(url_for("publico.escanear_equipo", codigo=codigo, _external=True))


@bp.route("/qr/organizacion/<slug>.svg")
def qr_organizacion(slug):
    return respuesta_qr(url_for("publico.reportar", slug=slug, _external=True))


@bp.route("/reportar/<slug>", methods=["GET", "POST"])
def reportar(slug):
    organizacion = obtener_organizacion_o_404(slug)
    conexion = get_db()

    # "Por clasificar" no se muestra al usuario: la asigna el clasificador
    categorias = conexion.execute(
        "SELECT id, nombre FROM categorias WHERE nombre <> ? ORDER BY nombre",
        (CATEGORIA_POR_CLASIFICAR,)
    ).fetchall()

    equipos = conexion.execute(
        """
        SELECT id, codigo, nombre
        FROM equipos
        WHERE organizacion_id = ?
        AND estado <> 'Dado de baja'
        ORDER BY codigo
        """,
        (organizacion["id"],)
    ).fetchall()

    datos = request.form if request.method == "POST" else {}
    equipo_codigo = (datos.get("equipo_codigo") or request.args.get("equipo", "")).strip()
    error = None

    if request.method == "POST":
        solicitante = datos.get("solicitante", "").strip()
        email = datos.get("email", "").strip()
        telefono = datos.get("telefono", "").strip()
        titulo = datos.get("titulo", "").strip()
        descripcion = datos.get("descripcion", "").strip()
        categoria_id = datos.get("categoria_id", "").strip()
        prioridad = datos.get("prioridad", "").strip()

        ids_categorias = [str(categoria["id"]) for categoria in categorias]
        equipos_por_codigo = {equipo["codigo"]: equipo["id"] for equipo in equipos}

        # Si vienen vacías se usa la sugerencia del clasificador
        if not solicitante or not titulo or not descripcion:
            error = "Debes completar tu nombre, el título y la descripción."
        elif prioridad and prioridad not in PRIORIDADES_VALIDAS:
            error = "La prioridad seleccionada no es válida."
        elif categoria_id and categoria_id not in ids_categorias:
            error = "La categoría seleccionada no es válida."
        elif equipo_codigo and equipo_codigo not in equipos_por_codigo:
            error = "El equipo seleccionado no existe."
        elif email and "@" not in email:
            error = "El correo ingresado no es válido."
        else:
            solicitante_id = obtener_solicitante(
                conexion, organizacion["id"], solicitante, email, telefono
            )

            ticket_id, codigo_seguimiento = registrar_ticket(
                conexion,
                organizacion["id"],
                solicitante_id,
                titulo,
                descripcion,
                categoria_id=categoria_id or None,
                prioridad=prioridad or None,
                equipo_id=equipos_por_codigo.get(equipo_codigo),
            )
            conexion.commit()

            flash(f"Tu solicitud #{ticket_id} fue registrada. Guarda este enlace para revisar su estado.")
            return redirect(url_for("publico.seguimiento", codigo=codigo_seguimiento))

    return render_template(
        "publico/reportar.html",
        organizacion=organizacion,
        categorias=categorias,
        equipos=equipos,
        equipo_codigo=equipo_codigo,
        datos=datos,
        error=error
    )


@bp.route("/seguimiento/<codigo>")
def seguimiento(codigo):
    conexion = get_db()

    ticket = conexion.execute(
        """
        SELECT t.*, c.nombre AS categoria, e.codigo AS equipo_codigo, e.nombre AS equipo_nombre
        FROM tickets t
        JOIN categorias c ON t.categoria_id = c.id
        LEFT JOIN equipos e ON t.equipo_id = e.id
        WHERE t.codigo_seguimiento = ?
        """,
        (codigo,)
    ).fetchone()

    if ticket is None:
        abort(404)

    cambios = conexion.execute(
        """
        SELECT fecha_cambio, valor_anterior, valor_nuevo
        FROM cambios_ticket
        WHERE ticket_id = ? AND campo = 'estado'
        ORDER BY id
        """,
        (ticket["id"],)
    ).fetchall()

    return render_template("publico/seguimiento.html", ticket=ticket, cambios=cambios)


@bp.route("/seguimiento/<codigo>/encuesta", methods=["POST"])
def encuesta(codigo):
    """Encuesta de una pregunta al cerrar el ticket (K8 CSAT)."""
    nota = request.form.get("satisfaccion", "").strip()

    if nota in ("1", "2", "3", "4", "5"):
        conexion = get_db()
        conexion.execute(
            """
            UPDATE tickets
            SET satisfaccion = ?
            WHERE codigo_seguimiento = ?
            AND estado IN ('Resuelto', 'Cerrado')
            AND satisfaccion IS NULL
            """,
            (int(nota), codigo)
        )
        conexion.commit()
        flash("¡Gracias por responder la encuesta!")

    return redirect(url_for("publico.seguimiento", codigo=codigo))


@bp.route("/ayuda/<slug>")
def ayuda(slug):
    """Soluciones frecuentes de la organización, antes de reportar."""
    organizacion = obtener_organizacion_o_404(slug)

    soluciones = get_db().execute(
        """
        SELECT s.titulo, s.pasos, c.nombre AS categoria
        FROM soluciones s
        JOIN categorias c ON s.categoria_id = c.id
        WHERE s.organizacion_id = ?
        ORDER BY c.nombre, s.titulo
        """,
        (organizacion["id"],)
    ).fetchall()

    return render_template("publico/ayuda.html", organizacion=organizacion, soluciones=soluciones)


@bp.route("/salud")
def salud():
    """Control para monitor externo (K9)."""
    get_db().execute("SELECT 1").fetchone()
    return jsonify({"estado": "ok"})
