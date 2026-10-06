import streamlit as st
import pandas as pd
from core.db_manager import get_connection

st.set_page_config(page_title="Research Hub", page_icon="🔬")
st.title("🔬 科研大创与课题追踪")
st.markdown("用于管理实验室项目、大创里程碑与文献调研进度。")

with st.expander("➕ 新增科研任务/里程碑", expanded=False):
    with st.form("research_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        t_name = c1.text_input("任务名称", placeholder="例如：多模态 AI 组会开题 PPT 准备")
        t_stage = c2.selectbox("当前阶段", ["文献调研", "开题准备", "模型训练/开发", "论文撰写", "已结题"])
        
        c3, c4 = st.columns(2)
        t_dead = c3.date_input("截止日期 (Deadline)")
        t_notes = c4.text_input("备注信息", placeholder="例如：重点参考 CVPR 的最新论文...")
        
        if st.form_submit_button("保存任务"):
            if t_name:
                with get_connection() as conn:
                    conn.execute("INSERT INTO research_tasks (task_name, stage, deadline, notes) VALUES (?, ?, ?, ?)", 
                                 (t_name, t_stage, t_dead, t_notes))
                    conn.commit()
                st.success("科研任务已成功保存！")
                st.rerun()

st.divider()

with get_connection() as conn:
    df = pd.read_sql_query("SELECT id, task_name as 任务名称, stage as 阶段, deadline as 截止日期, notes as 备注 FROM research_tasks", conn)

if not df.empty:
    st.subheader("📋 任务看板")
    # 隐藏底层的 ID 列，使界面更清爽
    st.dataframe(df.drop(columns=['id']), use_container_width=True)
else:
    st.info("💡 尚未录入科研任务，试着添加你的第一个大创里程碑吧。")