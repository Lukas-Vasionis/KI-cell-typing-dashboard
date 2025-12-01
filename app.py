# pages/1_Overview.py
import streamlit as st
import pandas as pd


def main():
    st.title("Overview")
    st.write("Upload TSV of adata.obs with cell adata, sample ids, MapMyCell output and UMAP coordinates")
    st.write("Navigate over pages to review different parts of the dataset")

    # --- File upload ---
    # uploaded_file = st.file_uploader("Upload TSV file", type=["tsv"])


    # Read data
    @st.cache_data
    def load_data(file):
        try:
            df = pd.read_csv(file, comment="#", sep="\t", index_col=0)
            print(df[["outlier", "mt_outlier"]].head().to_string())
        except Exception as e:
            st.error(f"Could not read the file as CSV: {e}")
            st.stop()

        return df

    # --- File upload ---
    uploaded = st.file_uploader("Upload data")

    if uploaded:
        st.session_state["data"] = load_data(uploaded)

        # Show shape / preview
        with st.expander("Show data preview"):
            st.write(st.session_state["data"].head())



if __name__ == "__main__":
    main()