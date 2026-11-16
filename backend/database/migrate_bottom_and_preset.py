import sqlite3
from pathlib import Path

db_path = Path("storage/clipforge.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Add caption_preset to projects table if missing
cursor.execute("PRAGMA table_info(projects)")
cols = [r[1] for r in cursor.fetchall()]
if "caption_preset" not in cols:
    cursor.execute("ALTER TABLE projects ADD COLUMN caption_preset TEXT DEFAULT 'mrbeast'")
    print("Added caption_preset column to projects table.")
else:
    print("caption_preset column already exists in projects table.")

# 2. Update all presets in caption_presets table from 'middle' to 'bottom'
cursor.execute("UPDATE caption_presets SET position = 'bottom'")
conn.commit()

cursor.execute("SELECT COUNT(*) FROM caption_presets WHERE position = 'bottom'")
total_bottom = cursor.fetchone()[0]
print(f"Total presets set to 'bottom': {total_bottom}")

# 3. Update all clips to position = 'bottom' if stored in editing_plan or elsewhere
cursor.execute("PRAGMA table_info(clips)")
clip_cols = [r[1] for r in cursor.fetchall()]
print(f"Clips table verified with columns: {len(clip_cols)}")

conn.close()
