import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Day Without BR Process", layout="wide")

st.title("Day Without BR Process")

# ---------------- FILE UPLOAD ----------------

file1 = st.file_uploader(
    "Upload First File (Client / NetClosing)",
    type=["csv", "xls", "xlsx"]
)

file2 = st.file_uploader(
    "Upload Second File (Allocation)",
    type=["csv", "xls", "xlsx"]
)

# ---------------- CONSTANTS ----------------

remove_clients = ["11858", "J1", "J2", "0"]

# ---------------- PROCESS BUTTON ----------------

if st.button("Process Files"):

    if file1 is None or file2 is None:
        st.error("Please upload both files")
        st.stop()

    # ================== READ FIRST FILE ==================

    try:
        if file1.name.endswith(".csv"):
            df1 = pd.read_csv(file1, low_memory=False)
        else:
            df1 = pd.read_excel(file1)

        df1 = df1[["Client", "NetClosing (C)"]]

    except Exception as e:
        st.error(f"First file error: {e}")
        st.stop()

    # CLEAN FIRST FILE
    df1["Client"] = (
        df1["Client"]
        .astype(str)
        .str.strip()
        .str.replace(r"[\[\]]", "", regex=True)
        .str.replace(r"[^A-Za-z0-9]", "", regex=True)
    )

    df1 = df1[
        (df1["Client"] != "") &
        (df1["Client"] != "0")
    ]

    df1 = df1[~df1["Client"].isin(remove_clients)]

    df1["NetClosing (C)"] = (
        pd.to_numeric(df1["NetClosing (C)"], errors="coerce")
        .fillna(0)
        .round(2)
    )

    pivot1 = df1.groupby("Client", as_index=False).agg({
        "NetClosing (C)": "sum"
    })

    # ================== READ SECOND FILE ==================

    try:
        if file2.name.endswith(".csv"):
            df2 = pd.read_csv(file2, low_memory=False)
        else:
            df2 = pd.read_excel(file2)

        df2 = df2[
            ["Client Code", "Allocated Cash/Cash Equivalent Collateral"]
        ]

    except Exception as e:
        st.error(f"Second file error: {e}")
        st.stop()

    # CLEAN SECOND FILE
    df2["Client Code"] = (
        df2["Client Code"]
        .astype(str)
        .str.strip()
        .str.replace(r"[\[\]]", "", regex=True)
        .str.replace(r"[^A-Za-z0-9]", "", regex=True)
    )

    df2 = df2[
        (df2["Client Code"] != "") &
        (df2["Client Code"] != "0")
    ]

    df2 = df2[~df2["Client Code"].isin(remove_clients)]

    df2["Allocated Cash/Cash Equivalent Collateral"] = (
        pd.to_numeric(
            df2["Allocated Cash/Cash Equivalent Collateral"],
            errors="coerce"
        )
        .fillna(0)
        .round(2)
    )

    pivot2 = df2.groupby("Client Code", as_index=False).agg({
        "Allocated Cash/Cash Equivalent Collateral": "sum"
    })

    # ================== MERGE ==================

    final_df = pd.merge(
        pivot1,
        pivot2,
        left_on="Client",
        right_on="Client Code",
        how="left"
    )

    final_df = final_df[
        ["Client", "NetClosing (C)", "Allocated Cash/Cash Equivalent Collateral"]
    ]

    # RENAME
    final_df.columns = ["Row Labels", "Credit Code", "Allocation"]

    # NUMERIC CONVERSION
    final_df["Credit Code"] = pd.to_numeric(final_df["Credit Code"], errors="coerce").fillna(0).round(2)
    final_df["Allocation"] = pd.to_numeric(final_df["Allocation"], errors="coerce").fillna(0).round(2)

    # TRUE/FALSE
    final_df["T/F"] = abs(final_df["Allocation"] - final_df["Credit Code"]) < 1e-9

    # DIFFERENCE
    final_df["DIFF"] = final_df["Allocation"] - final_df["Credit Code"]
    final_df["DIFF"] = final_df["DIFF"].apply(lambda x: 0 if abs(x) < 1e-9 else round(x, 2))

    final_df = final_df.sort_values("Row Labels")

    # ================== OUTPUT ==================

    st.success("Processing Completed Successfully!")

    st.dataframe(final_df, use_container_width=True)

    csv_data = final_df.to_csv(index=False).encode("utf-8")

    file_name = f"Day_Without_BR_{datetime.now().strftime('%d-%m-%Y')}.csv"

    st.download_button(
        label="Download Output CSV",
        data=csv_data,
        file_name=file_name,
        mime="text/csv"
    )
 