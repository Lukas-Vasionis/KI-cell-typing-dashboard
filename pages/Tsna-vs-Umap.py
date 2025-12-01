# TSNA vs UMAP with hierarchical taxonomy selectors

import streamlit as st
import matplotlib.pyplot as plt

# Get dataframe from session state
df = st.session_state.get("data")

st.title("Annotation view: UMAP vs TSNA")
"""
This plot shows how our annotations lay on coordinates of UMAP (produced by our processing) and TSNA (produced by authors of the paper)
"""

# Guard clause
if df is None:
    st.error("No dataset found in session_state under key 'data'.")
    st.stop()


# ---------------------------------------------------------------------
# Helpers for hierarchical taxonomy selectors
# ---------------------------------------------------------------------
def get_level_options(df, level, parent_level=None, parent_selection=None):
    """
    Return sorted unique categories for `level` given parent selection.
    If parent_selection is empty/None or parent_level is None, don't filter by parent.
    """
    if parent_level is None or not parent_selection:
        series = df[level]
    else:
        mask = df[parent_level].isin(parent_selection)
        series = df.loc[mask, level]

    return sorted(series.dropna().unique().tolist())


def taxonomy_selectors(df, key_prefix="tsne_umap_tax_", state_prefix="tsne_umap_saved_"):
    """Build linked widgets for supercluster → cluster → subcluster
    and persist selections for this page via session_state."""
    # --- SUPERCLUSTER ---
    widget_super = f"{key_prefix}super"
    state_super = f"{state_prefix}super"

    super_options = get_level_options(df, "supercluster_name")

    # init saved state once
    if state_super not in st.session_state:
        st.session_state[state_super] = []

    # keep only valid saved values
    saved_super = [v for v in st.session_state[state_super] if v in super_options]

    selected_super = st.multiselect(
        "Select supercluster_name (optional)",
        options=super_options,
        default=saved_super,
        key=widget_super,
    )
    st.session_state[state_super] = selected_super

    # --- CLUSTER (depends on supercluster) ---
    widget_cluster = f"{key_prefix}cluster"
    state_cluster = f"{state_prefix}cluster"

    cluster_options = get_level_options(
        df,
        "cluster_name",
        parent_level="supercluster_name",
        parent_selection=selected_super,
    )

    if state_cluster not in st.session_state:
        st.session_state[state_cluster] = []

    saved_cluster = [v for v in st.session_state[state_cluster] if v in cluster_options]

    selected_cluster = st.multiselect(
        "Select cluster_name (optional)",
        options=cluster_options,
        default=saved_cluster,
        key=widget_cluster,
    )
    st.session_state[state_cluster] = selected_cluster

    # --- SUBCLUSTER (depends on cluster) ---
    widget_sub = f"{key_prefix}subcluster"
    state_sub = f"{state_prefix}subcluster"

    subcluster_options = get_level_options(
        df,
        "subcluster_name",
        parent_level="cluster_name",
        parent_selection=selected_cluster,
    )

    if state_sub not in st.session_state:
        st.session_state[state_sub] = []

    saved_sub = [v for v in st.session_state[state_sub] if v in subcluster_options]

    selected_subcluster = st.multiselect(
        "Select subcluster_name (optional)",
        options=subcluster_options,
        default=saved_sub,
        key=widget_sub,
    )
    st.session_state[state_sub] = selected_subcluster

    return {
        "supercluster_name": selected_super,
        "cluster_name": selected_cluster,
        "subcluster_name": selected_subcluster,
    }



def get_active_level(selections):
    """Return the lowest non-empty level, or None if nothing is selected."""
    if selections["subcluster_name"]:
        return "subcluster_name"
    if selections["cluster_name"]:
        return "cluster_name"
    if selections["supercluster_name"]:
        return "supercluster_name"
    return None


def split_selected_other(df, selections):
    """
    Based on lowest non-empty level:
      - return df_selected (only selected categories at that level)
      - df_other (all remaining rows)
      - active_level
    If nothing selected: return (None, None, None).
    """
    level = get_active_level(selections)
    if level is None:
        return None, None, None

    selected_values = selections[level]
    mask = df[level].isin(selected_values)

    df_selected = df[mask].copy()
    df_other = df[~mask].copy()

    return df_selected, df_other, level


# ---------------------------------------------------------------------
# Widgets + plotting
# ---------------------------------------------------------------------

# 1) Hierarchical taxonomy widgets
selections = taxonomy_selectors(df, key_prefix="tsne_umap_tax_")
active_level = get_active_level(selections)

st.caption(
    f"Lowest non-empty selection level: **{active_level or 'none'}** "
    f"(super: {len(selections['supercluster_name'])}, "
    f"cluster: {len(selections['cluster_name'])}, "
    f"subcluster: {len(selections['subcluster_name'])})"
)

# 2) Prepare figure
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4), sharex=False, sharey=False)

# ---------- Case A: some selection exists → highlight selected vs others ----------
df_selected, df_other, level = split_selected_other(df, selections)

if level is not None:
    # Plot "other" cells in grey background
    if not df_other.empty:
        ax1.scatter(df_other["umap1"], df_other["umap2"], s=1, alpha=0.2, color="lightgrey", label="_nolegend_")
        ax2.scatter(df_other["tsna1"], df_other["tsna2"], s=1, alpha=0.2, color="lightgrey", label="_nolegend_")

    # Color map for selected categories
    cats = sorted(df_selected[level].dropna().unique().tolist())
    cmap = plt.get_cmap("tab20")
    colors = {cat: cmap(i % 20) for i, cat in enumerate(cats)}

    for cat in cats:
        subset = df_selected[df_selected[level] == cat]
        ax1.scatter(
            subset["umap1"], subset["umap2"],
            s=3, alpha=0.8, label=str(cat),
            color=colors[cat],
        )
        ax2.scatter(
            subset["tsna1"], subset["tsna2"],
            s=3, alpha=0.8, label=str(cat),
            color=colors[cat],
        )

    legend_title = f"{level} (selected)"

# ---------- Case B: no selection → fallback to coloring by supercluster ----------
else:
    taxonomy_column = "supercluster_name"
    cats = df[taxonomy_column].dropna().unique()
    cmap = plt.get_cmap("tab20")
    colors = {cat: cmap(i % 20) for i, cat in enumerate(cats)}

    for cat in cats:
        subset = df[df[taxonomy_column] == cat]
        ax1.scatter(
            subset["umap1"], subset["umap2"],
            s=1, alpha=0.7, label=str(cat),
            color=colors[cat],
        )
        ax2.scatter(
            subset["tsna1"], subset["tsna2"],
            s=1, alpha=0.7, label=str(cat),
            color=colors[cat],
        )

    # Plot NaN separately if exists
    if df[taxonomy_column].isna().any():
        subset_na = df[df[taxonomy_column].isna()]
        ax1.scatter(
            subset_na["umap1"], subset_na["umap2"],
            s=10, alpha=0.4, marker="x", label="(missing)", color="black",
        )
        ax2.scatter(
            subset_na["tsna1"], subset_na["tsna2"],
            s=10, alpha=0.4, marker="x", label="(missing)", color="black",
        )

    legend_title = f"{taxonomy_column} (no selection → default)"

# Titles and labels
ax1.set_title("UMAP")
ax1.set_xlabel("umap1")
ax1.set_ylabel("umap2")

ax2.set_title("tSNE")
ax2.set_xlabel("tsna1")
ax2.set_ylabel("tsna2")

# Shared legend outside the plots
handles, labels = ax1.get_legend_handles_labels()
legend = fig.legend(
    handles, labels,
    title=legend_title,
    loc="right",
    bbox_to_anchor=(1.15, 0.5),
    fontsize="small",
)

fig.tight_layout(rect=[0, 0, 0.85, 1])

# Show on Streamlit
st.pyplot(fig)
