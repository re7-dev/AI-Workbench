import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db_manager import get_connection

st.set_page_config(page_title="科研大创", page_icon="🔬", layout="wide")

st.title("🔬 个人科研与大创看板")
st.caption("多模态学习与计算机视觉方向")
st.divider()

# ==========================================
# 录入科研待办/任务
# ==========================================
with st.expander("➕ 添加新任务", expanded=False):
    with st.form("add_research_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            task_name = st.text_input("任务名称", placeholder="例如：阅读 CVPR 2026 综述文献")
            stage = st.selectbox("当前阶段", ["文献调研", "导师沟通", "模型训练", "论文撰写"])
        with col2:
            deadline = st.date_input("截止日期")
            notes = st.text_area("备注/想法", placeholder="记录关键思路...")
            
        submitted = st.form_submit_button("添加任务")
        
        if submitted and task_name:
            try:
                conn = get_connection()
                # 修复点：使用 text() 和字典传参
                query = text("INSERT INTO research_tasks (task_name, stage, deadline, notes) VALUES (:n, :s, :d, :note)")
                conn.execute(query, {"n": task_name, "s": stage, "d": deadline, "note": notes})
                conn.commit()
                st.success("任务添加成功！")
                st.rerun()
            except Exception as e:
                st.error(f"保存失败: {e}")

# ==========================================
# 任务看板渲染
# ==========================================
st.subheader("📋 科研任务进度流")
try:
    conn = get_connection()
    df_tasks = pd.read_sql_query("SELECT * FROM research_tasks", conn)
    
    if not df_tasks.empty:
        st.dataframe(
            df_tasks,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": None,
                "task_name": st.column_config.TextColumn("任务", width="large"),
                "stage": st.column_config.TextColumn("阶段"),
                "deadline": st.column_config.DateColumn("截止时间"),
                "notes": st.column_config.TextColumn("备注")
            }
        )
    else:
        st.info("当前无待办科研任务。")
except Exception as e:
    st.error("数据库读取失败。")