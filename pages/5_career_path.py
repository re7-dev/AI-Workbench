import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db_manager import get_connection

st.set_page_config(page_title="升学与网申", page_icon="✈️", layout="wide")

st.title("✈️ 境外升学与网申规划")
st.caption("高效追踪各院校网申 Deadline 与材料准备进度。")
st.divider()

# ==========================================
# 网申目标添加
# ==========================================
with st.expander("➕ 添加目标院校", expanded=False):
    with st.form("add_career_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            uni = st.text_input("目标院校", placeholder="如：NUS, NTU, IC, UCL")
            prog = st.text_input("专业项目", placeholder="如：MSc in AI / CS")
        with col2:
            ielts = st.number_input("雅思/托福目标", value=6.5, step=0.5)
            status = st.selectbox("当前进度", ["选校调研中", "材料准备", "网申已投递", "等待面试", "已拿 Offer"])
            ddl = st.date_input("网申截止日期")
            
        submitted = st.form_submit_button("加入院校库")
        
        if submitted and uni and prog:
            try:
                conn = get_connection()
                # 终极修复：严格遵循 SQLAlchemy 2.0 规范，使用字典传参[cite: 1, 2, 5]
                query = text("INSERT INTO career_applications (university, program, target_ielts, status, deadline) VALUES (:u, :p, :i, :s, :d)")
                conn.execute(query, {"u": uni, "p": prog, "i": ielts, "s": status, "d": ddl})
                conn.commit()
                st.success("成功加入清单！")
                st.rerun()
            except Exception as e:
                st.error(f"保存失败: {e}")

# ==========================================
# 升学进度大盘展示
# ==========================================
st.subheader("🎯 申请进度一览")
try:
    conn = get_connection()
    df_apps = pd.read_sql_query("SELECT * FROM career_applications", conn)
    
    if not df_apps.empty:
        # 为不同状态加上颜色标签，看起来更直观
        st.dataframe(
            df_apps,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": None,
                "university": st.column_config.TextColumn("学校", width="medium"),
                "program": st.column_config.TextColumn("专业", width="medium"),
                "target_ielts": st.column_config.NumberColumn("语言要求"),
                "status": st.column_config.TextColumn("进度状态"),
                "deadline": st.column_config.DateColumn("Deadline (D-Day)")
            }
        )
    else:
        st.info("尚未添加任何院校，赶快规划你的第一所 Dream School 吧！")
except Exception as e:
    st.error("数据库读取失败。")