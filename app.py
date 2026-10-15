import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db_manager import init_database, get_connection

# ==========================================
# 1. 全局页面配置 (必须在最前面)
# ==========================================
st.set_page_config(
    page_title="AI & Research Workbench",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化云端数据库表结构 (如果表不存在则自动创建)
try:
    init_database()
except Exception as e:
    st.sidebar.error(f"数据库初始化失败: {e}")

# ==========================================
# 2. 页面顶栏
# ==========================================
st.title("🌌 个人专属 AI 职业生涯工作台")
st.divider()

# ==========================================
# 3. 页面主体布局：左侧待办区，右侧名片区
# ==========================================
col1, col2 = st.columns([2, 1]) # 左侧内容更宽，比例为 2:1

with col1:
    st.subheader("🎯 最近动态与待办")
    
    # 交互式待办录入表单
    with st.container(border=True):
        with st.form("add_todo_form", clear_on_submit=True):
            st.write("添加新动态/待办事项：")
            new_todo = st.text_input("待办内容", label_visibility="collapsed", placeholder="例如：推进多模态 AI 大创开题...")
            submitted = st.form_submit_button("添加")
            
            if submitted and new_todo:
                try:
                    conn = get_connection()
                    # 【核心修复点】：使用 text() 和字典传参，彻底解决 ArgumentError
                    query = text("INSERT INTO sys_todos (content) VALUES (:c)")
                    conn.execute(query, {"c": new_todo})
                    conn.commit()
                    st.success("添加成功！")
                    st.rerun()
                except Exception as e:
                    st.error(f"保存失败: {e}")
    
    # 动态展示云端待办列表
    st.write("### 待办清单")
    try:
        conn = get_connection()
        # 按 ID 倒序排列，让最新的待办显示在最上面
        df_todos = pd.read_sql_query("SELECT * FROM sys_todos ORDER BY id DESC", conn)
        
        if not df_todos.empty:
            for index, row in df_todos.iterrows():
                # 使用 info 框让每一条待办看起来像一张小卡片
                st.info(f"📌 {row['content']}")
        else:
            st.caption("太棒了，当前暂无待办事项！")
    except Exception as e:
        st.error("无法加载待办事项，请检查数据库连接。")

with col2:
    # 专属开发者名片
    with st.container(border=True):
        st.markdown("### 👤 开发者名片")
        st.markdown("""
        * **姓名**：薛紫元
        * **学籍**：四川大学 人工智能学院
        * **专业**：人工智能
        * **学号**：2025141460548
        """)