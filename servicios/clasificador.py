"""
Clasificador automático de tickets (sugerencia de categoría y urgencia).

Usa dos fuentes de información:
  1. Palabras clave por categoría.
  2. Ejemplos de tickets ya clasificados: los 40 ejemplos obtenidos con el
     método Concierge del piloto + los tickets cerrados del sistema, que
     incluyen las correcciones hechas por el encargado. Así la sugerencia
     mejora a medida que se usa el sistema (riesgo R2).

No depende de servicios externos, por lo que no tiene costo de uso
(riesgo R6) y siempre se puede corregir manualmente.

Si la confianza es menor a UMBRAL_CONFIANZA, el ticket queda en la
categoría "Por clasificar" para que el encargado la revise.
"""

import re
import unicodedata

UMBRAL_CONFIANZA = 0.6

CATEGORIA_POR_CLASIFICAR = "Por clasificar"

# Cantidad mínima de palabras en común para considerar parecido un ejemplo
PALABRAS_EN_COMUN_MINIMAS = 2

PALABRAS_POR_CATEGORIA = {
    "Hardware": [
        "no enciende", "no prende", "pantalla", "monitor", "teclado",
        "mouse", "impresora", "imprime", "toner", "tinta", "papel atascado",
        "proyector", "parlante", "audio", "bateria", "cargador", "disco",
        "ruido", "se apaga", "sobrecalienta", "cable", "usb",
    ],
    "Software": [
        "programa", "aplicacion", "instalar", "actualizar", "actualizacion",
        "licencia", "office", "word", "excel", "powerpoint", "windows",
        "virus", "contrasena", "clave", "sesion", "error", "se cierra",
        "se congela", "lento", "correo", "outlook", "navegador", "chrome",
    ],
    "Conectividad": [
        "internet", "wifi", "wi-fi", "red", "conexion", "conectar",
        "router", "senal", "sin acceso", "vpn", "desconecta",
        "no carga la pagina", "cable de red",
    ],
}

PALABRAS_PRIORIDAD_ALTA = [
    "urgente", "no enciende", "no prende", "no funciona", "caido",
    "sin internet", "todos", "toda la sala", "clase", "examen", "virus",
]

PALABRAS_PRIORIDAD_BAJA = [
    "consulta", "cuando puedan", "no es urgente", "sugerencia",
    "instalar", "cambiar fondo",
]

# 40 ejemplos clasificados manualmente durante el piloto (método Concierge)
EJEMPLOS_PILOTO = [
    ("El computador de la sala no enciende aunque está enchufado", "Hardware"),
    ("La impresora de secretaría tiene papel atascado", "Hardware"),
    ("El proyector se apaga solo a los diez minutos", "Hardware"),
    ("El mouse del notebook no responde", "Hardware"),
    ("Faltan teclas en el teclado del computador de biblioteca", "Hardware"),
    ("La pantalla se ve con rayas de colores", "Hardware"),
    ("El parlante del proyector no tiene sonido", "Hardware"),
    ("El notebook no carga la batería con el cargador", "Hardware"),
    ("La impresora imprime hojas en blanco, parece que falta tóner", "Hardware"),
    ("El computador hace mucho ruido y se calienta", "Hardware"),
    ("El monitor parpadea y luego se pone negro", "Hardware"),
    ("El puerto usb no reconoce el pendrive", "Hardware"),
    ("El disco duro está lleno y el equipo hace ruido extraño", "Hardware"),
    ("El cable del proyector está cortado", "Hardware"),
    ("Necesito instalar el programa de notas en mi computador", "Software"),
    ("Word se cierra cada vez que abro un documento", "Software"),
    ("Excel muestra error al abrir la planilla de asistencia", "Software"),
    ("Olvidé mi contraseña del correo institucional", "Software"),
    ("Windows pide actualizar y no termina nunca", "Software"),
    ("Aparece un aviso de licencia vencida de Office", "Software"),
    ("El navegador abre páginas de publicidad, puede ser un virus", "Software"),
    ("El computador está muy lento al abrir programas", "Software"),
    ("No puedo iniciar sesión en el sistema de matrícula", "Software"),
    ("PowerPoint se congela al presentar en clase", "Software"),
    ("Outlook no descarga los correos nuevos", "Software"),
    ("Chrome muestra error de certificado en el libro de clases", "Software"),
    ("Necesito actualizar la aplicación de contabilidad", "Software"),
    ("No hay internet en la sala de profesores", "Conectividad"),
    ("El wifi se desconecta a cada rato en el segundo piso", "Conectividad"),
    ("El router de recepción tiene todas las luces apagadas", "Conectividad"),
    ("No llega señal de wifi a la sala de computación", "Conectividad"),
    ("El computador dice red no identificada", "Conectividad"),
    ("Sin acceso a internet en el laboratorio", "Conectividad"),
    ("La conexión está muy lenta, las páginas no cargan", "Conectividad"),
    ("No puedo conectar el notebook a la red del colegio", "Conectividad"),
    ("La vpn de la oficina no conecta desde la casa", "Conectividad"),
    ("El cable de red de la impresora compartida está suelto", "Conectividad"),
    ("Internet funciona en el celular pero no en el computador", "Conectividad"),
    ("Se cae la conexión cuando hay muchos alumnos conectados", "Conectividad"),
    ("No carga la página del ministerio, dice sin conexión", "Conectividad"),
]

# Palabras muy comunes que no ayudan a distinguir categorías
PALABRAS_IGNORADAS = {
    "para", "pero", "cada", "como", "esta", "este", "esto", "tiene", "hace",
    "sala", "desde", "cuando", "todas", "todos", "muy", "solo", "luego",
    "puedo", "necesito", "equipo", "computador", "notebook",
}


def normalizar(texto):
    """Pasa el texto a minúsculas y le quita los tildes."""
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(letra for letra in texto if unicodedata.category(letra) != "Mn")


def palabras_significativas(texto):
    """Conjunto de palabras de 4 o más letras que no están en PALABRAS_IGNORADAS."""
    palabras = re.findall(r"[a-z]+", normalizar(texto))
    return {
        palabra for palabra in palabras
        if len(palabra) >= 4 and palabra not in PALABRAS_IGNORADAS
    }


def contar_coincidencias(texto, palabras):
    """
    Cuenta cuántas palabras clave de la lista aparecen en el texto.
    Se buscan como palabras completas (\\b) para que, por ejemplo,
    "red" no coincida dentro de "pared".
    """
    return sum(
        1 for palabra in palabras
        if re.search(rf"\b{re.escape(palabra)}\b", texto)
    )


def sugerir_prioridad(texto):
    if contar_coincidencias(texto, PALABRAS_PRIORIDAD_ALTA) > 0:
        return "Alta"

    if contar_coincidencias(texto, PALABRAS_PRIORIDAD_BAJA) > 0:
        return "Baja"

    return "Media"


def clasificar_ticket(titulo, descripcion, ejemplos_extra=()):
    """
    Devuelve un diccionario con la sugerencia:
        categoria  -> nombre de la categoría sugerida
        prioridad  -> "Alta", "Media" o "Baja"
        confianza  -> número entre 0 y 1

    ejemplos_extra es una lista de tuplas (texto, categoria) con tickets
    reales ya cerrados, para aprender de las correcciones del encargado.

    La confianza es la proporción del puntaje que obtuvo la mejor
    categoría respecto del puntaje total.
    """
    texto = normalizar(f"{titulo} {descripcion}")
    palabras_ticket = palabras_significativas(texto)

    puntajes = {
        categoria: contar_coincidencias(texto, palabras)
        for categoria, palabras in PALABRAS_POR_CATEGORIA.items()
    }

    for texto_ejemplo, categoria in list(EJEMPLOS_PILOTO) + list(ejemplos_extra):
        if categoria not in puntajes:
            continue

        en_comun = palabras_ticket & palabras_significativas(texto_ejemplo)

        if len(en_comun) >= PALABRAS_EN_COMUN_MINIMAS:
            puntajes[categoria] += 1

    total = sum(puntajes.values())
    mejor_categoria = max(puntajes, key=puntajes.get)

    if total == 0:
        confianza = 0.0
    else:
        confianza = puntajes[mejor_categoria] / total

    if confianza < UMBRAL_CONFIANZA:
        mejor_categoria = CATEGORIA_POR_CLASIFICAR

    return {
        "categoria": mejor_categoria,
        "prioridad": sugerir_prioridad(texto),
        "confianza": round(confianza, 2),
    }
