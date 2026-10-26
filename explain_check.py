"""
College Student Analytics using MongoDB - BDA Mini Project
Step 4: Verify the effect of the index with explain("executionStats")
The top-10 CGPA query (Q2) is executed twice: first after dropping the
index on cgpa (full collection scan), then after re-creating it.
Usage: python explain_check.py
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
students = db.students

# the same shape as Q2: db.students.find({...}).sort({cgpa:-1}).limit(10)
COMMAND = {"find": "students", "filter": {}, "sort": {"cgpa": -1},
           "limit": 10, "projection": {"student_id": 1, "name": 1,
                                       "branch": 1, "cgpa": 1, "_id": 0}}


def run_explain(tag):
    plan = db.command("explain", COMMAND, verbosity="executionStats")
    stats = plan["executionStats"]
    stage = plan["queryPlanner"]["winningPlan"]
    while "inputStage" in stage:          # dig out the leaf stage
        stage = stage["inputStage"]
    print(f"\n--- {tag} ---")
    leaf = stage["stage"]
    extra = f" (index: {stage['indexName']})" if "indexName" in stage else ""
    print(f"winning plan stage : {leaf}{extra}")
    print(f"nReturned           : {stats['nReturned']}")
    print(f"totalKeysExamined   : {stats['totalKeysExamined']}")
    print(f"totalDocsExamined   : {stats['totalDocsExamined']}")
    print(f"executionTimeMillis : {stats['executionTimeMillis']}")
    return stats


print("=" * 68)
print("Verifying the index on students.cgpa with explain()")
print("Query: db.students.find({}, {student_id:1, name:1, branch:1, cgpa:1})")
print("        .sort({cgpa: -1}).limit(10)")
print("=" * 68)

# ---- before: without the index ----
students.drop_index("idx_cgpa_desc")
print("\nDropped index 'idx_cgpa_desc' to simulate a non-indexed collection.")
before = run_explain("WITHOUT index (full collection scan)")

# ---- after: with the index ----
students.create_index([("cgpa", -1)], name="idx_cgpa_desc")
print("\nRe-created index 'idx_cgpa_desc' = { cgpa: -1 }.")
after = run_explain("WITH index idx_cgpa_desc")

print("\nSummary")
print(f"  documents examined : {before['totalDocsExamined']} -> {after['totalDocsExamined']}")
print(f"  documents returned : {before['nReturned']} -> {after['nReturned']}")
red = 100 - 100 * after['totalDocsExamined'] / max(before['totalDocsExamined'], 1)
print(f"  the indexed plan examines {after['totalDocsExamined']} documents instead of "
      f"{before['totalDocsExamined']} - a reduction of {red:.1f}%.")

client.close()
