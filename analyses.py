"""
College Student Analytics using MongoDB - BDA Mini Project
Step 3: Analyses - queries, output and interpretation (Q1 to Q7)
Usage: python analyses.py
"""
import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()  # reads .env next to the scripts; real env vars take precedence

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise SystemExit("MONGO_URI is not set - copy .env.example to .env and fill in the Atlas connection string.")
client = MongoClient(MONGO_URI)
db = client["college_analytics"]


def banner(text):
    print("\n" + "=" * 68)
    print(text)
    print("=" * 68)


# ----------------------------------------------------------------- #
# Q1. Branch-wise strength and average CGPA
# ----------------------------------------------------------------- #
banner("Q1. Branch-wise student count and average CGPA")
q1 = [
    {"$group": {"_id": "$branch", "students": {"$sum": 1},
                "avg_cgpa": {"$avg": "$cgpa"},
                "avg_attendance": {"$avg": "$attendance_pct"}}},
    {"$sort": {"avg_cgpa": -1}},
]
for r in db.students.aggregate(q1):
    print(f"{r['_id']:4s} | students: {r['students']:4d} | "
          f"avg CGPA: {r['avg_cgpa']:.2f} | avg attendance: {r['avg_attendance']:.1f}%")

# ----------------------------------------------------------------- #
# Q2. Top 10 students by CGPA
# ----------------------------------------------------------------- #
banner("Q2. Top 10 students by CGPA (overall)")
for s in db.students.find({}, {"_id": 0, "student_id": 1, "name": 1, "branch": 1,
                               "cgpa": 1}).sort("cgpa", -1).limit(10):
    print(f"{s['student_id']} | {s['name']:22s} | {s['branch']:4s} | CGPA {s['cgpa']:.2f}")

# ----------------------------------------------------------------- #
# Q3. Subject-wise average marks and pass percentage
# ----------------------------------------------------------------- #
banner("Q3. Subject-wise average marks and pass percentage")
q3 = [
    {"$group": {"_id": {"code": "$subject_code", "name": "$subject"},
                "appeared": {"$sum": 1},
                "avg_total": {"$avg": "$total"},
                "passed": {"$sum": {"$cond": [{"$eq": ["$result", "PASS"]}, 1, 0]}}}},
    {"$addFields": {"pass_pct": {"$multiply": [{"$divide": ["$passed", "$appeared"]}, 100]}}},
    {"$sort": {"pass_pct": -1}},
    {"$limit": 12},
]
print(f"{'Subject':40s} {'App.':>5s} {'Avg':>6s} {'Pass%':>7s}")
for r in db.results.aggregate(q3):
    title = f"{r['_id']['code']} {r['_id']['name']}"
    print(f"{title:40s} {r['appeared']:5d} {r['avg_total']:6.1f} {r['pass_pct']:6.1f}%")

# ----------------------------------------------------------------- #
# Q4. Attendance-risk buckets (detention risk analysis)
# ----------------------------------------------------------------- #
banner("Q4. Attendance risk buckets (min 75% required by the college)")
q4 = [
    {"$bucket": {"groupBy": "$attendance_pct", "boundaries": [40, 60, 75, 85, 101],
                 "default": "unknown",
                 "output": {"students": {"$sum": 1}, "avg_cgpa": {"$avg": "$cgpa"}}}},
]
labels = {40: "40-59%  (critical)", 60: "60-74%  (warning)",
          75: "75-84%  (healthy)", 85: "85-100% (excellent)"}
for r in db.students.aggregate(q4):
    print(f"{labels.get(r['_id'], r['_id'])} | students: {r['students']:4d} | avg CGPA: {r['avg_cgpa']:.2f}")

# ----------------------------------------------------------------- #
# Q5. Students with backlogs (join results -> students with $lookup)
# ----------------------------------------------------------------- #
banner("Q5. Top 12 students by number of backlogs ($lookup join)")
q5 = [
    {"$match": {"result": "FAIL"}},
    {"$group": {"_id": "$student_id", "backlogs": {"$sum": 1}}},
    {"$sort": {"backlogs": -1}},
    {"$limit": 12},
    {"$lookup": {"from": "students", "localField": "_id",
                 "foreignField": "student_id", "as": "student"}},
    {"$unwind": "$student"},
    {"$project": {"_id": 0, "student_id": "$_id", "name": "$student.name",
                  "branch": "$student.branch", "backlogs": 1, "cgpa": "$student.cgpa"}},
    {"$sort": {"backlogs": -1, "cgpa": 1}},
]
for r in db.results.aggregate(q5):
    print(f"{r['student_id']} | {r['name']:22s} | {r['branch']:4s} | "
          f"backlogs: {r['backlogs']} | CGPA {r['cgpa']:.2f}")

# ----------------------------------------------------------------- #
# Q6. Hostellers vs day scholars
# ----------------------------------------------------------------- #
banner("Q6. Hostellers vs day scholars - performance comparison")
q6 = [
    {"$group": {"_id": "$hostel", "students": {"$sum": 1},
                "avg_cgpa": {"$avg": "$cgpa"},
                "avg_attendance": {"$avg": "$attendance_pct"},
                "with_backlog": {"$sum": {"$cond": [{"$gt": ["$backlogs", 0]}, 1, 0]}}}},
    {"$sort": {"_id": 1}},
]
for r in db.students.aggregate(q6):
    kind = "Hostellers   " if r["_id"] else "Day scholars "
    print(f"{kind} | students: {r['students']:4d} | avg CGPA: {r['avg_cgpa']:.2f} | "
          f"avg attendance: {r['avg_attendance']:.1f}% | with backlog: {r['with_backlog']}")

# ----------------------------------------------------------------- #
# Q7. Keyword search with a text index
# ----------------------------------------------------------------- #
banner("Q7. Keyword search - find students by surname using a text index")
db.students.create_index([("name", "text")], name="idx_name_text")
print("Created text index on students.name")
for s in db.students.find({"$text": {"$search": "kumar"}},
                          {"score": {"$meta": "textScore"}, "_id": 0,
                           "student_id": 1, "name": 1, "branch": 1, "cgpa": 1}
                          ).sort([("score", {"$meta": "textScore"})]).limit(5):
    print(f"{s['student_id']} | {s['name']:22s} | {s['branch']:4s} | "
          f"CGPA {s['cgpa']:.2f} | score {s['score']:.2f}")
n = db.students.count_documents({"$text": {"$search": "kumar"}})
print(f"Total students matching the keyword 'kumar': {n}")

client.close()
print("\nAll analyses completed.")
