import streamlit as st
import pandas as pd
import time

# ===================== CONFIG =====================
st.set_page_config(page_title="Adaptive Online Test", layout="centered")

DATA_PATH = "master_adaptive_exam_1485_FINAL.xlsx"
LEVELS = ["Easy", "Medium", "Hard"]

# ===================== LOAD DATA =====================
@st.cache_data
def load_data():
    df = pd.read_excel(DATA_PATH)
    df = df.fillna("")   # 🔥 prevent NaN issues
    return df

df = load_data()

# ===================== SESSION STATE =====================
def init_state():
    defaults = {
        "started": False,
        "q_index": 0,
        "score": 0,
        "questions": None,
        "start_time": None,
        "total_time": None,
        "difficulty": "Easy",
        "correct_streak": 0,
        "wrong_streak": 0
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ===================== START SCREEN =====================
if not st.session_state.started:
    st.title("📝 Adaptive Online Test")

    subject = st.selectbox("Select Subject", ["Aptitude", "GK", "English"])
    q_count = st.selectbox("Select Number of Questions", [30, 50, 100])

    if st.button("Start Test"):
        # STRICT EASY FILTER AT START
        pool = df[
            (df["subject"] == subject) &
            (df["difficulty"] == "Easy")
        ]

        if len(pool) < q_count:
            st.error("Not enough Easy questions available.")
            st.stop()

        st.session_state.questions = pool.sample(q_count).reset_index(drop=True)
        st.session_state.started = True
        st.session_state.q_index = 0
        st.session_state.score = 0
        st.session_state.start_time = time.time()
        st.session_state.total_time = q_count * 60
        st.session_state.correct_streak = 0
        st.session_state.wrong_streak = 0
        st.session_state.difficulty = "Easy"

        st.rerun()

# ===================== TEST SCREEN =====================
else:
    q_no = st.session_state.q_index
    questions = st.session_state.questions

    elapsed = int(time.time() - st.session_state.start_time)
    remaining = st.session_state.total_time - elapsed

    if remaining <= 0 or q_no >= len(questions):
        st.subheader("✅ Test Completed")
        st.write(f"Score: **{st.session_state.score} / {len(questions)}**")
        accuracy = round((st.session_state.score / len(questions)) * 100, 2)
        st.write(f"Accuracy: **{accuracy}%**")
        st.write(f"Final Difficulty Level: **{st.session_state.difficulty}**")
        st.stop()

    q = questions.iloc[q_no]

    # ===================== TIME + STATUS =====================
    st.progress((q_no + 1) / len(questions))
    st.write(f"⏳ Time Left: {remaining//60} min {remaining%60} sec")
    st.info(f"🎯 Current Difficulty: {st.session_state.difficulty}")

    st.subheader(f"Question {q_no + 1}")
    st.write(q["question_text"])

    # ===================== SAFE OPTIONS =====================
    options = {
        "A": q["option_a"] if q["option_a"] != "" else "Option not available",
        "B": q["option_b"] if q["option_b"] != "" else "Option not available",
        "C": q["option_c"] if q["option_c"] != "" else "Option not available",
        "D": q["option_d"] if q["option_d"] != "" else "Option not available",
    }

    # ===================== EASY-LEVEL VALIDATION =====================
    if st.session_state.difficulty == "Easy":
        # Skip numerically confusing options at Easy level
        bad_easy = any(
            str(v).isdigit() and len(str(v)) > 2
            for v in options.values()
        )
        if bad_easy:
            st.warning("⚠️ Skipping non-basic Easy question.")
            st.session_state.q_index += 1
            st.rerun()

    # ===================== OPTION SELECTION =====================
    radio_key = f"q_{q_no}"

    choice = st.radio(
        "Choose one option:",
        list(options.keys()),
        format_func=lambda x: f"{x}. {options[x]}",
        index=None,          # 🔥 prevents auto-selection
        key=radio_key
    )

    if st.button("Submit Answer"):
        if choice is None:
            st.warning("⚠️ Please select an option.")
            st.stop()

        correct = q["correct_option"]

        # ===================== CHECK ANSWER =====================
        if choice == correct:
            st.success("✅ Correct!")
            st.session_state.score += 1
            st.session_state.correct_streak += 1
            st.session_state.wrong_streak = 0
        else:
            st.error(f"❌ Wrong! Correct answer: {correct}")
            st.session_state.wrong_streak += 1
            st.session_state.correct_streak = 0

        # ===================== ADAPTIVE LOGIC =====================
        idx = LEVELS.index(st.session_state.difficulty)

        if st.session_state.correct_streak == 3 and idx < 2:
            st.session_state.difficulty = LEVELS[idx + 1]
            st.session_state.correct_streak = 0
            st.info(f"⬆ Difficulty increased to {st.session_state.difficulty}")

        if st.session_state.wrong_streak == 3 and idx > 0:
            st.session_state.difficulty = LEVELS[idx - 1]
            st.session_state.wrong_streak = 0
            st.info(f"⬇ Difficulty decreased to {st.session_state.difficulty}")

        # ===================== NEXT QUESTION =====================
        st.session_state.q_index += 1
        del st.session_state[radio_key]
        st.rerun()
