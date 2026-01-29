from pyspark.sql import SparkSession


spark = (SparkSession.builder 
    .appName("CrearArquitecturaMedallion") 
    .master("spark://spark-master:7077") 
    .config("spark.submit.deployMode", "client") 
    
    # Extensiones Delta
    .config("spark.sql.extensions",
            "io.delta.sql.DeltaSparkSessionExtension")
    
    # Crea el catalogo como un DeltaCatalog
    .config("spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    .config("spark.sql.warehouse.dir", "s3a://catalogo-datasets/")
    
    # Estamos usando hive en memoria, el catalogo no persiste entre sesiones
    # Establecer la conexion a minio
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") 
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin123") 
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") 
    .config("spark.hadoop.fs.s3a.path.style.access", "true") 
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") 
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")   
    .getOrCreate())

print("SparkSession creada")
# spark = SparkSession.builer.getOrCreate()

from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType, BinaryType
from pyspark.sql import Row


bronze_table_checkpoint="s3a://catalogo-datasets/bronze/pacientes_checkpoint"

# CREAR TABLA DE checkpoint SI NO EXISTE
schema_processed = StructType([
    StructField("last_lsn", BinaryType(), True)
])

checkpoint_df = spark.createDataFrame([], schema_processed)

# Crear DataFrame con la fila null
row_df = spark.createDataFrame([Row(last_lsn=None)], schema_processed)

# Unir (append)
checkpoint_df = checkpoint_df.union(row_df)

# Guardar como tabla Delta en S3
checkpoint_df.write \
  .format("delta") \
  .mode("overwrite") \
  .save(bronze_table_checkpoint)
