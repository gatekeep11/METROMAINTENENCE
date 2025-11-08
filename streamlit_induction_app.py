import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

st.set_page_config(layout="wide", page_title="Kochi Metro Induction - 30% Prototype")

st.title("Kochi Metro — Induction Planner (30% Prototype)")
st.markdown("""
This prototype ingests CSVs and generates a simple induction plan using rule-based filtering and heuristics.

**Inputs:**
- `sample_trainsets.csv` → Train info
- `job_cards.csv` → Open work orders
- `cleaning_slots.csv` → Available cleaning capacity

**Logic:**
- Excludes trains with expired fitness or open job-cards
- Limits cleaning by available slots
- Prioritises by branding urgency, then lower mileage
- Allocates Service / Standby / Maintenance
""")

# === File Uploaders ===
uploaded_trainsets = st.file_uploader("Upload trainsets CSV", type=["csv"], key="trainsets")
uploaded_jobs = st.file_uploader("Upload job-cards CSV", type=["csv"], key="jobs")
uploaded_cleaning = st.file_uploader("Upload cleaning slots CSV", type=["csv"], key="cleaning")

# Load data
if uploaded_trainsets is not None:
    df = pd.read_csv(uploaded_trainsets)
else:
    st.error("❌ Please upload a trainsets CSV (must contain at least 'train_id').")
    st.stop()

job_cards = pd.read_csv(uploaded_jobs) if uploaded_jobs is not None else None
cleaning_slots = pd.read_csv(uploaded_cleaning) if uploaded_cleaning is not None else None

# === Sidebar Parameters ===
st.sidebar.header("Parameters")
required_service_count = st.sidebar.number_input("Required trains for revenue service", value=15, min_value=1, max_value=40)
standby_count = st.sidebar.number_input("Standby count", value=6, min_value=0, max_value=40)
today_str = st.sidebar.text_input("Today's date (YYYY-MM-DD)", value="2025-09-16")

# === Ensure required columns exist ===
expected_cols = {
    "fitness_valid_until": pd.to_datetime(today_str),
    "job_card_open": False,
    "branding_priority": 0,
    "mileage_last_week": 0,
    "needs_cleaning": False,
    "bay_position": None,
}

for col, default in expected_cols.items():
    if col not in df.columns:
        st.warning(f"⚠️ Column '{col}' missing in CSV. Filling with default = {default}")
        df[col] = [default] * len(df)

df["fitness_valid_until"] = pd.to_datetime(df["fitness_valid_until"], errors="coerce")

# === Evaluation Function ===
def evaluate(df, today, job_cards=None, cleaning_slots=None):
    rows = []
    cleaning_capacity = None
    if cleaning_slots is not None and "available" in cleaning_slots.columns:
        cleaning_capacity = cleaning_slots[cleaning_slots["available"] == True].shape[0]

    cleaning_used = 0

    mileage_mean = df["mileage_last_week"].mean()
    mileage_std = df["mileage_last_week"].std() or 1

    for _, r in df.iterrows():
        reason = []
        eligible = True

        # Fitness
        if pd.isna(r["fitness_valid_until"]) or r["fitness_valid_until"] < today:
            eligible = False
            reason.append("Expired fitness")

        # Job-cards
        if job_cards is not None and r["train_id"] in job_cards["train_id"].values:
            eligible = False
            severity = (
                job_cards.loc[job_cards["train_id"] == r["train_id"], "severity"].iloc[0]
                if "severity" in job_cards.columns
                else "N/A"
            )
            reason.append(f"Open job-card ({severity})")

        # Cleaning slots
        if bool(r.get("needs_cleaning", False)):
            reason.append("Needs cleaning")
            if cleaning_capacity is not None and eligible:
                if cleaning_used < cleaning_capacity:
                    cleaning_used += 1
                else:
                    eligible = False
                    reason.append("No cleaning slot available")

        # Scoring
        branding = int(r.get("branding_priority", 0)) if not pd.isna(r.get("branding_priority", 0)) else 0
        mileage = float(r.get("mileage_last_week", 0)) if not pd.isna(r.get("mileage_last_week", 0)) else 0
        norm_mileage = (mileage - mileage_mean) / mileage_std
        score = branding * 1000 - norm_mileage * 100

        rows.append({
            "train_id": r.get("train_id", "Unknown"),
            "eligible": eligible,
            "score": score,
            "reason": "; ".join(reason) if reason else "OK",
            "branding_priority": branding,
            "mileage_last_week": mileage,
            "bay_position": r.get("bay_position", None)
        })
    return pd.DataFrame(rows)

# === Run evaluation ===
today = pd.to_datetime(today_str, errors="coerce")
if pd.isna(today):
    st.error("Invalid date format. Use YYYY-MM-DD.")
    st.stop()

evaluated = evaluate(df, today, job_cards=job_cards, cleaning_slots=cleaning_slots)

# === Rank and assign ===
eligible_df = evaluated[evaluated["eligible"]].sort_values(by=["score"], ascending=False).reset_index(drop=True)
ineligible_df = evaluated[~evaluated["eligible"]].reset_index(drop=True)

service = eligible_df.head(int(required_service_count)).copy()
service["assignment"] = "Service"

standby = eligible_df.iloc[int(required_service_count):int(required_service_count)+int(standby_count)].copy()
standby["assignment"] = "Standby"

remaining = pd.concat([eligible_df.iloc[int(required_service_count)+int(standby_count):], ineligible_df], ignore_index=True)
remaining["assignment"] = "Maintenance/Blocked"

result = pd.concat([service, standby, remaining], ignore_index=True)

# === Display Results ===
st.subheader("Generated Induction Plan")

def color_assign(val):
    if val == "Service": return "background-color: #c8e6c9"
    elif val == "Standby": return "background-color: #fff9c4"
    else: return "background-color: #ffcdd2"

st.dataframe(result.style.applymap(color_assign, subset=["assignment"]))

# === Summary Metrics ===
st.subheader("Summary Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Service trains", len(service))
col2.metric("Standby trains", len(standby))
col3.metric("Maintenance/Blocked", len(remaining))

# === Combined Visualization: All trains ===
st.subheader("📊 Combined View: All Trains")

fig, ax = plt.subplots(figsize=(12, 8))

# Sort trains by score
sorted_df = result.sort_values(by="score", ascending=False).reset_index(drop=True)

# Assign colors
color_map = {
    "Service": "green",
    "Standby": "orange",
    "Maintenance/Blocked": "red"
}

# Scatter plot
ax.scatter(
    sorted_df["score"], 
    sorted_df["train_id"], 
    c=sorted_df["assignment"].map(color_map), 
    s=100, alpha=0.7, edgecolor="black"
)

# Add bay position as text labels (if available)
if "bay_position" in sorted_df.columns and sorted_df["bay_position"].notna().any():
    for i, row in sorted_df.iterrows():
        if pd.notna(row["bay_position"]):
            ax.text(row["score"], row["train_id"], f"Bay {row['bay_position']}", 
                    fontsize=8, ha="left", va="center")

ax.set_xlabel("Score")
ax.set_ylabel("Train ID")
ax.set_title("All Trains by Score, Assignment, and Bay Position")

# Legend
handles = [plt.Line2D([0], [0], marker="o", color="w", label=lbl,
                      markerfacecolor=clr, markersize=10) 
           for lbl, clr in color_map.items()]
ax.legend(handles=handles, title="Assignment")

st.pyplot(fig)

# === Download option ===
st.download_button(
    "Download Plan as CSV",
    result.to_csv(index=False).encode("utf-8"),
    "induction_plan.csv",
    "text/csv"
)

# === What-if Simulation ===
st.subheader("What-if Simulation")
st.markdown("Edit table below and click **Re-run** to see how the plan changes.")

if hasattr(st, "data_editor"):
    edited = st.data_editor(df, num_rows="dynamic")
else:
    edited = st.experimental_data_editor(df, num_rows="dynamic")

if st.button("Re-run with edited data"):
    edited["fitness_valid_until"] = pd.to_datetime(edited["fitness_valid_until"], errors="coerce")
    new_eval = evaluate(edited, today, job_cards=job_cards, cleaning_slots=cleaning_slots)
    new_service = new_eval[new_eval["eligible"]].sort_values(by="score", ascending=False).head(int(required_service_count))
    st.write("Updated Service List:", list(new_service["train_id"]))
    st.write(new_eval.sort_values(by="score", ascending=False).head(10))

st.markdown("---")
st.write("To run this app again:")
st.code("python -m streamlit run streamlit_induction_app.py", language="bash")
