# pages/03_UMAP_by_sample.py

import io

import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import pandas as pd

@st.cache_data
def plot_umap_by_sample_seaborn(
    df,
    x_col="umap1",
    y_col="umap2",
    sample_col="sample",
    alpha=0.6,
    point_size=3,
    seed=0,
    palette="tab20",  # Seaborn will cycle automatically even if >20 categories
):
    """
    Plot all samples on one UMAP figure, layered randomly,
    using Seaborn for categorical coloring.
    """

    # Shuffle rows to randomize layering
    df_shuffled = df.sample(frac=1.0, random_state=seed)

    # Build the static figure
    plt.figure(figsize=(7, 7))

    # NOTE: Seaborn scatterplot must be drawn on a single axes
    ax = sns.scatterplot(
        data=df_shuffled,
        x=x_col,
        y=y_col,
        hue=sample_col,
        palette=palette,
        s=point_size,
        alpha=alpha,
        edgecolor=None,
        linewidth=0,
    )

    ax.set_title("UMAP by sample (random shuffling) (color = sample)")
    ax.set_xlabel("UMAP1")
    ax.set_ylabel("UMAP2")

    # legend removed (41 samples is huge)
    ax.get_legend().remove()

    plt.tight_layout()
    return ax.get_figure(), ax


# --- Streamlit page ---
def main():
    st.title("UMAP by Sample (static Seaborn plot)")
    st.markdown(
        """
        The plot should look like white noise - samples should not correlate with UMAP coordinates.
        
        The dataset is shuffled to randomise plotting. You may test different shuffling instances by sliding widget of `seed` bellow.""")
    # Get dataframe from session state
    df = st.session_state.get("data")


    # Guard clause
    if df is None:
        st.error("No dataset found in session_state under key 'data'.")
        st.stop()

    if df.empty:
        st.warning("Replace `load_data()` with your own loader so that `df` has columns: umap1, umap2, sample.")
        return

    seed = st.number_input("Random seed (layering order)", min_value=0, value=0, step=1)

    # Build figure
    fig, ax = plot_umap_by_sample_seaborn(
        df=df,
        x_col="umap1",
        y_col="umap2",
        seed=seed,
    )

    st.pyplot(fig, clear_figure=False)

    # --- Download button ---
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=400, bbox_inches="tight")
    buf.seek(0)

    st.download_button(
        label="Download UMAP as PNG",
        data=buf,
        file_name="umap_by_sample.png",
        mime="image/png",
    )


if __name__ == "__main__":

    main()
