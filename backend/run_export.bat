@echo off
REM Ejecuta el export de dispositivos HP Web Jetadmin -> Postgres.
REM Pensado para ser invocado por el Programador de tareas de Windows.

set SCRIPT_DIR=%~dp0
call "%SCRIPT_DIR%..\venv\Scripts\activate.bat"
cd /d "%SCRIPT_DIR%"
python manage.py run_export >> "%SCRIPT_DIR%run_export.log" 2>&1
