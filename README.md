# Mesa de Soporte TI

Proyecto académico de la Evaluación 3. Aplicación web pequeña para registrar y gestionar solicitudes de soporte técnico desde su creación hasta su cierre.

**Equipo:** Sebastian Velasco, Felipe Garces y Jeremmy Vidal.

**Estado actual:** preparación del H1 del 29 de septiembre de 2026. La aplicación todavía no está implementada. No existen pruebas de funcionamiento ni una base de datos de producción en esta etapa.

## Documentación inicial

- [H1: definición, requisitos, roles, calendario y minuta](docs/H1-29-09.md).
- [Tareas preparadas para GitHub Projects](docs/BACKLOG.md).
- [Bocetos de pantallas y modelo conceptual](docs/BOCETOS.html): abrir en un navegador.
- [Herramientas y entorno de desarrollo](docs/ENTORNO.md).

## Propuesta técnica

Python + Flask, páginas HTML/CSS y SQLite. Se propone una sola aplicación que recibe formularios, aplica validaciones y guarda los datos en una base relacional. La elección se revisará en H2 con los tres roles.

## Ejecución

Por ahora solo hay documentación y bocetos estáticos. Abrir `docs/BOCETOS.html` para ver el diseño inicial. Las instrucciones de instalación, creación de base de datos y ejecución se incorporarán al implementar la primera versión en H3.

## Trabajo por etapas

| Hito | Fecha | Resultado esperado |
|---|---|---|
| H1 | 29-09-2026 | Inicio, alcance v0.1, requisitos, tablero, repositorio, roles y bocetos |
| H2 | 30-09-2026 | Planificación v1.0, costos, horas, modelo ER, script inicial y plan de pruebas |
| H3 | 06-10-2026 | Versión funcional con RF-01 a RF-04 y reporte de avance 1 |
| H4 | 07-10-2026 | Filtros, resumen, integración, pruebas y reporte de avance 2 |
| Final | 13-10-2026 | MVP v1.0, informe, evidencias y demostración |

Las versiones se registrarán cuando exista el resultado correspondiente. Cada integrante debe revisar y registrar sus propios aportes. No se atribuirán cambios a personas que no los hayan realizado o revisado.

## Evidencias

Conservar las capturas del tablero por fecha, minutas, cambios reales y resultados de pruebas en `evidencias/`. Los bocetos son propuestas, no evidencia de funcionalidades terminadas. La validación del docente se registra solo cuando ocurra.
