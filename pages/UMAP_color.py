import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from pandas.api.types import (
    is_bool_dtype,
    is_categorical_dtype,
    is_numeric_dtype,
)

# Get dataframe from session state
df = st.session_state.get("data")

st.set_page_config(page_title="UMAP – Colored by Feature    ", layout="wide")
st.markdown("""
# UMAP colored by Feature
Colors UMAP plot by various features.
Mind that legend will not be displayed if feature has more than 41 categories.
""")
# Guard clause
if df is None:
    st.error("No dataset found in session_state under key 'data'.")
    st.stop()

# ---------------------------------------------------------------------
# 1. Detect categorical vs numeric columns (bool → categorical)
# ---------------------------------------------------------------------
coord_cols = {"umap1", "umap2"}

other_cols = [c for c in df.columns if c not in coord_cols]

categorical_cols = []
numeric_cols = []

for col in other_cols:
    s = df[col]
    if is_bool_dtype(s) or is_categorical_dtype(s) or s.dtype == "object":
        categorical_cols.append(col)
    elif is_numeric_dtype(s):
        numeric_cols.append(col)

if not categorical_cols and not numeric_cols:
    st.error("No non-UMAP columns found to use as color variables.")
    st.stop()

# ---------------------------------------------------------------------
# 2. Radio: choose categorical vs numerical
# ---------------------------------------------------------------------
default_color_type = "categorical" if categorical_cols else "numerical"

color_type = st.radio(
    "Type of color variable",
    ["categorical", "numerical"],
    index=0 if default_color_type == "categorical" else 1,
    horizontal=True,
    key="umap_color_type",
)

# Fallback if chosen type has no columns
if color_type == "categorical" and not categorical_cols:
    st.warning("No categorical columns detected, switching to numerical.")
    color_type = "numerical"
elif color_type == "numerical" and not numeric_cols:
    st.warning("No numerical columns detected, switching to categorical.")
    color_type = "categorical"

# ---------------------------------------------------------------------
# 3. Column selector based on radio
# ---------------------------------------------------------------------
if color_type == "categorical":
    color_col = st.selectbox(
        "Categorical column to color by",
        options=sorted(categorical_cols),
        key="umap_cat_color_col",
    )
else:
    color_col = st.selectbox(
        "Numerical column to color by",
        options=sorted(numeric_cols),
        key="umap_num_color_col",
    )

# ---------------------------------------------------------------------
# 4. Plotting: discrete legend (categorical) vs colorbar (numeric)
# ---------------------------------------------------------------------
with st.spinner("Plotting..."):
    fig, ax = plt.subplots()

    fig, ax = plt.subplots(figsize=(6, 5))

    if color_type == "categorical":
        # --- overlay style: grey background + colored categories ---
        ax.scatter(
            df["umap1"], df["umap2"],
            s=1, alpha=0.15, color="lightgrey", label="_background_"
        )

        cats = sorted(
            df[color_col].dropna().unique().tolist(),
            key=lambda x: str(x)
        )
        cmap = plt.get_cmap("tab20")
        colors = {cat: cmap(i % 20) for i, cat in enumerate(cats)}

        # Draw overlay
        for cat in cats:
            subset = df[df[color_col] == cat]
            if subset.empty:
                continue
            ax.scatter(
                subset["umap1"], subset["umap2"],
                s=1, alpha=0.8,
                label=str(cat),
                color=colors[cat],
            )

        # # Missing values shown separately
        # if df[color_col].isna().any():
        #     subset_na = df[df[color_col].isna()]
        #     ax.scatter(
        #         subset_na["umap1"], subset_na["umap2"],
        #         s=3, alpha=0.4, marker="x",
        #         label="(missing)", color="black",
        #     )

        # ---------- NEW FEATURE: disable legend if too many categories ----------
        max_legend_categories = 41

        if len(cats) <= max_legend_categories:
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                fig.legend(
                    handles, labels,
                    title=f"{color_col}",
                    loc="right",
                    bbox_to_anchor=(1.18, 0.5),
                    fontsize="small",
                )
            fig.tight_layout(rect=[0, 0, 0.82, 1])
        else:
            # No legend → normal tight layout
            fig.tight_layout()

    else:
        # numerical → continuous colormap + colorbar
        values = df[color_col].astype(float)
        sc = ax.scatter(
            df["umap1"],
            df["umap2"],
            s=1,
            alpha=0.8,
            c=values,
            cmap="viridis",
        )
        cbar = fig.colorbar(sc, ax=ax)
        cbar.set_label(color_col)
        fig.tight_layout()

    ax.set_xlabel("umap1")
    ax.set_ylabel("umap2")
    ax.set_title(f"UMAP colored by {color_col} ({color_type})")

    st.pyplot(fig)
