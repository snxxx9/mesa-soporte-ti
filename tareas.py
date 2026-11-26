"""
Script de tareas periódicas de SoporTI.

Uso:
    python tareas.py avisos     -> avisos de SLA y de alertas vencidas
    python tareas.py respaldo   -> copia de seguridad de la base de datos
    python tareas.py todo       -> ambas cosas
"""

import os
import sys

from db import BASE_DIR, DB_PATH, conectar, init_db
from servicios.tareas import avisar_alertas_vencidas, enviar_avisos_sla, respaldar_base_de_datos

CARPETA_RESPALDOS = os.path.join(BASE_DIR, "respaldos")


def ejecutar_avisos():
    conexion = conectar()
    tickets = enviar_avisos_sla(conexion)
    alertas = avisar_alertas_vencidas(conexion)
    conexion.close()
    print(f"Avisos de plazo enviados: {tickets}. Alertas vencidas avisadas: {alertas}.")


def ejecutar_respaldo():
    ruta = respaldar_base_de_datos(DB_PATH, CARPETA_RESPALDOS)
    print(f"Respaldo creado en: {ruta}")


if __name__ == "__main__":
    accion = sys.argv[1] if len(sys.argv) > 1 else "todo"

    init_db()

    if accion in ("avisos", "todo"):
        ejecutar_avisos()

    if accion in ("respaldo", "todo"):
        ejecutar_respaldo()

    if accion not in ("avisos", "respaldo", "todo"):
        print(__doc__)
