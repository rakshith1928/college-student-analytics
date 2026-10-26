"""
College Student Analytics - Streamlit Dashboard (Showcase Component)
=====================================================================
Connects to the MongoDB Atlas cluster named in .env (college_analytics
database), populated by generate_data.py / load_data.py and presents dashboards:

  1. Overview metrics (student count, average CGPA, average attendance)
  2. Branch-wise student strength and average CGPA (bar charts)
  3. CGPA distribution histogram
  4. Attendance risk bands (bar chart)
  5. Subject-wise average marks and pass percentage (CSE branch)
  6. Top 10 students by CGPA table

Usage:
    streamlit run streamlit_app.py

Requirements (in addition to the batch pipeline):
    streamlit, plotly, pandas
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv(override=True)

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    try:
        MONGO_URI = st.secrets["MONGO_URI"]
    except (FileNotFoundError, KeyError):
        MONGO_URI = None
DB_NAME = "college_analytics"

st.set_page_config(
    page_title="College Student Analytics - MongoDB Dashboard",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 College Student Analytics - MongoDB Dashboard")
st.caption(
    "Real-time dashboard over the college_analytics MongoDB database. "
    "Data generated and loaded by the batch pipeline (generate_data.py / load_data.py)."
)


# ------------------------------------------------------------------ #
# Data access
# ------------------------------------------------------------------ #
@st.cache_resource
def get_collection():
    if not MONGO_URI:
        raise RuntimeError("MONGO_URI is not set - add it to Streamlit app "
                           "Secrets (settings page) or .env for local runs.")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    client.admin.command("ping")
    return client[DB_NAME]["students"]


@st.cache_data(ttl=60)
def load_students():
    """Return all student documents as a pandas DataFrame."""
    coll = get_collection()
    docs = list(coll.find({}, {"_id": 0}))
    return pd.DataFrame(docs)


# ------------------------------------------------------------------ #
# Header metrics
# ------------------------------------------------------------------ #
try:
    df = load_students()
except Exception as exc:  # noqa: BLE001
    st.error(
        "Could not connect to MongoDB Atlas. Set MONGO_URI in Streamlit Secrets "
        "(app settings page) or .env for local runs, check the Atlas IP "
        "allowlist, and run load_data.py at least once."
    )
    st.exception(exc)
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Students", len(df))
c2.metric("Average CGPA", f"{df['cgpa'].mean():.2f}")
c3.metric("Average Attendance", f"{df['attendance_pct'].mean():.1f}%")
c4.metric("Students with Backlog", int((df["backlogs"] > 0).sum()))

st.divider()

# ------------------------------------------------------------------ #
# Branch-wise analysis
# ------------------------------------------------------------------ #
st.subheader("📊 Branch-wise Performance")

branch_stats = (
    df.groupby("branch", as_index=False)
    .agg(students=("student_id", "count"), avg_cgpa=("cgpa", "mean"),
         avg_attendance=("attendance_pct", "mean"))
    .sort_values("avg_cgpa", ascending=False)
)

col1, col2 = st.columns(2)
with col1:
    fig_strength = px.bar(
        branch_stats, x="branch", y="students",
        text="students", color="branch",
        title="Student Strength by Branch",
        labels={"branch": "Branch", "students": "Number of Students"},
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig_strength.update_traces(textposition="outside")
    fig_strength.update_layout(showlegend=False, height=380)
    st.plotly_chart(fig_strength, use_container_width=True)

with col2:
    fig_cgpa = px.bar(
        branch_stats, x="branch", y="avg_cgpa",
        text="avg_cgpa", color="branch",
        title="Average CGPA by Branch",
        labels={"branch": "Branch", "avg_cgpa": "Average CGPA"},
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig_cgpa.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig_cgpa.update_layout(showlegend=False, yaxis=dict(range=[0, 10]), height=380)
    st.plotly_chart(fig_cgpa, use_container_width=True)

# ------------------------------------------------------------------ #
# CGPA distribution
# ------------------------------------------------------------------ #
st.subheader("📈 CGPA Distribution")

fig_hist = px.histogram(
    df, x="cgpa", nbins=20,
    title="Distribution of Student CGPA",
    labels={"cgpa": "CGPA", "count": "Number of Students"},
    color_discrete_sequence=["#2F4A73"],
)
fig_hist.update_layout(height=380)
st.plotly_chart(fig_hist, use_container_width=True)

# ------------------------------------------------------------------ #
# Attendance bands
# ------------------------------------------------------------------ #
st.subheader("⚠️ Attendance Risk Bands")

attendance_bins = [0, 60, 75, 85, 101]
attendance_labels = ["<60% (Critical)", "60-74% (Warning)",
                     "75-84% (Healthy)", "85-100% (Excellent)"]
df["attendance_band"] = pd.cut(
    df["attendance_pct"], bins=attendance_bins, labels=attendance_labels,
    include_lowest=True,
)
band_counts = (
    df["attendance_band"].value_counts()
    .reindex(attendance_labels, fill_value=0)
    .reset_index()
)
band_counts.columns = ["attendance_band", "students"]

fig_band = px.bar(
    band_counts, x="attendance_band", y="students",
    text="students", color="attendance_band",
    title="Students by Attendance Band",
    labels={"attendance_band": "Attendance Band", "students": "Number of Students"},
    color_discrete_sequence=["#C44E52", "#DD8452", "#4C72B0", "#55A868"],
)
fig_band.update_traces(textposition="outside")
fig_band.update_layout(showlegend=False, height=380)
st.plotly_chart(fig_band, use_container_width=True)

# ------------------------------------------------------------------ #
# Top students
# ------------------------------------------------------------------ #
st.subheader("🏆 Top 10 Students by CGPA")

top_students = (
    df[["student_id", "name", "branch", "cgpa", "attendance_pct", "backlogs"]]
    .sort_values("cgpa", ascending=False)
    .head(10)
    .reset_index(drop=True)
)
top_students.index = top_students.index + 1  # start ranking at 1
top_students.columns = ["Student ID", "Name", "Branch", "CGPA",
                        "Attendance (%)", "Backlogs"]
st.dataframe(top_students, use_container_width=True, hide_index=False)

# ------------------------------------------------------------------ #
# Subject-wise performance (sample of CSE subjects)
# ------------------------------------------------------------------ #
st.subheader("📚 Subject-wise Performance (Sample: CSE)")
st.caption("Load results.json separately to see full subject-wise analytics. "
           "This dashboard shows summary metrics from the students collection.")

st.info(
    "Run the batch pipeline (python run_all.py) to regenerate data, reload "
    "MongoDB, and re-run the Q1-Q7 analyses with explain() verification."
)

st.divider()
st.caption(
    "College Student Analytics using MongoDB | BDA Mini Project | "
    "Streamlit Dashboard"
)
