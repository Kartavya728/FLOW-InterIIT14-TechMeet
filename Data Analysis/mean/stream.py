# stream.py
import csv, random, time
from datetime import datetime

file_path = "data.csv"

# Initialize CSV with header
with open(file_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "value"])

print("Streaming new data into data.csv...")

idx = 0
while True:
    with open(file_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([idx, random.randint(1, 100)])
    print(f"[{datetime.now().isoformat()}] Added row {idx}")
    idx += 1
    time.sleep(2)
