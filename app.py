import streamlit as st
from core.ui import setup, editor, show_records, backup
from core.auth import role
from core.db_manager import read_records
from core.dashboard import academic_dashboard, activity_dashboard, hero, section, today

setup('工作空间', '🌌')
hero('把热爱，积累成未来的底气', '在一个工作空间里，连接你的学业、工程实践与研究计划。每一步进展，都值得被看见。', [today().strftime('%Y / %m / %d'), 'LEARN · BUILD · DISCOVER'])
try:
    grades = read_records('grades')
    todos = read_records('sys_todos')
    projects = read_records('projects')
    algorithms = read_records('algorithms')
    research = read_records('research_tasks')
    applications = read_records('career_applications')
except Exception:
    st.error('数据暂时无法读取，请稍后重试。')
    st.stop()

section('ACADEMIC PERFORMANCE', '学业仪表盘')
academic_dashboard(grades)
activity_dashboard(todos, projects, algorithms, research, applications)
st.write('')
left, right = st.columns([1.45, 1])
with left, st.container(border=True):
    section('FOCUS & FOLLOW THROUGH', '今日聚焦')
    editor('sys_todos', todos)
    show_records('sys_todos', todos)
with right, st.container(border=True):
    section('EXPLORE YOUR SPACE', '开启下一段探索')
    st.page_link('pages/1_academics.py', label='学业大盘', icon='🎓')
    st.caption('课程明细 · 学期对比 · 成绩分析')
    st.page_link('pages/2_projects.py', label='工程资产', icon='💻')
    st.caption('项目积累 · 技术实践 · 作品归档')
    st.page_link('pages/4_research_hub.py', label='科研任务', icon='🔬')
    st.caption('文献阅读 · 实验记录 · 研究进度')
if role() == 'admin':
    with st.expander('数据备份'):
        st.caption('备份包含各模块原始 CSV 数据，请妥善保存。')
        if st.button('生成全量备份'):
            st.download_button('下载备份 ZIP', backup(), f'workbench-{today()}.zip', 'application/zip')
