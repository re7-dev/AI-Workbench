import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db_manager import get_connection

st.set_page_config(page_title="工程资产", page_icon="💻", layout="wide")

st.title("💻 动态工程与研发资产库")
st.divider()

# ==========================================
# 交互式项目录入表单
# ==========================================
with st.expander("➕ 录入新项目", expanded=False):
    with st.form("add_project_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            project_name = st.text_input("项目名称", placeholder="例如：AI 职业生涯工作台")
            tech_stack = st.text_input("技术栈", placeholder="例如：Python, Streamlit, PostgreSQL")
        with col2:
            status = st.selectbox("当前状态", ["需求规划", "开发中", "已部署", "已归档"])
            repo_url = st.text_input("代码仓库链接", placeholder="例如：https://github.com/...")
        
        submitted = st.form_submit_button("保存项目")
        
        if submitted and project_name:
            try:
                conn = get_connection()
                query = text("INSERT INTO projects (project_name, tech_stack, status, repo_url) VALUES (:n, :t, :s, :r)")
                conn.execute(query, {"n": project_name, "t": tech_stack, "s": status, "r": repo_url})
                conn.commit()
                st.success("项目录入成功！")
                st.rerun()
            except Exception as e:
                st.error(f"保存失败: {e}")

# ==========================================
# 双视图动态渲染区
# ==========================================
st.subheader("📂 云端项目大盘")
try:
    conn = get_connection()
    df_projects = pd.read_sql_query("SELECT * FROM projects", conn)
    
    if not df_projects.empty:
        # 提供表格和卡片两种专业级查看模式
        tab1, tab2 = st.tabs(["🗂️ 卡片视图", "📊 数据表格视图"])
        
        with tab1:
            cols = st.columns(3) # 一排展示三个项目卡片
            for index, row in df_projects.iterrows():
                with cols[index % 3]:
                    with st.container(border=True):
                        st.subheader(row['project_name'])
                        st.caption(f"技术栈: {row['tech_stack']}")
                        st.write(f"状态: **{row['status']}**")
                        if row['repo_url']:
                            st.link_button("查看仓库", row['repo_url'])
        
        with tab2:
            st.dataframe(
                df_projects,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": None,
                    "project_name": st.column_config.TextColumn("项目名称", width="medium"),
                    "tech_stack": st.column_config.TextColumn("技术栈", width="medium"),
                    "status": st.column_config.TextColumn("状态"),
                    "repo_url": st.column_config.LinkColumn("代码仓库")
                }
            )
    else:
        st.info("目前没有在动态数据库中录入项目，请在上方添加你的第一个工程。")
except Exception as e:
    st.error("数据库读取失败，请检查连接。")