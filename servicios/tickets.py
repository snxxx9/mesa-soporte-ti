"""
Lógica para registrar tickets, compartida por el formulario público.
"""

import secrets

from servicios.alertas import revisar_alerta_equipo
from servicios.clasificador import clasificar_ticket

ESTADOS_VALIDOS = ("Nuevo", "En proceso", "Resuelto", "Cerrado")
ESTADOS_CERRADOS = ("Resuelto", "Cerrado")
PRIORIDADES_VALIDAS = ("Baja", "Media", "Alta")

# Cuántos tickets cerrados se usan como ejemplos para el clasificador
EJEMPLOS_APRENDIDOS_MAXIMOS = 300


def buscar_categoria_id(conexion, nombre):
    categoria = conexion.execute(
        "SELECT id FROM categorias WHERE nombre = ?",
        (nombre,)
    ).fetchone()

    return categoria["id"] if categoria else None


def ejemplos_aprendidos(conexion, organizacion_id):
    """
    Tickets cerrados de la organización con su categoría final.
    Incluyen las correcciones del encargado, por eso ayudan a que el
    clasificador mejore con el uso.
    """
    filas = conexion.execute(
        """
        SELECT t.titulo || ' ' || t.descripcion AS texto, c.nombre AS categoria
        FROM tickets t
        JOIN categorias c ON t.categoria_id = c.id
        WHERE t.organizacion_id = ?
        AND t.estado IN ('Resuelto', 'Cerrado')
        ORDER BY t.id DESC
        LIMIT ?
        """,
        (organizacion_id, EJEMPLOS_APRENDIDOS_MAXIMOS)
    ).fetchall()

    return [(fila["texto"], fila["categoria"]) for fila in filas]


def obtener_solicitante(conexion, organizacion_id, nombre, email, telefono):
    """Busca al solicitante por nombre dentro de la organización o lo crea."""
    usuario = conexion.execute(
        """
        SELECT id
        FROM usuarios
        WHERE organizacion_id = ?
        AND LOWER(nombre) = LOWER(?)
        AND rol = 'solicitante'
        LIMIT 1
        """,
        (organizacion_id, nombre)
    ).fetchone()

    if usuario is None:
        cursor = conexion.execute(
            """
            INSERT INTO usuarios (organizacion_id, nombre, rol, email, telefono)
            VALUES (?, ?, 'solicitante', ?, ?)
            """,
            (organizacion_id, nombre, email or None, telefono or None)
        )
        return cursor.lastrowid

    # Si deja un contacto nuevo, se actualiza (solo se guarda lo necesario)
    if email or telefono:
        conexion.execute(
            """
            UPDATE usuarios
            SET email = COALESCE(?, email), telefono = COALESCE(?, telefono)
            WHERE id = ?
            """,
            (email or None, telefono or None, usuario["id"])
        )

    return usuario["id"]


def registrar_ticket(conexion, organizacion_id, solicitante_id, titulo, descripcion,
                     categoria_id=None, prioridad=None, equipo_id=None):
    """
    Guarda un ticket nuevo. Si no se indica categoría o prioridad, se usa
    la sugerencia del clasificador. Devuelve (id, codigo_seguimiento).
    """
    sugerencia = clasificar_ticket(
        titulo,
        descripcion,
        ejemplos_aprendidos(conexion, organizacion_id)
    )
    categoria_sugerida_id = buscar_categoria_id(conexion, sugerencia["categoria"])

    codigo_seguimiento = secrets.token_urlsafe(8)

    cursor = conexion.execute(
        """
        INSERT INTO tickets (
            organizacion_id,
            codigo_seguimiento,
            titulo,
            descripcion,
            prioridad,
            solicitante_id,
            categoria_id,
            equipo_id,
            categoria_sugerida_id,
            prioridad_sugerida,
            confianza_ia
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            organizacion_id,
            codigo_seguimiento,
            titulo,
            descripcion,
            prioridad or sugerencia["prioridad"],
            solicitante_id,
            categoria_id or categoria_sugerida_id,
            equipo_id,
            categoria_sugerida_id,
            sugerencia["prioridad"],
            sugerencia["confianza"],
        )
    )

    if equipo_id:
        revisar_alerta_equipo(conexion, equipo_id)

    return cursor.lastrowid, codigo_seguimiento
