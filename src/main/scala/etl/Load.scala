package etl

import org.apache.spark.sql.DataFrame
import java.io.PrintWriter

/** Writes the cleaned/enriched trips to partitioned Parquet. */
object Load {

  /** Writes only the year/month partitions present in `df`, leaving every other
    * partition already on disk untouched. Without dynamic partition overwrite mode,
    * Spark's default "overwrite" wipes the *entire* outputPath on every run — this
    * setting scopes the overwrite to just the partitions being written, which also
    * makes reruns of the same month idempotent (it replaces that month, not the dataset).
    */
  def writeParquet(df: DataFrame, outputPath: String): Unit = {
    df.sparkSession.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
    df.write
      .mode("overwrite")
      .partitionBy("year", "month")
      .parquet(outputPath)
  }

  /** Writes a one-row JSON summary the dashboard reads independently of the Parquet output,
    * since counts computed during the run aren't otherwise persisted anywhere.
    */
  def writeQualitySummary(
      path: String,
      rawCount: Long,
      cleanCount: Long,
      suspiciousCount: Long
  ): Unit = {
    val droppedCount = rawCount - cleanCount
    val droppedPct = if (rawCount > 0) 100.0 * droppedCount / rawCount else 0.0
    val suspiciousPct = if (cleanCount > 0) 100.0 * suspiciousCount / cleanCount else 0.0
    val json =
      s"""{
         |  "rawCount": $rawCount,
         |  "cleanCount": $cleanCount,
         |  "droppedCount": $droppedCount,
         |  "droppedPct": ${f"$droppedPct%.4f"},
         |  "suspiciousCount": $suspiciousCount,
         |  "suspiciousPct": ${f"$suspiciousPct%.4f"}
         |}
         |""".stripMargin
    val writer = new PrintWriter(path)
    try writer.write(json)
    finally writer.close()
  }
}
