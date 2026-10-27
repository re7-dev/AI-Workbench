from datetime import date, timedelta
import pandas as pd
import streamlit as st
from core.ui import setup, editor, show_records, backup
from core.auth import role
from core.db_manager import read_records

setup('工作空间', '🌌')
st.caption('把学习计划、工程实践和研究进展，汇聚在一起。')
try:
    todos = read_records('sys_todos')
    projects = read_records('projects')
    algorithms = read_records('algorithms')
    research = read_records('research_tasks')
    applications = read_records('career_applications')
except Exception:
    st.error('数据暂时无法读取，请稍后重试。')
    st.stop()
cols = st.columns(4)
cols[0].metric('待完成事项', int((todos.status.fillna('待办') != '已完成').sum()))
cols[1].metric('工程项目', len(projects))
cols[2].metric('已掌握算法', int((algorithms.status == '已掌握').sum()))
cols[3].metric('科研任务', len(research))
st.write('')
left, right = st.columns([2, 1])
with left:
    st.subheader('今日聚焦')
    editor('sys_todos', todos)
    show_records('sys_todos', todos)
with right:
    with st.container(border=True):
        st.subheader('近期截止')
        upcoming = []
        for frame, label, field in [(research, '科研', 'task_name'), (applications, '升学', 'university')]:
            for _, row in frame.iterrows():
                if row.get('status', row.get('stage')) in ('已完成', '已结束', '已拿 Offer'):
                    continue
                deadline = pd.to_datetime(row['deadline'], errors='coerce')
                if pd.notna(deadline) and deadline.date() <= date.today() + timedelta(days=14):
                    upcoming.append((deadline.date(), label, row[field]))
        for deadline, label, title in sorted(upcoming):
            days = (deadline - date.today()).days
            st.write(f'{title}')
            st.caption(f"{label} · {deadline} · {'已逾期 ' + str(-days) + ' 天' if days < 0 else str(days) + ' 天后截止'}")
        if not upcoming:
            st.caption('未来两周暂无截止事项。')
    with st.container(border=True):
        st.subheader('快速前往')
        st.page_link('pages/1_academics.py', label='学业大盘', icon='🎓')
        st.page_link('pages/2_projects.py', label='工程资产', icon='💻')
        st.page_link('pages/4_research_hub.py', label='科研任务', icon='🔬')
if role() == 'admin':
    with st.expander('数据备份'):
        st.caption('备份包含各模块原始 CSV 数据，请妥善保存。')
        if st.button('生成全量备份'):
            st.download_button('下载备份 ZIP', backup(), f'workbench-{date.today()}.zip', 'application/zip')
