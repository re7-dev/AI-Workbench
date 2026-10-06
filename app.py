import streamlit as st
import pandas as pd
# 修改点 1：从最新的 core.db_manager 导入新函数
from core.db_manager import init_database, get_connection

st.set_page_config(page_title="AI Workbench", page_icon="🖥", layout="wide")

# 修改点 2：调用全新的建表函数
init_database()

st.title("🖥️ 薛紫元的数字工作台中枢")
st.markdown("欢迎回来。以下是你的专业学业与科研数据总览。")
st.markdown("---")

# ======== 1. 核心指标面板 (从数据库实时读取) ========
conn = get_connection()

try:
    grades_df = pd.read_sql_query("SELECT credits FROM grades", conn)
    total_courses = len(grades_df)
    total_credits = grades_df['credits'].astype(float).sum() if not grades_df.empty else 0.0
except:
    total_courses, total_credits = 0, 0.0

try:
    proj_count = pd.read_sql_query("SELECT COUNT(*) FROM projects", conn).iloc[0,0]
    algo_count = pd.read_sql_query("SELECT COUNT(*) FROM algorithms", conn).iloc[0,0]
except:
    proj_count, algo_count = 0, 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("已录入课程", f"{total_courses} 门")
c2.metric("已修总学分", f"{total_credits:.2f}")
c3.metric("工程项目归档", f"{proj_count} 个")
c4.metric("算法题库累积", f"{algo_count} 题")

st.markdown("---")

# ======== 2. 开发者名片 & 动态待办 ========
col_left, col_right = st.columns([2, 1])

with col_right:
    st.info("""
    **👤 开发者名片**
    - **学籍**：四川大学 计算机学院
    - **专业**：人工智能专业 1班
    - **学号**：2025141460548
    """)

with col_left:
    st.subheader("🎯 最近动态与待办")
    
    # 录入新待办的输入框
    with st.form("todo_form", clear_on_submit=True):
        new_todo = st.text_input("添加新动态/待办事项：", placeholder="例如：推进多模态 AI 大创开题...")
        if st.form_submit_button("添加"):
            if new_todo:
                # 修改点 3：对齐最新的系统待办表名 sys_todos
                conn.execute("INSERT INTO sys_todos (content) VALUES (?)", (new_todo,))
                conn.commit()
                st.rerun()
                
    # 展示待办列表并提供删除功能
    try:
        todos_df = pd.read_sql_query("SELECT id, content FROM sys_todos ORDER BY id DESC", conn)
        if not todos_df.empty:
            for _, row in todos_df.iterrows():
                col_text, col_btn = st.columns([8, 1])
                col_text.markdown(f"🔹 {row['content']}")
                if col_btn.button("🗑️", key=f"del_{row['id']}"):
                    conn.execute("DELETE FROM sys_todos WHERE id=?", (row['id'],))
                    conn.commit()
                    st.rerun()
        else:
            st.write("暂无动态，请在上方添加。")
    except:
        st.write("数据加载中...")

conn.close()