from datetime import date
from urllib.parse import urlparse
import io
import zipfile
import pandas as pd
import streamlit as st
from core.auth import login_gate, role, require_access
from core.db_manager import init_database, read_records, save_record, delete_record, FIELDS

# label, input kind/options, required
SCHEMAS = {
 'sys_todos': ('待办清单', '☑️', {'content': ('待办内容', 'text', True), 'status': ('状态', ['待办', '进行中', '已完成'], True)}),
 'grades': ('学业大盘', '🎓', {'course_name': ('课程名称', 'text', True), 'credits': ('学分', 'credits', True), 'grade': ('成绩', 'text', True), 'course_type': ('修读性质', ['必修', '选修', '实践'], True)}),
 'projects': ('工程资产', '💻', {'project_name': ('项目名称', 'text', True), 'tech_stack': ('技术栈', 'text', False), 'status': ('状态', ['需求规划', '开发中', '已部署', '已归档'], True), 'repo_url': ('仓库链接', 'url', False)}),
 'algorithms': ('算法题库', '🧩', {'title': ('题目名称', 'text', True), 'difficulty': ('难度', ['简单', '中等', '困难'], True), 'tags': ('知识点标签', 'text', False), 'status': ('掌握状态', ['未开始', '一刷完成', '需复习', '已掌握'], True), 'review_count': ('复习次数', 'count', False)}),
 'research_tasks': ('科研任务', '🔬', {'task_name': ('任务名称', 'text', True), 'stage': ('当前阶段', ['文献调研', '导师沟通', '模型训练', '论文撰写', '已完成'], True), 'deadline': ('截止日期', 'date', False), 'notes': ('备注', 'area', False)}),
 'career_applications': ('升学规划', '✈️', {'university': ('目标院校', 'text', True), 'program': ('专业项目', 'text', True), 'target_ielts': ('雅思目标', 'ielts', False), 'status': ('申请状态', ['选校调研中', '材料准备', '网申已投递', '等待面试', '已拿 Offer', '已结束'], True), 'deadline': ('截止日期', 'date', False)}),
}


def setup(title, icon):
    st.set_page_config(page_title=f'{title} · AI Workbench', page_icon=icon, layout='wide')
    st.markdown('''<style>
    .block-container {max-width:1240px;padding-top:2.5rem;}
    [data-testid="stMetric"] {border:1px solid #334155;border-radius:14px;padding:18px;}
    [data-testid="stSidebar"] {border-right:1px solid #334155;}
    h1 {letter-spacing:-.035em;font-size:2.4rem;}
    h2 {font-size:1.5rem;}
    .stButton>button,.stDownloadButton>button {border-radius:9px;}
    </style>''', unsafe_allow_html=True)
    login_gate()
    try:
        init_database()
    except Exception:
        st.error('数据库暂时无法连接。请管理员检查数据库服务、连接配置和部署日志。')
        st.stop()
    st.sidebar.title('AI Workbench')
    st.sidebar.caption('LEARN · BUILD · DISCOVER')
    st.sidebar.page_link('app.py', label='工作空间', icon='🌌')
    for path, label, nav_icon in [('1_academics.py', '学业大盘', '🎓'), ('2_projects.py', '工程资产', '💻'), ('3_algorithms.py', '算法题库', '🧩'), ('4_research_hub.py', '科研任务', '🔬'), ('5_career_path.py', '升学规划', '✈️')]:
        st.sidebar.page_link('pages/' + path, label=label, icon=nav_icon)
    if role() == 'admin':
        st.sidebar.page_link('pages/6_llm_sandbox.py', label='模型沙箱', icon='🤖')
    st.sidebar.info('管理员可管理数据与导出备份。' if role() == 'admin' else '浏览模式：可查看、搜索和筛选。')
    st.title(f'{icon} {title}')


def clean(value):
    return None if value is None or pd.isna(value) else value


def validate(name, values):
    for field, (label, kind, required) in SCHEMAS[name][2].items():
        value = values[field]
        if required and (value is None or isinstance(value, str) and not value.strip()):
            raise ValueError(f'请填写{label}')
        if kind == 'url' and value:
            parsed = urlparse(value)
            if parsed.scheme not in ('https', 'http') or not parsed.hostname:
                raise ValueError('仓库链接必须是有效的 HTTP/HTTPS 地址')
    if name == 'grades':
        grade = values['grade'].upper()
        if grade not in ('A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F', '优秀', '良好', '中等', '及格', '不及格', '通过', '不通过'):
            try:
                score = float(grade)
                if not 0 <= score <= 100:
                    raise ValueError()
            except ValueError:
                raise ValueError('成绩请输入 0–100 的分数或有效等级')


def editor(name, frame):
    if role() != 'admin':
        return
    schema = SCHEMAS[name][2]
    with st.expander('添加 / 编辑记录'):
        ids = [None] + frame['id'].tolist()
        primary = next(iter(schema))
        selected = st.selectbox('选择记录', ids, format_func=lambda x: '＋ 新建记录' if x is None else f"#{x} · {frame.loc[frame.id == x, primary].iloc[0]}", key=f'{name}_select')
        row = {} if selected is None else frame.loc[frame.id == selected].iloc[0].to_dict()
        with st.form(f'{name}_edit_{selected}'):
            values = {}
            for field, (label, kind, required) in schema.items():
                value = clean(row.get(field))
                label += ' *' if required else ''
                if isinstance(kind, list):
                    options = kind if value is None or value in kind else [value] + kind
                    values[field] = st.selectbox(label, options, index=options.index(value) if value in options else 0)
                elif kind == 'date':
                    values[field] = st.date_input(label, value=pd.to_datetime(value).date() if value else None)
                elif kind in ('credits', 'ielts', 'count'):
                    if kind == 'count':
                        values[field] = st.number_input(label, min_value=0, max_value=100000, value=int(value or 0), step=1)
                    else:
                        values[field] = st.number_input(label, min_value=0.5 if kind == 'credits' else 0.0, max_value=100.0 if kind == 'credits' else 9.0, value=float(value if value is not None else (1.0 if kind == 'credits' else 6.5)), step=0.5)
                else:
                    widget = st.text_area if kind == 'area' else st.text_input
                    values[field] = widget(label, value=str(value or ''), max_chars=5000 if kind == 'area' else 500).strip()
            if st.form_submit_button('保存记录', type='primary'):
                try:
                    validate(name, values)
                    save_record(name, values, selected)
                except ValueError as exc:
                    st.error(str(exc))
                except Exception:
                    st.error('保存失败，请检查数据格式或稍后重试。')
                else:
                    st.rerun()
        if selected is not None:
            confirmed = st.checkbox('确认永久删除这条记录', key=f'delete_confirm_{name}_{selected}')
            if st.button('删除记录', disabled=not confirmed, key=f'delete_{name}_{selected}'):
                try:
                    delete_record(name, selected)
                except Exception:
                    st.error('删除失败，请稍后重试。')
                else:
                    st.rerun()


def show_records(name, frame):
    schema = SCHEMAS[name][2]
    query = st.text_input('搜索记录', placeholder='输入名称、标签或备注…', key=f'search_{name}')
    filtered = frame
    if query:
        mask = frame.astype(str).apply(lambda col: col.str.contains(query, case=False, regex=False)).any(axis=1)
        filtered = frame[mask]
    for field, (label, kind, _) in schema.items():
        if isinstance(kind, list):
            options = sorted(frame[field].dropna().unique().tolist())
            chosen = st.multiselect(f'筛选{label}', options, key=f'filter_{name}_{field}')
            if chosen:
                filtered = filtered[filtered[field].isin(chosen)]
    st.caption(f'显示 {len(filtered)} / {len(frame)} 条记录')
    if filtered.empty:
        st.info('暂无匹配记录。')
    else:
        display = filtered.rename(columns={field: spec[0] for field, spec in schema.items()}).drop(columns=['id'])
        st.dataframe(display, hide_index=True, use_container_width=True)
        if name == 'projects':
            for _, row in filtered.iterrows():
                url = str(row['repo_url'] or '')
                if urlparse(url).scheme in ('http', 'https') and urlparse(url).hostname:
                    st.link_button(str(row['project_name']), url)
    if role() == 'admin':
        # Neutralize spreadsheet formulas in exported user-controlled cells.
        exported = filtered.map(lambda v: "'" + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@')) else v)
        st.download_button('导出筛选结果 CSV', exported.to_csv(index=False).encode('utf-8-sig'), f'{name}.csv', 'text/csv')


def records_page(name):
    title, icon, _ = SCHEMAS[name]
    setup(title, icon)
    st.caption('把每一次积累，变成可追踪的进步。')
    try:
        frame = read_records(name)
    except Exception:
        st.error('数据暂时无法读取，请稍后重试。')
        st.stop()
    if name == 'grades':
        from core.scu_gpa_engine import process_academic_metrics
        metrics = process_academic_metrics(frame)
        cols = st.columns(3)
        cols[0].metric('课程数', len(frame))
        cols[1].metric('已录入学分', f"{frame.credits.sum():g}")
        cols[2].metric('百分制加权均分', f"{metrics['overall_avg']:.2f}" if metrics else '—')
        st.caption('加权均分仅纳入百分制课程；等级成绩保留展示。')
    else:
        cols = st.columns(3)
        cols[0].metric('记录总数', len(frame))
        if 'status' in frame:
            cols[1].metric('已完成 / 已掌握', int(frame.status.isin(['已完成', '已掌握', '已部署', '已拿 Offer']).sum()))
        if 'deadline' in frame:
            dates = pd.to_datetime(frame.deadline, errors='coerce')
            active = ~frame.get('status', frame.get('stage', pd.Series('', index=frame.index))).isin(['已完成', '已结束', '已拿 Offer'])
            cols[2].metric('逾期未完成', int(((dates.dt.date < date.today()) & active).sum()))
    editor(name, frame)
    show_records(name, frame)


def backup():
    require_access(admin=True)
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in FIELDS:
            archive.writestr(f'{name}.csv', read_records(name).to_csv(index=False).encode('utf-8-sig'))
    return output.getvalue()
