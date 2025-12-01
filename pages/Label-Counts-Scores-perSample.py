# Label-Counts-Scores-perSample.py
from pathlib import Path

import plotly.io
import streamlit as st
import plotly.express as px
import plotly.io as pio

def get_label_fraction_per_sample(df):
    # Compute counts per sample × supercluster
    counts = (
        df.groupby(["sample", "supercluster_name"])
          .size()
          .reset_index(name="count")
          .sort_values(by=["sample", "supercluster_name"], ascending=False)
    )

    # Compute fractions per sample — transform keeps index aligned
    counts["fraction"] = (
        counts["count"] / counts.groupby("sample")["count"].transform("sum")
    )

    # Plotly Express stacked bar
    fig = px.bar(
        counts,
        x="sample",
        y="fraction",
        color="supercluster_name",
        title="Fraction of Supercluster Labels per Sample",
        labels={
            "sample": "Sample",
            "fraction": "Fraction of Cells",
        },
        height=1000,
        text_auto=True
    )

    fig.update_layout(
        barmode="stack",
        xaxis_title="Sample",
        yaxis_title="Fraction",
        yaxis=dict(range=[0, 1])
    )
    pio.write_json(fig, f"figs/superclusters_per_sample.json")

# =======================================
# ------------ MAIN ---------------------
# =======================================
def main():
    st.set_page_config(page_title="Label Counts and Confidence scores per Sample", layout="wide")

    st.markdown(
        """
        WARNING: This page takes time to load. Please browse other pages in a mean time :)
        
        This page is for analysing annotation counts and their confidence scores.
        
        Bellow you can filter subgroups by SuperClusters, Clusters and Subclusters and get appropriate graphs of counts and confidence scores.

        """)


    # --- Load data from session_state ---
    df = st.session_state.get("data")
    if df is None:
        st.error("No data found in session_state['data']. Load data on the main page first.")
        return



    label_options = ["supercluster_name", "cluster_name", "subcluster_name"]

    # -----------------------------------------------------------------------
    # Section 1: Fractions of labels per sample
    # -----------------------------------------------------------------------
    # --- Pre calculating plot of label fractions ---

    file_superclusters_per_sample = Path("figs/superclusters_per_sample.json")
    if not file_superclusters_per_sample.is_file():
        file_superclusters_per_sample.parent.mkdir(parents=True, exist_ok=True)
        with st.spinner("Computing supercluster fractions…"):
            get_label_fraction_per_sample(df)

    fig_fraction = plotly.io.read_json("figs/superclusters_per_sample.json")
    st.plotly_chart(fig_fraction, width='stretch',)

    # -----------------------------------------------------------------------
    # Section 2: Histogram of counts of a selected category per sample
    # -----------------------------------------------------------------------
    st.subheader("Counts of Selected Taxonomy per Sample")

    # 1) Choose label column
    col_label_for_hist = st.selectbox(
        "Taxonomy level for label selection",
        options=label_options,
        index=0,
        key="hist_label_level",
    )
    # Compute counts per sample – this avoids duplicate column names
    counts_taxo = (
        df
        .groupby(col_label_for_hist)
        .size()
        .reset_index(name="count")
    )

    # Plot histogram (bar plot) of counts per sample
    fig_counts_taxo = px.bar(
        counts_taxo,
        x=col_label_for_hist,
        y="count",
        title=f"Counts of cells per {col_label_for_hist}",
        labels={
            "sample": "Sample",
            "count": "Number of Cells",
        },
    )
    st.plotly_chart(fig_counts_taxo, width='stretch')



    # 2) Choose category value within that column (selectbox is searchable)
    categories = sorted(
        df[col_label_for_hist].dropna().unique().tolist()
    )

    if len(categories) == 0:
        st.warning(f"No labels found in column '{col_label_for_hist}'.")
        return

    selected_category = st.selectbox(
        f"Select {col_label_for_hist} category",
        options=categories,
        key="selected_category",
        placeholder=f"Type to search {col_label_for_hist}...",
    )

    # Filter data to the selected category
    df_sel = df[df[col_label_for_hist] == selected_category]

    if df_sel.empty:
        st.warning(f"No rows found for {col_label_for_hist} = '{selected_category}'.")
        return

    # Compute counts per sample – this avoids duplicate column names
    counts = (
        df_sel
        .groupby("sample")
        .size()
        .reset_index(name="count")
    )

    # Plot histogram (bar plot) of counts per sample
    fig_counts = px.bar(
        counts,
        x="sample",
        y="count",
        title=f"Counts of '{selected_category}' ({col_label_for_hist}) per Sample",
        labels={
            "sample": "Sample",
            "count": "Number of Cells",
        },
    )

    st.plotly_chart(fig_counts, width='stretch')

    # -----------------------------------------------------------------------
    # Section 3: Bootstrapping probability by taxonomy (hierarchical)
    # -----------------------------------------------------------------------
    st.markdown("---")
    st.subheader("Bootstrapping Probability by Taxonomy")

    # ---------- 3.1 SUPERCLUSTER ----------
    st.markdown("**Supercluster level**")

    if "supercluster_name" not in df.columns or \
            "supercluster_bootstrapping_probability" not in df.columns:
        st.warning("Supercluster column not found in data.")
    else:
        super_options = sorted(df["supercluster_name"].dropna().unique().tolist())
        st.markdown(f"Supercluster options: {super_options}")
        selected_super = st.multiselect(
            "Filter supercluster_name (default = all)",
            options=super_options,
            default=super_options,
            key="super_box_super_filter",
        )

        df_super = df[df["supercluster_name"].isin(selected_super)] if selected_super else df

        df_super_box = df_super[["supercluster_name", "supercluster_bootstrapping_probability"]].dropna()

        if df_super_box.empty:
            st.warning("No data available for selected supercluster_name filter.")
        else:
            fig_super = px.box(
                df_super_box,
                x="supercluster_name",
                y="supercluster_bootstrapping_probability",
                title="Supercluster bootstrapping probability",
                labels={
                    "supercluster_name": "Supercluster",
                    "supercluster_bootstrapping_probability": "Bootstrapping probability",
                },
                height=600,
            )
            st.plotly_chart(fig_super, width='stretch')

    st.divider()

    # ---------- 3.2 CLUSTER ----------
    st.markdown("**Cluster level**")

    if ("supercluster_name" not in df.columns or
            "cluster_name" not in df.columns or
            "cluster_bootstrapping_probability" not in df.columns):
        st.warning("Cluster-related columns not found in data.")
    else:
        super_options = sorted(df["supercluster_name"].dropna().unique().tolist())

        selected_super_for_cluster = st.multiselect(
            "Filter supercluster_name for clusters (optional)",
            options=super_options,
            default=[],
            key="cluster_super_filter",
        )

        df_for_clusters = (
            df[df["supercluster_name"].isin(selected_super_for_cluster)]
            if selected_super_for_cluster else df
        )

        cluster_options = sorted(df_for_clusters["cluster_name"].dropna().unique().tolist())

        selected_clusters = st.multiselect(
            "Select cluster_name categories (optional)",
            options=cluster_options,
            default=[],
            key="cluster_name_filter",
        )

        df_cluster = (
            df_for_clusters[df_for_clusters["cluster_name"].isin(selected_clusters)]
            if selected_clusters else df_for_clusters
        )

        df_cluster_box = df_cluster[["cluster_name", "cluster_bootstrapping_probability"]].dropna()

        if df_cluster_box.empty:
            st.warning("No data available for selected cluster_name / supercluster_name filters.")
        else:
            fig_cluster = px.box(
                df_cluster_box,
                x="cluster_name",
                y="cluster_bootstrapping_probability",
                title=f"Cluster bootstrapping probability",
                labels={
                    "cluster_name": "Cluster",
                    "cluster_bootstrapping_probability": "Bootstrapping probability",
                },
                height=600,
            )
            st.plotly_chart(fig_cluster, width='stretch')

    st.divider()

    # ---------- 3.3 SUBCLUSTER ----------
    st.markdown("**Subcluster level**")

    if ("cluster_name" not in df.columns or
            "subcluster_name" not in df.columns or
            "subcluster_bootstrapping_probability" not in df.columns):
        st.warning("Subcluster-related columns not found in data.")
    else:
        cluster_options = sorted(df["cluster_name"].dropna().unique().tolist())

        selected_clusters_for_sub = st.multiselect(
            "Filter cluster_name for subclusters (optional)",
            options=cluster_options,
            default=[],
            key="subcluster_cluster_filter",
        )

        df_for_sub = (
            df[df["cluster_name"].isin(selected_clusters_for_sub)]
            if selected_clusters_for_sub else df
        )

        subcluster_options = sorted(df_for_sub["subcluster_name"].dropna().unique().tolist())

        selected_subclusters = st.multiselect(
            "Select subcluster_name categories (optional)",
            options=subcluster_options,
            default=[],
            key="subcluster_name_filter",
        )

        df_sub = (
            df_for_sub[df_for_sub["subcluster_name"].isin(selected_subclusters)]
            if selected_subclusters else df_for_sub
        )

        df_sub_box = df_sub[["subcluster_name", "subcluster_bootstrapping_probability"]].dropna()

        if df_sub_box.empty:
            st.warning("No data available for selected subcluster_name / cluster_name filters.")
        else:
            fig_sub = px.box(
                df_sub_box,
                x="subcluster_name",
                y="subcluster_bootstrapping_probability",
                title="Subcluster bootstrapping probability",
                labels={
                    "subcluster_name": "Subcluster",
                    "subcluster_bootstrapping_probability": "Bootstrapping probability",
                },
                height=600,
            )
            st.plotly_chart(fig_sub, width='stretch')


if __name__ == "__main__":
    main()

