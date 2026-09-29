# Herramientas para trabajar

## Propuesta

Usar **Visual Studio Code + Python + Flask + SQLite + Git/GitHub**. El navegador ya instalado sirve para probar las pantallas. Esta es una propuesta técnica para revisar en H2, no una tecnología impuesta por el docente.

| Herramienta | Para qué sirve | Situación verificada el 29-09-2026 |
|---|---|---|
| Visual Studio Code | Abrir y editar el proyecto. | Encontrado en la instalación del usuario. |
| Python | Ejecutar la lógica de la aplicación. | Hay Python 3.12.14 en las herramientas de esta sesión; no se encontró `python` o `py` en PATH. |
| Flask | Recibir formularios y mostrar las páginas. | No instalado en el Python comprobado; se instalará en un entorno del proyecto. |
| SQLite | Guardar datos relacionales en un archivo. | Disponible mediante sqlite3 en el Python comprobado. No requiere servidor separado. |
| Git | Guardar el historial del proyecto. | Disponible en las herramientas de esta sesión. |
| GitHub y GitHub Projects | Compartir código y gestionar tareas. | Usuario eligió ambas herramientas; requieren sesión en la cuenta del equipo. |
| Chrome/Edge | Abrir y probar la web. | Ambos aparecen instalados. |

La disponibilidad de Python y Git dentro de esta sesión no garantiza que los compañeros puedan ejecutarlos desde sus propias terminales. Antes de H3 se comprobará el entorno de cada equipo.

## Qué preparar antes de programar

1. Mantener Visual Studio Code. Instalar su extensión oficial Python de Microsoft para facilitar ejecución y depuración.
2. Instalar una versión mantenida de Python 3 compatible con Flask desde python.org. Preparar la misma versión principal/secundaria para los tres equipos y registrar la elegida. No es necesario instalar Python para revisar los documentos de H1.
3. Comprobar Git en la terminal de cada integrante; instalar Git for Windows si no está disponible. Configurar cada uno su nombre y correo de autor, sin compartir credenciales.
4. Crear un entorno `.venv` dentro del proyecto e instalar Flask allí. Las versiones exactas se guardarán cuando configuremos el entorno en H2.
5. Usar SQLite a través de Python. No hace falta instalar MySQL, SQL Server, XAMPP ni un servidor de base de datos para esta propuesta.
6. Compartir usuarios GitHub del equipo para dar acceso y asociar tareas. El profesor debe poder acceder a los enlaces de las evidencias.

## Comandos previstos, todavía no ejecutados como instalación

En la carpeta del proyecto, una vez instalado Python:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install Flask
```

Se utiliza el ejecutable del entorno directamente para no depender de activar scripts en PowerShell. Más adelante se agregará un archivo de dependencias con las versiones comprobadas e instrucciones reproducibles para el resto del equipo.

## Cómo funcionará la aplicación

Abrirás una dirección local en el navegador. Flask ejecutará la aplicación en el computador, y SQLite guardará los datos en un archivo local. El código y scripts estarán en Git; el entorno `.venv`, credenciales y base de datos de uso local quedan fuera del repositorio. El script permitirá recrear datos ficticios para las demostraciones.

## Referencias oficiales verificadas

- Flask, instalación y entornos virtuales: https://flask.palletsprojects.com/en/stable/installation/
- Python, sqlite3: https://docs.python.org/3/library/sqlite3.html
- Python en Visual Studio Code: https://code.visualstudio.com/docs/languages/python
- GitHub Projects: https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects
- Descargas oficiales de Python: https://www.python.org/downloads/windows/
- Git para Windows: https://git-scm.com/downloads/win
