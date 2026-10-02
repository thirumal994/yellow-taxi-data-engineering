# Databricks notebook source
# DBTITLE 1,Read data from Bronze layer

from pyspark.sql import functions as F

bronze_table = "yellow_taxi_bronze"

df_bronze = spark.table(bronze_table)

print("Bronze record count:", df_bronze.count())

display(df_bronze.limit(10))

# COMMAND ----------

# DBTITLE 1,Adding the Silver quality flags
df_silver = (
    df_bronze

    # --------------------------------------------------
    # 1. January 2019 validation
    # --------------------------------------------------
    .withColumn(
        "pickup_date_valid",
        (
            (F.col("tpep_pickup_datetime") >= F.to_timestamp(F.lit("2019-01-01"))) &
            (F.col("tpep_pickup_datetime") < F.to_timestamp(F.lit("2019-02-01")))
        )
    )

    # --------------------------------------------------
    # 2. Passenger validation
    # --------------------------------------------------
    .withColumn(
        "passenger_count_valid",
        F.col("passenger_count") > 0
    )

    # --------------------------------------------------
    # 3. Distance validation
    # --------------------------------------------------
    .withColumn(
        "trip_distance_valid",
        F.col("trip_distance") >= 0
    )

    # --------------------------------------------------
    # 4. Trip duration validation
    # --------------------------------------------------
    .withColumn(
        "trip_duration_valid",
        F.col("tpep_dropoff_datetime") >= F.col("tpep_pickup_datetime")
    )

    # --------------------------------------------------
    # 5. Financial validation
    # --------------------------------------------------
    .withColumn(
        "financial_amount_valid",
        F.col("total_amount") >= 0
    )
)

display(df_silver.limit(10))

# COMMAND ----------

# DBTITLE 1,Add useful derived columns
df_silver = (
    df_silver

    .withColumn(
        "pickup_date",
        F.to_date("tpep_pickup_datetime")
    )

    .withColumn(
        "pickup_hour",
        F.hour("tpep_pickup_datetime")
    )

    .withColumn(
        "trip_duration_minutes",
        (
            F.unix_timestamp("tpep_dropoff_datetime")
            - F.unix_timestamp("tpep_pickup_datetime")
        ) / 60
    )
)

display(df_silver.limit(10))

# COMMAND ----------

# DBTITLE 1,Adding overall quality status column
#Overall status gives the summary; individual flags give the explanation.
df_silver = df_silver.withColumn(
    "record_quality",
    F.when(
        F.col("pickup_date_valid") &
        F.col("passenger_count_valid") &
        F.col("trip_distance_valid") &
        F.col("trip_duration_valid") &
        F.col("financial_amount_valid"),
        "VALID"
    ).otherwise("CHECK")
)

display(
    df_silver.groupBy("record_quality")
             .count()
             .orderBy("record_quality")
)

# COMMAND ----------

# DBTITLE 1,Verifying Silver
print("Bronze count:", df_bronze.count())
print("Silver count:", df_silver.count())

# COMMAND ----------

display(
    df_silver.groupBy("record_quality")
             .count()
             .orderBy("record_quality")
)

# COMMAND ----------

display(
    df_silver.select(
        F.sum(F.when(~F.col("pickup_date_valid"), 1).otherwise(0))
            .alias("invalid_period"),

        F.sum(F.when(~F.col("passenger_count_valid"), 1).otherwise(0))
            .alias("invalid_passenger"),

        F.sum(F.when(~F.col("trip_distance_valid"), 1).otherwise(0))
            .alias("invalid_distance"),

        F.sum(F.when(~F.col("trip_duration_valid"), 1).otherwise(0))
            .alias("invalid_duration"),

        F.sum(F.when(~F.col("financial_amount_valid"), 1).otherwise(0))
            .alias("invalid_financial")
    )
)

# COMMAND ----------

df_silver.groupBy(
    "pickup_date_valid",
    "passenger_count_valid",
    "trip_distance_valid",
    "trip_duration_valid",
    "financial_amount_valid"
).count().orderBy(F.desc("count")).show(truncate=False)

# COMMAND ----------

# DBTITLE 1,verify that every VALID record actually satisfies all five rules.
invalid_valid_records = df_silver.filter(
    (F.col("record_quality") == "VALID") &
    (
        ~F.col("pickup_date_valid") |
        ~F.col("passenger_count_valid") |
        ~F.col("trip_distance_valid") |
        ~F.col("trip_duration_valid") |
        ~F.col("financial_amount_valid")
    )
)

print("Invalid VALID records:", invalid_valid_records.count())

# COMMAND ----------

# DBTITLE 1,Add a column identifying the source
df_silver = df_silver.withColumn(
    "source_file",
    F.lit("yellow_tripdata_2019-01.csv.gz")
)

# COMMAND ----------

# DBTITLE 1,Saved dataset as silver_table
silver_table = "yellow_taxi_silver"

(
    df_silver.write
    .format("delta")
    .mode("overwrite")
    .saveAsTable(silver_table)
)

# COMMAND ----------

# DBTITLE 1,Post verification
df_silver_table = spark.table("yellow_taxi_silver")

print("Silver table count:", df_silver_table.count())

display(df_silver_table.limit(10))

# COMMAND ----------

bronze_count = spark.table("yellow_taxi_bronze").count()
silver_count = spark.table("yellow_taxi_silver").count()

print("Bronze records:", bronze_count)
print("Silver records:", silver_count)

assert bronze_count == silver_count, "Record count mismatch!"

print("SUCCESS: Bronze and Silver counts match.")

# COMMAND ----------

