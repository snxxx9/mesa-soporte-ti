"""
Carga datos de ejemplo que simulan el piloto descrito en el informe.

Organización ficticia: un colegio pequeño con 25 equipos (cada uno con su
QR) y 30 usuarios, con tickets durante las tres semanas anteriores a la
actual (S7, S8 y S9 de la Carta Gantt). Los datos están armados para que
el cuadro de mando muestre resultados parecidos a los del informe:
K3 84,5 %, K4 91,7 %, K5 ≈ 26 h, K6 70 %, K7 66,7 %, K8 86,8 %,
K1 93 %, K2 +9,5 % y K9 99,6 %.

También se crea una segunda organización (una pyme) para mostrar que
cada organización ve solo sus propios datos.

ATENCIÓN: este script BORRA la base de datos actual.

Uso:
    python datos_demo.py
"""

import os
import random
import secrets
from datetime import timedelta

from werkzeug.security import generate_password_hash

from db import DB_PATH, conectar, init_db
from servicios.clasificador import EJEMPLOS_PILOTO
from servicios.indicadores import ultimas_semanas
from servicios.sla import FORMATO_FECHA, ahora_utc, texto_a_fecha

# Semilla fija: siempre se generan los mismos datos
random.seed(2026)

AHORA = ahora_utc()

# ---------------------------------------------------------------------
# Plan del piloto (valores tomados del reporte de validación del informe)
# ---------------------------------------------------------------------

PLAN_SEMANAS = {
    "S7": {"tickets": 24, "resueltos": 21, "horas_promedio": 31, "ia_aceptadas": 15,
           "encuestas": 12, "encuestas_positivas": 10, "externas": 7},
    "S8": {"tickets": 20, "resueltos": 19, "horas_promedio": 26, "ia_aceptadas": 14,
           "encuestas": 15, "encuestas_positivas": 13, "externas": 3},
    "S9": {"tickets": 16, "resueltos": 15, "horas_promedio": 19, "ia_aceptadas": 13,
           "encuestas": 11, "encuestas_positivas": 10, "externas": 1},
}

# Equipos que acumulan 3 fallas y generan una alerta preventiva:
# (índice del equipo, semanas de sus 3 tickets, ¿la alerta fue revisada?)
EQUIPOS_CON_ALERTA = [
    (0, ("S7", "S7", "S8"), True),
    (1, ("S7", "S8", "S8"), False),
    (2, ("S7", "S8", "S9"), True),
    (3, ("S8", "S9", "S9"), True),
    (4, ("S7", "S9", "S9"), True),
    (5, ("S8", "S8", "S9"), False),
]

# Mediciones semanales del proyecto: K1 (tareas), K2 (costos), K9 (horas)
MEDICIONES = {
    "S7": (10, 9, 40000, 43000, 168, 168),
    "S8": (10, 10, 40000, 45400, 168, 166),
    "S9": (10, 9, 40000, 43000, 168, 168),
}

EQUIPOS_COLEGIO = [
    # (nombre, tipo, ubicación, marca, año de compra)
    ("Notebook Dirección", "Notebook", "Dirección", "Lenovo", 2018),
    ("Impresora Secretaría", "Impresora", "Secretaría", "HP", 2016),
    ("Computador Sala de Profesores 1", "Computador", "Sala de profesores", "Dell", 2017),
    ("Proyector Sala 3", "Proyector", "Sala 3", "Epson", 2019),
    ("Router Pabellón A", "Red", "Pabellón A", "TP-Link", 2020),
    ("Computador Biblioteca 1", "Computador", "Biblioteca", "HP", 2018),
    ("Computador Sala de Profesores 2", "Computador", "Sala de profesores", "Dell", 2021),
    ("Computador Sala de Profesores 3", "Computador", "Sala de profesores", "Dell", 2021),
    ("Notebook UTP", "Notebook", "UTP", "Lenovo", 2022),
    ("Notebook Inspectoría", "Notebook", "Inspectoría", "Asus", 2020),
    ("Impresora Sala de Profesores", "Impresora", "Sala de profesores", "Brother", 2021),
    ("Proyector Sala 1", "Proyector", "Sala 1", "Epson", 2022),
    ("Proyector Sala 2", "Proyector", "Sala 2", "Epson", 2022),
    ("Proyector Sala 4", "Proyector", "Sala 4", "ViewSonic", 2020),
    ("Proyector Sala 5", "Proyector", "Sala 5", "ViewSonic", 2023),
    ("Computador Laboratorio 1", "Computador", "Laboratorio", "HP", 2019),
    ("Computador Laboratorio 2", "Computador", "Laboratorio", "HP", 2019),
    ("Computador Laboratorio 3", "Computador", "Laboratorio", "HP", 2019),
    ("Computador Laboratorio 4", "Computador", "Laboratorio", "HP", 2024),
    ("Computador Biblioteca 2", "Computador", "Biblioteca", "Lenovo", 2023),
    ("Computador Secretaría", "Computador", "Secretaría", "Dell", 2020),
    ("Computador Recepción", "Computador", "Recepción", "Dell", 2022),
    ("Router Pabellón B", "Red", "Pabellón B", "TP-Link", 2021),
    ("Notebook Orientación", "Notebook", "Orientación", "Asus", 2023),
    ("Impresora Biblioteca", "Impresora", "Biblioteca", "HP", 2024),
]

USUARIOS_COLEGIO = [
    "Ana Muñoz", "Bruno Rojas", "Carla Soto", "Daniel Pérez", "Elena Díaz",
    "Felipe Contreras", "Gabriela Silva", "Héctor Morales", "Isabel Reyes",
    "Javier Fuentes", "Karen Castillo", "Luis Herrera", "María Torres",
    "Nicolás Vargas", "Olga Espinoza", "Pablo Núñez", "Rocío Sepúlveda",
    "Sergio Araya", "Tamara Valenzuela", "Ulises Cortés", "Valentina Lagos",
    "Walter Pizarro", "Ximena Bravo", "Yolanda Carrasco", "Zoe Figueroa",
    "Andrés Gallardo", "Beatriz Tapia", "Cristián Vera", "Daniela Olivares",
    "Esteban Molina",
]

SOLUCIONES = [
    ("La impresora no imprime", 1,
     "1. Revisa que tenga papel y que no haya hojas atascadas.\n"
     "2. Apágala 30 segundos y vuelve a encenderla.\n"
     "3. Si sigue sin imprimir, reporta la falla con el QR."),
    ("No hay internet en el computador", 3,
     "1. Revisa que el cable de red esté conectado o que el wifi esté activo.\n"
     "2. Reinicia el computador.\n"
     "3. Si otros equipos tampoco tienen internet, repórtalo como prioridad alta."),
    ("Olvidé mi contraseña del correo", 2,
     "1. Entra a la página del correo y presiona «¿Olvidaste tu contraseña?».\n"
     "2. Si no tienes correo de recuperación, reporta la solicitud."),
    ("El proyector no muestra imagen", 1,
     "1. Revisa que el cable HDMI esté bien conectado en ambos extremos.\n"
     "2. En el notebook presiona Windows + P y elige «Duplicar»."),
    ("El computador está muy lento", 2,
     "1. Cierra los programas que no estés usando.\n"
     "2. Reinicia el equipo (no solo lo suspendas).\n"
     "3. Si sigue lento, repórtalo para una mantención."),
]

CATEGORIAS = {"Hardware": 1, "Software": 2, "Conectividad": 3, "Por clasificar": 4}

EJEMPLOS_POR_CATEGORIA = {}
for texto, categoria in EJEMPLOS_PILOTO:
    EJEMPLOS_POR_CATEGORIA.setdefault(categoria, []).append(texto)


# ---------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------

def fecha_texto(fecha):
    return fecha.strftime(FORMATO_FECHA)


def momento_en_semana(inicio_semana):
    """Fecha y hora aleatoria de lunes a viernes, entre 8:00 y 17:59."""
    fecha = inicio_semana + timedelta(
        days=random.randint(0, 4),
        hours=random.randint(8, 17),
        minutes=random.randint(0, 59)
    )
    return min(fecha, AHORA - timedelta(hours=1))


def duraciones_con_promedio(cantidad, promedio):
    """Lista de duraciones en horas, variadas, cuyo promedio es exacto."""
    factores = [random.uniform(0.2, 1.8) for _ in range(cantidad)]
    ajuste = promedio * cantidad / sum(factores)
    return [factor * ajuste for factor in factores]


def categoria_para_equipo(tipo):
    if tipo in ("Impresora", "Proyector"):
        return "Hardware"
    if tipo == "Red":
        return "Conectividad"
    if tipo is None:
        return random.choice(["Software", "Conectividad"])
    return random.choice(["Hardware", "Software", "Software", "Conectividad"])


def crear_cuenta(conexion, organizacion_id, nombre, rol, usuario, clave, email):
    cursor = conexion.execute(
        """
        INSERT INTO usuarios (organizacion_id, nombre, rol, usuario, clave_hash, email)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (organizacion_id, nombre, rol, usuario, generate_password_hash(clave), email)
    )
    return cursor.lastrowid


def insertar_ticket(conexion, datos):
    columnas = ", ".join(datos.keys())
    marcas = ", ".join("?" for _ in datos)
    cursor = conexion.execute(
        f"INSERT INTO tickets ({columnas}) VALUES ({marcas})",
        list(datos.values())
    )
    return cursor.lastrowid


def registrar_cambio(conexion, ticket_id, fecha, campo, anterior, nuevo):
    conexion.execute(
        """
        INSERT INTO cambios_ticket (ticket_id, fecha_cambio, campo, valor_anterior, valor_nuevo)
        VALUES (?, ?, ?, ?, ?)
        """,
        (ticket_id, fecha_texto(fecha), campo, anterior, nuevo)
    )


def sugerencia_erronea(categoria, prioridad):
    """Sugerencia que el encargado tuvo que corregir (para K6)."""
    opcion = random.choice(["por_clasificar", "otra_categoria", "otra_prioridad"])

    if opcion == "por_clasificar":
        return "Por clasificar", prioridad, round(random.uniform(0.34, 0.55), 2)

    if opcion == "otra_categoria":
        otra = random.choice([c for c in ("Hardware", "Software", "Conectividad") if c != categoria])
        return otra, prioridad, round(random.uniform(0.6, 0.75), 2)

    otra_prioridad = random.choice([p for p in ("Baja", "Media", "Alta") if p != prioridad])
    return categoria, otra_prioridad, round(random.uniform(0.6, 0.9), 2)


# ---------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------

def crear_colegio(conexion, semanas):
    cursor = conexion.execute(
        "INSERT INTO organizaciones (nombre, slug, tipo) VALUES (?, ?, 'Colegio')",
        ("Colegio Los Aromos (demo)", "colegio-los-aromos")
    )
    organizacion_id = cursor.lastrowid

    encargado_id = crear_cuenta(conexion, organizacion_id, "Marcela Ibáñez", "encargado",
                                "encargado", "encargado123", "encargado@colegio-demo.example")
    tecnico_id = crear_cuenta(conexion, organizacion_id, "Rodrigo Campos", "tecnico",
                              "tecnico", "tecnico123", "tecnico@colegio-demo.example")
    responsables = [(encargado_id, "Marcela Ibáñez"), (tecnico_id, "Rodrigo Campos")]

    # Equipos activos con su QR
    equipos = []
    for numero, (nombre, tipo, ubicacion, marca, anio) in enumerate(EQUIPOS_COLEGIO, start=1):
        codigo = f"COL-{numero:03d}"
        cursor = conexion.execute(
            """
            INSERT INTO equipos (organizacion_id, codigo, nombre, tipo, marca, modelo,
                                 numero_serie, ubicacion, fecha_compra)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (organizacion_id, codigo, nombre, tipo, marca, "Modelo genérico",
             f"SN{random.randint(100000, 999999)}", ubicacion, f"{anio}-03-01")
        )
        equipos.append({"id": cursor.lastrowid, "codigo": codigo, "nombre": nombre, "tipo": tipo})

    # Equipos dados de baja (reporte Ley REP)
    for codigo, nombre, tipo, motivo in (
        ("COL-026", "Computador antiguo Laboratorio", "Computador", "Placa madre dañada, reparación no conveniente"),
        ("COL-027", "Impresora matriz Secretaría", "Impresora", "Obsoleta, sin repuestos"),
    ):
        conexion.execute(
            """
            INSERT INTO equipos (organizacion_id, codigo, nombre, tipo, marca, ubicacion,
                                 fecha_compra, estado, fecha_baja, motivo_baja)
            VALUES (?, ?, ?, ?, 'Genérica', 'Bodega', '2012-03-01', 'Dado de baja', ?, ?)
            """,
            (organizacion_id, codigo, nombre, tipo, semanas["S8"].date().isoformat(), motivo)
        )

    # 30 usuarios solicitantes (algunos dejaron un contacto)
    solicitantes = []
    for numero, nombre in enumerate(USUARIOS_COLEGIO):
        email = f"usuario{numero + 1}@colegio-demo.example" if numero % 3 == 0 else None
        telefono = f"+56 9 5555 {1000 + numero}" if numero % 4 == 0 else None
        cursor = conexion.execute(
            """
            INSERT INTO usuarios (organizacion_id, nombre, rol, email, telefono)
            VALUES (?, ?, 'solicitante', ?, ?)
            """,
            (organizacion_id, nombre, email, telefono)
        )
        solicitantes.append(cursor.lastrowid)

    # Se reparte cada ticket del piloto en su semana y su equipo
    tickets_por_semana = {semana: [] for semana in PLAN_SEMANAS}

    for indice, semanas_tickets, _ in EQUIPOS_CON_ALERTA:
        for semana in semanas_tickets:
            tickets_por_semana[semana].append(equipos[indice])

    # Los demás equipos tienen como máximo 2 tickets (no generan alerta)
    otros = [equipo for equipo in equipos[len(EQUIPOS_CON_ALERTA):] for _ in range(2)]
    random.shuffle(otros)

    for semana, plan in PLAN_SEMANAS.items():
        while len(tickets_por_semana[semana]) < plan["tickets"]:
            tickets_por_semana[semana].append(otros.pop() if otros else None)
        random.shuffle(tickets_por_semana[semana])

    # Tickets del piloto
    tickets_creados = []  # (ticket_id, equipo, fecha_creacion)

    for semana, plan in PLAN_SEMANAS.items():
        lista = tickets_por_semana[semana]
        duraciones = duraciones_con_promedio(plan["resueltos"], plan["horas_promedio"])

        for posicion, equipo in enumerate(lista):
            tipo = equipo["tipo"] if equipo else None
            categoria = categoria_para_equipo(tipo)
            texto = random.choice(EJEMPLOS_POR_CATEGORIA[categoria])
            prioridad = random.choices(["Alta", "Media", "Baja"], weights=[1, 2, 1])[0]
            creacion = momento_en_semana(semanas[semana])

            # Sugerencia del clasificador: las primeras se aceptaron sin cambios
            if posicion < plan["ia_aceptadas"]:
                sugerida, prioridad_sugerida = categoria, prioridad
                confianza = round(random.uniform(0.67, 1.0), 2)
            else:
                sugerida, prioridad_sugerida, confianza = sugerencia_erronea(categoria, prioridad)

            resuelto = posicion < plan["resueltos"]
            tiene_encuesta = posicion < plan["encuestas"]
            responsable_id, responsable_nombre = random.choice(responsables)

            datos = {
                "organizacion_id": organizacion_id,
                "codigo_seguimiento": secrets.token_urlsafe(8),
                "titulo": texto[:60],
                "descripcion": texto + (f". Equipo ubicado en {equipo['nombre']}." if equipo else "."),
                "fecha_creacion": fecha_texto(creacion),
                "prioridad": prioridad,
                "solicitante_id": random.choice(solicitantes),
                "responsable_id": responsable_id,
                "categoria_id": CATEGORIAS[categoria],
                "equipo_id": equipo["id"] if equipo else None,
                "categoria_sugerida_id": CATEGORIAS[sugerida],
                "prioridad_sugerida": prioridad_sugerida,
                "confianza_ia": confianza,
                "aviso_sla_enviado": 1,
            }

            if resuelto:
                cierre = min(creacion + timedelta(hours=duraciones[posicion]), AHORA - timedelta(minutes=30))
                datos.update({
                    "estado": "Cerrado" if tiene_encuesta else "Resuelto",
                    "fecha_cierre": fecha_texto(cierre),
                    "solucion": "Se revisó el equipo y se solucionó el problema.",
                })

                if tiene_encuesta:
                    positiva = posicion < plan["encuestas_positivas"]
                    datos["satisfaccion"] = random.choice([4, 5, 5]) if positiva else random.choice([2, 3])
            else:
                datos["estado"] = "En proceso"

            ticket_id = insertar_ticket(conexion, datos)
            tickets_creados.append((ticket_id, equipo, creacion))

            # Historial de cambios para la trazabilidad
            registrar_cambio(conexion, ticket_id, creacion + timedelta(minutes=20),
                             "responsable", "Sin asignar", responsable_nombre)
            registrar_cambio(conexion, ticket_id, creacion + timedelta(minutes=25),
                             "estado", "Nuevo", "En proceso")

            if sugerida != categoria:
                registrar_cambio(conexion, ticket_id, creacion + timedelta(minutes=22),
                                 "categoria", sugerida, categoria)
            if prioridad_sugerida != prioridad:
                registrar_cambio(conexion, ticket_id, creacion + timedelta(minutes=23),
                                 "prioridad", prioridad_sugerida, prioridad)
            if resuelto:
                registrar_cambio(conexion, ticket_id, cierre, "estado", "En proceso", "Resuelto")

    # Alertas preventivas: se crean al registrarse la 3.a falla del equipo
    for indice, _, revisada in EQUIPOS_CON_ALERTA:
        equipo = equipos[indice]
        fechas = sorted(fecha for _, eq, fecha in tickets_creados if eq is equipo)
        creada = fechas[2] + timedelta(minutes=1)

        conexion.execute(
            """
            INSERT INTO alertas (equipo_id, motivo, fecha_creacion, fecha_limite,
                                 estado, fecha_revision, aviso_vencida_enviado)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
            (
                equipo["id"],
                "3 fallas en los últimos 60 días. Se recomienda una revisión preventiva.",
                fecha_texto(creada),
                fecha_texto(creada + timedelta(days=7)),
                "Revisada" if revisada else "Pendiente",
                fecha_texto(min(creada + timedelta(days=2), AHORA)) if revisada else None,
            )
        )

    # Los 2 equipos que se repararon en vez de reemplazarse (impacto del informe)
    solucion_reparacion = (
        "Revisión preventiva por alerta: se cambió la fuente de poder y se limpió "
        "el equipo. Se reparó en vez de reemplazarlo."
    )
    for indice in (0, 2):
        conexion.execute(
            """
            UPDATE tickets
            SET solucion = ?
            WHERE id = (
                SELECT MAX(id) FROM tickets WHERE equipo_id = ? AND estado IN ('Resuelto', 'Cerrado')
            )
            """,
            (solucion_reparacion, equipos[indice]["id"])
        )

    # Incidencias que llegaron por WhatsApp, correo o verbal (K3)
    for semana, plan in PLAN_SEMANAS.items():
        for _ in range(plan["externas"]):
            conexion.execute(
                "INSERT INTO incidencias_externas (organizacion_id, fecha, canal, descripcion) VALUES (?, ?, ?, ?)",
                (
                    organizacion_id,
                    fecha_texto(momento_en_semana(semanas[semana])),
                    random.choice(["WhatsApp", "WhatsApp", "Verbal", "Correo"]),
                    random.choice(["Aviso de falla de proyector", "No funciona internet en sala",
                                   "Impresora sin tóner", "Problema con el correo"]),
                )
            )

    # Tickets de la semana actual (para ver los avisos de plazo y "Por clasificar")
    actuales = [
        ("El proyector no enciende y hay clase en 10 minutos", "Hardware", "Alta", 3.5, equipos[12]),
        ("Necesito instalar el programa de notas", "Software", "Media", 1, equipos[8]),
        ("Algo raro pasa con mi equipo", "Por clasificar", "Media", 0.5, None),
    ]
    for titulo, categoria, prioridad, horas_atras, equipo in actuales:
        insertar_ticket(conexion, {
            "organizacion_id": organizacion_id,
            "codigo_seguimiento": secrets.token_urlsafe(8),
            "titulo": titulo,
            "descripcion": titulo + ".",
            "fecha_creacion": fecha_texto(AHORA - timedelta(hours=horas_atras)),
            "prioridad": prioridad,
            "solicitante_id": random.choice(solicitantes),
            "categoria_id": CATEGORIAS[categoria],
            "equipo_id": equipo["id"] if equipo else None,
            "categoria_sugerida_id": CATEGORIAS[categoria],
            "prioridad_sugerida": prioridad,
            "confianza_ia": 0.4 if categoria == "Por clasificar" else 1.0,
        })

    for titulo, categoria_id, pasos in SOLUCIONES:
        conexion.execute(
            "INSERT INTO soluciones (organizacion_id, categoria_id, titulo, pasos) VALUES (?, ?, ?, ?)",
            (organizacion_id, categoria_id, titulo, pasos)
        )


def crear_pyme(conexion, semanas):
    cursor = conexion.execute(
        "INSERT INTO organizaciones (nombre, slug, tipo) VALUES (?, ?, 'Pyme')",
        ("Pyme Demo Ltda.", "pyme-demo")
    )
    organizacion_id = cursor.lastrowid

    encargado_id = crear_cuenta(conexion, organizacion_id, "Jorge Salinas", "encargado",
                                "pyme", "pyme12345", "ti@pyme-demo.example")

    equipos = []
    for numero, (nombre, tipo) in enumerate(
        [("Notebook Gerencia", "Notebook"), ("Computador Ventas", "Computador"),
         ("Impresora Oficina", "Impresora"), ("Router Oficina", "Red")],
        start=1
    ):
        cursor = conexion.execute(
            """
            INSERT INTO equipos (organizacion_id, codigo, nombre, tipo, ubicacion, fecha_compra)
            VALUES (?, ?, ?, ?, 'Oficina', '2021-06-01')
            """,
            (organizacion_id, f"PYM-{numero:03d}", nombre, tipo)
        )
        equipos.append((cursor.lastrowid, tipo))

    cursor = conexion.execute(
        "INSERT INTO usuarios (organizacion_id, nombre, rol) VALUES (?, 'Paula Riquelme', 'solicitante')",
        (organizacion_id,)
    )
    solicitante_id = cursor.lastrowid

    for semana in ("S8", "S9"):
        for equipo_id, tipo in equipos[:3]:
            categoria = categoria_para_equipo(tipo)
            creacion = momento_en_semana(semanas[semana])
            insertar_ticket(conexion, {
                "organizacion_id": organizacion_id,
                "codigo_seguimiento": secrets.token_urlsafe(8),
                "titulo": random.choice(EJEMPLOS_POR_CATEGORIA[categoria])[:60],
                "descripcion": "Ticket de ejemplo de la pyme.",
                "fecha_creacion": fecha_texto(creacion),
                "prioridad": "Media",
                "estado": "Resuelto",
                "fecha_cierre": fecha_texto(min(creacion + timedelta(hours=8), AHORA)),
                "solicitante_id": solicitante_id,
                "responsable_id": encargado_id,
                "categoria_id": CATEGORIAS[categoria],
                "equipo_id": equipo_id,
                "categoria_sugerida_id": CATEGORIAS[categoria],
                "prioridad_sugerida": "Media",
                "confianza_ia": 0.9,
                "aviso_sla_enviado": 1,
            })


def crear_mediciones(conexion, semanas):
    for semana, valores in MEDICIONES.items():
        conexion.execute(
            """
            INSERT INTO mediciones_semanales (
                semana_inicio, tareas_planificadas, tareas_terminadas,
                costo_presupuestado, costo_real, horas_totales, horas_en_linea
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [semanas[semana].date().isoformat()] + list(valores)
        )


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    init_db()
    conexion = conectar()

    # S7, S8 y S9 son las tres semanas anteriores a la actual
    periodos = ultimas_semanas(4)[:3]
    semanas = {
        nombre: texto_a_fecha(f"{desde} 00:00:00")
        for nombre, (_, desde, _) in zip(PLAN_SEMANAS, periodos)
    }

    crear_colegio(conexion, semanas)
    crear_pyme(conexion, semanas)
    crear_mediciones(conexion, semanas)

    conexion.commit()
    conexion.close()

    print("Datos de ejemplo cargados.")
    print("Cuentas de prueba (usuario / clave):")
    print("  admin / admin123          -> administrador SoporTI")
    print("  encargado / encargado123  -> encargado TI del colegio")
    print("  tecnico / tecnico123      -> técnico del colegio")
    print("  pyme / pyme12345          -> encargado TI de la pyme")


if __name__ == "__main__":
    main()
