"""
College Student Analytics using MongoDB - BDA Mini Project
Step 6: Run the complete pipeline end-to-end:
  generate -> load + index -> analyses Q1-Q7 -> index verification -> charts
Usage: python run_all.py
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = ["generate_data.py", "load_data.py", "analyses.py",
           "explain_check.py", "visualise.py"]

for script in SCRIPTS:
    print()
    print("#" * 68)
    print(f"### RUNNING {script}")
    print("#" * 68)
    result = subprocess.run([sys.executable, os.path.join(HERE, script)])
    if result.returncode != 0:
        sys.exit(f"*** {script} failed with exit code {result.returncode} ***")

print("\nPipeline finished successfully.")
