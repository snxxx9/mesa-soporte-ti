# Plan de pruebas inicial · H2

Este plan define qué vamos a comprobar cuando exista una versión funcional. En H2 todavía no registramos resultados porque el MVP aún no está programado.

| ID | Qué se prueba | Acción | Resultado esperado | Relación |
|---|---|---|---|---|
| CP-01 | Registrar una solicitud válida | Completar todos los campos y guardar | Se crea el ticket y aparece registrado | RF-01 |
| CP-02 | Validar campos obligatorios | Intentar guardar con un campo obligatorio vacío | No se guarda y aparece un mensaje claro | CAL-01 |
| CP-03 | Generar ID y fecha | Crear dos tickets | Ambos tienen ID distinto y fecha de creación | RF-02 |
| CP-04 | Listar solicitudes | Abrir la pantalla principal después de registrar tickets | Se muestran estado, prioridad y responsable | RF-03 |
| CP-05 | Asignar responsable | Elegir un responsable y guardar | La asignación queda guardada al volver a abrir | RF-04 |
| CP-06 | Cambiar estado | Cambiar un ticket entre estados permitidos | El nuevo estado queda guardado | RF-04 |
| CP-07 | Filtrar solicitudes | Aplicar filtros de estado, prioridad y categoría | Solo aparecen las coincidencias | RF-05 |
| CP-08 | Revisar resumen | Comparar contadores con los tickets guardados | El total y cantidades por estado coinciden | RF-06 |
| CP-09 | Comprobar persistencia | Cerrar y volver a iniciar la aplicación | Los datos siguen guardados | BD-01 |
| CP-10 | Revisar historial | Cambiar estado o responsable | Se crea un registro con fecha, campo y valores anterior/nuevo | BD-01 |

## Cómo vamos a registrar los resultados

Cuando ejecutemos las pruebas vamos a agregar:

- Estado: Aprobada o Fallida.
- Fecha.
- Quién la ejecutó.
- Evidencia.
- Defecto encontrado, si corresponde.
- Resultado del retest después de corregir.

No vamos a marcar pruebas como aprobadas antes de ejecutarlas.
