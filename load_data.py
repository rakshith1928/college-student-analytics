"""
College Student Analytics using MongoDB - BDA Mini Project
Step 2: Load the generated data into MongoDB and create indexes
Usage: python load_data.py
"""
import json

import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()  # reads .env next to the scripts; real env vars take precedence

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise SystemExit("MONGO_URI is not set - copy .env.example to .env and fill in the Atlas connection string.")
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = "college_analytics"


def main():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    # start from a clean database on every run
    db.students.drop()
    db.results.drop()

    with open(os.path.join(OUT_DIR, "students.json")) as f:
        students = json.load(f)
    with open(os.path.join(OUT_DIR, "results.json")) as f:
        results = json.load(f)

    s1 = db.students.insert_many(students)
    s2 = db.results.insert_many(results)
    print(f"Loaded {len(s1.inserted_ids)} documents into 'students' collection")
    print(f"Loaded {len(s2.inserted_ids)} documents into 'results' collection")

    # ---------------- indexes (see report section 7.4) ----------------
    db.students.create_index("student_id", unique=True, name="uniq_student_id")
    db.students.create_index([("cgpa", -1)], name="idx_cgpa_desc")
    db.students.create_index([("branch", 1), ("cgpa", -1)], name="idx_branch_cgpa")
    db.students.create_index([("branch", 1), ("attendance_pct", 1)], name="idx_branch_attendance")
    db.results.create_index("student_id", name="idx_result_student")
    db.results.create_index([("subject_code", 1), ("result", 1)], name="idx_subject_result")
    db.results.create_index([("result", 1), ("total", -1)], name="idx_result_total")

    print("\nIndexes created:")
    for coll in ("students", "results"):
        for name, keys in db[coll].index_information().items():
            if name != "_id_":
                print(f"  {coll}: {name} -> {keys['key']}")

    print("\nCollections in database '" + DB_NAME + "':", db.list_collection_names())
    print(f"students count  : {db.students.estimated_document_count()}")
    print(f"results count   : {db.results.estimated_document_count()}")
    client.close()


if __name__ == "__main__":
    main()
