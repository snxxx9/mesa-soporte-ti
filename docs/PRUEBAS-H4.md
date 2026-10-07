# Pruebas funcionales e integración · H4

Fecha: 07 de octubre de 2026

Durante el Hito 4 realizamos pruebas sobre las nuevas funciones RF-05 y RF-06 y también comprobamos que siguieran funcionando correctamente junto con las funciones desarrolladas anteriormente.

## Resultados de las pruebas

| Caso | Prueba realizada | Resultado |
|---|---|---|
| CP-H4-01 | Filtrar solicitudes por estado | OK |
| CP-H4-02 | Filtrar solicitudes por prioridad | OK |
| CP-H4-03 | Filtrar solicitudes por categoría | OK |
| CP-H4-04 | Utilizar más de un filtro al mismo tiempo | OK |
| CP-H4-05 | Limpiar los filtros y volver al listado completo | OK |
| CP-H4-06 | Mostrar total de solicitudes y cantidad por estado | OK |
| CP-H4-07 | Registrar un ticket y actualizar automáticamente el resumen | OK |
| CP-H4-08 | Cambiar el estado de un ticket y actualizar el resumen | OK |
| CP-H4-09 | Reiniciar la aplicación y mantener la información almacenada | OK |
| CP-H4-10 | Verificar la corrección visual de la tabla de tickets | OK |

## Prueba de RF-05

Se probaron los filtros por estado, prioridad y categoría. Al seleccionar un filtro, el listado mostró solamente las solicitudes que cumplían con la condición seleccionada.

También se realizaron pruebas combinando filtros y posteriormente utilizando la opción “Limpiar filtros” para volver al listado completo.

## Prueba de RF-06

El sistema muestra un resumen con el total de solicitudes y la cantidad de tickets que se encuentran en los estados Nuevo, En proceso, Resuelto y Cerrado.

Durante la prueba inicial existían dos tickets, por lo que el resumen mostró un total de 2 solicitudes.

Posteriormente se registró un tercer ticket. El contador total aumentó automáticamente de 2 a 3 y el contador de tickets nuevos también aumentó.

## Prueba de integración

Para comprobar que las funciones de los hitos anteriores siguieran funcionando junto con RF-05 y RF-06, se creó un nuevo ticket y posteriormente se le asignó un responsable y se cambió su estado desde Nuevo a Resuelto.

Después del cambio, el resumen quedó de la siguiente manera:

- Total: 3
- Nuevo: 1
- En proceso: 1
- Resuelto: 1
- Cerrado: 0

Esto permitió comprobar que el cambio de estado de un ticket también actualiza correctamente el resumen general.

## Persistencia

Se detuvo completamente la aplicación utilizando Ctrl + C y posteriormente se volvió a ejecutar con `python app.py`.

Después de reiniciar Flask, los tres tickets continuaban almacenados y el resumen mantenía los mismos valores, por lo que la persistencia mediante SQLite continuó funcionando correctamente.

## Corrección realizada

Durante el Hito 3 habíamos detectado que la tabla principal podía provocar desplazamiento horizontal de toda la página cuando el espacio disponible era reducido.

Durante el Hito 4 se corrigió este detalle ajustando la estructura de la tabla y su CSS. Después de la modificación se volvió a revisar la pantalla principal y la tabla se mostró correctamente sin provocar el desplazamiento horizontal general de la página.

## Resultado general

Las pruebas realizadas durante el Hito 4 fueron satisfactorias y no se detectaron errores funcionales bloqueantes.

RF-05 y RF-06 quedaron integrados con las funciones desarrolladas anteriormente y la aplicación mantuvo correctamente el registro, listado, responsables, estados y persistencia de los tickets.