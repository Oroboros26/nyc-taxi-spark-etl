import plotly.graph_objects as go
import streamlit as st

from lib.data import download_button, get_filtered_trips
from lib.theme import BLUE_SEQUENTIAL, DAY_ORDER, TEXT_MUTED, apply_chart_theme

st.set_page_config(page_title="Demand — NYC Taxi ETL", layout="wide")
st.title("Demand")

filtered = get_filtered_trips()

st.header("When is rider demand highest?")
st.caption("Trip count by day of week and hour of day.")
demand_grid = (
    filtered.groupby(["day_of_week", "hour_of_day"])
    .size()
    .reset_index(name="trip_count")
    .pivot(index="day_of_week", columns="hour_of_day", values="trip_count")
    .reindex(DAY_ORDER)
)
fig_demand = go.Figure(
    data=go.Heatmap(
        z=demand_grid.values,
        x=demand_grid.columns,
        y=demand_grid.index,
        colorscale=BLUE_SEQUENTIAL,
        colorbar=dict(title="Trips", tickfont=dict(color=TEXT_MUTED)),
        hovertemplate="%{y}, %{x}:00 — %{z:,.0f} trips<extra></extra>",
    )
)
apply_chart_theme(fig_demand, xaxis_title="Hour of day")
st.plotly_chart(fig_demand, use_container_width=True)
with st.expander("View as table"):
    st.dataframe(demand_grid)
    download_button(demand_grid.reset_index(), "Download as CSV", "demand_by_day_hour.csv")
