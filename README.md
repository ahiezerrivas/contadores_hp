# Proyecto HP - Contadores de dispositivos

Aplicación para importar, almacenar y visualizar contadores de impresoras HP provenientes de HP Web Jetadmin y archivos Excel mensuales.

- **Backend:** Django + Django REST Framework + PostgreSQL
- **Frontend:** React + Vite + TailwindCSS
- **Origen de datos:** SQL Server (HP Web Jetadmin, instancia `HPWJA`)

---

## Estructura

```
hp/
├── backend/              # API y lógica Django
│   ├── manage.py
│   ├── config/           # Configuración del proyecto
│   ├── devices/          # Modelos, comandos, vistas
│   └── .env              # Variables de entorno (no versionar)
├── frontend/             # Aplicación React + Vite
├── venv/                 # Entorno virtual Python
├── export_dispositivos.py
└── README.md
```

---

## Instalación

Para desarrollo local, consulta [README_LOCAL.md](README_LOCAL.md).

Para ejecutar la aplicación de forma permanente con IIS y NSSM, consulta [README_IIS_NSSM.md](README_IIS_NSSM.md).

### 1. Backend

```powershell
# Desde la raíz del proyecto
python -m venv venv
.\venv\Scripts\activate
pip install -r backend\requirements.txt
```

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

---

## Variables de entorno

Crea el archivo `backend/.env` con al menos:

```ini
SECRET_KEY=tu-clave-django
DEBUG=True
DB_NAME=hp_dispositivos
DB_USER=hp_app
DB_PASSWORD=hp_app_pass
DB_HOST=localhost
DB_PORT=5432
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

> **Nota:** `backend/.env` ya está ignorado por Git.

---

## Comandos útiles

```powershell
# Aplicar migraciones
python backend\manage.py migrate

# Crear superusuario
python backend\manage.py createsuperuser

# Iniciar backend
python backend\manage.py runserver

# Iniciar frontend (en otra terminal)
cd frontend
npm run dev
```

---

## Extraer / respaldar la base de datos

### Opción A: Extraer dispositivos desde HP Web Jetadmin a PostgreSQL

Para traer los dispositivos de HPWJA y guardarlos en la base de datos de Django:

```powershell
.\venv\Scripts\activate
python backend\manage.py run_export --force
```

> `--force` fuerza la ejecución sin importar la hora programada.

---



### Opción C: Backup de PostgreSQL a `.sql` con `pg_dump`

> **Requisito:** `pg_dump` viene con PostgreSQL. Si PowerShell dice que no reconoce el comando, significa que `pg_dump` no está en el `PATH` o no está instalado.

Si no tienes PostgreSQL en este equipo, usa la **Opción B** arriba.

Si lo tienes instalado, localiza `pg_dump.exe` en una ruta similar a:

```
C:\Program Files\PostgreSQL\16\bin\pg_dump.exe
```

Ajusta el comando con la ruta completa:

```powershell
 & "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -h localhost -U postgres -d hp_dispositivos -f "db_backup.sql"
```

Si no sabes dónde está PostgreSQL, búscalo con PowerShell:

```powershell
Get-ChildItem -Path C:\, D:\, E:\ -Filter pg_dump.exe -Recurse -ErrorAction SilentlyContinue
```

---

### Importar / restaurar un backup

#### Restaurar desde un archivo `.sql` (PostgreSQL)

Si ya tienes un archivo `.sql` generado con `pg_dump` (por ejemplo `db_backup_2026-08-03-1118.sql`), restáuralo con `psql`:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -U postgres -d hp_dispositivos -f "db_backup_2026-08-03-1118.sql"
```

Si la base de datos no existe, créala antes:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\createdb.exe" -h localhost -U postgres hp_dispositivos
```
```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -c "CREATE ROLE hp_app WITH LOGIN PASSWORD 'hp_app_pass';"
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE hp_dispositivos TO hp_app;"
```


#### Restaurar desde un archivo `.json` (Django)

Si hiciste el backup con `dumpdata`, importa los datos con `loaddata`:

```powershell
.\venv\Scripts\activate
python backend\manage.py loaddata db_backup_2026-08-03.json
```

> **Nota:** Si quieres empezar desde cero antes de restaurar, borra los datos actuales con:
> ```powershell
> python backend\manage.py flush
> ```

---

## Importar contadores mensuales desde Excel

Mira el archivo `backend/README_import_counters.md` para el flujo completo.

```powershell
.\venv\Scripts\activate
python backend\manage.py import_counters "Contador de Pagina Torre Junio del 01 al 30.xlsx" --dry-run
python backend\manage.py import_counters "Contador de Pagina Torre Junio del 01 al 30.xlsx"
```

---

## Notas

- El archivo `dispositivos.txt` puede generarse también con el script `export_dispositivos.py` (sin depender de Django):

  ```powershell
  .\venv\Scripts\python export_dispositivos.py
  ```

- Para programar la extracción automática se puede usar `backend/run_export.bat` con el Programador de tareas de Windows.


npx vite --host

## Despliegue en Windows con IIS

Para producción, no uses `runserver` ni `vite --host`. IIS sirve el frontend compilado y reenvía `/api` hacia Django ejecutándose con Waitress.

### Preparar el proyecto

Desde PowerShell en la raíz del proyecto:

```powershell
.\venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\venv\Scripts\python.exe backend\manage.py migrate
.\venv\Scripts\python.exe backend\manage.py collectstatic --noinput
cd frontend
npm install
npm run build
```

El frontend listo para IIS queda en `frontend\dist`. El archivo `frontend\public\web.config` se copia automáticamente a esa carpeta y configura las rutas de React y el proxy de `/api`.

### Configurar IIS

1. Instala IIS.
2. Instala **URL Rewrite** y **Application Request Routing (ARR)** mediante sus instaladores MSI independientes. Microsoft retiró Web Platform Installer en 2022, por lo que no debe usarse esa herramienta.
3. En IIS Manager, habilita **Proxy** en `Application Request Routing Cache > Server Proxy Settings`.
4. Crea un sitio cuyo directorio físico sea la ruta absoluta a `frontend\dist`.
5. Configura el binding HTTP, por ejemplo en el puerto `80`.
6. En `backend\.env`, configura `DEBUG=False` y `ALLOWED_HOSTS` con el nombre o IP del servidor.

Las páginas oficiales de descarga son [URL Rewrite](https://www.iis.net/downloads/microsoft/url-rewrite) y [Application Request Routing](https://www.iis.net/downloads/microsoft/application-request-routing). Si una página redirige o no ofrece el instalador, busca en Microsoft Download Center los instaladores x64 `rewrite_amd64_en-US.msi` y `requestRouter_amd64.msi`.

### Ejecutar Django como servicio

Instala NSSM y crea un servicio apuntando a:

```text
Application:  C:\ruta\hp\venv\Scripts\python.exe
Arguments:    -m waitress --listen=10.0.114.27:8001 config.wsgi:application
Startup dir:  C:\ruta\hp\backend
```

Inicia el servicio y verifica primero `http://10.0.114.27:8001/api/`. Después accede al sitio mediante IIS. Si el puerto debe ser accesible desde otra computadora, permite TCP 8001 en el Firewall de Windows.



