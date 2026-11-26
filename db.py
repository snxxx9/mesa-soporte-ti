"""
Conexión a la base de datos SQLite.

Se abre una conexión por petición (se guarda en flask.g) y se cierra
automáticamente al terminar la petición con close_db().
"""

import os
import sqlite3

from flask import g
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("SOPORTI_DB", os.path.join(BASE_DIR, "database", "soporte.db"))
SCHEMA_PATH = os.path.join(BASE_DIR, "database", "schema.sql")


def conectar():
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def get_db():
    """Devuelve la conexión de la petición actual (la crea si no existe)."""
    if "db" not in g:
        g.db = conectar()
    return g.db


def close_db(error=None):
    conexion = g.pop("db", None)
    if conexion is not None:
        conexion.close()


def init_db():
    """Crea las tablas y una cuenta de administrador si todavía no existe."""
    conexion = conectar()

    with open(SCHEMA_PATH, "r", encoding="utf-8") as archivo:
        conexion.executescript(archivo.read())

    existe_admin = conexion.execute(
        "SELECT id FROM usuarios WHERE rol = 'admin'"
    ).fetchone()

    if existe_admin is None:
        usuario = os.environ.get("ADMIN_USUARIO", "admin")
        clave = os.environ.get("ADMIN_CLAVE", "admin123")

        conexion.execute(
            """
            INSERT INTO usuarios (nombre, rol, usuario, clave_hash)
            VALUES ('Administrador SoporTI', 'admin', ?, ?)
            """,
            (usuario, generate_password_hash(clave))
        )

        print(f"Se creó la cuenta de administrador '{usuario}'. Cambia su clave al ingresar.")

    conexion.commit()
    conexion.close()
