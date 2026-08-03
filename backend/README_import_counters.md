# Importar contadores mensuales (Excel)

Este comando carga los reportes mensuales de "Contador de Pagina" (Torre / Oficina)
al modelo `MonthlyCounterEntry`, visible y editable desde el admin de Django
(`/admin/devices/monthlycounterentry/`).

## Requisitos

- Backend corriendo con el venv activo.
- El paquete `openpyxl` instalado (ya esta en `backend/requirements.txt`).

```powershell
venv\Scripts\pip.exe install -r backend\requirements.txt
```

## Columnas esperadas en el Excel

La primera fila del archivo debe tener estos encabezados (en cualquier orden):

```
Region | Nombre Oficina | Piso | Nombre de Host Sede | Asignada o Ubicacion |
DisplayName | IPv4Address | SerialNumber | Contador del Mes Anterior |
Contador Semana 1 | Contador Final Semana 1 | Contador Semana 2 |
Contador Final Semana 2 | Contador Semana 3 | Contador Final Semana 3 |
Contador Semana 4 | Contador Final Semana 4 | Contador Semana 5 |
Contador Final Semana 5 | Contador Mensual | Equipos con contadores en 0 |
Fecha | Observaciones | Status Impresora
```

El comando detecta las columnas por nombre (ignora mayusculas/acentos), asi que
no importa el orden en que vengan en el archivo.

## Uso basico

Desde la raiz del proyecto (`hp/`), con el venv activo:

```powershell
python backend\manage.py import_counters "Contador de Pagina Torre Julio del 01 al 31.xlsx"
python backend\manage.py import_counters "Contador de Pagina Oficina Julio del 01 al 31.xlsx"
```

Puedes pasar una ruta relativa (si el archivo esta en `hp/`) o una ruta absoluta
a cualquier carpeta donde tengas los Excel guardados.

## Probar sin guardar nada (`--dry-run`)

Siempre es buena idea correr primero con `--dry-run` para ver cuantas filas
se detectan antes de tocar la base de datos:

```powershell
python backend\manage.py import_counters "archivo.xlsx" --dry-run
```

Salida esperada:

```
[dry-run] 51 filas se importarian, 0 filas omitidas (vacias).
```

## Cargar meses anteriores

El periodo (columna `Fecha`) se toma automaticamente del Excel (ej. `jun-26`).
Si el archivo no tiene la columna `Fecha` bien poblada, o quieres forzar el mes
manualmente, usa `--period`:

```powershell
python backend\manage.py import_counters "Contador de Pagina Torre Mayo.xlsx" --period may-26
```

Tambien puedes forzar el valor de `Region` para todo el archivo (util si el
Excel no trae esa columna, o para renombrarla):

```powershell
python backend\manage.py import_counters "archivo.xlsx" --region Torre
```

Si el archivo tiene varias hojas y necesitas una en especifico:

```powershell
python backend\manage.py import_counters "archivo.xlsx" --sheet "Hoja1"
```

## Re-importar sin duplicar

El comando identifica cada fila por `(SerialNumber, Fecha)` si hay numero de
serie, o por `(IPv4Address, Fecha)` si no lo hay. Si vuelves a importar el
mismo archivo (o una version corregida), las filas existentes se **actualizan**
en vez de duplicarse.

## Flujo recomendado para cargar meses anteriores

1. Copia los archivos `.xlsx` de meses anteriores a una carpeta local (pueden
   quedarse en `hp/` o en cualquier otra ruta).
2. Corre `--dry-run` sobre cada archivo para confirmar el numero de filas.
3. Corre el import real, uno por archivo (Torre y Oficina son archivos
   separados, hay que importarlos ambos):

```powershell
python backend\manage.py import_counters "Contador de Pagina Torre Junio del 01 al 30.xlsx" --dry-run
python backend\manage.py import_counters "Contador de Pagina Oficina Junio del 01 al 30.xlsx"
```

4. Verifica en el admin (`/admin/devices/monthlycounterentry/`) filtrando por
   `period` que los datos del mes se vean correctos.

## Editar manualmente desde el admin

Si necesitas agregar o corregir un registro puntual sin usar Excel, entra a
`/admin/devices/monthlycounterentry/add/` y completa el formulario (los campos
estan agrupados en Ubicacion, Dispositivo, Contadores, y Periodo y notas).
