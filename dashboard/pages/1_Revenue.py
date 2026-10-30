import plotly.graph_objects as go
import streamlit as st

from lib.data import download_button, get_filtered_trips
from lib.theme import BLUE_SEQUENTIAL, CATEGORICAL, DAY_ORDER, TEXT_MUTED, apply_chart_theme

st.set_page_config(page_title="Revenue — NYC Taxi ETL", layout="wide")
st.title("Revenue")

filtered = get_filtered_trips()

st.header("When do we earn the most money?")
st.caption("Total revenue by day of week and hour of day.")
revenue_grid = (
    filtered.groupby(["day_of_week", "hour_of_day"])["total_amount"]
    .sum()
    .reset_index()
    .pivot(index="day_of_week", columns="hour_of_day", values="total_amount")
    .reindex(DAY_ORDER)
)
fig_revenue = go.Figure(
    data=go.Heatmap(
        z=revenue_grid.values,
        x=revenue_grid.columns,
        y=revenue_grid.index,
        colorscale=BLUE_SEQUENTIAL,
        colorbar=dict(title="Revenue ($)", tickfont=dict(color=TEXT_MUTED)),
        hovertemplate="%{y}, %{x}:00 — $%{z:,.0f}<extra></extra>",
    )
)
apply_chart_theme(fig_revenue, xaxis_title="Hour of day")
st.plotly_chart(fig_revenue, use_container_width=True)
with st.expander("View as table"):
    st.dataframe(revenue_grid)
    download_button(revenue_grid.reset_index(), "Download as CSV", "revenue_by_day_hour.csv")

st.header("Which pickup zones generate the most revenue?")
zones = (
    filtered.dropna(subset=["pu_zone"])
    .groupby(["pu_zone", "pu_borough"])["total_amount"]
    .sum()
    .reset_index()
    .sort_values("total_amount", ascending=False)
    .head(15)
)
zones["zone_label"] = zones["pu_zone"] + " (" + zones["pu_borough"] + ")"
fig_zones = go.Figure(
    go.Bar(
        x=zones["total_amount"],
        y=zones["zone_label"],
        orientation="h",
        marker_color=CATEGORICAL[0],
        text=[f"${v:,.0f}" for v in zones["total_amount"]],
        textposition="outside",
        hovertemplate="%{y}: $%{x:,.0f}<extra></extra>",
    )
)
fig_zones.update_yaxes(autorange="reversed")
apply_chart_theme(fig_zones, xaxis_title="Total revenue ($)")
st.plotly_chart(fig_zones, use_container_width=True)
with st.expander("View as table"):
    st.dataframe(zones[["pu_zone", "pu_borough", "total_amount"]], use_container_width=True)
    download_button(zones[["pu_zone", "pu_borough", "total_amount"]], "Download as CSV", "top_revenue_zones.csv")
