import os
import sqlite3
from datetime import datetime

from servicios.notificaciones import avisar_encargados
from servicios.sla import calcular_sla

# Cantidad de respaldos que se conservan (los más antiguos se borran)
RESPALDOS_A_CONSERVAR = 14


def enviar_avisos_sla(conexion):
    tickets = conexion.execute("""
        SELECT id, organizacion_id, titulo, prioridad, estado,
               fecha_creacion, fecha_cierre
        FROM tickets
        WHERE estado IN ('Nuevo', 'En proceso')
        AND aviso_sla_enviado = 0
    """).fetchall()

    avisos = 0

    for ticket in tickets:
        sla = calcular_sla(ticket)

        if sla["estado"] in ("Por vencer", "Vencido"):
            avisar_encargados(
                conexion,
                ticket["organizacion_id"],
                f"Ticket #{ticket['id']} {sla['estado'].lower()}",
                f"El ticket '{ticket['titulo']}' (prioridad {ticket['prioridad']}) "
                f"tiene plazo hasta {sla['fecha_limite']} UTC."
            )

            conexion.execute(
                "UPDATE tickets SET aviso_sla_enviado = 1 WHERE id = ?",
                (ticket["id"],)
            )
            avisos += 1

    conexion.commit()
    return avisos


def avisar_alertas_vencidas(conexion):
    alertas = conexion.execute("""
        SELECT a.id, e.organizacion_id, e.codigo, e.nombre
        FROM alertas a
        JOIN equipos e ON a.equipo_id = e.id
        WHERE a.estado = 'Pendiente'
        AND a.fecha_limite < CURRENT_TIMESTAMP
        AND a.aviso_vencida_enviado = 0
    """).fetchall()

    for alerta in alertas:
        avisar_encargados(
            conexion,
            alerta["organizacion_id"],
            f"Alerta preventiva vencida: {alerta['codigo']}",
            f"La alerta del equipo {alerta['nombre']} superó el plazo de revisión."
        )

        conexion.execute(
            "UPDATE alertas SET aviso_vencida_enviado = 1 WHERE id = ?",
            (alerta["id"],)
        )

    conexion.commit()
    return len(alertas)


def respaldar_base_de_datos(ruta_bd, carpeta_respaldos):
    os.makedirs(carpeta_respaldos, exist_ok=True)

    nombre = f"soporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    ruta_respaldo = os.path.join(carpeta_respaldos, nombre)

    origen = sqlite3.connect(ruta_bd)
    destino = sqlite3.connect(ruta_respaldo)
    origen.backup(destino)
    destino.close()
    origen.close()

    # Se conservan solo los respaldos más recientes
    respaldos = sorted(
        archivo for archivo in os.listdir(carpeta_respaldos)
        if archivo.startswith("soporte_") and archivo.endswith(".db")
    )
    for archivo in respaldos[:-RESPALDOS_A_CONSERVAR]:
        os.remove(os.path.join(carpeta_respaldos, archivo))

    return ruta_respaldo
