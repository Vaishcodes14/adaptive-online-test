import streamlit as st
import pandas as pd
import time
import random

# ------------------ CONFIG ------------------
st.set_page_config(page_title="Adaptive Online Exam", layout="centered")

DATA_PATH = "master_adaptive_exam_1485_questions.xlsx"

# ------------------ LOAD DATA ------------------
@st.cache_data
def load_data():
    return pd.read_excel(DATA_PATH)

df = load_data()

# ------------------ SESSION STATE ------------------
if "started" not in st.session_state:
    st.session_state.started = False
if "q_index" not in st.session_state:
    st.session_state.q_index = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "questions" not in st.session_state:
    st.session_state.questions = []
if "answers" not in st.session_state:
    st.session_state.answers = []

# ------------------ START SCREEN ------------------
if not st.session_state.started:
    st.title("📝 Online Test System")

    subject = st.selectbox(
        "Select Subject",
        ["Aptitude", "GK", "English"]
    )

    q_count = st.selectbox(
        "Select Number of Questions",
        [30, 50, 100]
    )

    if st.button("Start Test"):
        subset = df[df["subject"] == subject].sample(q_count)
        st.session_state.questions = subset.reset_index(drop=True)
        st.session_state.started = True
        st.session_state.start_time = time.time()
        st.session_state.total_time = q_count * 60
        st.rerun()

# ------------------ TEST SCREEN ------------------
else:
    questions = st.session_state.questions
    q_no = st.session_state.q_index

    elapsed = int(time.time() - st.session_state.start_time)
    remaining = st.session_state.total_time - elapsed

    if remaining <= 0 or q_no >= len(questions):
        st.subheader("⏱ Test Completed")
        st.write(f"Score: **{st.session_state.score} / {len(questions)}**")

        percent = round((st.session_state.score / len(questions)) * 100, 2)
        st.write(f"Accuracy: **{percent}%**")

        st.stop()

    q = questions.iloc[q_no]

    st.progress(q_no / len(questions))
    st.write(f"⏳ Time Left: {remaining//60} min {remaining%60} sec")

    st.subheader(f"Question {q_no + 1}")
    st.write(q["question_text"])

    options = {
        "A": q["option_a"],
        "B": q["option_b"],
        "C": q["option_c"],
        "D": q["option_d"],
    }

    choice = st.radio(
        "Choose an option:",
        options.keys(),
        format_func=lambda x: f"{x}. {options[x]}"
    )

    if st.button("Submit Answer"):
        correct = q["correct_option"]

        if choice == correct:
            st.success("✅ Correct!")
            st.session_state.score += 1
        else:
            st.error(f"❌ Wrong! Correct Answer: {correct}")

        st.session_state.answers.append(choice)
        st.session_state.q_index += 1
        st.rerun()
