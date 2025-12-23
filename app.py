import streamlit as st
import pandas as pd
import time
from datetime import datetime
@st.cache_data
def load_data():
    return pd.read_csv("govt_exam_3000_questions_SYNTHETIC_FIXED_TIME.csv")

df = load_data()

