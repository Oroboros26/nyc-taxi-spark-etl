package etl

import org.apache.spark.sql.{Row, SparkSession}
import org.apache.spark.sql.types._
import org.scalatest.BeforeAndAfterAll
import org.scalatest.matchers.should.Matchers
import org.scalatest.wordspec.AnyWordSpec

import java.sql.Timestamp

class TransformSpec extends AnyWordSpec with Matchers with BeforeAndAfterAll {

  private var spark: SparkSession = _

  override def beforeAll(): Unit = {
    spark = SparkSession.builder()
      .appName("TransformSpec")
      .master("local[1]")
      .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
  }

  override def afterAll(): Unit = spark.stop()

  private val schema = StructType(Seq(
    StructField("taxiType", StringType),
    StructField("VendorID", IntegerType),
    StructField("pickupDatetime", TimestampType),
    StructField("dropoffDatetime", TimestampType),
    StructField("passenger_count", LongType),
    StructField("trip_distance", DoubleType),
    StructField("PULocationID", IntegerType),
    StructField("DOLocationID", IntegerType),
    StructField("payment_type", LongType),
    StructField("fare_amount", DoubleType),
    StructField("tip_amount", DoubleType),
    StructField("total_amount", DoubleType)
  ))

  private val pickup = Timestamp.valueOf("2024-01-15 08:00:00")
  private val dropoff = Timestamp.valueOf("2024-01-15 08:20:00")

  /** A row that passes every rule in Transform.clean, with named overrides for the field(s)
    * under test in each case.
    */
  private def validRow(
      pickupDatetime: Timestamp = pickup,
      dropoffDatetime: Timestamp = dropoff,
      passengerCount: java.lang.Long = 1L,
      puLocationId: java.lang.Integer = 100,
      doLocationId: java.lang.Integer = 200,
      fareAmount: java.lang.Double = 10.0,
      tripDistance: java.lang.Double = 2.0
  ): Row =
    Row(
      "yellow", 1, pickupDatetime, dropoffDatetime, passengerCount, tripDistance,
      puLocationId, doLocationId, 1L, fareAmount, 1.0, fareAmount + 1.0
    )

  private def cleanRows(rows: Row*) = {
    val df = spark.createDataFrame(spark.sparkContext.parallelize(rows), schema)
    Transform.clean(df).collect()
  }

  "Transform.clean" should {

    "drop rows with fare_amount <= 0" in {
      cleanRows(validRow(fareAmount = 0.0), validRow(fareAmount = -5.0)) shouldBe empty
    }

    "keep rows with fare_amount > 0" in {
      cleanRows(validRow(fareAmount = 10.0)) should have length 1
    }

    "drop rows where dropoff is not after pickup" in {
      cleanRows(validRow(pickupDatetime = dropoff, dropoffDatetime = pickup)) shouldBe empty
      cleanRows(validRow(pickupDatetime = pickup, dropoffDatetime = pickup)) shouldBe empty
    }

    "drop rows with passenger_count = 0 but keep null passenger_count" in {
      cleanRows(validRow(passengerCount = 0L)) shouldBe empty
      cleanRows(validRow(passengerCount = null)) should have length 1
    }

    "drop rows with a missing pickup or dropoff location id" in {
      cleanRows(validRow(puLocationId = null)) shouldBe empty
      cleanRows(validRow(doLocationId = null)) shouldBe empty
    }

    "flag zero-distance, nonzero-fare rows as suspicious instead of dropping them" in {
      val result = cleanRows(validRow(tripDistance = 0.0, fareAmount = 10.0))
      result should have length 1
      result.head.getAs[Boolean]("is_suspicious_zero_distance") shouldBe true
    }

    "not flag normal trips as suspicious" in {
      val result = cleanRows(validRow(tripDistance = 2.0, fareAmount = 10.0))
      result.head.getAs[Boolean]("is_suspicious_zero_distance") shouldBe false
    }
  }
}
