# Reporte de Avance N.º 1 · H3

Fecha: 06 de octubre de 2026

## 1. Estado general

Durante este hito nos enfocamos en construir una primera versión funcional de la Mesa de Soporte TI. El objetivo principal era llegar a un MVP v0.1 que permitiera registrar solicitudes, guardarlas en la base de datos, listarlas, asignar un responsable y cambiar su estado.

Al cierre del trabajo logramos dejar funcionando las características principales correspondientes a RF-01, RF-02, RF-03 y RF-04.

## 2. Roles del hito

Para este hito se realizó la rotación de roles definida en la planificación:

- Jeremmy Vidal: Líder de Proyecto y Control.
- Sebastian Velasco: Solución y Desarrollo.
- Felipe Garces: Datos, Calidad y Pruebas.

## 3. Avance planificado vs. real

| Actividad | Planificado | Resultado real | Estado |
|---|---|---|---|
| Preparar estructura de Flask | Crear la base de la aplicación web | Se creó la estructura con Flask, templates y archivos estáticos | Cumplido |
| Implementar RF-01 | Registrar una solicitud con sus datos principales | El formulario permite registrar solicitante, título, descripción, categoría y prioridad | Cumplido |
| Implementar RF-02 | Generar ID y fecha automáticamente | SQLite genera un ID único y registra la fecha de creación | Cumplido |
| Implementar RF-03 | Mostrar las solicitudes registradas | El listado muestra ID, título, solicitante, categoría, prioridad, estado, responsable y fecha | Cumplido |
| Implementar RF-04 | Asignar responsable y cambiar estado | Se puede asignar un técnico y cambiar entre Nuevo, En proceso, Resuelto y Cerrado | Cumplido |
| Persistencia | Mantener los datos guardados en SQLite | Los tickets siguen registrados después de reiniciar Flask | Cumplido |
| Pruebas iniciales | Ejecutar pruebas sobre las funciones principales | Se realizaron pruebas de registro, validaciones, ID, listado, responsable, estado y persistencia | Cumplido |

## 4. Problemas y bloqueos encontrados

Durante la preparación del entorno local aparecieron algunos problemas antes de comenzar el desarrollo. Git y Python no estaban disponibles inicialmente en el equipo utilizado para programar y PowerShell bloqueó la activación del entorno virtual.

Para solucionarlo se instalaron las herramientas necesarias, se creó un entorno virtual y se habilitó temporalmente la ejecución del script de activación.

También detectamos que la tabla principal puede necesitar desplazamiento horizontal cuando se muestran todas las columnas. Este problema es solamente visual y no afecta las funciones del MVP.

## 5. Decisiones tomadas

Se mantuvo la arquitectura definida en el Hito 2 utilizando Python con Flask para la lógica de la aplicación y SQLite para la persistencia de los datos.

También se decidió mantener el MVP pequeño y concentrarnos primero en las funciones RF-01 a RF-04 antes de avanzar con filtros y resumen, ya que esas funcionalidades corresponden a la siguiente etapa del proyecto.

## 6. Resultado del hito

Al finalizar el Hito 3 contamos con una versión funcional v0.1 de la Mesa de Soporte TI. Actualmente se pueden registrar tickets, almacenarlos en SQLite, visualizarlos en un listado, abrir su detalle, asignar un responsable y modificar su estado.

Las funciones desarrolladas fueron probadas de forma inicial y los datos se mantienen guardados después de reiniciar la aplicación.

El siguiente paso será continuar con la integración y las funciones restantes del proyecto, además de corregir los detalles visuales que todavía puedan mejorarse.