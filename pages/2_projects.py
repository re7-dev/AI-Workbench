import streamlit as st
import pandas as pd
from core.db_manager import get_connection

st.set_page_config(page_title="Projects", page_icon="📁")
st.title("📁 个人项目与代码资产库")

with st.expander("➕ 归档新项目", expanded=False):
    with st.form("project_form"):
        c1, c2 = st.columns(2)
        p_name = c1.text_input("项目名称", placeholder="例如：SyntaxEditor")
        p_stack = c2.text_input("技术栈", placeholder="例如：Qt C++")
        
        c3, c4 = st.columns(2)
        p_status = c3.selectbox("当前状态", ["开发中", "已归档", "维护中", "计划中"])
        p_desc = c4.text_input("一句话简介")
        
        if st.form_submit_button("💾 保存至项目库"):
            if p_name:
                with get_connection() as conn:
                    conn.execute("INSERT INTO projects (project_name, tech_stack, status, repo_url) VALUES (?, ?, ?, ?)", 
                                 (p_name, p_stack, p_status, p_desc))
                    conn.commit()
                st.success(f"项目《{p_name}》已成功归档！")
                st.rerun()

st.divider()

with get_connection() as conn:
    df = pd.read_sql_query("SELECT project_name as 项目名称, tech_stack as 技术栈, status as 状态, repo_url as 描述简介 FROM projects", conn)

if not df.empty:
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("💡 目前项目库为空，请在上方录入你的第一个开发项目。")