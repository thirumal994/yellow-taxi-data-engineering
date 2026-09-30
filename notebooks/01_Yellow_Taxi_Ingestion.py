# Databricks notebook source
# Step 1: Read the raw January 2019 Yellow Taxi CSV
df_bronze = spark.read.format("csv") \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .load("/databricks-datasets/nyctaxi/tripdata/yellow/yellow_tripdata_2019-01.csv.gz")

# Step 2: Save the raw data as a Bronze Delta table
df_bronze.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable("yellow_taxi_bronze")

# Step 3: Verify the Bronze table
print("Bronze record count:", spark.table("yellow_taxi_bronze").count())

display(spark.table("yellow_taxi_bronze").limit(5))

# COMMAND ----------

