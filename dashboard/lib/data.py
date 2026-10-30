import json
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
OUTPUT_DIR = DATA_DIR / "output"
QUALITY_SUMMARY_PATH = DATA_DIR / "quality_summary.json"

# Columns read from the Parquet output - kept to what the dashboard's charts
# actually use, since Spark's columnar format makes a narrow read cheap.
TRIP_COLUMNS = [
    "taxiType",
    "pickupDatetime",
    "trip_distance",
    "trip_duration_minutes",
    "PULocationID",
    "DOLocationID",
    "payment_type",
    "fare_amount",
    "tip_amount",
    "total_amount",
    "is_suspicious_zero_distance",
    "tip_percentage",
    "day_of_week",
    "hour_of_day",
    "pu_borough",
    "pu_zone",
    "do_borough",
]


def require_pipeline_output():
    if not OUTPUT_DIR.exists() or not QUALITY_SUMMARY_PATH.exists():
        st.error(
            "No pipeline output found. Run `sbt run` from the project root first — "
            "it writes data/output/ and data/quality_summary.json."
        )
        st.stop()


@st.cache_data
def load_quality_summary():
    with open(QUALITY_SUMMARY_PATH) as f:
        return json.load(f)


@st.cache_data
def load_trips():
    return pd.read_parquet(OUTPUT_DIR, columns=TRIP_COLUMNS)


def render_sidebar_filters(trips):
    """Renders the shared filter widgets. Uses fixed widget keys so selections
    persist as the user navigates between pages (Streamlit keeps session_state
    for the lifetime of the browser session, independent of which page script
    is currently running)."""
    st.sidebar.header("Filters")

    min_date = trips["pickupDatetime"].min().date()
    max_date = trips["pickupDatetime"].max().date()
    date_range = st.sidebar.date_input(
        "Pickup date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="filter_date_range",
    )

    taxi_types = sorted(trips["taxiType"].dropna().unique())
    selected_types = st.sidebar.multiselect(
        "Taxi type", taxi_types, default=taxi_types, key="filter_taxi_types"
    )

    boroughs = sorted(trips["pu_borough"].dropna().unique())
    selected_boroughs = st.sidebar.multiselect(
        "Pickup borough", boroughs, default=boroughs, key="filter_boroughs"
    )

    return date_range, selected_types, selected_boroughs


def apply_filters(trips, date_range, selected_types, selected_boroughs):
    df = trips
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        df = df[(df["pickupDatetime"].dt.date >= start) & (df["pickupDatetime"].dt.date <= end)]
    if selected_types:
        df = df[df["taxiType"].isin(selected_types)]
    if selected_boroughs:
        df = df[df["pu_borough"].isin(selected_boroughs)]
    return df


def get_filtered_trips():
    """Convenience used by every page: load, render the sidebar, filter, and
    warn (rather than crash) if the selection is empty."""
    require_pipeline_output()
    trips = load_trips()
    date_range, selected_types, selected_boroughs = render_sidebar_filters(trips)
    filtered = apply_filters(trips, date_range, selected_types, selected_boroughs)
    if filtered.empty:
        st.warning("No trips match the current filter selection.")
        st.stop()
    return filtered


def download_button(df, label, file_name):
    st.download_button(
        label,
        df.to_csv(index=False).encode("utf-8"),
        file_name=file_name,
        mime="text/csv",
    )
