SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
AXIS_LINE = "#c3c2b7"
FONT_FAMILY = "system-ui, -apple-system, 'Segoe UI', sans-serif"

CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
BLUE_SEQUENTIAL = [[0.0, "#cde2fb"], [0.2, "#9ec5f4"], [0.4, "#5598e7"], [0.6, "#2a78d6"], [0.8, "#184f95"], [1.0, "#0d366b"]]
STATUS_GOOD = "#0ca30c"
STATUS_WARNING = "#fab219"

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

PAYMENT_TYPE_NAMES = {1: "Credit card", 2: "Cash", 3: "No charge", 4: "Dispute", 5: "Unknown", 6: "Voided trip"}
PAYMENT_TYPE_COLORS = {code: CATEGORICAL[i % len(CATEGORICAL)] for i, code in enumerate(PAYMENT_TYPE_NAMES)}

# Fixed (not cycled) slots from CATEGORICAL, chosen to match what "yellow"/"green"
# taxi actually mean rather than an arbitrary hue assignment.
TAXI_TYPE_COLORS = {"yellow": CATEGORICAL[3], "green": CATEGORICAL[2]}


def format_compact(value, prefix=""):
    """Stat-tile value formatting: 1,284 / 12.9K / $4.2M."""
    magnitude = abs(value)
    if magnitude >= 1_000_000:
        return f"{prefix}{value / 1_000_000:.1f}M"
    if magnitude >= 1_000:
        return f"{prefix}{value / 1_000:.1f}K"
    return f"{prefix}{value:,.0f}"


def apply_chart_theme(fig, xaxis_title="", yaxis_title="", show_legend=False):
    fig.update_layout(
        plot_bgcolor=SURFACE,
        paper_bgcolor=SURFACE,
        font=dict(color=TEXT_PRIMARY, family=FONT_FAMILY),
        xaxis=dict(title=xaxis_title, gridcolor=GRIDLINE, linecolor=AXIS_LINE, tickfont=dict(color=TEXT_MUTED)),
        yaxis=dict(title=yaxis_title, gridcolor=GRIDLINE, linecolor=AXIS_LINE, tickfont=dict(color=TEXT_MUTED)),
        showlegend=show_legend,
        margin=dict(l=10, r=10, t=30, b=10),
    )
    return fig
