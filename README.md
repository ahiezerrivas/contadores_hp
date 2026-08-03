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

### Opción B: Exportar datos de Django a JSON (recomendado si no tienes pg_dump)

Este comando no requiere instalar nada adicional. Crea un respaldo portable de los datos manejados por Django:

```powershell
.\venv\Scripts\activate
$fecha = Get-Date -Format "yyyy-MM-dd"; python backend\manage.py dumpdata --indent 2 > db_backup_$fecha.json
```

> **Nota:** `dumpdata` usa la base de datos configurada en `backend/.env`. Es ideal para respaldar/restaurar datos en cualquier entorno.

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
$fecha = Get-Date -Format "yyyy-MM-dd-HHmm"; & "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -h localhost -U postgres -d hp_dispositivos -f "db_backup_$fecha.sql"
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
