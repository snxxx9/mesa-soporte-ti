from datetime import date, timedelta

MARGEN_AMARILLO = 0.10

DEFINICIONES = {
    "K1": ("Avance del plan", "Tareas terminadas ÷ tareas planificadas × 100", "%", 90, True),
    "K2": ("Desviación presupuestaria", "(Costo real − costo presupuestado) ÷ costo presupuestado × 100", "%", 10, False),
    "K3": ("Adopción", "Tickets en plataforma ÷ total de incidencias reportadas × 100", "%", 80, True),
    "K4": ("Tasa de resolución", "Tickets resueltos ÷ tickets registrados × 100", "%", 90, True),
    "K5": ("Tiempo promedio de resolución (TPR)", "Σ (fecha cierre − fecha apertura) ÷ N° tickets cerrados", "h", 24, False),
    "K6": ("Precisión de la IA", "Sugerencias aceptadas sin cambio ÷ total de sugerencias × 100", "%", 75, True),
    "K7": ("Alertas preventivas atendidas", "Alertas con revisión realizada ÷ alertas generadas × 100", "%", 70, True),
    "K8": ("Satisfacción (CSAT)", "Respuestas con nota 4 o 5 ÷ total de respuestas × 100", "%", 80, True),
    "K9": ("Disponibilidad", "Horas en línea ÷ horas totales × 100", "%", 99, True),
}

KPI_SISTEMA = ("K3", "K4", "K5", "K6", "K7", "K8")
KPI_PROYECTO = ("K1", "K2", "K9")


def porcentaje(parte, total):
    if not total:
        return None
    return round((parte or 0) * 100 / total, 1)


def semaforo(valor, meta, mayor_es_mejor=True):
    """Devuelve 'verde', 'amarillo', 'rojo' o 'sin-datos'."""
    if valor is None:
        return "sin-datos"

    if mayor_es_mejor:
        if valor >= meta:
            return "verde"
        if valor >= meta * (1 - MARGEN_AMARILLO):
            return "amarillo"
    else:
        if valor <= meta:
            return "verde"
        if valor <= meta * (1 + MARGEN_AMARILLO):
            return "amarillo"

    return "rojo"


def ultimas_semanas(cantidad, hoy=None):
    """
    Devuelve una lista de periodos (nombre, desde, hasta) de lunes a lunes,
    desde la semana más antigua hasta la actual.
    """
    hoy = hoy or date.today()
    lunes_actual = hoy - timedelta(days=hoy.weekday())

    periodos = []
    for numero in range(cantidad - 1, -1, -1):
        desde = lunes_actual - timedelta(weeks=numero)
        hasta = desde + timedelta(weeks=1)
        periodos.append((f"Semana {desde.strftime('%d/%m')}", desde.isoformat(), hasta.isoformat()))

    return periodos


def filtro_sql(columna_fecha, columna_org, organizacion_id, desde, hasta):
    """Arma la parte WHERE de una consulta según organización y fechas."""
    condiciones = ["1 = 1"]
    parametros = []

    if organizacion_id is not None:
        condiciones.append(f"{columna_org} = ?")
        parametros.append(organizacion_id)

    if desde:
        condiciones.append(f"{columna_fecha} >= ?")
        parametros.append(desde)

    if hasta:
        condiciones.append(f"{columna_fecha} < ?")
        parametros.append(hasta)

    return " AND ".join(condiciones), parametros


def valores_sistema(conexion, organizacion_id=None, desde=None, hasta=None):
    """Calcula K3 a K8 para una organización (o todas) en un periodo."""
    where, parametros = filtro_sql(
        "fecha_creacion", "organizacion_id", organizacion_id, desde, hasta
    )

    tickets = conexion.execute(f"""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN estado IN ('Resuelto', 'Cerrado') THEN 1 ELSE 0 END) AS resueltos,
            AVG(
                CASE WHEN fecha_cierre IS NOT NULL
                THEN (julianday(fecha_cierre) - julianday(fecha_creacion)) * 24
                END
            ) AS horas_promedio,
            SUM(CASE WHEN categoria_sugerida_id IS NOT NULL THEN 1 ELSE 0 END) AS sugerencias,
            SUM(
                CASE WHEN categoria_id = categoria_sugerida_id
                AND prioridad = prioridad_sugerida
                THEN 1 ELSE 0 END
            ) AS sugerencias_aceptadas,
            SUM(CASE WHEN satisfaccion IS NOT NULL THEN 1 ELSE 0 END) AS encuestas,
            SUM(CASE WHEN satisfaccion >= 4 THEN 1 ELSE 0 END) AS encuestas_positivas
        FROM tickets
        WHERE {where}
    """, parametros).fetchone()

    where, parametros = filtro_sql(
        "fecha", "organizacion_id", organizacion_id, desde, hasta
    )
    externas = conexion.execute(
        f"SELECT COUNT(*) FROM incidencias_externas WHERE {where}", parametros
    ).fetchone()[0]

    where, parametros = filtro_sql(
        "a.fecha_creacion", "e.organizacion_id", organizacion_id, desde, hasta
    )
    alertas = conexion.execute(f"""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN a.estado = 'Revisada' THEN 1 ELSE 0 END) AS revisadas
        FROM alertas a
        JOIN equipos e ON a.equipo_id = e.id
        WHERE {where}
    """, parametros).fetchone()

    horas_promedio = tickets["horas_promedio"]
    if horas_promedio is not None:
        horas_promedio = round(horas_promedio, 1)

    return {
        "K3": porcentaje(tickets["total"], tickets["total"] + externas),
        "K4": porcentaje(tickets["resueltos"], tickets["total"]),
        "K5": horas_promedio,
        "K6": porcentaje(tickets["sugerencias_aceptadas"], tickets["sugerencias"]),
        "K7": porcentaje(alertas["revisadas"], alertas["total"]),
        "K8": porcentaje(tickets["encuestas_positivas"], tickets["encuestas"]),
    }


def valores_proyecto(conexion, desde=None, hasta=None):
    """Calcula K1, K2 y K9 con las mediciones semanales del proyecto."""
    where, parametros = filtro_sql("semana_inicio", None, None, desde, hasta)

    fila = conexion.execute(f"""
        SELECT
            SUM(tareas_planificadas) AS planificadas,
            SUM(tareas_terminadas) AS terminadas,
            SUM(costo_presupuestado) AS presupuestado,
            SUM(costo_real) AS real,
            SUM(horas_totales) AS horas_totales,
            SUM(horas_en_linea) AS horas_en_linea
        FROM mediciones_semanales
        WHERE {where}
    """, parametros).fetchone()

    desviacion = None
    if fila["presupuestado"]:
        desviacion = porcentaje(fila["real"] - fila["presupuestado"], fila["presupuestado"])

    return {
        "K1": porcentaje(fila["terminadas"], fila["planificadas"]),
        "K2": desviacion,
        "K9": porcentaje(fila["horas_en_linea"], fila["horas_totales"]),
    }


def cuadro_de_mando(conexion, organizacion_id=None, incluir_proyecto=False, semanas=4):
    """
    Arma las filas del cuadro de mando con el valor de cada semana y el
    total. Si organizacion_id es None se consideran todas las organizaciones.
    """
    periodos = ultimas_semanas(semanas)

    def valores(desde, hasta):
        resultado = valores_sistema(conexion, organizacion_id, desde, hasta)
        if incluir_proyecto:
            resultado.update(valores_proyecto(conexion, desde, hasta))
        return resultado

    por_semana = [valores(desde, hasta) for _, desde, hasta in periodos]
    total = valores(None, None)

    codigos = sorted(total.keys())
    filas = []

    for codigo in codigos:
        nombre, formula, unidad, meta, mayor_es_mejor = DEFINICIONES[codigo]
        simbolo = "≥" if mayor_es_mejor else "≤"

        filas.append({
            "codigo": codigo,
            "nombre": nombre,
            "formula": formula,
            "unidad": unidad,
            "meta": f"{simbolo} {meta} {unidad}",
            "semanas": [
                {"valor": semana[codigo], "estado": semaforo(semana[codigo], meta, mayor_es_mejor)}
                for semana in por_semana
            ],
            "valor": total[codigo],
            "estado": semaforo(total[codigo], meta, mayor_es_mejor),
        })

    return {
        "periodos": [nombre for nombre, _, _ in periodos],
        "filas": filas,
    }
