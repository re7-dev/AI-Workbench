import streamlit as st
import pandas as pd
from core.db_manager import get_connection
from core.scu_gpa_engine import process_academic_metrics

st.set_page_config(page_title="Academic Records", page_icon="📊")
st.title("📊 学业与 GPA 管理")

with st.expander("➕ 录入新成绩", expanded=False):
    with st.form("grade_form"):
        c1, c2, c3, c4 = st.columns(4)
        name = c1.text_input("课程名称")
        credits = c2.number_input("学分", min_value=0.0, step=0.25, value=2.0)
        grade = c3.text_input("成绩 (纯数字输入, 如: 89, 92.5)")
        ctype = c4.selectbox("性质", ["必修", "通识", "跨专", "专业选修"])
        
        if st.form_submit_button("保存至数据库"):
            if name and grade:
                with get_connection() as conn:
                    conn.execute("INSERT INTO grades (course_name, credits, grade, course_type) VALUES (?, ?, ?, ?)", 
                                 (name, credits, grade, ctype))
                    conn.commit()
                st.success(f"《{name}》录入成功！")
                st.rerun()

st.divider()

with get_connection() as conn:
    # 修正点 1：直接查询英文原字段，不在这里做中文映射，确保引擎能读取到 'credits'
    df = pd.read_sql_query("SELECT course_name, credits, grade, course_type FROM grades", conn)

if not df.empty:
    # 此时传入的 df 包含标准英文字段，底层引擎不再报错
    metrics = process_academic_metrics(df)
    
    st.subheader("🎯 核心指标看板")
    
    st.markdown("**全部课程 (Overall)**")
    c1, c2, c3 = st.columns(3)
    c1.metric("全部加权均分", f"{metrics['overall_avg']:.2f}")
    c2.metric("全部绩点 (官方标准)", f"{metrics['overall_gpa']:.2f}")
    c3.metric("总计学分", f"{metrics['total_credits']:.2f}")
    
    st.markdown("**必修课程 (Required Only)**")
    c4, c5, c6 = st.columns(3)
    c4.metric("必修加权均分", f"{metrics['req_avg']:.2f}")
    c5.metric("必修绩点", f"{metrics['req_gpa']:.2f}")
    c6.metric("必修学分", f"{metrics['req_credits']:.2f}")
    
    st.divider()
    
    # 修正点 2：在展示给用户看之前，利用 pandas 将英文列名重命名为中文表头
    display_df = df.rename(columns={
        'course_name': '课程', 
        'credits': '学分', 
        'grade': '成绩', 
        'course_type': '性质',
        'gpa': '单科绩点'
    })
    st.dataframe(display_df, use_container_width=True)
else:
    st.info("数据库目前为空，请尝试在上方录入第一门课程的数据。")