#!/usr/bin/env python3
import sys
from collections import defaultdict
from datetime import datetime

archivo = sys.argv[1]
totales = defaultdict(int)

with open(archivo, newline="") as f:
    for linea in f:
        try:
            campos = linea.strip().split(",")
            if len(campos) != 8 or campos[0] == "id":
                continue
            fecha = datetime.strptime(campos[1], "%Y-%m-%d %H:%M:%S")
            cantidad = int(campos[5])
            totales[(campos[7], fecha.weekday())] += cantidad
        except (ValueError, IndexError):
            continue

for (metodo, dia) in sorted(totales):
    print(f"{metodo},{dia}\t{totales[(metodo, dia)]}")
