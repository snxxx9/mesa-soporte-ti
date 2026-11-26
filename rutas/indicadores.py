"""
Cuadro de mando de la organización y reporte mensual para la dirección.
"""

from datetime import date

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from db import get_db
from seguridad import organizacion_actual, rol_requerido
from servicios.indicadores import DEFINICIONES, KPI_SISTEMA, cuadro_de_mando, semaforo, valores_sistema
from servicios.notificaciones import enviar_correo

bp = Blueprint("indicadores", __name__)

# 3 semanas del piloto + la semana actual
SEMANAS_EN_PANEL = 4


@bp.route("/indicadores")
@rol_requerido("encargado")
def panel():
    cuadro = cuadro_de_mando(get_db(), organizacion_actual(), semanas=SEMANAS_EN_PANEL)
    return render_template("indicadores/panel.html", cuadro=cuadro)


def rango_del_mes(texto_mes):
    """Recibe 'AAAA-MM' y devuelve (desde, hasta) como textos AAAA-MM-DD."""
    anio, mes = (int(parte) for parte in texto_mes.split("-"))
    desde = date(anio, mes, 1)
    hasta = date(anio + 1, 1, 1) if mes == 12 else date(anio, mes + 1, 1)
    return desde.isoformat(), hasta.isoformat()


def datos_reporte_mensual(conexion, organizacion_id, texto_mes):
    desde, hasta = rango_del_mes(texto_mes)

    valores = valores_sistema(conexion, organizacion_id, desde, hasta)
    kpis = []
    for codigo in KPI_SISTEMA:
        nombre, _, unidad, meta, mayor_es_mejor = DEFINICIONES[codigo]
        kpis.append({
            "codigo": codigo,
            "nombre": nombre,
            "valor": valores[codigo],
            "unidad": unidad,
            "estado": semaforo(valores[codigo], meta, mayor_es_mejor),
        })

    totales = conexion.execute("""
        SELECT
            COUNT(*) AS registrados,
            SUM(CASE WHEN estado IN ('Resuelto', 'Cerrado') THEN 1 ELSE 0 END) AS resueltos
        FROM tickets
        WHERE organizacion_id = ? AND fecha_creacion >= ? AND fecha_creacion < ?
    """, (organizacion_id, desde, hasta)).fetchone()

    equipos_con_mas_fallas = conexion.execute("""
        SELECT e.codigo, e.nombre, COUNT(*) AS fallas
        FROM tickets t
        JOIN equipos e ON t.equipo_id = e.id
        WHERE t.organizacion_id = ? AND t.fecha_creacion >= ? AND t.fecha_creacion < ?
        GROUP BY e.id
        ORDER BY fallas DESC
        LIMIT 5
    """, (organizacion_id, desde, hasta)).fetchall()

    # Reconocimiento al área (ubicación) con más reportes resueltos (ADKAR: Refuerzo)
    area_destacada = conexion.execute("""
        SELECT e.ubicacion, COUNT(*) AS resueltos
        FROM tickets t
        JOIN equipos e ON t.equipo_id = e.id
        WHERE t.organizacion_id = ? AND t.fecha_creacion >= ? AND t.fecha_creacion < ?
        AND t.estado IN ('Resuelto', 'Cerrado')
        AND e.ubicacion IS NOT NULL
        GROUP BY e.ubicacion
        ORDER BY resueltos DESC
        LIMIT 1
    """, (organizacion_id, desde, hasta)).fetchone()

    return {
        "mes": texto_mes,
        "kpis": kpis,
        "totales": totales,
        "equipos_con_mas_fallas": equipos_con_mas_fallas,
        "area_destacada": area_destacada,
    }


def reporte_como_texto(reporte, organizacion):
    lineas = [
        f"Reporte mensual SoporTI - {organizacion} - {reporte['mes']}",
        "",
        f"Tickets registrados: {reporte['totales']['registrados']}",
        f"Tickets resueltos: {reporte['totales']['resueltos'] or 0}",
        "",
        "Indicadores:",
    ]

    for kpi in reporte["kpis"]:
        valor = "sin datos" if kpi["valor"] is None else f"{kpi['valor']} {kpi['unidad']}"
        lineas.append(f"  {kpi['codigo']} {kpi['nombre']}: {valor} ({kpi['estado']})")

    if reporte["area_destacada"]:
        lineas.append("")
        lineas.append(
            f"Área destacada: {reporte['area_destacada']['ubicacion']} "
            f"con {reporte['area_destacada']['resueltos']} reportes resueltos."
        )

    return "\n".join(lineas)


@bp.route("/reporte-mensual", methods=["GET", "POST"])
@rol_requerido("encargado")
def reporte_mensual():
    texto_mes = request.values.get("mes") or date.today().strftime("%Y-%m")

    try:
        reporte = datos_reporte_mensual(get_db(), organizacion_actual(), texto_mes)
    except ValueError:
        flash("El mes indicado no es válido.")
        return redirect(url_for("indicadores.reporte_mensual"))

    if request.method == "POST":
        destinatarios = [
            correo.strip()
            for correo in request.form.get("destinatarios", "").split(",")
            if "@" in correo
        ]

        enviado = enviar_correo(
            destinatarios,
            f"Reporte mensual SoporTI {texto_mes}",
            reporte_como_texto(reporte, g.usuario["organizacion"])
        )

        if enviado:
            flash("Reporte enviado por correo.")
        else:
            flash("No se pudo enviar el correo (revisa los destinatarios o la configuración SMTP).")

        return redirect(url_for("indicadores.reporte_mensual", mes=texto_mes))

    return render_template("indicadores/reporte_mensual.html", reporte=reporte)
