#!/usr/bin/env python3
import os
import sys
import psycopg2

archivo = sys.argv[1] if len(sys.argv) > 1 else "/data/output/resultado/part-00000"

conn = psycopg2.connect(
    host=os.environ.get("POSTGRES_HOST", "db"),
    dbname=os.environ["POSTGRES_DB"],
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
)

cargados = 0
with conn, conn.cursor() as cur, open(archivo) as f:
    for linea in f:
        try:
            clave, valor = linea.rstrip("\n").split("\t")
            metodo, dia = clave.split(",")
            cur.execute(
                "INSERT INTO resultados (metodo_pago, dia_semana, unidades) "
                "VALUES (%s, %s, %s) "
                "ON CONFLICT (metodo_pago, dia_semana) "
                "DO UPDATE SET unidades = EXCLUDED.unidades",
                (metodo, int(dia), int(valor)),
            )
            cargados += 1
        except ValueError:
            continue
conn.close()
print(f"Registros cargados: {cargados}")
