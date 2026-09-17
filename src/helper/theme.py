"""
Visual identity of the NappeCast app: colours and Plotly layout.
No Streamlit import here -> importable by any chart module.
"""
from types import MappingProxyType
from typing import Final

# ---------------------------- PALETTE ----------------------------
C_DEEP: Final = "#0b4f6c"   # deep water blue (headers)
C_BLUE = "#1b98c9"      # mid blue (accent)
C_TEAL = "#20a4a0"      # teal-green
C_INK = "#12333f"      # near-black ink for text
C_GRID = "#d8e6ec"      # light grid
C_BG = "#f5fafc"        # very light background
RDBU = "RdBu"           # diverging colormap for standardized indices

# Water / hydro palette
DRIVER_PALETTE: Final = (
    (C_BLUE, C_TEAL, C_DEEP, "#e07b39", "#8e5ea2", "#3cb371", "#c0504d", "#4f81bd", "#9bbb59")
)

# ---------------------------- PLOTLY ----------------------------
PLOTLY_LAYOUT: Final = MappingProxyType(dict(
    template="plotly_white",
    font=dict(family="Inter, Segoe UI, sans-serif", color=C_INK, size=13),
    title_font=dict(color=C_DEEP, size=18),
    margin=dict(l=60, r=30, t=60, b=50),
    plot_bgcolor="white",
    paper_bgcolor="white",
    hovermode="x unified",
))
