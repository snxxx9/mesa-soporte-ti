# Qué mostrar hoy · H1 del 29 de septiembre

Esta entrega demuestra el inicio del proyecto. Hoy no corresponde presentar una web funcionando ni una base de datos implementada.

## Abrir estos tres elementos

1. **Repositorio:** https://github.com/snxxx9/mesa-soporte-ti
2. **Tablero:** https://github.com/users/snxxx9/projects/1 — la vista “H1 · 29-09-2026 · Tareas” contiene doce tareas con responsables, fecha, prioridad y estimación.
3. **Minuta y definición H1:** https://github.com/snxxx9/mesa-soporte-ti/blob/main/docs/H1-29-09.md

La captura del tablero está en `evidencias/2026-09-29-H1-tareas-inicio.png`. La otra captura muestra responsables y fechas; la lectura de la interfaz conserva todos los datos de las doce tareas. Estas evidencias también están en el repositorio.

## Orden sugerido para explicarlo

### 1. Problema y objetivo

“Queremos ordenar las solicitudes de soporte que hoy llegan por distintos medios. La aplicación permitirá registrar cada solicitud, asignar un responsable y seguir su estado hasta cerrarla.”

### 2. Qué incluirá la aplicación

Mostrar alcance v0.1 e historias HU-01 a HU-10 en `docs/H1-29-09.md`: registro, identificador y fecha, listado, asignación y estados, filtros, resumen, persistencia, cambios relevantes y validaciones.

Explicar que funciones como chat, notificaciones o una aplicación móvil quedan fuera del alcance inicial.

### 3. Organización inicial

Distribución propuesta para hoy: Sebastian Velasco coordina; Felipe Garces se encarga de solución y desarrollo; Jeremmy Vidal, de datos, calidad y pruebas. Mostrar la matriz de rotación y el calendario preliminar de hitos. El equipo debe revisar y confirmar esta distribución antes de presentarla como acordada.

### 4. Bocetos y datos

Abrir `docs/BOCETOS.html` desde la carpeta descargada, con doble clic. Mostrar las tres pantallas dibujadas y el esquema conceptual. Aclarar que es un boceto estático; los botones no guardan datos.

Propuesta inicial: navegador → Python/Flask → SQLite. Cuatro entidades conceptuales: usuario, ticket, categoría y cambio de ticket. El diseño detallado y script corresponden a H2.

### 5. Evidencia de inicio

Mostrar repositorio, tablero, captura fechada y minuta. Las tareas de preparar repositorio, tablero y evidencia están terminadas; las revisiones del material por el equipo permanecen pendientes hasta realizarlas.

## Antes de la revisión docente

- Los tres integrantes revisan nombres, reparto de roles, alcance y bocetos. Registrar ajustes reales en la minuta y actualizar las tarjetas correspondientes.
- Repositorio y tablero son privados: abrirlos con la sesión del propietario para mostrarlos. Para que el profesor o compañeros accedan por su cuenta, habrá que agregar sus cuentas; todavía no se han proporcionado esos usuarios.
- Registrar la validación y observaciones del profesor después de la revisión, no antes.

## Qué queda para otro día

No se ha realizado H2: línea base definitiva, costos, modelo ER detallado, script de base de datos y plan de pruebas. Tampoco se ha programado la aplicación, instalado Flask ni ejecutado pruebas funcionales.

Las herramientas para más adelante se explican en `docs/ENTORNO.md`. Hoy basta con revisar los archivos y los enlaces de GitHub.
