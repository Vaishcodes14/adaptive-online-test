import streamlit as st
import pandas as pd
import time
from datetime import datetime

# -------------------------------
# Load Dataset
# -------------------------------
@st.cache_data
def load_data():
    return pd.read_csv("govt_exam_3000_questions_SYNTHETIC_FIXED_TIME.csv")

df = load_data()

# -------------------------------
# Helper Functions
# -------------------------------
def get_questions_by_subject(subject):
    return df[df["subject"] == subject].copy()

def select_question(questions_df, difficulty, asked_ids, easy_toggle):
    pool = questions_df[~questions_df["question_id"].isin(asked_ids)]

    if difficulty == 1:
        if easy_toggle == 0:
            pool = pool[
                (pool["difficulty_level"] == 1) &
                (pool["topic"] == "Percentages")
            ]
        else:
            pool = pool[
                (pool["difficulty_level"] == 1) &
                (pool["topic"] == "Ratio & Proportion")
            ]
    else:
        pool = pool[pool["difficulty_level"] == difficulty]

    if pool.empty:
        pool = questions_df[~questions_df["question_id"].isin(asked_ids)]

    return pool.sample(1).iloc[0]

# -------------------------------
# Session State Initialization
# -------------------------------
if "started" not in st.session_state:
    st.session_state.started = False
    st.session_state.subject = None
    st.session_state.total_questions = 0
    st.session_state.start_time = None
    st.session_state.current_q = 1
    st.session_state.current_difficulty = 1
    st.session_state.easy_toggle = 0
    st.session_state.easy_block_total = 0
    st.session_state.easy_block_correct = 0
    st.session_state.asked_ids = set()
    st.session_state.attempts = []
    st.session_state.current_question = None

# -------------------------------
# Start Screen
# -------------------------------
# -------------------------------
# Start Screen
# -------------------------------
st.title("📝 Adaptive Online Test")

if not st.session_state.started:
    subject = st.selectbox("Select Subject", ["Aptitude", "English", "GK"])
    total_questions = st.selectbox("Select Number of Questions", [30, 50, 100])

    if st.button("Start Test"):
        st.session_state.started = True
        st.session_state.subject = subject
        st.session_state.total_questions = total_questions
        st.session_state.start_time = time.time()
        st.session_state.current_q = 1
        st.session_state.current_difficulty = 1
        st.session_state.easy_toggle = 0
        st.session_state.easy_block_total = 0
        st.session_state.easy_block_correct = 0
        st.session_state.asked_ids = set()
        st.session_state.attempts = []
        st.rerun()
