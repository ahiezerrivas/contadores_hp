# Despliegue en Windows con IIS y NSSM

Esta guía explica cómo ejecutar el frontend React con IIS y el backend Django con Waitress administrado por NSSM.

## Rutas del proyecto

Ajusta estas rutas si el proyecto se mueve:

```text
Proyecto:       C:\Users\admin-c606401\Documents\hp
Backend:        C:\Users\admin-c606401\Documents\hp\backend
Frontend build: C:\Users\admin-c606401\Documents\hp\frontend\dist
Python:         C:\Users\admin-c606401\Documents\hp\venv\Scripts\python.exe
Servicio:       HPBackend
API:            10.0.114.27:8001
Sitio IIS:      10.0.114.27:5173
```

## Primera instalación

### 1. Preparar Django

Abre PowerShell como administrador o con el usuario que administra el proyecto:

```powershell
cd C:\Users\admin-c606401\Documents\hp
.\venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\venv\Scripts\python.exe backend\manage.py migrate
.\venv\Scripts\python.exe backend\manage.py collectstatic --noinput
```

En `backend\.env` usa una configuración de producción, especialmente:

```ini
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,10.0.114.27
```

### 2. Compilar React

La variable `frontend\.env` debe usar la ruta relativa:

```ini
VITE_API_URL=/api
```

Compila el frontend:

```powershell
cd C:\Users\admin-c606401\Documents\hp\frontend
npm install
npm run build
```

IIS debe tener como directorio físico:

```text
C:\Users\admin-c606401\Documents\hp\frontend\dist
```

El archivo `dist\web.config` configura las rutas de React y reenvía `/api` hacia Django.


colocar el dist en disco c

### 3. Instalar NSSM

Descarga NSSM desde [nssm.cc](https://nssm.cc/download), extrae la versión de 64 bits, por ejemplo en:

```text
C:\nssm
```

Crea el servicio:

```powershell
C:\nssm\win64\nssm.exe install HPBackend
```

En la ventana de NSSM configura:

```text
Application path:
C:\Users\admin-c606401\Documents\hp\venv\Scripts\python.exe

Arguments:
-m waitress --listen=10.0.114.27:8001 config.wsgi:application

Startup directory:
C:\Users\admin-c606401\Documents\hp\backend
```

instalar waitress==3.0.2 en el venv del proyecto

Después ejecuta:

```powershell
Set-Service HPBackend -StartupType Automatic
Start-Service HPBackend
Get-Service HPBackend
```

El estado esperado es `Running`.

### 4. Firewall

Si otros equipos accederán directamente al puerto `8001`, permite TCP 8001:

```powershell
New-NetFirewallRule `
  -DisplayName "HP Django API 8001" `
  -Direction Inbound `
  -Protocol TCP `
  -LocalPort 8001 `
  -Action Allow
```

## Actualizar el frontend

Cuando cambies React, CSS o cualquier archivo de `frontend\src`:

```powershell
cd C:\Users\admin-c606401\Documents\hp\frontend
npm run build
```

El build reemplaza `frontend\dist`. Normalmente no es necesario reiniciar IIS, pero puedes hacerlo si el navegador sigue mostrando archivos antiguos:

```powershell
iisreset
```

Después usa `Ctrl + F5` en el navegador.

## Actualizar el backend

Cuando cambies código Python en `backend`:

```powershell
cd C:\Users\admin-c606401\Documents\hp
Restart-Service HPBackend
```

El reinicio es necesario porque el servicio Waitress mantiene el proceso Python en memoria.

Si agregaste o cambiaste dependencias:

```powershell
cd C:\Users\admin-c606401\Documents\hp
.\venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Restart-Service HPBackend
```

Si cambiaste modelos o creaste migraciones:

```powershell
cd C:\Users\admin-c606401\Documents\hp
.\venv\Scripts\python.exe backend\manage.py makemigrations
.\venv\Scripts\python.exe backend\manage.py migrate
Restart-Service HPBackend
```

Si cambiaste archivos estáticos de Django o el panel administrativo:

```powershell
.\venv\Scripts\python.exe backend\manage.py collectstatic --noinput
Restart-Service HPBackend
```

## Comprobar el servicio

```powershell
Get-Service HPBackend
Invoke-WebRequest http://10.0.114.27:8001/api/ -UseBasicParsing
```

Una respuesta `401`, `403`, `404` o JSON confirma que Django responde. La aplicación completa se abre desde el sitio configurado en IIS:

```text
http://10.0.114.27:5173
```

## Ver errores del servicio

Si el servicio no inicia, revisa la configuración de NSSM:

```powershell
C:\nssm\win64\nssm.exe get HPBackend Application
C:\nssm\win64\nssm.exe get HPBackend AppParameters
C:\nssm\win64\nssm.exe get HPBackend AppDirectory
```

También puedes ejecutar temporalmente el comando en una consola para ver el error directamente:

```powershell
cd C:\Users\admin-c606401\Documents\hp\backend
..\venv\Scripts\python.exe -m waitress --listen=10.0.114.27:8001 config.wsgi:application
```

## Comandos del servicio

```powershell
Start-Service HPBackend
Stop-Service HPBackend
Restart-Service HPBackend
Set-Service HPBackend -StartupType Automatic
```
