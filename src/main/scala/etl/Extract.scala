package etl

import org.apache.spark.sql.{DataFrame, Dataset, SparkSession}
import org.apache.spark.sql.functions.{col, lit}

/** Reads raw TLC trip data and the zone lookup table, normalizing Yellow/Green's differing
  * pickup/dropoff column names (`tpep_*` vs `lpep_*`) into one common schema.
  */
object Extract {

  private val commonColumns = Seq(
    "taxiType",
    "VendorID",
    "pickupDatetime",
    "dropoffDatetime",
    "passenger_count",
    "trip_distance",
    "PULocationID",
    "DOLocationID",
    "payment_type",
    "fare_amount",
    "tip_amount",
    "total_amount"
  )

  def readYellow(spark: SparkSession, path: String): DataFrame =
    spark.read.parquet(path)
      .withColumn("taxiType", lit("yellow"))
      .withColumnRenamed("tpep_pickup_datetime", "pickupDatetime")
      .withColumnRenamed("tpep_dropoff_datetime", "dropoffDatetime")
      .select(commonColumns.map(col): _*)

  def readGreen(spark: SparkSession, path: String): DataFrame =
    spark.read.parquet(path)
      .withColumn("taxiType", lit("green"))
      .withColumnRenamed("lpep_pickup_datetime", "pickupDatetime")
      .withColumnRenamed("lpep_dropoff_datetime", "dropoffDatetime")
      .select(commonColumns.map(col): _*)

  def readZoneLookup(spark: SparkSession, path: String): DataFrame =
    spark.read.option("header", "true").option("inferSchema", "true").csv(path)

  /** Reads and normalizes both taxi types, unioned into one raw DataFrame (pre-cleaning). */
  def extractTrips(spark: SparkSession, yellowPath: String, greenPath: String): DataFrame =
    readYellow(spark, yellowPath).unionByName(readGreen(spark, greenPath))
}
