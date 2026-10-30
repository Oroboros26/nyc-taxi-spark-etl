import plotly.graph_objects as go
import streamlit as st

from lib.data import download_button, get_filtered_trips
from lib.theme import CATEGORICAL, PAYMENT_TYPE_COLORS, PAYMENT_TYPE_NAMES, TEXT_MUTED, apply_chart_theme

st.set_page_config(page_title="Tipping — NYC Taxi ETL", layout="wide")
st.title("Tipping")

filtered = get_filtered_trips()
valid = filtered[filtered["tip_percentage"].between(0, 100)]

st.header("How do people tip, and what factors correlate with higher tips?")
c1, c2 = st.columns(2)
with c1:
    tip_pay = valid.groupby("payment_type")["tip_percentage"].mean().reset_index()
    tip_pay["payment_type_name"] = tip_pay["payment_type"].map(PAYMENT_TYPE_NAMES).fillna("Unknown code")
    tip_pay = tip_pay.sort_values("payment_type")
    colors = [PAYMENT_TYPE_COLORS.get(pt, TEXT_MUTED) for pt in tip_pay["payment_type"]]
    fig_tip_pay = go.Figure(
        go.Bar(
            x=tip_pay["payment_type_name"],
            y=tip_pay["tip_percentage"],
            marker_color=colors,
            text=[f"{v:.1f}%" for v in tip_pay["tip_percentage"]],
            textposition="outside",
        )
    )
    apply_chart_theme(fig_tip_pay, yaxis_title="Avg tip (%)")
    st.caption("Average tip % by payment type")
    st.plotly_chart(fig_tip_pay, use_container_width=True)
with c2:
    tip_hour = valid.groupby("hour_of_day")["tip_percentage"].mean().reset_index()
    fig_tip_hour = go.Figure(
        go.Scatter(
            x=tip_hour["hour_of_day"],
            y=tip_hour["tip_percentage"],
            mode="lines+markers",
            line=dict(color=CATEGORICAL[0], width=2),
            marker=dict(size=8),
        )
    )
    apply_chart_theme(fig_tip_hour, xaxis_title="Hour of day", yaxis_title="Avg tip (%)")
    st.caption("Average tip % by hour of day")
    st.plotly_chart(fig_tip_hour, use_container_width=True)
with st.expander("View as table"):
    st.dataframe(tip_pay[["payment_type_name", "tip_percentage"]], use_container_width=True)
    download_button(tip_pay[["payment_type_name", "tip_percentage"]], "Download tip-by-payment CSV", "tip_by_payment.csv")
    st.dataframe(tip_hour, use_container_width=True)
    download_button(tip_hour, "Download tip-by-hour CSV", "tip_by_hour.csv")
