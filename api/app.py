import os
import time
import psycopg2
from flask import Flask, jsonify, request

app = Flask(__name__)


def get_conn():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "db"),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )


def init_db():
    # depends_on solo espera a que el contenedor arranque, no a que Postgres este listo
    for _ in range(30):
        try:
            conn = get_conn()
            break
        except psycopg2.OperationalError:
            time.sleep(2)
    else:
        raise RuntimeError("No se pudo conectar a la base de datos")
    with conn, conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS resultados (
                id SERIAL PRIMARY KEY,
                metodo_pago TEXT NOT NULL,
                dia_semana INT NOT NULL,
                unidades BIGINT NOT NULL,
                UNIQUE (metodo_pago, dia_semana)
            )
        """)
    conn.close()


def fila_a_dict(r):
    return {"id": r[0], "metodo_pago": r[1], "dia_semana": r[2], "unidades": r[3]}


@app.get("/resultados")
def listar():
    conn = get_conn()
    with conn, conn.cursor() as cur:
        cur.execute("SELECT id, metodo_pago, dia_semana, unidades FROM resultados ORDER BY metodo_pago, dia_semana")
        datos = [fila_a_dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(datos)


@app.get("/resultados/<metodo>")
def por_metodo(metodo):
    conn = get_conn()
    with conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, metodo_pago, dia_semana, unidades FROM resultados "
            "WHERE metodo_pago = %s ORDER BY dia_semana", (metodo,))
        datos = [fila_a_dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(datos)


@app.post("/resultados")
def crear():
    d = request.get_json()
    conn = get_conn()
    with conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO resultados (metodo_pago, dia_semana, unidades) VALUES (%s, %s, %s) "
            "RETURNING id, metodo_pago, dia_semana, unidades",
            (d["metodo_pago"], d["dia_semana"], d["unidades"]))
        nuevo = fila_a_dict(cur.fetchone())
    conn.close()
    return jsonify(nuevo), 201


@app.put("/resultados/<int:rid>")
def actualizar(rid):
    d = request.get_json()
    conn = get_conn()
    with conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE resultados SET unidades = %s WHERE id = %s "
            "RETURNING id, metodo_pago, dia_semana, unidades", (d["unidades"], rid))
        fila = cur.fetchone()
    conn.close()
    if fila is None:
        return jsonify({"error": "no encontrado"}), 404
    return jsonify(fila_a_dict(fila))


@app.delete("/resultados/<int:rid>")
def borrar(rid):
    conn = get_conn()
    with conn, conn.cursor() as cur:
        cur.execute("DELETE FROM resultados WHERE id = %s", (rid,))
        borrados = cur.rowcount
    conn.close()
    if borrados == 0:
        return jsonify({"error": "no encontrado"}), 404
    return jsonify({"borrado": rid})


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
