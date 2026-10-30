"""Monthly NYC Taxi ETL DAG (skeleton, per ROADMAP.md v0.1).

Not deployed anywhere yet - this is the DAG shape described in ROADMAP.md,
written so it can be dropped into an Airflow `dags/` folder once Airflow is
actually stood up. It replaces the current manual workflow (curl, then
`sbt run`, then reload Streamlit by hand) with a scheduled DAG: discover the
month's file -> skip if already processed -> download raw data -> run the
Scala/Spark ETL -> validate the output -> notify.

TLC publishes with roughly a 2-month lag, so this runs monthly and each run
processes the month two months before its logical date (e.g. the run
scheduled for 2024-03-01 processes January 2024 data) rather than a
hardcoded month.

Requires (not installed/run in this environment):
    pip install -r orchestration/requirements.txt
And an Airflow home with this file copied into its `dags/` folder.
"""
from __future__ import annotations

import json
import logging
from datetime import timedelta
from pathlib import Path

import requests
from airflow import DAG
from airflow.exceptions import AirflowFailException, AirflowSkipException
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

logger = logging.getLogger(__name__)

# Repo-relative paths; BashOperator tasks `cd` into this before running sbt/curl.
PROJECT_ROOT = "/workspaces/Scala_Project_NYC_TAXI"
TLC_BASE_URL = "https://d37ci6vzurychx.cloudfront.net"

# Fail the run loudly if more than this share of raw rows gets dropped -
# a sudden spike usually means TLC changed their schema, not that the
# data is fine (see ROADMAP.md "validate_output").
MAX_DROPPED_PCT = 20.0

default_args = {
    "owner": "nyc-taxi-etl",
    "retries": 2,
    "retry_delay": timedelta(minutes=15),
}


def _year_month(logical_date) -> str:
    """TLC publishes with ~2 month lag, so a DAG run scheduled for month M
    processes data for month M-2. `logical_date` is a pendulum DateTime,
    which supports `.subtract(...)` directly."""
    return logical_date.subtract(months=2).strftime("%Y-%m")


def discover_available_month(logical_date=None, **_context) -> None:
    """HEAD-request the target month's yellow file; skip the run if TLC
    hasn't published it yet instead of failing (it's not an error, just
    early)."""
    ym = _year_month(logical_date)
    url = f"{TLC_BASE_URL}/trip-data/yellow_tripdata_{ym}.parquet"
    resp = requests.head(url, timeout=30)
    if resp.status_code != 200:
        raise AirflowSkipException(
            f"{ym} not published yet at {url} (status {resp.status_code})"
        )
    logger.info("Confirmed %s is available at %s", ym, url)


def skip_if_already_processed(logical_date=None, **_context) -> None:
    """Guard against reprocessing a month whose output partition already
    exists. `Load.writeParquet`'s dynamic-partition-overwrite fix makes a
    rerun *safe* (it only replaces that month, not the whole dataset), but
    it's still wasted download/Spark work - skip it instead. Partition dirs
    are named by Spark's `year`/`month` int columns, e.g. `year=2024/month=1`
    (no zero-padding), which differs from the YYYY-MM strings used for raw
    filenames elsewhere in this DAG."""
    target = logical_date.subtract(months=2)
    partition_dir = (
        Path(PROJECT_ROOT) / "data" / "output" / f"year={target.year}" / f"month={target.month}"
    )
    if partition_dir.exists() and any(partition_dir.iterdir()):
        raise AirflowSkipException(
            f"{partition_dir} already exists - {target.strftime('%Y-%m')} was already processed"
        )


def validate_output(logical_date=None, **_context) -> None:
    """Sanity-check the quality summary this run's ETL step just wrote."""
    ym = _year_month(logical_date)
    summary_path = Path(PROJECT_ROOT) / "data" / "quality_summary" / f"{ym}.json"
    summary = json.loads(summary_path.read_text())

    if summary["rawCount"] <= 0:
        raise AirflowFailException(f"{ym}: rawCount is {summary['rawCount']}, expected > 0")
    if summary["droppedPct"] > MAX_DROPPED_PCT:
        raise AirflowFailException(
            f"{ym}: droppedPct {summary['droppedPct']:.2f}% exceeds "
            f"{MAX_DROPPED_PCT}% threshold - check for a TLC schema change"
        )
    logger.info("%s passed validation: %s", ym, summary)


with DAG(
    dag_id="nyc_taxi_monthly_dag",
    description="Download -> ETL -> validate the NYC TLC trip data, monthly",
    default_args=default_args,
    schedule_interval="@monthly",
    start_date=days_ago(1),
    catchup=False,
    max_active_runs=1,
    tags=["nyc-taxi", "etl"],
) as dag:

    # Same month-minus-2 rule as _year_month(), expressed as a Jinja template
    # so it can be interpolated into each BashOperator's shell command below.
    ym = "{{ logical_date.subtract(months=2).strftime('%Y-%m') }}"

    discover = PythonOperator(
        task_id="discover_available_month",
        python_callable=discover_available_month,
    )

    skip_check = PythonOperator(
        task_id="skip_if_already_processed",
        python_callable=skip_if_already_processed,
    )

    download_yellow = BashOperator(
        task_id="download_yellow",
        bash_command=(
            f"mkdir -p {PROJECT_ROOT}/data/raw/yellow/{ym} && "
            f"curl -f -o {PROJECT_ROOT}/data/raw/yellow/{ym}/yellow_tripdata_{ym}.parquet "
            f"{TLC_BASE_URL}/trip-data/yellow_tripdata_{ym}.parquet"
        ),
    )

    download_green = BashOperator(
        task_id="download_green",
        bash_command=(
            f"mkdir -p {PROJECT_ROOT}/data/raw/green/{ym} && "
            f"curl -f -o {PROJECT_ROOT}/data/raw/green/{ym}/green_tripdata_{ym}.parquet "
            f"{TLC_BASE_URL}/trip-data/green_tripdata_{ym}.parquet"
        ),
    )

    download_zone_lookup = BashOperator(
        task_id="download_zone_lookup",
        # Static reference file, not month-specific - re-downloaded each run in case TLC updates it.
        bash_command=(
            f"mkdir -p {PROJECT_ROOT}/data/raw && "
            f"curl -f -o {PROJECT_ROOT}/data/raw/taxi_zone_lookup.csv "
            f"{TLC_BASE_URL}/misc/taxi_zone_lookup.csv"
        ),
    )

    run_etl = BashOperator(
        task_id="run_etl",
        bash_command=(
            f"cd {PROJECT_ROOT} && "
            f"mkdir -p data/quality_summary && "
            f"sbt \"run "
            f"data/raw/yellow/{ym} "
            f"data/raw/green/{ym} "
            f"data/raw/taxi_zone_lookup.csv "
            f"data/output "
            f"data/quality_summary/{ym}.json\""
        ),
    )

    validate = PythonOperator(
        task_id="validate_output",
        python_callable=validate_output,
    )

    notify = BashOperator(
        task_id="notify",
        # Placeholder - swap for an EmailOperator/SlackWebhookOperator once
        # a notification channel is chosen; runs regardless of upstream
        # success/failure so a bad run doesn't go unnoticed.
        bash_command=f'echo "nyc_taxi_monthly_dag run for {ym}: {{{{ task_instance.state }}}}"',
        trigger_rule="all_done",
    )

    discover >> skip_check >> [download_yellow, download_green, download_zone_lookup] >> run_etl >> validate >> notify
