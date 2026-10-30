package etl.models

import java.sql.Timestamp

/** Unified schema for a single trip record, after Yellow/Green column names have been
  * normalized in Extract (e.g. `tpep_pickup_datetime` / `lpep_pickup_datetime` -> `pickupDatetime`).
  */
case class Trip(
    taxiType: String,
    vendorId: Option[Int],
    pickupDatetime: Timestamp,
    dropoffDatetime: Timestamp,
    passengerCount: Option[Long],
    tripDistance: Double,
    puLocationId: Int,
    doLocationId: Int,
    paymentType: Option[Long],
    fareAmount: Double,
    tipAmount: Double,
    totalAmount: Double
)
