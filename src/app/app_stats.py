"""
Groundwater statistical dashboard

Run: streamlit run app_stats.py
"""

# --------------------------- LIBRARY --------------------------------
import pandas as pd
import streamlit as st
import numpy as np


import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.seasonal import STL
from src.helper.constants import DRIVER_LABELS, TARGET_COL, SPLI_COL, DROUGHT_THRESHOLDS, DROUGHT_EVENT_THRESHOLD
from src.helper.indices import (characterize_events, cross_corr, longest_and_most_intense,
                                monthly, to_datetime_index)
from src.helper.theme import PLOTLY_LAYOUT, C_INK, C_BLUE, C_TEAL,C_DEEP, C_GRID, RDBU, DRIVER_PALETTE



# --------------------------------------------------------------------------- #
# Cached computations (Streamlit wrapper around the pure helpers)
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner=False)
def spli_droughts(spli_monthly: pd.Series):
    """Return (events_df, longest_event, most_intense_event) for the SPLI series."""
    events = characterize_events(spli_monthly, threshold=DROUGHT_EVENT_THRESHOLD)
    longest, most_intense = longest_and_most_intense(events)
    return events, longest, most_intense

# --------------------------------------------------------------------------- #
# Chart builders
# --------------------------------------------------------------------------- #
def fig_stl(gwl: pd.Series) -> go.Figure:
    """STL decomposition of the raw groundwater level (temporal — Noise section)."""
    series = gwl.dropna()
    stl = STL(series, period=365, robust=True).fit()
    parts = [
        ("Observed groundwater level", series, C_INK),
        ("Trend: long-term movement", stl.trend, C_DEEP),
        ("Seasonal: repeating yearly cycle", stl.seasonal, C_TEAL),
        ("Residual: noise & anomalies", stl.resid, C_BLUE),
    ]
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                        subplot_titles=[p[0] for p in parts])
    for i, (name, s, color) in enumerate(parts, start=1):
        fig.add_trace(go.Scatter(x=s.index, y=s.values, mode="lines", name=name,
                                 line=dict(color=color, width=1.1)), row=i, col=1)
        if name.startswith("Residual"):
            fig.add_hline(y=0, line=dict(color="grey", width=0.6, dash="dot"), row=i, col=1)
    fig.update_layout(**PLOTLY_LAYOUT, height=760, showlegend=False,
                      title="Signal, seasonality & noise (STL decomposition of the groundwater level)")
    fig.update_yaxes(gridcolor=C_GRID)
    fig.update_xaxes(gridcolor=C_GRID)
    return fig
 
 
def fig_spli_monthly(spli_monthly: pd.Series) -> go.Figure:
    """Monthly SPLI diverging bars with severity lines (temporal — last graph)."""
    vals = spli_monthly.values
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=spli_monthly.index, y=vals,
        marker=dict(color=vals, colorscale=RDBU, cmin=-3, cmax=3,
                    colorbar=dict(title="SPLI", thickness=12)),
        hovertemplate="%{x|%b %Y}<br>SPLI = %{y:.2f}<extra></extra>",
        name="SPLI",
    ))
    for label, y in DROUGHT_THRESHOLDS.items():
        fig.add_hline(y=y, line=dict(color="grey", width=0.7, dash="dash"))
        fig.add_annotation(x=spli_monthly.index[-1], y=y, text=f" {label}",
                           showarrow=False, xanchor="left", font=dict(color="grey", size=10))
    fig.add_hline(y=0, line=dict(color="black", width=0.8))
    fig.update_layout(**PLOTLY_LAYOUT, height=430, showlegend=False,
                      title="Standardised Piezometric Level Index (monthly)")
    fig.update_yaxes(title="SPLI", range=[-3, 3], gridcolor=C_GRID)
    fig.update_xaxes(gridcolor=C_GRID)
    return fig
 
 
def fig_spli_events(gwl: pd.Series, spli_monthly: pd.Series, longest, most_intense) -> go.Figure:
    """Groundwater level + SPLI with extreme-drought boxes
    (red = longest, blue = most intense)."""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.06,
                        subplot_titles=["Groundwater level", "SPLI with extreme droughts"],
                        row_heights=[0.42, 0.58])
    fig.add_trace(go.Scatter(x=gwl.index, y=gwl.values, mode="lines",
                             line=dict(color=C_INK, width=0.8), name="GWL"), row=1, col=1)
    fig.add_trace(go.Bar(
        x=spli_monthly.index, y=spli_monthly.values,
        marker=dict(color=spli_monthly.values, colorscale=RDBU, cmin=-3, cmax=3),
        hovertemplate="%{x|%b %Y}<br>SPLI = %{y:.2f}<extra></extra>",
        showlegend=False), row=2, col=1)
    for y in DROUGHT_THRESHOLDS.values():
        fig.add_hline(y=y, line=dict(color="grey", width=0.5, dash="dash"), row=2, col=1)
    fig.add_hline(y=0, line=dict(color="black", width=0.5), row=2, col=1)
    fig.update_yaxes(range=[-3, 3], row=2, col=1)
    if longest is not None:
        fig.add_vrect(x0=longest["start"], x1=longest["end"], fillcolor="red",
                      opacity=0.15, line_width=0, row=2, col=1,
                      annotation_text="longest", annotation_position="top left",
                      annotation_font_color="#c0392b")
    if most_intense is not None:
        fig.add_vrect(x0=most_intense["start"], x1=most_intense["end"], fillcolor="blue",
                      opacity=0.15, line_width=0, row=2, col=1,
                      annotation_text="most intense", annotation_position="top right",
                      annotation_font_color="#2471a3")
    fig.update_layout(**PLOTLY_LAYOUT, height=560, showlegend=False,
                      title="Extreme droughts on the SPLI (red = longest, blue = most intense)")
    fig.update_yaxes(gridcolor=C_GRID)
    fig.update_xaxes(gridcolor=C_GRID)
    return fig
 
 
def fig_ccf(monthly_indices: dict, selected_drivers, maxlag=12):
    """Cross-correlation of selected drivers vs SPLI (extreme_events — last graph)."""
    resp = monthly_indices[SPLI_COL]
    fig = go.Figure()
    best_txt = []
    for i, name in enumerate(selected_drivers):
        if name not in monthly_indices:
            continue
        c = cross_corr(monthly_indices[name], resp, maxlag)
        lags, rs = list(c.keys()), list(c.values())
        valid = {k: v for k, v in c.items() if not np.isnan(v)}
        if valid:
            best_lag = max(valid, key=valid.get)
            best_txt.append(f"**{DRIVER_LABELS.get(name, name)}** → peak r = "
                            f"{valid[best_lag]:.2f} at lag {best_lag} mo")
        fig.add_trace(go.Scatter(
            x=lags, y=rs, mode="lines+markers", name=DRIVER_LABELS.get(name, name),
            line=dict(color=DRIVER_PALETTE[i % len(DRIVER_PALETTE)], width=2), marker=dict(size=7),
            hovertemplate=DRIVER_LABELS.get(name, name) +
            "<br>lag = %{x} mo<br>r = %{y:.2f}<extra></extra>"))
    fig.add_hline(y=0, line=dict(color="grey", width=0.6))
    layout = {**PLOTLY_LAYOUT, "hovermode": "closest"}
    fig.update_layout(**layout, height=480,
                      title="Cross-correlation of climate drivers with groundwater (SPLI)",
                      legend=dict(orientation="h", yanchor="bottom", y=-0.28))
    fig.update_xaxes(title="Driver leads SPLI (months of lag)", dtick=1,
                     gridcolor=C_GRID, range=[-0.3, maxlag + 0.3])
    fig.update_yaxes(title="Pearson correlation r", gridcolor=C_GRID)
    return fig, best_txt


def render_stats(df_processed: pd.DataFrame):
    if df_processed is None or df_processed.empty:
        st.warning("No dataset loaded.")
        st.stop()
    df = to_datetime_index(df_processed)
    
    # Required columns check
    missing_core = [c for c in (TARGET_COL, SPLI_COL) if c not in df.columns]
    if missing_core:
        st.error(f"Missing required column(s): {missing_core}. "
                f"The dataset must contain `{TARGET_COL}` (raw level) and `{SPLI_COL}` (index).")
        st.stop()
    
    present_drivers = [c for c in DRIVER_LABELS if c in df.columns]
    missing_drivers = [c for c in DRIVER_LABELS if c not in df.columns]
    
    # Monthly views of every available index column
    monthly_indices = {name: monthly(df[name]) for name in [SPLI_COL] + present_drivers}
    spli_m = monthly_indices[SPLI_COL]
    
    # KPI row
    span = f"{df.index.min().date()} → {df.index.max().date()}"
    ev_all, longest, most_intense = spli_droughts(spli_m)    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Records (daily)", f"{len(df):,}")
    k2.metric("Period covered", span)
    k3.metric("Months of SPLI", f"{spli_m.notna().sum()}")
    k4.metric(f"Drought events (SPLI<{DROUGHT_EVENT_THRESHOLD})", f"{len(ev_all)}")
    
    if missing_drivers:
        st.caption(f"Note: driver indices not found in the dataset, skipped: {missing_drivers}")
    
    st.divider()
    
    # ---- Section 1: Temporal structure ----
    st.header("1 · Temporal structure of the groundwater level")
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Signal, seasonality & noise")
    st.markdown(
        '<p class="caption">STL (Seasonal-Trend decomposition using LOESS) splits the daily '
        'level into a slow <b>trend</b>, a repeating <b>seasonal</b> cycle and the residual '
        '<b>noise</b>. LOESS = locally weighted regression fitted on a sliding window; '
        '<code>robust=True</code> down-weights weather anomalies.</p>',
        unsafe_allow_html=True,
    )
    with st.spinner("Fitting STL decomposition…"):
        st.plotly_chart(fig_stl(df[TARGET_COL]), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Standardised Piezometric Level Index (SPLI)")
        st.markdown(
            '<p class="caption">SPLI standardises each month against its own history: 0 is the '
            'historical median, blue is wetter, red drier. Dashed lines mark the standard drought '
            'severity thresholds (moderate −1, severe −1.5, extreme −2). Read directly from the '
            '<code>SPLI</code> column.</p>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(fig_spli_monthly(spli_m), use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)
        
    st.divider()
    
    # ---- Section 2: Extreme events ----
    st.header("2 · Extreme hydrological events")
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Extreme droughts on the SPLI")
    st.markdown(
        '<p class="caption">Droughts detected by events below SPLI = −1.5 '
        '<span style="color:#c0392b;font-weight:600">Red box</span> = longest event, '
        '<span style="color:#2471a3;font-weight:600">blue box</span> = most intense event.</p>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig_spli_events(df[TARGET_COL], spli_m, longest, most_intense), use_container_width=True)
    if longest is not None:
        cA, cB = st.columns(2)
        cA.metric("Longest drought (months)", int(longest["duration_m"]),
                f"{longest['start'].date()} → {longest['end'].date()}")
        cB.metric("Most intense (peak SPLI)", f"{most_intense['peak']:.2f}",
                f"{most_intense['start'].date()} → {most_intense['end'].date()}")
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("What drives the groundwater · lagged cross-correlation")
    st.markdown(
        '<p class="caption">Each curve is the Pearson correlation between a climate driver at '
        'month <i>t</i> and the SPLI at month <i>t + lag</i>. The lag of the peak is the effective '
        '<b>recharge delay</b>. Select drivers and move the lag horizon.</p>',
        unsafe_allow_html=True,
    )
    if not present_drivers:
        st.info("No driver index columns found in the dataset.")
    else:
        default_sel = [n for n in ["SPI", "SPEI", "SSMI"] if n in present_drivers] or present_drivers[:3]
        c_left, c_right = st.columns([2, 1])
        with c_left:
            selected = st.multiselect("Climate drivers to display", options=present_drivers,
                                    default=default_sel,
                                    format_func=lambda n: DRIVER_LABELS.get(n, n))
        with c_right:
            maxlag = st.slider("Max lag (months)", 3, 24, 12)
        if not selected:
            st.info("Select at least one driver above.")
        else:
            fig_c, best_txt = fig_ccf(monthly_indices, selected, maxlag)
            st.plotly_chart(fig_c, use_container_width=True)
            st.markdown("  \n".join(best_txt))
    st.markdown("</div>", unsafe_allow_html=True)
    