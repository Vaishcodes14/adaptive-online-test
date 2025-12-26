import streamlit as st
import pandas as pd
import time

# ================= CONFIG =================
st.set_page_config(page_title="Adaptive Online Test", layout="centered")

DATA_PATH = "master_adaptive_exam_1485_FINAL.xls"
LEVELS = ["Easy", "Easy-Medium", "Medium", "Medium-Hard", "Hard"]

# ================= LOAD DATA =================
@st.cache_data
def load_data():
    df = pd.read_excel(DATA_PATH)
    df = df.fillna("")

    # Normalize columns
    for col in ["Subject", "Concept", "Difficulty"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df

df = load_data()

# ================= STRICT EASY FILTER =================
def is_truly_easy(row):
    text = str(row["Question"]).lower()

    # too long → not easy
    if len(text) > 120:
        return False

    # avoid complex concepts
    bad_words = [
        "mixture", "alligation", "compound", "per annum",
        "successive", "discount", "speed", "work together"
    ]
    if any(w in text for w in bad_words):
        return False

    # avoid large numbers
    for token in text.split():
        if token.isdigit() and int(token) > 100:
            return False

    return True

# ================= SESSION STATE =================
if "started" not in st.session_state:
    st.session_state.started = False
    st.session_state.q_index = 0
    st.session_state.score = 0
    st.session_state.level_index = 0
    st.session_state.block_answers = []
    st.session_state.used_ids = set()
    st.session_state.used_concepts = set()

# ================= START SCREEN =================
if not st.session_state.started:
    st.title("📝 Adaptive Online Test")

    subject = st.selectbox(
        "Select Subject",
        sorted(df["Subject"].unique())
    )
    total_qs = st.selectbox("Number of Questions", [30, 50, 100])

    if st.button("Start Test"):
        st.session_state.started = True
        st.session_state.subject = subject
        st.session_state.total_qs = total_qs
        st.session_state.start_time = time.time()

        # reset state
        st.session_state.q_index = 0
        st.session_state.score = 0
        st.session_state.level_index = 0
        st.session_state.block_answers = []
        st.session_state.used_ids = set()
        st.session_state.used_concepts = set()

        st.rerun()

# ================= QUESTION PICKER =================
def get_question():
    level = LEVELS[st.session_state.level_index]
    subject = st.session_state.subject

    pool = df[
        (df["Subject"] == subject) &
        (df["Difficulty"].str.contains(level.split("-")[0], case=False))
    ]

    pool = pool[~pool.index.isin(st.session_state.used_ids)]

    # FIRST 3 → STRICT EASY
    if st.session_state.q_index < 3:
        pool = pool[pool.apply(is_truly_easy, axis=1)]

    # rotate concepts
    if st.session_state.used_concepts:
        pool = pool[~pool["Concept"].isin(st.session_state.used_concepts)]

    if pool.empty:
        pool = df[df["Subject"] == subject]

    q = pool.sample(1).iloc[0]
    return q

# ================= TEST SCREEN =================
if st.session_state.started:
    if st.session_state.q_index >= st.session_state.total_qs:
        st.subheader("✅ Test Completed")
        st.write(f"Score: **{st.session_state.score}/{st.session_state.total_qs}**")
        st.write(f"Final Level: **{LEVELS[st.session_state.level_index]}**")
        st.stop()

    q = get_question()
    q_id = q.name

    st.session_state.used_ids.add(q_id)
    st.session_state.used_concepts.add(q["Concept"])

    st.info(f"Difficulty Level: {LEVELS[st.session_state.level_index]}")
    st.subheader(f"Question {st.session_state.q_index + 1}")
    st.write(q["Question"])

    options = {
        "A": q["Option_A"],
        "B": q["Option_B"],
        "C": q["Option_C"],
        "D": q["Option_D"],
    }

    radio_key = f"q_{st.session_state.q_index}"

    choice = st.radio(
        "Choose one option:",
        list(options.keys()),
        format_func=lambda x: f"{x}. {options[x]}",
        index=None,
        key=radio_key
    )

    if st.button("Submit Answer"):
        correct = q["Correct_Option"]

        if choice == correct:
            st.success("✅ Correct")
            st.session_state.score += 1
            st.session_state.block_answers.append(True)
        else:
            st.error(f"❌ Wrong | Correct answer: {correct}")
            st.session_state.block_answers.append(False)

        st.session_state.q_index += 1

        # ---- 3 QUESTION ADAPTIVE RULE ----
        if len(st.session_state.block_answers) == 3:
            if all(st.session_state.block_answers):
                if st.session_state.level_index < len(LEVELS) - 1:
                    st.session_state.level_index += 1
            st.session_state.block_answers.clear()
            st.session_state.used_concepts.clear()

        # 🔥 clear radio (prevents auto selection)
        if radio_key in st.session_state:
            del st.session_state[radio_key]

        st.rerun()
