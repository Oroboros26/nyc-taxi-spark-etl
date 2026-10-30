package etl

import org.apache.spark.sql.DataFrame
import org.apache.spark.sql.functions._

/** Data-quality filtering, derived columns, and zone-name enrichment. */
object Transform {

  /** Drops rows that fail the hard data-quality rules. Rows are also flagged (not dropped)
    * when trip_distance = 0 but fare_amount > 0, since that pattern is suspicious but not
    * necessarily invalid (e.g. flat-rate airport trips, cancelled-but-charged trips).
    */
  def clean(df: DataFrame): DataFrame =
    df
      .filter(col("fare_amount") > 0)
      .filter(col("dropoffDatetime") > col("pickupDatetime"))
      .filter(col("passenger_count").isNull || col("passenger_count") > 0)
      .filter(col("PULocationID").isNotNull && col("DOLocationID").isNotNull)
      .withColumn(
        "is_suspicious_zero_distance",
        col("trip_distance") === 0 && col("fare_amount") > 0
      )

  def addDerivedColumns(df: DataFrame): DataFrame =
    df
      .withColumn(
        "trip_duration_minutes",
        (unix_timestamp(col("dropoffDatetime")) - unix_timestamp(col("pickupDatetime"))) / 60.0
      )
      .withColumn(
        "tip_percentage",
        when(col("fare_amount") > 0, col("tip_amount") / col("fare_amount") * 100).otherwise(lit(null))
      )
      .withColumn("day_of_week", date_format(col("pickupDatetime"), "EEEE"))
      .withColumn("hour_of_day", hour(col("pickupDatetime")))
      .withColumn("year", year(col("pickupDatetime")))
      .withColumn("month", month(col("pickupDatetime")))

  /** Joins pickup and dropoff location IDs against the zone lookup table to attach
    * human-readable borough/zone names for both ends of the trip.
    */
  def enrichWithZones(df: DataFrame, zoneLookup: DataFrame): DataFrame = {
    val pickupZones = zoneLookup
      .select(
        col("LocationID").as("pu_zone_id"),
        col("Borough").as("pu_borough"),
        col("Zone").as("pu_zone")
      )
    val dropoffZones = zoneLookup
      .select(
        col("LocationID").as("do_zone_id"),
        col("Borough").as("do_borough"),
        col("Zone").as("do_zone")
      )

    df
      .join(pickupZones, df("PULocationID") === pickupZones("pu_zone_id"), "left")
      .join(dropoffZones, df("DOLocationID") === dropoffZones("do_zone_id"), "left")
      .drop("pu_zone_id", "do_zone_id")
  }
}
