# Mesa de Soporte TI → SoporTI

> **Actualización SoporTI (Entregable Parte II) creada por Milton Zambrano Tobar y Sebastián Velasco.** Ver la sección [SoporTI – versión del Entregable Parte II](#soporti--versión-del-entregable-parte-ii).

Proyecto académico correspondiente a la Evaluación 3 de Gestión de Proyectos Informáticos.

El proyecto consiste en una aplicación web para registrar y realizar seguimiento a solicitudes de soporte TI, manteniendo trazabilidad sobre solicitante, categoría, prioridad, responsable y estado.

## Integrantes

- Sebastian Velasco
- Felipe Garces
- Jeremmy Vidal

## Estado final del proyecto

El proyecto llegó a su versión **MVP v1.0**, con los requisitos RF-01 a RF-06 implementados e integrados.

### Funciones principales

- RF-01: Registrar solicitudes de soporte.
- RF-02: Generar ID único y fecha de creación.
- RF-03: Listar solicitudes con estado, prioridad y responsable.
- RF-04: Asignar responsable y modificar estado.
- RF-05: Filtrar solicitudes por estado, prioridad y categoría.
- RF-06: Mostrar resumen total y cantidad de tickets por estado.
- Persistencia mediante SQLite.
- Validaciones básicas del formulario.
- Registro de cambios relevantes sobre los tickets.

## SoporTI – versión del Entregable Parte II

> **Autores de esta actualización (SoporTI):** Milton Zambrano Tobar y Sebastián Velasco.
> Desarrollada para el Entregable Parte II (PEP801) de Ingeniería de Ejecución en Informática mención Desarrollo de Sistemas, Escuela de Construcción e Ingeniería, sección 4721.
>
> | Integrante | Cargos en el proyecto |
> |---|---|
> | Milton Zambrano Tobar (MZ) | Jefe de Proyecto · Desarrollador Backend, BD e IA |
> | Sebastián Velasco (SV) | Desarrollador Frontend y UX · Encargado de Calidad (QA) · Encargado de Implementación, Soporte y Comercial |
>
> La versión MVP v1.0 anterior (Mesa de Soporte TI) fue desarrollada por Sebastian Velasco, Felipe Garces y Jeremmy Vidal.

A partir del informe (plan de ejecución, piloto, validación y estrategia de evolución) el sistema pasó a llamarse **SoporTI · Tu soporte TI, ordenado y preventivo** e incluye todo lo descrito en el informe.

### Funciones del MVP validado y ajustes del piloto

| Función | Dónde está | Relación con el informe |
|---|---|---|
| Reporte de fallas con código QR por equipo y afiche con QR de la organización | `rutas/publico.py`, `/equipos/etiquetas`, `/equipos/afiche` | Registro en ≤ 1 minuto, ajuste de capacitación (K3) |
| Seguimiento del ticket por el solicitante sin crear cuenta | `/seguimiento/<codigo>` | Impacto social |
| Clasificación automática de categoría y urgencia, umbral de confianza 60 % («Por clasificar»), 40 ejemplos del piloto y aprendizaje con las correcciones | `servicios/clasificador.py` | K6, riesgo R2, ajuste del piloto |
| Corrección manual de categoría y prioridad con trazabilidad | `rutas/tickets.py` | Riesgo R2 |
| Plazos (SLA) por prioridad: Alta 4 h, Media 24 h, Baja 48 h, aviso al 80 % | `servicios/sla.py`, `servicios/tareas.py` | K5, ajuste del piloto |
| Alertas preventivas (3 fallas en 60 días), revisión en 7 días, aviso por correo | `servicios/alertas.py` | K7, riesgo R8 |
| Encuesta de satisfacción al cierre | `/seguimiento/<codigo>` | K8 |
| Registro de incidencias llegadas por WhatsApp, correo o verbal | `/incidencias` | K3 |
| Cuadro de mando K1 a K9 por semana con semáforo verde, amarillo y rojo | `servicios/indicadores.py` | Punto 3 y reporte de validación |
| Inicio de sesión, roles (solicitante, técnico, encargado, admin), claves cifradas y protección CSRF | `seguridad.py`, `rutas/auth.py` | Riesgo R5 (Ley 21.719) |
| Respaldos automáticos de la base de datos | `tareas.py respaldo` | Riesgo R4 |
| Punto de control `/salud` para un monitor externo | `rutas/publico.py` | K9 |
| Clasificación local, sin costo por uso de una API externa | `servicios/clasificador.py` | Riesgo R6 |

### Versión 2 y versión 3 (estrategia de evolución)

| Función | Dónde está |
|---|---|
| Vista móvil (las tablas se muestran como tarjetas en el celular) | `static/styles.css` |
| Notificaciones por correo al encargado y al solicitante, y enlace directo a WhatsApp | `servicios/notificaciones.py` |
| Inventario completo de equipos (marca, modelo, serie, fecha de compra, estado) | `rutas/equipos.py` |
| Base de soluciones frecuentes (página de ayuda pública) | `rutas/soluciones.py`, `/ayuda/<organizacion>` |
| Plataforma multiorganización (SaaS): cada organización ve solo sus datos | `organizacion_id` en las tablas, `rutas/admin.py` |
| Mantenimiento predictivo con el historial de cada equipo | `servicios/prediccion.py` |
| Reporte de equipos dados de baja para reciclaje (Ley REP) con descarga CSV | `/equipos/reciclaje` |
| Reporte mensual para la dirección con reconocimiento al área destacada (ADKAR: Refuerzo) | `/reporte-mensual` |

### Estructura del código

```
app.py              crea la aplicación y registra las rutas
db.py               conexión a SQLite y creación de tablas
seguridad.py        sesión, permisos por rol y protección CSRF
datos_demo.py       carga los datos de ejemplo del piloto
tareas.py           avisos por correo y respaldos (tarea programada)
rutas/              una página o grupo de páginas por archivo (Blueprints)
servicios/          lógica del negocio: clasificador, SLA, alertas, KPI, etc.
templates/          plantillas HTML separadas por área
database/schema.sql estructura de la base de datos
```

### Datos de ejemplo (simulación del piloto)

```powershell
python datos_demo.py
```

Este comando **borra la base de datos** y carga un colegio ficticio con 25 equipos, 30 usuarios y tickets durante las tres semanas anteriores (S7, S8 y S9). Con esos datos el cuadro de mando muestra resultados como los del informe: K3 77/87/94 %, K5 31/26/19 h, K6 62,5/70/81 %, K7 1 de 2 y 3 de 4 alertas, K8 86,8 %, K1 93 %, K2 +9,5 % y K9 99,6 %. También agrega tickets de la semana actual (para ver los avisos de plazo y «Por clasificar») y una segunda organización (pyme).

Cuentas de prueba (solo para la demo local):

| Usuario | Clave | Rol |
|---|---|---|
| `admin` | `admin123` | Administrador SoporTI (organizaciones, cuentas y control del proyecto) |
| `encargado` | `encargado123` | Encargado TI del colegio |
| `tecnico` | `tecnico123` | Técnico del colegio |
| `pyme` | `pyme12345` | Encargado TI de la pyme |

Formulario público de reporte del colegio: `http://127.0.0.1:5000/reportar/colegio-los-aromos`

Si no se cargan los datos de ejemplo, al iniciar se crea solo la cuenta `admin` / `admin123` (se puede cambiar con las variables de entorno `ADMIN_USUARIO` y `ADMIN_CLAVE`).

### Avisos por correo y respaldos (opcional)

Para enviar correos se definen estas variables de entorno antes de ejecutar la aplicación. Si no se definen, los avisos solo se muestran en la terminal:

```powershell
$env:SMTP_SERVIDOR = "smtp.gmail.com"
$env:SMTP_PUERTO = "587"
$env:SMTP_USUARIO = "cuenta@ejemplo.com"
$env:SMTP_CLAVE = "clave-de-aplicacion"
$env:SECRET_KEY = "una-clave-larga-y-secreta"
```

Los avisos de plazo, las alertas vencidas y los respaldos se ejecutan con `python tareas.py todo`. Se recomienda programarlo cada hora con el Programador de tareas de Windows. Los respaldos quedan en la carpeta `respaldos/`.

### Base de datos de una versión anterior

La estructura de la base de datos cambió. Si ya existe `database/soporte.db` de la versión 1.0, hay que eliminarlo (o ejecutar `python datos_demo.py`) para que se cree con las tablas nuevas.

### Probar el QR desde un celular

El QR apunta a la dirección con la que se abrió la página. Para escanearlo desde un celular conectado a la misma red, ejecuta Flask con `app.run(debug=True, host="0.0.0.0")` y abre la aplicación usando la IP del computador (por ejemplo `http://192.168.1.10:5000`).

## Tecnologías utilizadas

- Python
- Flask
- SQLite
- HTML
- CSS
- Git
- GitHub
- GitHub Projects

## Evolución del proyecto

- H1 — Inicio y planificación, 29 de septiembre de 2026.
- H2 — Línea base del proyecto, 30 de septiembre de 2026.
- H3 — MVP funcional v0.1, 06 de octubre de 2026.
- H4 — Integración, QA y control, 07 de octubre de 2026.
- Final — MVP v1.0, 13 de octubre de 2026.

## Organización y documentación

- [Tablero de tareas](https://github.com/users/snxxx9/projects/1)
- [Documentación H1](docs/H1-29-09.md)
- [Documentación H2](docs/H2-30-09.md)
- [Backlog priorizado](docs/BACKLOG-H2.md)
- [Modelo ER](docs/MODELO-ER-H2.md)
- [Plan de pruebas inicial](docs/PLAN-PRUEBAS-H2.md)
- [Pruebas H3](docs/PRUEBAS-H3.md)
- [Reporte de Avance N.º 1](docs/REPORTE-AVANCE-H3.md)
- [Pruebas H4](docs/PRUEBAS-H4.md)
- [Reporte de Avance N.º 2](docs/REPORTE-AVANCE-H4.md)
- [Script de base de datos](database/schema.sql)
- [Instrucciones de ejecución para el profesor](README_PROFESOR)

## Evidencias

Las capturas correspondientes a los distintos hitos, pruebas, tablero y commits se encuentran dentro de la carpeta:

`evidencias/`

## Ejecución

Para ejecutar el proyecto y realizar una demostración completa, revisar el archivo:

`README_PROFESOR`