# Biblioteca Aurora - Tarea 4: pruebas automatizadas con Selenium

Aplicación web individual de biblioteca con inicio de sesión y operaciones CRUD para ejecutar pruebas automatizadas en Selenium/Python. La interfaz, los datos de demostración y los criterios están en español.

## Requisitos

- Python 3.10 o posterior.
- Google Chrome instalado. Selenium Manager localiza o descarga el controlador compatible al ejecutar las pruebas.
- Dependencias de `requirements.txt`.

## Instalación y ejecución

En Windows PowerShell, desde la raíz del proyecto:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Abre `http://127.0.0.1:5000`. Acceso de demostración: usuario `demo`, contraseña `Selenium123`. La base SQLite se crea en `instance/biblioteca.db` al iniciar.

## Ejecutar la suite Selenium

```powershell
python -m pytest
```

La suite levanta una instancia temporal de la aplicación y Chrome en modo headless. Cada escenario guarda una captura en `evidencias/capturas/` y `pytest-html` genera el reporte autocontenido en `evidencias/reporte.html`, con las capturas dentro del reporte.

Para ver el navegador durante una grabación local:

```powershell
$env:HEADLESS = "false"
python -m pytest -vv
Remove-Item Env:HEADLESS
```

### Grabar el video demostrativo en vivo

1. Abre OBS Studio y crea una escena que muestre la ventana de PowerShell y la ventana de Chrome (puedes usar Captura de ventana o Captura de pantalla).
2. Inicia la grabación en OBS antes de correr las pruebas.
3. En PowerShell, desde la carpeta del proyecto, activa el entorno y ejecuta:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   $env:HEADLESS = "false"
   python -m pytest -vv
   Remove-Item Env:HEADLESS
   ```

4. Espera a que la consola muestre `17 passed` y detén la grabación.
5. Abre `evidencias/reporte.html` para mostrar el reporte y las capturas automáticas. OBS guarda el video en la ruta que tenga configurada en sus ajustes.

Las pruebas inician su propio servidor local temporal: no hace falta ejecutar `python app.py` en otra consola para la demostración de Selenium. Para una demostración manual de la aplicación, ejecuta `python app.py` y abre `http://127.0.0.1:5000` en Chrome.

Se automatizan 17 escenarios sobre cinco historias: autenticación; alta; consulta/búsqueda; edición; eliminación. Cada historia incluye camino feliz, escenario negativo y límite. Los escenarios están en `tests/test_acceptance.py`, y sus criterios están en `docs/historias-de-usuario.md`.

## Entregables locales

- Código de la aplicación: `app.py`, `templates/`, `static/`.
- Código de pruebas Selenium: `tests/`.
- Historias y criterios de aceptación/rechazo: `docs/historias-de-usuario.md`.
- CSV de importación de cinco historias en Jira: `docs/historias-jira.csv`.
- Reporte y capturas: `evidencias/` (se generan al ejecutar la suite).

## Publicación requerida por la consigna

El código está listo para publicarse en un repositorio GitHub/Azure y las historias tienen un CSV listo para importar a Jira. Para cumplir la parte pública, publica las historias en un tablero Jira/Azure DevOps y sube una grabación continua de la ejecución a YouTube u OneDrive. No se incluyen enlaces ficticios ni se presenta una publicación local como si fuera pública.

Guion sugerido para el video: mostrar la biblioteca, iniciar sesión, agregar/editar/buscar/eliminar un libro; ejecutar `python -m pytest` con `HEADLESS=false`; mostrar el resultado de las 17 pruebas y abrir el reporte HTML con capturas.
