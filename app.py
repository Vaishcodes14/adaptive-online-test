import streamlit as st
import pandas as pd
import time
from datetime import datetime

# =========================================
# LOAD DATASET
# =========================================
@st.cache_data
def load_data():
    return pd.read_csv("govt_exam_3000_questions_SYNTHETIC_FIXED_TIME.csv")

df = load_data()

# =========================================
# SESSION STATE INITIALIZATION
# =========================================
if "started" not in st.session_state:
    st.session_state.started = False
    st.session_state.subject = None
    st.session_state.total_questions = 0
    st.session_state.start_time = None
    st.session_state.current_q = 1
    st.session_state.current_difficulty = 1
    st.session_state.block_total = 0
    st.session_state.block_correct = 0
    st.session_state.block_wrong = 0
    st.session_state.asked_ids = set()
    st.session_state.attempts = []
    st.session_state.current_question = None

# =========================================
# HELPER FUNCTIONS
# =========================================
def get_questions_by_subject(subject):
    return df[df["subject"] == subject].copy()

def select_question(questions_df, difficulty, asked_ids):
    pool = questions_df[
        (questions_df["difficulty_level"] == difficulty) &
        (~questions_df["question_id"].isin(asked_ids))
    ]

    if pool.empty:
        pool = questions_df[~questions_df["question_id"].isin(asked_ids)]

    return pool.sample(1).iloc[0]

# =========================================
# START SCREEN
# =========================================
st.title("📝 Adaptive Online Test")

if not st.session_state.started:

    subject = st.selectbox(
        "Select Subject",
        ["-- Select Subject --", "Aptitude", "English", "GK"]
    )

    total_questions = st.selectbox(
        "Select Number of Questions",
        ["-- Select Count --", 30, 50, 100]
    )

    if st.button("Start Test"):
        if subject == "-- Select Subject --" or total_questions == "-- Select Count --":
            st.warning("⚠️ Please select subject and number of questions")
        else:
            st.session_state.started = True
            st.session_state.subject = subject
            st.session_state.total_questions = total_questions
            st.session_state.start_time = time.time()

            st.session_state.current_q = 1
            st.session_state.current_difficulty = 1
            st.session_state.block_total = 0
            st.session_state.block_correct = 0
            st.session_state.block_wrong = 0
            st.session_state.asked_ids = set()
            st.session_state.attempts = []
            st.session_state.current_question = None

            st.rerun()

# =========================================
# TEST SCREEN
# =========================================
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
            st.session_state.asked_ids
        )
        st.session_state.current_question = question
        st.session_state.asked_ids.add(question["question_id"])
    else:
        question = st.session_state.current_question

    st.subheader(f"Question {st.session_state.current_q}")
    st.write(question["question_text"])

    options = {
        "-- Select an option --": "",
        "A": question["option_a"],
        "B": question["option_b"],
        "C": question["option_c"],
        "D": question["option_d"]
    }

    answer = st.radio(
        "Choose your answer",
        options.keys(),
        format_func=lambda x: x if x.startswith("--") else f"{x}. {options[x]}",
        key=f"q_{st.session_state.current_q}"
    )

    if st.button("Submit Answer"):

        if answer == "-- Select an option --":
            st.warning("⚠️ Please select an option")
            st.stop()

        correct = (answer == question["correct_option"])

        if correct:
            st.success("✅ Correct")
            st.session_state.block_correct += 1
        else:
            st.error(
                f"❌ Wrong | Correct: {question['correct_option']}. "
                f"{options[question['correct_option']]}"
            )
            st.session_state.block_wrong += 1

        st.session_state.block_total += 1

        # =========================================
        # BLOCK-BASED DIFFICULTY UPDATE
        # =========================================
        if st.session_state.block_total == 3:

            if st.session_state.block_correct == 3:
                st.session_state.current_difficulty = min(
                    st.session_state.current_difficulty + 1, 5
                )
                st.success("⬆ Difficulty Increased")

            elif st.session_state.block_wrong == 3:
                st.session_state.current_difficulty = max(
                    st.session_state.current_difficulty - 1, 1
                )
                st.warning("⬇ Difficulty Decreased")

            # Reset block counters
            st.session_state.block_total = 0
            st.session_state.block_correct = 0
            st.session_state.block_wrong = 0

        # LOG ATTEMPT
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
            st.success("🎉 Test Completed")
            st.write("### Final Result")
            st.write(pd.DataFrame(st.session_state.attempts))
        else:
            st.rerun()
