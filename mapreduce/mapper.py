#!/usr/bin/env python3
import sys
from datetime import datetime

for linea in sys.stdin:
    try:
        campos = linea.strip().split(",")
        if len(campos) != 8:
            continue
        if campos[0] == "id":          # encabezado
            continue
        fecha = datetime.strptime(campos[1], "%Y-%m-%d %H:%M:%S")
        cantidad = int(campos[5])
        metodo = campos[7]
        dia = fecha.weekday()           # 0 = lunes ... 6 = domingo
        print(f"{metodo},{dia}\t{cantidad}")
    except (ValueError, IndexError):
        continue                        # linea mal formada: se ignora
