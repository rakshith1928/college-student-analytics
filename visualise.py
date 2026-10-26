"""
College Student Analytics using MongoDB - BDA Mini Project
Step 5: Visualisation of the analysis results (all charts are built from
live aggregation queries on the college_analytics database)
Usage: python visualise.py
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "charts")
os.makedirs(OUT, exist_ok=True)

load_dotenv()  # reads .env next to the scripts

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise SystemExit("MONGO_URI is not set - copy .env.example to .env and fill in the Atlas connection string.")
client = MongoClient(MONGO_URI)
db = client["college_analytics"]

BLUE, NAVY, ORANGE, GREEN, RED, GRAY = "#4C72B0", "#203A5F", "#DD8452", "#55A868", "#C44E52", "#8C8C8C"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False})


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


# ---------------- Figure 1: branch-wise strength ----------------
rows = list(db.students.aggregate([
    {"$group": {"_id": "$branch", "n": {"$sum": 1}}},
    {"$sort": {"n": -1}}]))
fig, ax = plt.subplots(figsize=(6.6, 3.4))
bars = ax.bar([r["_id"] for r in rows], [r["n"] for r in rows], color=BLUE)
ax.bar_label(bars, fmt="%d")
ax.set_ylabel("Number of students")
ax.set_xlabel("Branch")
ax.set_title("Branch-wise student strength (1,200 students)")
save(fig, "fig1_branch_strength.png")

# ---------------- Figure 2: branch-wise average CGPA ----------------
rows = list(db.students.aggregate([
    {"$group": {"_id": "$branch", "avg": {"$avg": "$cgpa"}}},
    {"$sort": {"avg": -1}}]))
fig, ax = plt.subplots(figsize=(6.6, 3.4))
bars = ax.bar([r["_id"] for r in rows], [r["avg"] for r in rows], color=NAVY)
ax.bar_label(bars, fmt="%.2f")
ax.set_ylim(0, 10)
ax.set_ylabel("Average CGPA (out of 10)")
ax.set_xlabel("Branch")
ax.set_title("Branch-wise average CGPA")
save(fig, "fig2_branch_cgpa.png")

# ---------------- Figure 3: CGPA distribution ----------------
cgpas = [d["cgpa"] for d in db.students.find({}, {"cgpa": 1, "_id": 0})]
fig, ax = plt.subplots(figsize=(6.6, 3.4))
ax.hist(cgpas, bins=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        color=BLUE, edgecolor="white")
ax.axvline(sum(cgpas) / len(cgpas), color=RED, linestyle="--", linewidth=1.4,
           label=f"mean = {sum(cgpas)/len(cgpas):.2f}")
ax.set_xlabel("CGPA")
ax.set_ylabel("Number of students")
ax.set_title("Distribution of student CGPA")
ax.legend(frameon=False)
save(fig, "fig3_cgpa_distribution.png")

# ---------------- Figure 4: attendance risk buckets ----------------
rows = list(db.students.aggregate([
    {"$bucket": {"groupBy": "$attendance_pct", "boundaries": [40, 60, 75, 85, 101],
                 "default": "unknown", "output": {"n": {"$sum": 1}}}}]))
labels = {40: "40-59%\n(critical)", 60: "60-74%\n(warning)",
          75: "75-84%\n(healthy)", 85: "85-100%\n(excellent)"}
rows.sort(key=lambda r: r["_id"])
fig, ax = plt.subplots(figsize=(6.6, 3.4))
colors = [RED, ORANGE, BLUE, GREEN]
bars = ax.bar([labels[r["_id"]] for r in rows], [r["n"] for r in rows], color=colors)
ax.bar_label(bars, fmt="%d")
ax.set_ylabel("Number of students")
ax.set_title("Attendance bands (75% is the minimum requirement)")
save(fig, "fig4_attendance_bands.png")

# ---------------- Figure 5: CSE subject-wise performance ----------------
rows = list(db.results.aggregate([
    {"$match": {"branch": "CSE"}},
    {"$group": {"_id": {"code": "$subject_code", "name": "$subject"},
                "avg": {"$avg": "$total"},
                "passed": {"$sum": {"$cond": [{"$eq": ["$result", "PASS"]}, 1, 0]}},
                "n": {"$sum": 1}}},
    {"$sort": {"_id.code": 1}}]))
codes = [r["_id"]["code"] for r in rows]
pct = [100 * r["passed"] / r["n"] for r in rows]
avg = [r["avg"] for r in rows]
fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.4))
axes[0].bar(codes, avg, color=BLUE)
axes[0].set_ylabel("Average total marks")
axes[0].set_ylim(0, 100)
axes[0].set_title("CSE: average marks")
axes[1].bar(codes, pct, color=GREEN)
axes[1].set_ylabel("Pass percentage")
axes[1].set_ylim(0, 100)
axes[1].set_title("CSE: pass percentage")
for a in axes:
    a.tick_params(axis="x", rotation=45)
save(fig, "fig5_cse_subjects.png")

# ---------------- Figure 6: hostellers vs day scholars ----------------
rows = list(db.students.aggregate([
    {"$group": {"_id": "$hostel", "n": {"$sum": 1},
                "cgpa": {"$avg": "$cgpa"}, "att": {"$avg": "$attendance_pct"}}}]))
rows.sort(key=lambda r: r["_id"])
names = ["Day scholars", "Hostellers"]
fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.4))
b1 = axes[0].bar(names, [r["cgpa"] for r in rows], color=[GRAY, NAVY], width=0.5)
axes[0].bar_label(b1, fmt="%.2f")
axes[0].set_ylim(0, 10)
axes[0].set_ylabel("Average CGPA")
axes[0].set_title("Average CGPA")
b2 = axes[1].bar(names, [r["att"] for r in rows], color=[GRAY, NAVY], width=0.5)
axes[1].bar_label(b2, fmt="%.1f%%")
axes[1].set_ylim(0, 100)
axes[1].set_ylabel("Average attendance (%)")
axes[1].set_title("Average attendance")
save(fig, "fig6_hostel_compare.png")

client.close()
print("All charts generated in", OUT)
