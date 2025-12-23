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

# -------------------------------
# Test Screen
# -------------------------------
if st.session_state.started:

    elapsed = time.time() - st.session_state.start_time
    remaining = st.session_state.total_questions * 60 - elapsed

    if remaining <= 0:
        st.warning("⏰ Time is up!")
        st.session_state.started = False
        st.rerun()

    st.info(f"⏳ Remaining Time: {int(remaining//60)}m {int(remaining%60)}s")
    st.write(f"**Subject:** {st.session_state.subject}")
    st.write(f"**Difficulty Level:** {st.session_state.current_difficulty}")

    questions_df = get_questions_by_subject(st.session_state.subject)

    if st.session_state.current_question is None:
        question = select_question(
            questions_df,
            st.session_state.current_difficulty,
            st.session_state.asked_ids,
            st.session_state.easy_toggle
        )
        st.session_state.current_question = question
        st.session_state.asked_ids.add(question["question_id"])
    else:
        question = st.session_state.current_question

    st.subheader(f"Question {st.session_state.current_q}")
    st.write(question["question_text"])

    answer = st.radio(
        "Choose your answer",
        ["A", "B", "C", "D"],
        key=f"q_{st.session_state.current_q}"
    )

    if st.button("Submit Answer"):
        correct_option = question["correct_option"]
        correct = (answer == correct_option)

        if correct:
            st.success("✅ Correct Answer")
        else:
            st.error(f"❌ Wrong Answer | Correct: {correct_option}")

        # -------------------------------
        # EASY BLOCK LOGIC (3 QUESTIONS)
        # -------------------------------
        if st.session_state.current_difficulty == 1:
            st.session_state.easy_block_total += 1
            if correct:
                st.session_state.easy_block_correct += 1

            if st.session_state.easy_block_total == 3:
                if st.session_state.easy_block_correct == 3:
                    st.session_state.current_difficulty = 2
                    st.success("🎯 Promoted to Easy–Medium level!")
                else:
                    st.info("🔁 Staying at Easy level for more practice")

                st.session_state.easy_block_total = 0
                st.session_state.easy_block_correct = 0

            st.session_state.easy_toggle = 1 - st.session_state.easy_toggle

        # -------------------------------
        # Log Attempt
        # -------------------------------
        st.session_state.attempts.append({
            "question_no": st.session_state.current_q,
            "question_id": question["question_id"],
            "difficulty": st.session_state.current_difficulty,
            "correct": int(correct),
            "timestamp": datetime.now().isoformat()
        })

        st.session_state.current_q += 1
        st.session_state.current_question = None

        if st.session_state.current_q > st.session_state.total_questions:
            st.session_state.started = False
            st.success("🎉 Test Completed!")
            st.write("### Final Result")
            result_df = pd.DataFrame(st.session_state.attempts)
            st.write(result_df)
        else:
            st.rerun()
