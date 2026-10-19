# Ejecución local en Windows

Esta guía es para desarrollo. En local se ejecuta Django con `runserver` y React con Vite. No se necesita IIS ni NSSM.

## Requisitos

- Python y el entorno virtual en `venv`.
- Node.js y npm.
- PostgreSQL funcionando.
- El archivo `backend\.env` configurado.

## Primera instalación

Desde la raíz del proyecto:

```powershell
cd C:\Users\admin-c606401\Documents\hp
.\venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\venv\Scripts\python.exe backend\manage.py migrate
```

Instala las dependencias del frontend:

```powershell
cd frontend
npm install
```

Para desarrollo, `frontend\.env` puede conservar:

```ini
VITE_API_URL=/api
```

El proxy de `frontend\vite.config.js` reenvía `/api` y `/admin` a Django en `127.0.0.1:8001`.

## Iniciar la aplicación

Abre dos terminales.

### Terminal 1: backend

```powershell
cd C:\Users\admin-c606401\Documents\hp
.\venv\Scripts\python.exe backend\manage.py runserver 127.0.0.1:8001
```

### Terminal 2: frontend

```powershell
cd C:\Users\admin-c606401\Documents\hp\frontend
npm run dev
```

Abre la dirección que muestre Vite, normalmente:

```text
http://localhost:5173
```

No uses `npm run build` para el trabajo diario local. Vite actualiza la página automáticamente cuando guardas cambios.

## Cambios en el frontend

Modifica archivos dentro de `frontend\src` y guarda. Vite actualizará el navegador automáticamente.

Si cambias `frontend\.env` o `frontend\vite.config.js`, detén y vuelve a iniciar Vite:

```text
Ctrl + C
npm run dev
```

## Cambios en el backend

Si cambias archivos Python dentro de `backend`, Django normalmente reinicia el proceso automáticamente. Si no lo hace, detén y vuelve a ejecutar el comando:

```text
Ctrl + C
.\venv\Scripts\python.exe backend\manage.py runserver 127.0.0.1:8001
```

Si agregaste o cambiaste dependencias:

```powershell
.\venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Si cambiaste modelos:

```powershell
.\venv\Scripts\python.exe backend\manage.py makemigrations
.\venv\Scripts\python.exe backend\manage.py migrate
```

Si cambiaste comandos de administración, puedes ejecutarlos directamente:

```powershell
.\venv\Scripts\python.exe backend\manage.py nombre_del_comando
```

## Crear un usuario administrador

```powershell
.\venv\Scripts\python.exe backend\manage.py createsuperuser
```

## Pruebas rápidas

Comprobar la configuración de Django:

```powershell
.\venv\Scripts\python.exe backend\manage.py check
```

Ejecutar las pruebas:

```powershell
.\venv\Scripts\python.exe backend\manage.py test
```

Comprobar el frontend:

```powershell
cd frontend
npm run lint
npm run build
```

## URLs locales

```text
Frontend: http://localhost:5173
Backend:  http://127.0.0.1:8001
API:      http://localhost:5173/api/
Admin:    http://localhost:5173/admin/
```

En desarrollo, el navegador debe usar `/api` a través de Vite. No es necesario abrir el puerto 8001 al firewall.
