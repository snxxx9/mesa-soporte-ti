"""
Mantenimiento predictivo con el historial de cada equipo.

Se calcula un puntaje de riesgo simple y explicable:
  - 2 puntos por cada falla en los últimos DIAS_HISTORIAL días
  - 1 punto si el equipo tiene 3 o más años, 2 puntos si tiene 5 o más
  - 2 puntos si tiene una alerta preventiva pendiente

Con el puntaje se define el nivel de riesgo y una recomendación.
"""

from datetime import date

DIAS_HISTORIAL = 90

PUNTOS_RIESGO_ALTO = 6
PUNTOS_RIESGO_MEDIO = 3


def anios_de_uso(fecha_compra, hoy=None):
    if not fecha_compra:
        return None

    hoy = hoy or date.today()
    compra = date.fromisoformat(fecha_compra[:10])
    return (hoy - compra).days // 365


def calcular_riesgo(fallas_recientes, anios, alerta_pendiente):
    puntos = fallas_recientes * 2

    if anios is not None and anios >= 5:
        puntos += 2
    elif anios is not None and anios >= 3:
        puntos += 1

    if alerta_pendiente:
        puntos += 2

    if puntos >= PUNTOS_RIESGO_ALTO:
        return {"nivel": "Alto", "puntos": puntos,
                "recomendacion": "Programar mantención esta semana y evaluar reparación o reemplazo."}

    if puntos >= PUNTOS_RIESGO_MEDIO:
        return {"nivel": "Medio", "puntos": puntos,
                "recomendacion": "Incluir en la próxima mantención preventiva."}

    return {"nivel": "Bajo", "puntos": puntos, "recomendacion": "Sin acciones por ahora."}


def riesgo_de_equipos(conexion, organizacion_id):
    """Devuelve un diccionario {equipo_id: riesgo} de los equipos activos."""
    filas = conexion.execute(
        """
        SELECT
            e.id,
            e.fecha_compra,
            (
                SELECT COUNT(*) FROM tickets t
                WHERE t.equipo_id = e.id
                AND t.fecha_creacion >= datetime('now', ?)
            ) AS fallas_recientes,
            (
                SELECT COUNT(*) FROM alertas a
                WHERE a.equipo_id = e.id AND a.estado = 'Pendiente'
            ) AS alertas_pendientes
        FROM equipos e
        WHERE e.organizacion_id = ?
        AND e.estado <> 'Dado de baja'
        """,
        (f"-{DIAS_HISTORIAL} days", organizacion_id)
    ).fetchall()

    return {
        fila["id"]: calcular_riesgo(
            fila["fallas_recientes"],
            anios_de_uso(fila["fecha_compra"]),
            fila["alertas_pendientes"] > 0
        )
        for fila in filas
    }
