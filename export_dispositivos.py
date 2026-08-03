"""
Script para conectarse a la base de datos SQL Server de HP Web Jetadmin (instancia HPWJA)
y exportar informacion de dispositivos a un archivo de texto.

Columnas exportadas:
    - Modelo de dispositivo   -> model_name
    - Direccion IP            -> ipv4_address
   
    - Recuento de paginas     -> page_count
      (proxy de "recuento de ciclo del motor"; HPWJA no expone un contador
       de ciclos de motor separado, el mas cercano disponible es page_count)

Requiere:
    pip install pyodbc
    Driver instalado: "ODBC Driver 17 for SQL Server"
"""

import pyodbc
from datetime import datetime

SERVER = r"localhost\HPWJA"
DATABASE = "HPWJA"
OUTPUT_FILE = "dispositivos.txt"

CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
)

QUERY = """
    SELECT
        model_name,
        ipv4_address,
        
        page_count
    FROM dbo.PUBLIC_DEV_CON_INFO_VW
    ORDER BY model_name
"""


def main():
    try:
        conn = pyodbc.connect(CONN_STR, timeout=10)
    except pyodbc.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return

    try:
        cur = conn.cursor()
        cur.execute(QUERY)
        rows = cur.fetchall()

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(f"Reporte de dispositivos - generado {datetime.now():%Y-%m-%d %H:%M:%S}\n")
            f.write("=" * 80 + "\n")
            f.write(f"{'Modelo':<35}{'IP':<18}{'Paginas':>10}\n")
            f.write("-" * 80 + "\n")

            for row in rows:
                modelo = row.model_name or ""
                ip = row.ipv4_address or ""
                
                paginas = row.page_count if row.page_count is not None else ""
                f.write(f"{modelo:<35}{ip:<18}{str(paginas):>10}\n")

            f.write("-" * 80 + "\n")
            f.write(f"Total de dispositivos: {len(rows)}\n")

        print(f"Archivo generado: {OUTPUT_FILE} ({len(rows)} dispositivos)")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
