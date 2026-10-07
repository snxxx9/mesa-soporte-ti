# Reporte de Avance N.º 2 · H4

Fecha: 07 de octubre de 2026

## Estado general del proyecto

Durante el Hito 4 trabajamos principalmente en la integración final de las funciones pendientes del MVP y en la revisión general del sistema.

En esta etapa implementamos RF-05 y RF-06, correspondientes a los filtros de solicitudes y al resumen de tickets por estado. También realizamos pruebas de integración para comprobar que estas nuevas funciones siguieran trabajando correctamente junto con el registro de tickets, asignación de responsables, cambio de estados y persistencia en SQLite.

## Roles del Hito 4

Durante este hito trabajamos de forma conjunta en la integración y revisión del sistema, manteniendo la participación de los tres integrantes en las tareas de desarrollo, control y pruebas.

## Avance planificado vs. avance real

| Actividad | Planificado | Resultado real | Estado |
|---|---|---|---|
| Implementar RF-05 | Agregar filtros por estado, prioridad y categoría | Los tres filtros quedaron funcionando correctamente | Cumplido |
| Implementar RF-06 | Mostrar total de solicitudes y totales por estado | Se agregó un resumen con Total, Nuevo, En proceso, Resuelto y Cerrado | Cumplido |
| Integrar funciones del MVP | Mantener funcionando RF-01 a RF-06 de forma conjunta | Las funciones quedaron integradas correctamente | Cumplido |
| Ejecutar pruebas funcionales | Probar filtros, resumen y funciones anteriores | Se realizaron pruebas funcionales y de integración | Cumplido |
| Revisar persistencia | Comprobar que la información siga almacenada | Los datos se mantuvieron después de reiniciar Flask | Cumplido |
| Realizar correcciones | Corregir problemas detectados durante el desarrollo | Se corrigió el problema visual de la tabla | Cumplido |
| Registrar cambio o imprevisto | Documentar una situación que requiriera ajuste | Se tomó el problema de desplazamiento horizontal de la tabla y se corrigió | Cumplido |

## RF-05 – Filtros

Se implementaron filtros para facilitar la búsqueda de solicitudes.

Actualmente el sistema permite filtrar los tickets por:

- Estado.
- Prioridad.
- Categoría.

También se pueden combinar filtros y utilizar la opción “Limpiar filtros” para volver a mostrar todas las solicitudes.

Durante las pruebas los filtros mostraron correctamente solamente los tickets que cumplían con los criterios seleccionados.

## RF-06 – Resumen de solicitudes

Se agregó un resumen en la pantalla principal con los siguientes valores:

- Total de solicitudes.
- Nuevo.
- En proceso.
- Resuelto.
- Cerrado.

El resumen se actualiza automáticamente cuando se registra un nuevo ticket o cuando cambia el estado de una solicitud.

## Pruebas de integración

Durante este hito también se realizaron pruebas para comprobar que RF-05 y RF-06 no afectaran las funciones desarrolladas anteriormente.

Se creó un nuevo ticket, se asignó un responsable y se cambió su estado a Resuelto.

Después del cambio, el resumen se actualizó correctamente y mostró:

- Total: 3
- Nuevo: 1
- En proceso: 1
- Resuelto: 1
- Cerrado: 0

También se reinició la aplicación y se comprobó que los tickets y los valores del resumen continuaran almacenados.

## Cambio o imprevisto tratado

Durante el Hito 3 habíamos detectado un problema visual en la tabla principal de tickets.

Cuando la aplicación se utilizaba en una ventana con menor espacio disponible, la tabla podía provocar un desplazamiento horizontal de toda la página.

Durante el Hito 4 decidimos tratar este problema como un ajuste de interfaz. Se modificó la estructura de la tabla y los estilos CSS para controlar mejor su comportamiento.

Después de realizar la corrección se volvió a revisar la pantalla principal y el problema dejó de afectar la navegación general de la página.

Este cambio no modificó el alcance funcional del proyecto ni generó retrasos importantes en el cronograma.

## Decisiones tomadas

Durante el Hito 4 decidimos mantener la estructura actual de Flask y SQLite, ya que había funcionado correctamente durante los hitos anteriores.

También decidimos mantener RF-05 y RF-06 dentro de la pantalla principal para que la información importante y las opciones de búsqueda estuvieran disponibles desde un mismo lugar.

Para la corrección visual se optó por modificar solamente la estructura y estilos de la tabla, evitando cambios innecesarios en la lógica del sistema.

## Resultado del Hito 4

El resultado general del Hito 4 fue satisfactorio.

RF-05 y RF-06 quedaron implementados y funcionando correctamente, se realizaron pruebas de integración, se volvió a comprobar la persistencia de los datos y se corrigió el principal detalle visual detectado anteriormente.

Con esto el sistema queda mucho más cercano a la versión final del proyecto y las funciones principales definidas entre RF-01 y RF-06 se encuentran integradas.