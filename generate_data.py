"""
College Student Analytics using MongoDB - BDA Mini Project
Step 1: Data generation (input)
Generates a realistic synthetic dataset for one college semester:
  - students.json : 1,200 student profile documents
  - results.json  : subject-wise result documents (6 subjects per student)
Usage: python generate_data.py
"""
import json
import random
import os

random.seed(42)                     # reproducible dataset
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ #
# Reference data used by the generator
# ------------------------------------------------------------------ #
MALE_NAMES = ["Rahul", "Karthik", "Vikram", "Sandeep", "Manoj", "Praveen",
              "Naveen", "Arjun", "Sagar", "Tejas", "Rohit", "Kiran",
              "Anil", "Harsha", "Pavan", "Shreyas", "Nikhil", "Yashwanth",
              "Amit", "Sumanth", "Darshan", "Ganesh", "Vinay", "Akash"]
FEMALE_NAMES = ["Ananya", "Sneha", "Divya", "Pooja", "Kavya", "Meghana",
                "Shruti", "Aishwarya", "Nandini", "Rakshitha", "Bhavana",
                "Chaitra", "Deepika", "Harini", "Keerthi", "Lakshmi",
                "Manasa", "Nisha", "Rashmi", "Sanjana", "Sowmya", "Vaishnavi"]
SURNAMES = ["Shetty", "Gowda", "Reddy", "Rao", "Kumar", "Hegde", "Naik",
            "Pai", "Joshi", "Kulkarni", "Sharma", "Patil", "Nayak",
            "Bhat", "Rai", "Pillai", "Menon", "Desai", "Kamath", "Salian"]
CITIES = ["Bangalore", "Mysuru", "Mangaluru", "Hubballi", "Belagavi",
          "Davanagere", "Shivamogga", "Kalaburagi", "Tumakuru", "Bijapur"]

# Branch and its six fifth-semester subjects (code, name, credits)
BRANCH_PLAN = [("CSE", 360), ("ECE", 280), ("ISE", 240), ("ME", 180), ("CV", 140)]
SUBJECTS = {
    "CSE": [("CS501", "Computer Networks", 4), ("CS502", "Theory of Computation", 4),
            ("CS503", "Software Engineering", 3), ("CS504", "Database Management Systems", 4),
            ("CS505", "Operating Systems", 4), ("CS506", "Web Technologies", 3)],
    "ECE": [("EC501", "Signals and Systems", 4), ("EC502", "Digital Signal Processing", 4),
            ("EC503", "Analog Communication", 3), ("EC504", "Microcontrollers", 4),
            ("EC505", "VLSI Design", 3), ("EC506", "Digital Electronics", 4)],
    "ISE": [("IS501", "Data Structures", 4), ("IS502", "Database Management Systems", 4),
            ("IS503", "Software Engineering", 3), ("IS504", "Design and Analysis of Algorithms", 4),
            ("IS505", "Computer Networks", 4), ("IS506", "Information Retrieval", 3)],
    "ME":  [("ME501", "Heat Transfer", 4), ("ME502", "Dynamics of Machinery", 4),
            ("ME503", "Design of Machine Elements", 4), ("ME504", "Manufacturing Processes", 3),
            ("ME505", "Fluid Machinery", 4), ("ME506", "Metrology and Quality Control", 3)],
    "CV":  [("CV501", "Structural Analysis", 4), ("CV502", "Geotechnical Engineering", 4),
            ("CV503", "Transportation Engineering", 4), ("CV504", "Concrete Technology", 3),
            ("CV505", "Fluid Mechanics", 4), ("CV506", "Estimation and Costing", 3)],
}
GRADE_POINTS = {"S": 10, "A": 9, "B": 8, "C": 7, "D": 6, "E": 5, "F": 0}


def clamp(value, low, high):
    return max(low, min(high, value))


def grade_for(total):
    """VTU-style letter grade from total marks (out of 100)."""
    if total >= 90: return "S"
    if total >= 80: return "A"
    if total >= 70: return "B"
    if total >= 60: return "C"
    if total >= 50: return "D"
    if total >= 40: return "E"
    return "F"


def main():
    students, results = [], []

    # Expand branch plan into a shuffled list of branches (realistic mix)
    branch_list = [b for b, n in BRANCH_PLAN for _ in range(n)]
    random.shuffle(branch_list)

    for i, branch in enumerate(branch_list, start=1):
        gender = "Female" if random.random() < 0.42 else "Male"
        first = random.choice(FEMALE_NAMES if gender == "Female" else MALE_NAMES)
        last = random.choice(SURNAMES)
        sid = f"STU{i:04d}"

        # latent ability drives marks, CGPA and attendance consistently
        ability = clamp(random.gauss(0.70, 0.15), 0.28, 0.90)

        marks_all = []
        for code, name, credits in SUBJECTS[branch]:
            internal = int(clamp(round(ability * 50 + random.gauss(0, 4)), 10, 50))
            external = int(clamp(round(ability * 50 + random.gauss(0, 7)), 5, 50))
            total = internal + external
            grade = grade_for(total)
            marks_all.append({
                "student_id": sid, "branch": branch, "semester": 5,
                "subject_code": code, "subject": name, "credits": credits,
                "internal": internal, "external": external, "total": total,
                "grade": grade,
                "result": "PASS" if grade != "F" else "FAIL",
            })
        results.extend(marks_all)

        fail_count = sum(1 for m in marks_all if m["result"] == "FAIL")
        cgpa = round(sum(GRADE_POINTS[m["grade"]] for m in marks_all) / len(marks_all), 2)
        attendance = round(clamp(random.gauss(85 - fail_count * 4, 7), 45, 98), 1)

        students.append({
            "student_id": sid,
            "name": f"{first} {last}",
            "gender": gender,
            "age": random.randint(19, 21),
            "branch": branch,
            "semester": 5,
            "section": random.choice(["A", "B", "C"]),
            "city": random.choice(CITIES),
            "admission_year": 2023,
            "hostel": random.random() < 0.42,
            "fee_paid": random.random() > 0.11,
            "cgpa": cgpa,
            "attendance_pct": attendance,
            "backlogs": fail_count,
            "email": f"{first.lower()}.{last.lower()}{i:04d}@amc.edu.in",
        })

    with open(os.path.join(OUT_DIR, "students.json"), "w") as f:
        json.dump(students, f, indent=2)
    with open(os.path.join(OUT_DIR, "results.json"), "w") as f:
        json.dump(results, f, indent=2)

    fails = sum(1 for r in results if r["result"] == "FAIL")
    print(f"Generated {len(students)} students -> students.json")
    print(f"Generated {len(results)} result records -> results.json")
    print(f"Failed subject records: {fails} ({fails / len(results) * 100:.1f}% of all results)")


if __name__ == "__main__":
    main()
