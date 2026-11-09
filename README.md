# Examen Parcial 2 - Manejo Masivo de Datos (Big Data)

**Alumno:** Santiago MArtin Motes Rubio
**Matrícula:** 125052194
**Pregunta asignada (último dígito 4):** Unidades vendidas por método de pago y día de la semana.

- Clave: `metodo_pago,dia_semana` (0 = lunes ... 6 = domingo, según `datetime.weekday()`)
- Valor: suma de `cantidad`
- Resultado esperado: 28 filas (4 métodos de pago x 7 días)

## Arquitectura

Tres servicios en una red de Docker Compose llamada `red`:

| Servicio | Imagen | Función |
|---|---|---|
| `hadoop` | Build propio (`hadoop/Dockerfile`, Debian bookworm-slim, OpenJDK 17, Hadoop 3.3.6 standalone, OpenSSH) | Ejecuta el job de Hadoop Streaming. El dataset se monta de solo lectura en `/data/input` |
| `db` | `postgres:16` | Guarda los resultados. Volumen nombrado `pgdata` y credenciales en `.env` |
| `api` | Build propio (`api/Dockerfile`, Python 3.12 + Flask) | CRUD sobre la tabla `resultados`. Se conecta a `db` por nombre de servicio |

`api` declara `depends_on: db`. Como eso solo espera a que el contenedor arranque (no a que Postgres acepte conexiones), `app.py` reintenta la conexión hasta 30 veces.

## Estructura del repositorio

```
examen-p2-125052194/
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml
├── generar_dataset.py
├── hadoop/
│   ├── Dockerfile
│   └── entrypoint.sh
├── mapreduce/
│   ├── mapper.py
│   ├── reducer.py
│   └── secuencial.py
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
├── scripts/
│   └── cargar_resultados.py
└── evidencias/
```

El CSV, el archivo `.env` y la carpeta `ssh_keys/` **no se suben** al repositorio (están en `.gitignore`).

## Cómo reproducir

### 1. Clonar y preparar archivos que no están en Git

```bash
git clone <URL_DEL_REPO> examen-p2-125052194
cd examen-p2-125052194

# Dataset (tarda unos minutos, genera ~336 MB y 5,000,000 de filas)
python3 generar_dataset.py 125052194

# Variables de entorno
cp .env.example .env
nano .env        # poner una contraseña real en POSTGRES_PASSWORD

# Llaves SSH sin passphrase (se montan por volumen, no van en la imagen)
mkdir -p ssh_keys
ssh-keygen -t rsa -b 4096 -N "" -f ssh_keys/id_rsa
```

### 2. Levantar el ambiente

```bash
docker compose up --build -d
docker compose ps
```

Deben aparecer `hadoop`, `db` y `api` en estado `running`.

### 3. Verificar Hadoop (Parte A)

```bash
docker compose exec hadoop hadoop version
```

### 4. Verificar SSH sin contraseña (Parte B)

```bash
# Dentro del contenedor hadoop
docker compose exec -u hadoop hadoop ssh localhost "hostname && whoami"

# Desde el contenedor api hacia hadoop por nombre de servicio
docker compose exec api bash -c '
mkdir -p ~/.ssh &&
cp /ssh_keys/id_rsa ~/.ssh/id_rsa &&
chmod 600 ~/.ssh/id_rsa &&
ssh -o StrictHostKeyChecking=no hadoop@hadoop "hostname && whoami"'
```

La llave privada se copia a `~/.ssh` porque el montaje es de solo lectura y SSH exige permisos 600.

### 5. Ejecutar el job de Hadoop Streaming (Parte C1)

```bash
docker compose exec -u hadoop hadoop bash -c '
cd /app/mapreduce && rm -rf /data/output/resultado &&
time hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -input /data/input/ventas_125052194.csv \
  -output /data/output/resultado \
  -mapper "python3 mapper.py" -reducer "python3 reducer.py" \
  -file mapper.py -file reducer.py'
```

El mapper ignora el encabezado (`campos[0] == "id"`) y descarta con `continue` las líneas con número de campos distinto de 8 o valores no convertibles, así que una línea mala no detiene el job.

### 6. Cargar resultados a la base de datos (Parte D)

```bash
docker compose cp hadoop:/data/output/resultado/part-00000 evidencias/part-00000
docker compose exec api python /scripts/cargar_resultados.py /evidencias/part-00000
```

Debe imprimir `Registros cargados: 28`. El script usa `INSERT ... ON CONFLICT DO UPDATE`, por lo que se puede ejecutar varias veces sin duplicar filas.

### 7. Consultar la API

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/resultados` | Todos los registros |
| GET | `/resultados/<metodo_pago>` | Filtro por método de pago (ej. `/resultados/Tarjeta`) |
| POST | `/resultados` | Crea un registro (JSON con `metodo_pago`, `dia_semana`, `unidades`) |
| PUT | `/resultados/<id>` | Actualiza las unidades de un registro |
| DELETE | `/resultados/<id>` | Elimina un registro |

```bash
curl localhost:5000/resultados
curl localhost:5000/resultados/Tarjeta
curl -X PUT localhost:5000/resultados/1 \
  -H "Content-Type: application/json" -d '{"unidades": 999}'
```

### 8. Persistencia

```bash
docker compose down          # elimina contenedores y red, conserva volúmenes
docker compose up -d
curl localhost:5000/resultados   # los datos siguen ahí

docker compose down -v       # además elimina los volúmenes
docker compose up -d
curl localhost:5000/resultados   # devuelve []
```

Tras `down -v` se recarga con el paso 6.

## Comparativa de rendimiento (Parte C2)

Misma pregunta, tres formas de resolverla, sobre el mismo CSV de 5,000,000 de registros:

| Método | Tiempo (real) |
|---|---|
| Script secuencial en Python (`secuencial.py`) | ~23.2 s |
| Pipeline local `mapper \| sort \| reducer` | ~29.8 s |
| Hadoop Streaming (standalone, en contenedor) | ~29.1 s |

Los tres resultados son idénticos (`diff` sin diferencias, 28 filas, 32,496,635 unidades en total).

**Explicación:** el script secuencial fue el más rápido porque hace una sola pasada por el archivo y acumula en memoria solo 28 claves, sin escribir nada intermedio. El enfoque MapReduce, en cambio, emite una línea intermedia por cada uno de los 5 millones de registros, las ordena (fase de shuffle/sort) y las vuelve a leer en el reducer, lo que implica mucha
1. Modos de Hadoop (3 pts)
 TEORIA
Standalone: todo corre en una sola JVM, sin demonios, y usa el sistema de archivos local. Sirve para pruebas y depuración. Es el que usaste tú.
Pseudo-distribuido: corre todos los demonios (NameNode, DataNode, ResourceManager, NodeManager) en una sola máquina, cada uno en su propio proceso, simulando un clúster. Por eso Hadoop requiere SSH sin contraseña para arrancarlos.
Totalmente distribuido: los demonios se reparten en varias máquinas reales, con datos y cómputo repartidos entre nodos.
HDFS se usa en el pseudo-distribuido y en el totalmente distribuido. En standalone no.

2. Dataset como volumen y no con COPY (3 pts)
Tamaño de la imagen: con COPY, los 336 MB quedan dentro de una capa de la imagen, que se vuelve más pesada y lenta de construir, subir y descargar.
Separación de datos y código: con un volumen puedes cambiar o regenerar el dataset sin reconstruir la imagen. Con COPY, cada cambio invalida la caché y obliga a un nuevo build.
Solo lectura y datos fuera de Git: el montaje :ro protege el original de modificaciones, y el CSV no queda incrustado en una imagen que podrías compartir o subir a un registro.
3. docker compose down vs down -v (3 pts)

docker compose down elimina los contenedores y la red, pero conserva los volúmenes nombrados, así que los datos de Postgres (en pgdata) siguen ahí al hacer up otra vez. Lo comprobaste: los registros reaparecieron sin recargar.
docker compose down -v elimina además los volúmenes nombrados declarados en el compose, así que pgdata se borra y la tabla vuelve vacía ([]). Hay que recargar los resultados.

4. MapReduce vs script secuencial (3 pts)

Con 336 MB, el secuencial fue más rápido (~23 s contra ~29 s). MapReduce añade arranque de la JVM, emisión de una línea intermedia por registro, ordenamiento (shuffle/sort) y serialización, y en standalone no hay paralelismo real.
Conviene MapReduce cuando los datos no caben en la memoria o el disco de una sola máquina (cientos de GB a TB), cuando hay un clúster con HDFS para procesar bloques en paralelo, y cuando el trabajo es lo bastante pesado como para amortizar el costo fijo del framework. También aporta tolerancia a fallos en clústeres grandes.

5. CMD vs ENTRYPOINT y COPY vs ADD (3 pts)

CMD define el comando por defecto del contenedor y es fácil de sobrescribir al hacer docker run imagen otro-comando. ENTRYPOINT define el ejecutable fijo del contenedor; lo que pases al run se recibe como argumentos, y para reemplazarlo hay que usar --entrypoint. Lo viste: tu imagen de Hadoop tiene ENTRYPOINT ["/entrypoint.sh"], y para correr hadoop version usaste --entrypoint hadoop. Suelen combinarse: ENTRYPOINT como programa y CMD como argumentos por defecto.
COPY solo copia archivos o carpetas del contexto de build a la imagen. ADD hace lo mismo, pero además descomprime automáticamente archivos .tar locales y acepta URLs remotas. Por ser más predecible, se recomienda COPY salvo que se necesite esa extracción.
