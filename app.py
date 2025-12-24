import streamlit as st
import pandas as pd
import time
import random

st.set_page_config(page_title="Online Test", layout="centered")

DATA_PATH = "master_adaptive_exam_1485_questions.xlsx"

@st.cache_data
def load_data():
    return pd.read_excel(DATA_PATH)

df = load_data()

# ---------------- SESSION STATE ----------------
if "started" not in st.session_state:
    st.session_state.started = False
if "q_index" not in st.session_state:
    st.session_state.q_index = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "questions" not in st.session_state:
    st.session_state.questions = []
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "total_time" not in st.session_state:
    st.session_state.total_time = None

# ---------------- START SCREEN ----------------
if not st.session_state.started:
    st.title("📝 Online Test System")

    subject = st.selectbox("Select Subject", ["Aptitude", "GK", "English"])
    q_count = st.selectbox("Select Number of Questions", [30, 50, 100])

    if st.button("Start Test"):
        subset = df[df["subject"] == subject].sample(q_count).reset_index(drop=True)

        st.session_state.questions = subset
        st.session_state.started = True
        st.session_state.q_index = 0
        st.session_state.score = 0
        st.session_state.start_time = time.time()
        st.session_state.total_time = q_count * 60

        st.rerun()

# ---------------- TEST SCREEN ----------------
else:
    questions = st.session_state.questions
    q_no = st.session_state.q_index

    elapsed = int(time.time() - st.session_state.start_time)
    remaining = st.session_state.total_time - elapsed

    if remaining <= 0 or q_no >= len(questions):
        st.subheader("✅ Test Completed")
        st.write(f"Score: **{st.session_state.score} / {len(questions)}**")
        accuracy = round((st.session_state.score / len(questions)) * 100, 2)
        st.write(f"Accuracy: **{accuracy}%**")
        st.stop()

    q = questions.iloc[q_no]

    st.progress((q_no + 1) / len(questions))
    st.write(f"⏳ Time Left: {remaining//60} min {remaining%60} sec")

    st.subheader(f"Question {q_no + 1}")
    st.write(q["question_text"])

    options = {
        "A": q["option_a"],
        "B": q["option_b"],
        "C": q["option_c"],
        "D": q["option_d"],
    }

    # 🔑 UNIQUE KEY PER QUESTION (THIS FIXES AUTO-SELECTION)
    radio_key = f"q_{q_no}"

    choice = st.radio(
        "Choose one option:",
        list(options.keys()),
        format_func=lambda x: f"{x}. {options[x]}",
        index=None,                 # ❗ prevents auto-selection
        key=radio_key
    )

    if st.button("Submit Answer"):
        if choice is None:
            st.warning("⚠️ Please select an option before submitting.")
            st.stop()

        correct = q["correct_option"]

        if choice == correct:
            st.success("✅ Correct!")
            st.session_state.score += 1
        else:
            st.error(f"❌ Wrong! Correct answer: {correct}")

        # 🔄 MOVE TO NEXT QUESTION
        st.session_state.q_index += 1

        # ❗ CLEAR RADIO STATE
        del st.session_state[radio_key]

        st.rerun()
