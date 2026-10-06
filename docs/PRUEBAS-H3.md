# Pruebas funcionales · H3

Fecha: 06 de octubre de 2026

Durante este hito realizamos pruebas sobre las funciones principales del MVP v0.1. El objetivo fue comprobar que las solicitudes se puedan registrar, guardar y consultar correctamente antes de continuar con las funciones restantes.

| ID | Prueba | Resultado esperado | Resultado obtenido | Estado |
|---|---|---|---|---|
| CP-01 | Registrar una solicitud válida | El ticket se guarda y aparece en el listado | El ticket fue registrado correctamente | OK |
| CP-02 | Validar campos obligatorios | No debe permitir guardar si faltan datos | El formulario bloqueó el registro al dejar campos vacíos | OK |
| CP-03 | Generar ID y fecha | Cada ticket debe tener un ID distinto y fecha de creación | Se generaron los ID 1 y 2 con fechas diferentes | OK |
| CP-04 | Listar solicitudes | Deben aparecer los tickets guardados con sus datos principales | Los dos tickets aparecen correctamente en el listado | OK |
| CP-05 | Asignar responsable | El responsable debe quedar guardado | Se asignó "Tecnico de prueba" al ticket 1 | OK |
| CP-06 | Cambiar estado | El nuevo estado debe mantenerse guardado | El ticket 1 cambió de Nuevo a En proceso | OK |
| CP-09 | Comprobar persistencia | Los datos deben seguir guardados al reiniciar la aplicación | Después de reiniciar Flask los tickets siguieron registrados | OK |

## Observaciones

Durante las pruebas no encontramos errores que impidieran utilizar las funciones principales del MVP v0.1. Se detectó un detalle visual en el listado, ya que al mostrar muchas columnas la tabla puede necesitar desplazamiento horizontal. Este punto no afecta el funcionamiento y puede corregirse durante la etapa de integración.

También tuvimos un bloqueo inicial al preparar el entorno de desarrollo, porque el equipo no tenía instalados Git y Python y PowerShell bloqueó inicialmente la activación del entorno virtual. El problema se resolvió instalando las herramientas necesarias y habilitando temporalmente la ejecución del entorno virtual.