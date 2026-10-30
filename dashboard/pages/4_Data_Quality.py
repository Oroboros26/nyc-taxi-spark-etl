import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib.data import download_button, get_filtered_trips, load_quality_summary
from lib.theme import CATEGORICAL, STATUS_GOOD, STATUS_WARNING, apply_chart_theme

st.set_page_config(page_title="Data Quality — NYC Taxi ETL", layout="wide")
st.title("Data Quality")

filtered = get_filtered_trips()
quality = load_quality_summary()

st.header("What percentage of raw rows were invalid, and why?")
st.caption(
    "Pipeline-wide, from the full ETL run — dropped rows never reach the Parquet output, "
    "so this section is not affected by the sidebar filters."
)

col1, col2, col3 = st.columns(3)
col1.metric("Raw rows", f"{quality['rawCount']:,}")
col2.metric("Clean rows", f"{quality['cleanCount']:,}")
col3.metric("Dropped (invalid)", f"{quality['droppedCount']:,}", f"-{quality['droppedPct']:.2f}%")

status_color = STATUS_GOOD if quality["droppedPct"] < 5 else STATUS_WARNING
st.markdown(
    f"<span style='color:{status_color}'>&#9679;</span> "
    f"{quality['droppedPct']:.2f}% of raw rows failed data-quality checks "
    f"(bad fares, timestamps, or missing zones). A further {quality['suspiciousPct']:.2f}% of "
    f"clean rows were flagged — not dropped — for zero trip distance with a nonzero fare.",
    unsafe_allow_html=True,
)

fig_breakdown = go.Figure(
    go.Bar(
        x=["Clean", "Dropped", "Suspicious (subset of clean)"],
        y=[quality["cleanCount"], quality["droppedCount"], quality["suspiciousCount"]],
        marker_color=[CATEGORICAL[2], CATEGORICAL[7], CATEGORICAL[3]],
        text=[f"{v:,}" for v in [quality["cleanCount"], quality["droppedCount"], quality["suspiciousCount"]]],
        textposition="outside",
    )
)
apply_chart_theme(fig_breakdown, yaxis_title="Rows")
st.plotly_chart(fig_breakdown, use_container_width=True)

with st.expander("View pipeline-wide summary as table"):
    summary_table = pd.DataFrame([quality])
    st.dataframe(summary_table, use_container_width=True)
    download_button(summary_table, "Download as CSV", "quality_summary.csv")

st.divider()
st.header("Within the current filter selection")
suspicious_in_filter = int(filtered["is_suspicious_zero_distance"].sum())
st.metric(
    "Suspicious rows (zero-distance, nonzero-fare)",
    f"{suspicious_in_filter:,}",
    f"{100 * suspicious_in_filter / len(filtered):.2f}% of filtered rows",
)
