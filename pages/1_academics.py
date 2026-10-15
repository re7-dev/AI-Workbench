import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db_manager import get_connection

st.set_page_config(page_title="学业大盘", page_icon="🎓", layout="wide")

st.title("🎓 动态学业数据看板")
st.divider()

# ==========================================
# 交互式数据录入表单
# ==========================================
with st.expander("➕ 录入新成绩", expanded=False):
    with st.form("add_grade_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            course_name = st.text_input("课程名称", placeholder="例如：线性代数")
        with col2:
            credits = st.number_input("学分", min_value=0.5, step=0.5)
        with col3:
            grade = st.text_input("分数/等级", placeholder="例如：95 或 A")
        
        course_type = st.selectbox("修读性质", ["必修", "选修", "实践"])
        submitted = st.form_submit_button("保存至云端数据库")
        
        if submitted and course_name and grade:
            try:
                conn = get_connection()
                # 动态写入云端数据库
                query = text("INSERT INTO grades (course_name, credits, grade, course_type) VALUES (:c, :cr, :g, :ct)")
                conn.execute(query, {"c": course_name, "cr": credits, "g": grade, "ct": course_type})
                conn.commit()
                st.success("添加成功！")
                st.rerun() # 刷新页面显示最新数据
            except Exception as e:
                st.error(f"保存失败: {e}")

# ==========================================
# 动态指标与表格展示
# ==========================================
conn = get_connection()
df_grades = pd.read_sql_query("SELECT * FROM grades", conn)

st.subheader("📊 核心指标看板")
col1, col2, col3, col4 = st.columns(4)

# 根据数据库真实数据动态计算
total_courses = len(df_grades)
total_credits = df_grades['credits'].sum() if not df_grades.empty else 0

with col1:
    st.metric(label="已修课程总数", value=f"{total_courses} 门")
with col2:
    st.metric(label="累计获得学分", value=f"{total_credits}")
with col3:
    st.metric(label="云端数据库状态", value="已连接", delta="实时同步")
with col4:
    st.metric(label="底层架构", value="Supabase", delta="PostgreSQL", delta_color="off")

st.divider()

st.subheader("📂 课程成绩库")
if not df_grades.empty:
    st.dataframe(
        df_grades,
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": None, # 隐藏数据库生成的内部 ID
            "course_name": st.column_config.TextColumn("课程名称", width="large"),
            "credits": st.column_config.NumberColumn("学分", format="%.1f"),
            "grade": st.column_config.TextColumn("分数/等级"),
            "course_type": st.column_config.TextColumn("修读性质")
        }
    )
else:
    st.info("暂无成绩数据，请在上方表单中录入第一条数据。")