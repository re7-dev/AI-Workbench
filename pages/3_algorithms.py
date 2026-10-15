import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db_manager import get_connection

st.set_page_config(page_title="算法题库", page_icon="🧩", layout="wide")

st.title("🧩 算法刷题追踪矩阵")
st.divider()

# ==========================================
# 交互式题目添加
# ==========================================
with st.expander("➕ 添加新算法题", expanded=False):
    with st.form("add_algo_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("题目名称", placeholder="例如：LeetCode 1. 两数之和")
            difficulty = st.selectbox("难度", ["简单", "中等", "困难"])
        with col2:
            tags = st.text_input("知识点标签", placeholder="例如：哈希表, 双指针")
            status = st.selectbox("掌握状态", ["未开始", "一刷完成", "需复习", "已掌握"])
        
        submitted = st.form_submit_button("记录题目")
        
        if submitted and title:
            try:
                conn = get_connection()
                # 修复点：使用 text() 和字典传参
                query = text("INSERT INTO algorithms (title, difficulty, tags, status) VALUES (:t, :d, :tag, :s)")
                conn.execute(query, {"t": title, "d": difficulty, "tag": tags, "s": status})
                conn.commit()
                st.success("成功添加到云端题库！")
                st.rerun()
            except Exception as e:
                st.error(f"保存失败: {e}")

# ==========================================
# 题库数据展示
# ==========================================
st.subheader("📚 我的题库")
try:
    conn = get_connection()
    df_algos = pd.read_sql_query("SELECT * FROM algorithms", conn)
    
    if not df_algos.empty:
        st.dataframe(
            df_algos,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": None,
                "title": st.column_config.TextColumn("题目"),
                "difficulty": st.column_config.TextColumn("难度"),
                "tags": st.column_config.TextColumn("知识点标签"),
                "status": st.column_config.TextColumn("当前状态"),
                "review_count": st.column_config.NumberColumn("复习次数")
            }
        )
    else:
        st.info("题库为空，快去刷第一道题吧！")
except Exception as e:
    st.error("读取数据失败。")