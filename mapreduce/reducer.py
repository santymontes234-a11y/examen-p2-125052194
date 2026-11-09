#!/usr/bin/env python3
import sys

clave_actual = None
total = 0

for linea in sys.stdin:
    try:
        clave, valor = linea.rstrip("\n").split("\t")
        valor = int(valor)
    except ValueError:
        continue

    if clave == clave_actual:
        total += valor
    else:
        if clave_actual is not None:
            print(f"{clave_actual}\t{total}")
        clave_actual = clave
        total = valor

if clave_actual is not None:
    print(f"{clave_actual}\t{total}")

