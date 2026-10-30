name := "nyc-taxi-etl"
version := "0.1.0"
scalaVersion := "2.12.18"

val sparkVersion = "3.5.1"

libraryDependencies ++= Seq(
  "org.apache.spark" %% "spark-core" % sparkVersion,
  "org.apache.spark" %% "spark-sql"  % sparkVersion,
  "org.scalatest"    %% "scalatest"  % "3.2.19" % Test
)

// Spark needs these --add-opens flags to run on JDK 17+ (JPMS blocks its reflective access
// to internal java.base/java.nio classes otherwise).
val sparkJavaOptions = Seq(
  "-Dhadoop.home.dir=/tmp",
  "--add-opens=java.base/java.lang=ALL-UNNAMED",
  "--add-opens=java.base/java.lang.invoke=ALL-UNNAMED",
  "--add-opens=java.base/java.lang.reflect=ALL-UNNAMED",
  "--add-opens=java.base/java.io=ALL-UNNAMED",
  "--add-opens=java.base/java.net=ALL-UNNAMED",
  "--add-opens=java.base/java.nio=ALL-UNNAMED",
  "--add-opens=java.base/java.util=ALL-UNNAMED",
  "--add-opens=java.base/java.util.concurrent=ALL-UNNAMED",
  "--add-opens=java.base/sun.nio.ch=ALL-UNNAMED",
  "--add-opens=java.base/sun.security.action=ALL-UNNAMED",
  "--add-opens=java.base/sun.util.calendar=ALL-UNNAMED"
)

Compile / run / fork := true
Compile / run / javaOptions ++= sparkJavaOptions

Test / fork := true
Test / javaOptions ++= sparkJavaOptions
