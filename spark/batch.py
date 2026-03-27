from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("data-crunch-pipeline").master("local[*]").getOrCreate()