# MapMyCells-Summary.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Cluster Bootstrapping Explorer", layout="wide")

st.title("Cluster Bootstrapping Explorer")

st.markdown(
    """
Upload a CSV file that contains these columns:

- **Numeric**
  - `supercluster_bootstrapping_probability`
  - `cluster_bootstrapping_probability`
  - `subcluster_bootstrapping_probability`
- **Categorical**
  - `supercluster_name`
  - `cluster_name`
  - `subcluster_name`
"""
)

# --- Read from session ---
if "data" in st.session_state:
    df = st.session_state["data"]


# Expected columns
numeric_cols = [
    "supercluster_bootstrapping_probability",
    "cluster_bootstrapping_probability",
    "subcluster_bootstrapping_probability",
]

categorical_cols = [
    "supercluster_label",
    "cluster_label",
    "subcluster_label",
]

# Check which columns exist
missing_numeric = [c for c in numeric_cols if c not in df.columns]
missing_cat = [c for c in categorical_cols if c not in df.columns]

if missing_numeric or missing_cat:
    if missing_numeric:
        st.warning(f"Missing numeric columns: {missing_numeric}")
    if missing_cat:
        st.warning(f"Missing categorical columns: {missing_cat}")
    st.info("The app will use only the columns that are present.")

available_numeric = [c for c in numeric_cols if c in df.columns]
available_cat = [c for c in categorical_cols if c in df.columns]

if not available_numeric and not available_cat:
    st.error("None of the expected columns are present in the uploaded file.")
    st.stop()

# Sidebar controls
st.sidebar.header("Histogram settings")

bins = st.sidebar.slider(
    "Number of bins for numeric histograms",
    min_value=5,
    max_value=100,
    value=30,
    step=1,
)

normalize = st.sidebar.checkbox(
    "Normalize numeric histograms (show percent)", value=False
)

top_n_cat = st.sidebar.slider(
    "Show top N categories (by count)",
    min_value=5,
    max_value=50,
    value=20,
    step=1,
)

st.sidebar.caption("Tip: Reduce N if you have many rare categories.")

# Decide histnorm for numeric plots
histnorm = "percent" if normalize else None
y_label = "Percent" if normalize else "Count"

# --- Numeric histograms ---
if available_numeric:
    st.subheader("Numeric variables – histograms & cumulative histograms")

    # Show two variables per row where possible
    ncols = 2
    for i in range(0, len(available_numeric), ncols):
        row_cols = available_numeric[i : i + ncols]
        cols = st.columns(len(row_cols))
        for col_idx, col_name in enumerate(row_cols):
            with cols[col_idx]:
                col_data = df[col_name].dropna()
                if col_data.empty:
                    st.write(f"**{col_name}** – no non-null data.")
                    continue

                st.markdown(f"**{col_name}**")

                # Two tabs: regular histogram and cumulative percent histogram
                tab_hist, tab_cum = st.tabs(["Histogram", "Cumulative % histogram"])

                # ---- Regular histogram (Plotly Express) ----
                with tab_hist:
                    fig_hist = px.histogram(
                        df,
                        x=col_name,
                        nbins=bins,
                        histnorm=histnorm,  # None or "percent"
                        marginal="box",     # adds small boxplot on top
                    )
                    fig_hist.update_layout(
                        bargap=0.05,
                        xaxis_title=col_name,
                        yaxis_title=y_label,
                        title=f"{col_name} – histogram",
                    )
                    st.plotly_chart(fig_hist,width='stretch')

                # ---- Cumulative percent histogram (Plotly Graph Objects) ----
                with tab_cum:
                    fig_cum = go.Figure(
                        go.Histogram(
                            x=col_data,
                            nbinsx=bins,
                            histnorm="percent",       # ALWAYS show percent
                            cumulative_enabled=True
                        )
                    )

                    fig_cum.update_layout(
                        xaxis_title=col_name,
                        yaxis_title="Cumulative percent",
                        title=f"{col_name} – cumulative percent histogram",
                        bargap=0.05,
                        yaxis=dict(range=[0, 100]),  # lock at 0–100%
                    )

                    st.plotly_chart(fig_cum,width='stretch')
else:
    st.info("No numeric variables available to plot.")

# --- Categorical bar charts + summary + cumulative ---
if available_cat:
    st.subheader("Categorical variables – frequency, summary & cumulative")

    ncols = 2
    for i in range(0, len(available_cat), ncols):
        row_cols = available_cat[i : i + ncols]
        cols = st.columns(len(row_cols))
        for col_idx, col_name in enumerate(row_cols):
            with cols[col_idx]:
                # Work with full column (for stats)
                col_series_full = df[col_name].astype(str).fillna("NA")

                if col_series_full.dropna().empty:
                    st.write(f"**{col_name}** – no non-null data.")
                    continue

                st.markdown(f"**{col_name}**")

                # FULL counts (for summary statistics)
                counts_full = (
                    col_series_full
                    .value_counts()
                    .reset_index()
                )
                counts_full.columns = [col_name, "count"]

                # TOP N counts (for plots)
                counts_top = counts_full.head(top_n_cat)

                tab_bar, tab_stats, tab_cum_cat = st.tabs(
                    ["Bar chart", "Summary stats", "Cumulative % histogram"]
                )

                # ---- Bar chart tab (Top N only) ----
                with tab_bar:
                    fig_cat = px.bar(
                        counts_top,
                        x=col_name,
                        y="count",
                        title=f"{col_name} – top {min(top_n_cat, len(counts_top))} categories",
                    )
                    fig_cat.update_layout(
                        xaxis_title=col_name,
                        yaxis_title="Count",
                        xaxis_tickangle=-45,
                    )
                    st.plotly_chart(fig_cat, width='content')

                # ---- Summary statistics tab (FULL dataset) ----
                with tab_stats:
                    if counts_full.empty:
                        st.write("No categories to summarize.")
                    else:
                        total_unique_full = counts_full.shape[0]
                        total_rows_full = counts_full["count"].sum()

                        max_count = counts_full["count"].max()
                        min_count = counts_full["count"].min()

                        max_cats = counts_full[counts_full["count"] == max_count][col_name].tolist()
                        min_cats = counts_full[counts_full["count"] == min_count][col_name].tolist()

                        st.markdown("**Summary statistics (full column)**")
                        st.write(
                            f"- Unique categories in dataset: `{total_unique_full}`"
                        )
                        st.write(
                            f"- Total rows (non-null after casting to string): `{total_rows_full}`"
                        )
                        st.write(f"- **Max count**: `{max_count}`")
                        st.write(f"  - Categories: `{max_cats}`")
                        st.write(f"- **Min count**: `{min_count}`")
                        st.write(f"  - Categories: `{min_cats}`")

                        st.markdown(
                            f"**Top {min(top_n_cat, len(counts_top))} categories (for charts)**"
                        )
                        st.dataframe(counts_top, width='content')

                # ---- Cumulative % histogram tab (Top N only, same style as numeric) ----
                with tab_cum_cat:
                    if counts_top.empty:
                        st.write("No data for cumulative histogram.")
                    else:
                        # Categories to include in cumulative plot (Top N)
                        top_categories = counts_top[col_name].tolist()

                        data_for_hist = col_series_full[
                            col_series_full.isin(top_categories)
                        ]

                        fig_cum_cat = go.Figure(
                            go.Histogram(
                                x=data_for_hist,
                                histnorm="percent",
                                cumulative_enabled=True,
                            )
                        )

                        fig_cum_cat.update_layout(
                            title=f"{col_name} – cumulative percent histogram (top {len(top_categories)})",
                            xaxis_title=col_name,
                            yaxis_title="Cumulative percent",
                            xaxis=dict(
                                categoryorder="array",
                                categoryarray=top_categories,
                            ),
                            yaxis=dict(range=[0, 100]),
                            bargap=0.05,
                        )

                        st.plotly_chart(fig_cum_cat, width='content')
else:
    st.info("No categorical variables available to plot.")

st.markdown("---")
