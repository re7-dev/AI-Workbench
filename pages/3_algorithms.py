import streamlit as st
import pandas as pd
from core.db_manager import get_connection

st.set_page_config(page_title="Algorithms", page_icon="🧩")
st.title("🧩 算法与竞赛错题本")

with st.form("algo_form", clear_on_submit=True):
    c1, c2, c3 = st.columns([2, 1, 1])
    title = c1.text_input("题目名称", placeholder="如：1. 两数之和")
    diff = c2.selectbox("难度", ["简单", "中等", "困难"])
    tags = c3.text_input("标签", placeholder="如：动态规划, 图论")
    
    if st.form_submit_button("录入题库"):
        if title:
            with get_connection() as conn:
                conn.execute("INSERT INTO algorithms (title, difficulty, tags, status) VALUES (?, ?, ?, ?)",
                             (title, diff, tags, "需复习"))
                conn.commit()
            st.success("题目已归档！")
            st.rerun()

st.divider()

with get_connection() as conn:
    df = pd.read_sql_query("SELECT title as 题目, difficulty as 难度, tags as 标签, status as 状态, review_count as 复习次数 FROM algorithms", conn)

if not df.empty:
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("题库空空如也，今天刷一道 LeetCode 吧！")