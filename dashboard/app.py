import plotly.graph_objects as go
import streamlit as st

from lib.data import download_button, get_filtered_trips, load_quality_summary
from lib.theme import TAXI_TYPE_COLORS, apply_chart_theme, format_compact

st.set_page_config(page_title="NYC Taxi ETL & Analytics", layout="wide")

st.title("NYC Taxi ETL & Analytics Pipeline")
st.caption("Yellow + Green trips — cleaned and enriched by the Scala/Spark ETL pipeline.")

filtered = get_filtered_trips()
quality = load_quality_summary()
valid_tips = filtered["tip_percentage"].between(0, 100)

st.subheader("Key metrics")
row1 = st.columns(4)
row1[0].metric("Total revenue", format_compact(filtered["total_amount"].sum(), prefix="$"))
row1[1].metric("Total trips", format_compact(len(filtered)))
row1[2].metric("Avg fare per trip", f"${filtered['fare_amount'].mean():.2f}")
row1[3].metric("Avg tip", f"{filtered.loc[valid_tips, 'tip_percentage'].mean():.1f}%" if valid_tips.any() else "n/a")

row2 = st.columns(4)
row2[0].metric("Avg trip distance", f"{filtered['trip_distance'].mean():.1f} mi")
row2[1].metric("Avg trip duration", f"{filtered['trip_duration_minutes'].mean():.0f} min")
peak_hour = int(filtered.groupby("hour_of_day")["total_amount"].sum().idxmax())
row2[2].metric("Peak revenue hour", f"{peak_hour:02d}:00")
row2[3].metric("Data-quality score", f"{100 - quality['droppedPct']:.1f}%")

st.caption(
    "The metrics above reflect the current filter selection, except data-quality "
    "score, which is pipeline-wide (share of raw rows that passed validation) — "
    "see the Data Quality page for details."
)

st.divider()

st.subheader("Revenue and demand trend")
st.caption("Aggregated by month, since the pipeline itself runs and partitions output monthly.")
trend_source = filtered.copy()
trend_source["year_month"] = trend_source["pickupDatetime"].dt.to_period("M").astype(str)
trend = (
    trend_source.groupby("year_month")
    .agg(revenue=("total_amount", "sum"), trips=("total_amount", "size"))
    .reset_index()
    .sort_values("year_month")
)

if len(trend) < 2:
    st.info("Only one month is selected — add more months to the filter to see a trend.")
else:
    tcol1, tcol2 = st.columns(2)
    with tcol1:
        fig_rev_trend = go.Figure(
            go.Scatter(
                x=trend["year_month"],
                y=trend["revenue"],
                mode="lines+markers",
                line=dict(color=TAXI_TYPE_COLORS["yellow"], width=2),
                marker=dict(size=8),
                hovertemplate="%{x}: $%{y:,.0f}<extra></extra>",
            )
        )
        apply_chart_theme(fig_rev_trend, yaxis_title="Revenue ($)")
        st.caption("Monthly revenue")
        st.plotly_chart(fig_rev_trend, use_container_width=True)
    with tcol2:
        fig_trip_trend = go.Figure(
            go.Scatter(
                x=trend["year_month"],
                y=trend["trips"],
                mode="lines+markers",
                line=dict(color=TAXI_TYPE_COLORS["green"], width=2),
                marker=dict(size=8),
                hovertemplate="%{x}: %{y:,.0f} trips<extra></extra>",
            )
        )
        apply_chart_theme(fig_trip_trend, yaxis_title="Trips")
        st.caption("Monthly trip count")
        st.plotly_chart(fig_trip_trend, use_container_width=True)
    with st.expander("View as table"):
        st.dataframe(trend, use_container_width=True)
        download_button(trend, "Download as CSV", "monthly_trend.csv")

st.divider()

st.subheader("Revenue by taxi type")
by_type = filtered.groupby("taxiType")["total_amount"].sum().reindex(["yellow", "green"]).dropna()
fig_split = go.Figure()
running_total = 0
for taxi_type, revenue in by_type.items():
    fig_split.add_trace(
        go.Bar(
            name=taxi_type.capitalize(),
            x=[revenue],
            y=["Revenue"],
            orientation="h",
            marker_color=TAXI_TYPE_COLORS[taxi_type],
            text=f"{taxi_type.capitalize()}: ${revenue:,.0f}",
            textposition="inside",
            hovertemplate=f"{taxi_type.capitalize()}: $%{{x:,.0f}}<extra></extra>",
        )
    )
    running_total += revenue
fig_split.update_layout(barmode="stack")
apply_chart_theme(fig_split, xaxis_title="Total revenue ($)", show_legend=True)
fig_split.update_yaxes(visible=False)
st.plotly_chart(fig_split, use_container_width=True)
with st.expander("View as table"):
    split_table = by_type.reset_index().rename(columns={"total_amount": "revenue"})
    st.dataframe(split_table, use_container_width=True)
    download_button(split_table, "Download as CSV", "revenue_by_taxi_type.csv")

st.divider()
st.markdown(
    "Use the pages in the sidebar for **Revenue**, **Demand**, **Tipping**, and "
    "**Data Quality** deep-dives — each respects the filters set here."
)
