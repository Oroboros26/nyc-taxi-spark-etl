package etl

import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.functions.col

/** Entry point: Extract -> Transform -> Load, with before/after row counts printed
  * and persisted to data/quality_summary.json so the dashboard can read the
  * data-quality stat without recomputing it.
  *
  * Usage: run [yellowPath] [greenPath] [zoneLookupPath] [outputPath] [qualitySummaryPath]
  * All args are optional; defaults point at the local data/ folder.
  */
object Main {
  def main(args: Array[String]): Unit = {
    val yellowPath = args.lift(0).getOrElse("data/raw/yellow")
    val greenPath = args.lift(1).getOrElse("data/raw/green")
    val zoneLookupPath = args.lift(2).getOrElse("data/raw/taxi_zone_lookup.csv")
    val outputPath = args.lift(3).getOrElse("data/output")
    val qualitySummaryPath = args.lift(4).getOrElse("data/quality_summary.json")

    val spark = SparkSession.builder()
      .appName("NYC Taxi ETL")
      .master("local[*]")
      .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    try {
      val rawDf = Extract.extractTrips(spark, yellowPath, greenPath)
      val rawCount = rawDf.count()

      val cleanDf = Transform.clean(rawDf)
      val cleanCount = cleanDf.count()

      val zoneLookup = Extract.readZoneLookup(spark, zoneLookupPath)
      val enrichedDf = Transform.enrichWithZones(Transform.addDerivedColumns(cleanDf), zoneLookup)

      Load.writeParquet(enrichedDf, outputPath)

      val suspiciousCount = enrichedDf.filter(col("is_suspicious_zero_distance")).count()
      Load.writeQualitySummary(qualitySummaryPath, rawCount, cleanCount, suspiciousCount)

      val droppedCount = rawCount - cleanCount
      val droppedPct = if (rawCount > 0) 100.0 * droppedCount / rawCount else 0.0
      println(s"Raw rows:     $rawCount")
      println(s"Clean rows:   $cleanCount")
      println(f"Dropped rows: $droppedCount ($droppedPct%.2f%%)")
      println(s"Suspicious (zero-distance, nonzero-fare) rows: $suspiciousCount")
      println(s"Output written to: $outputPath")
      println(s"Quality summary written to: $qualitySummaryPath")
    } finally {
      spark.stop()
    }
  }
}
