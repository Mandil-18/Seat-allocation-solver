import streamlit as st
import pandas as pd
from solver import solve

st.set_page_config(page_title="Seat Allocation Solver", layout="wide")

st.title("🪑 Seat Allocation Solver")
st.write("Upload **subteams.csv** and **bays.csv** to run the solver.")

# --- File Uploads ---
subteams_file = st.file_uploader("Upload subteams.csv", type=["csv"])
bays_file = st.file_uploader("Upload bays.csv", type=["csv"])

if subteams_file and bays_file:
    try:
        # Load datasets
        subteams_df = pd.read_csv(subteams_file).set_index("Subteam")
        bays_df = pd.read_csv(bays_file).set_index("Bay")

        st.subheader("📊 Subteams Data")
        st.dataframe(subteams_df)

        st.subheader("📊 Bays Data")
        st.dataframe(bays_df)

        # --- Run Solver ---
        if st.button("🚀 Run Solver"):
            with st.spinner("Running optimization model... Please wait ⏳"):
                try:
                    # Solver returns 2 DataFrames: summary + expanded
                    summary_df, expanded_df = solve(subteams_df, bays_df)
                    st.success("Solver Finished!")

                    # Show Summary Table
                    st.subheader("📊 Seat Schedule Summary")
                    st.dataframe(summary_df)

                    # Show Expanded Table
                    st.subheader("📋 Seat Schedule Expanded")
                    st.dataframe(expanded_df)

                    # --- Download buttons ---
                    csv_summary = summary_df.to_csv().encode("utf-8")
                    st.download_button(
                        label="📥 Download Summary as CSV",
                        data=csv_summary,
                        file_name="seat_schedule_summary.csv",
                        mime="text/csv",
                    )

                    csv_expanded = expanded_df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Download Expanded as CSV",
                        data=csv_expanded,
                        file_name="seat_schedule_expanded.csv",
                        mime="text/csv",
                    )

                except Exception as e:
                    st.error(f"❌ Error while running solver: {e}")
    except Exception as e:
        st.error(f"❌ Failed to read files: {e}")
else:
    st.info("Please upload both files to begin.")
