from servicios.notificaciones import avisar_encargados

FALLAS_PARA_ALERTA = 3
DIAS_VENTANA = 60
DIAS_PLAZO_REVISION = 7


def revisar_alerta_equipo(conexion, equipo_id):
    """Crea una alerta si se cumple la regla."""
    fallas = conexion.execute(
        """
        SELECT COUNT(*) AS cantidad
        FROM tickets
        WHERE equipo_id = ?
        AND fecha_creacion >= datetime('now', ?)
        """,
        (equipo_id, f"-{DIAS_VENTANA} days")
    ).fetchone()["cantidad"]

    if fallas < FALLAS_PARA_ALERTA:
        return False

    alerta_pendiente = conexion.execute(
        """
        SELECT id
        FROM alertas
        WHERE equipo_id = ?
        AND estado = 'Pendiente'
        """,
        (equipo_id,)
    ).fetchone()

    if alerta_pendiente:
        return False

    equipo = conexion.execute(
        "SELECT organizacion_id, codigo, nombre FROM equipos WHERE id = ?",
        (equipo_id,)
    ).fetchone()

    motivo = (
        f"{fallas} fallas en los últimos {DIAS_VENTANA} días. "
        "Se recomienda una revisión preventiva."
    )

    conexion.execute(
        """
        INSERT INTO alertas (equipo_id, motivo, fecha_limite)
        VALUES (?, ?, datetime('now', ?))
        """,
        (equipo_id, motivo, f"+{DIAS_PLAZO_REVISION} days")
    )

    avisar_encargados(
        conexion,
        equipo["organizacion_id"],
        f"Alerta preventiva: {equipo['codigo']} - {equipo['nombre']}",
        f"{motivo} Plazo máximo de revisión: {DIAS_PLAZO_REVISION} días."
    )

    return True
