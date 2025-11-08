import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Output folder
out_dir = os.path.dirname(__file__)

# Random seed (change or comment out for different data each run)
np.random.seed()

today = datetime.now().date()

# --- Generate Trainsets ---
n_trains = 25
train_ids = [f"TS{str(i).zfill(2)}" for i in range(1, n_trains+1)]

fitness_valid_until = []
for i in range(n_trains):
    # 70% valid in future, 30% expired in past
    if np.random.rand() < 0.7:
        fitness_valid_until.append(today + timedelta(days=np.random.randint(1, 10)))
    else:
        fitness_valid_until.append(today - timedelta(days=np.random.randint(1, 5)))

job_card_open = np.random.choice([False, True], size=n_trains, p=[0.75, 0.25])
branding_priority = np.random.choice(range(6), size=n_trains, p=[0.25, 0.25, 0.2, 0.15, 0.1, 0.05])
mileage_last_week = np.random.randint(200, 1500, size=n_trains)
needs_cleaning = np.random.choice([False, True], size=n_trains, p=[0.7, 0.3])
bay_position = np.random.choice(range(1, 11), size=n_trains)

df_trains = pd.DataFrame({
    "train_id": train_ids,
    "fitness_valid_until": fitness_valid_until,
    "job_card_open": job_card_open,
    "branding_priority": branding_priority,
    "mileage_last_week": mileage_last_week,
    "needs_cleaning": needs_cleaning,
    "bay_position": bay_position
})

df_trains.to_csv(os.path.join(out_dir, "sample_trainsets.csv"), index=False)
print("✅ sample_trainsets.csv generated")

# --- Generate Job Cards ---
job_cards = []
for tid, open_flag in zip(train_ids, job_card_open):
    if open_flag:
        job_cards.append({
            "train_id": tid,
            "job_card_id": f"JC-{tid}",
            "severity": np.random.choice(["low", "medium", "high"], p=[0.4, 0.4, 0.2])
        })
df_jobs = pd.DataFrame(job_cards)
df_jobs.to_csv(os.path.join(out_dir, "job_cards.csv"), index=False)
print("✅ job_cards.csv generated")

# --- Generate Cleaning Slots ---
slots = []
for i in range(1, 7):  # 6 slots
    slots.append({
        "slot_id": f"CS{i}",
        "available": bool(np.random.choice([True, False], p=[0.7, 0.3])),
        "shift": "night"
    })
df_cleaning = pd.DataFrame(slots)
df_cleaning.to_csv(os.path.join(out_dir, "cleaning_slots.csv"), index=False)
print("✅ cleaning_slots.csv generated")

print("\n🎉 Sample data generated! Try uploading these files into your Streamlit app.")
