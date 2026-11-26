from datetime import datetime, timedelta, timezone

HORAS_SLA = {
    "Alta": 4,
    "Media": 24,
    "Baja": 48,
}

PORCENTAJE_AVISO = 0.8

FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"

ESTADOS_ABIERTOS = ("Nuevo", "En proceso")


def ahora_utc():

    return datetime.now(timezone.utc).replace(tzinfo=None)


def texto_a_fecha(texto):
    return datetime.strptime(texto, FORMATO_FECHA)


def calcular_sla(ticket):

    creacion = texto_a_fecha(ticket["fecha_creacion"])
    plazo = timedelta(hours=HORAS_SLA[ticket["prioridad"]])
    fecha_limite = creacion + plazo

    if ticket["estado"] in ESTADOS_ABIERTOS:
        tiempo_usado = ahora_utc() - creacion

        if tiempo_usado > plazo:
            estado = "Vencido"
        elif tiempo_usado >= plazo * PORCENTAJE_AVISO:
            estado = "Por vencer"
        else:
            estado = "En plazo"

    else:
        # Ticket resuelto o cerrado: se revisa si se cerró a tiempo
        cierre = texto_a_fecha(ticket["fecha_cierre"]) if ticket["fecha_cierre"] else fecha_limite

        estado = "Cumplido" if cierre <= fecha_limite else "Fuera de plazo"

    return {
        "fecha_limite": fecha_limite.strftime(FORMATO_FECHA),
        "estado": estado,
    }
