from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from html import escape
import altair as alt
import pandas as pd
import streamlit as st
from core.academics import academic_summary, semester_summary

TEAL = '#22aaa0'
PURPLE = '#8270d8'
PALETTE = ['#22aaa0', '#8270d8', '#f4ac74', '#e46e84', '#c9d1df']
POLICY_NOTE = '统计口径：A- 按 85 分；形势与政策每门按 0.25 学分。原始记录保持不变，均分按统计学分加权。'


def today():
    return datetime.now(ZoneInfo('Asia/Shanghai')).date()


def hero(heading, subtitle, chips=()):
    tags = ''.join(f'<span class="wb-chip">{escape(str(chip))}</span>' for chip in chips)
    st.markdown(f'<div class="wb-hero"><p class="eyebrow">YOUR PERSONAL GROWTH SPACE</p><h2>{escape(heading)}</h2><p>{escape(subtitle)}</p>{tags}</div>', unsafe_allow_html=True)


def section(kicker, title):
    st.markdown(f'<div class="wb-overline">{escape(kicker)}</div>', unsafe_allow_html=True)
    st.subheader(title)


def chart_style(chart):
    return chart.configure_view(stroke=None).configure_axis(gridColor='#edf0f5', domain=False, tickSize=0, labelColor='#7b899c', titleColor='#7b899c', labelFontSize=11, titleFontSize=11).configure_legend(labelColor='#728197', title=None).properties(background='transparent')


def academic_dashboard(frame, detailed=False):
    summary = academic_summary(frame)
    columns = st.columns(4)
    columns[0].metric('已录入课程', f"{summary['courses']} 门")
    columns[1].metric('累计统计学分', f"{summary['credits']:g}", help=f"原始学分 {summary['source_credits']:g}；形策每门按 0.25 学分统计")
    columns[2].metric('加权均分', f"{summary['average']:.2f}" if summary['average'] is not None else '—')
    columns[3].metric('90 分及以上', f"{summary['excellent']} 门")
    st.caption(POLICY_NOTE)
    st.write('')
    left, right = st.columns([1.45, 1])
    with left, st.container(border=True):
        section('SEMESTER OVERVIEW', '每一学期，都有积累')
        semesters = semester_summary(frame)
        if semesters.empty:
            st.markdown('<div class="wb-empty">录入成绩后，在这里查看学期趋势</div>', unsafe_allow_html=True)
        else:
            st.caption('柱形为统计学分，折线为加权均分；当前学期可能尚未录入完整。')
            order = semesters['学期'].tolist()
            base = alt.Chart(semesters).encode(x=alt.X('学期:N', sort=order, axis=alt.Axis(labelAngle=0), title=None), tooltip=['学期:N', '课程数:Q', alt.Tooltip('已获学分:Q', format='.2f'), alt.Tooltip('加权均分:Q', format='.2f')])
            bars = base.mark_bar(color=TEAL, opacity=.65, size=48, cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(y=alt.Y('已获学分:Q', title='统计学分', scale=alt.Scale(domainMin=0)))
            line = base.mark_line(color=PURPLE, strokeWidth=3, point=alt.OverlayMarkDef(size=85, filled=True, color=PURPLE)).encode(y=alt.Y('加权均分:Q', title='加权均分', scale=alt.Scale(domain=[0, 100])))
            st.altair_chart(chart_style(alt.layer(bars, line).resolve_scale(y='independent').properties(height=235)), use_container_width=True)
    with right, st.container(border=True):
        section('GRADE DISTRIBUTION', '成绩分布')
        numeric = summary['numeric']
        if numeric.empty:
            st.markdown('<div class="wb-empty">还没有可统计的成绩</div>', unsafe_allow_html=True)
        else:
            bands = pd.cut(numeric.score, bins=[-1, 59.999, 69.999, 79.999, 89.999, 100], labels=['60 以下', '60–69', '70–79', '80–89', '90–100'])
            counts = bands.value_counts(sort=False).rename_axis('成绩区间').reset_index(name='课程数')
            order = ['90–100', '80–89', '70–79', '60–69', '60 以下']
            donut = alt.Chart(counts).mark_arc(innerRadius=62, outerRadius=94, cornerRadius=4, padAngle=.04).encode(theta='课程数:Q', color=alt.Color('成绩区间:N', scale=alt.Scale(domain=order, range=PALETTE), legend=alt.Legend(orient='right')), tooltip=['成绩区间:N', '课程数:Q'])
            label = alt.Chart(pd.DataFrame({'label': [f"{summary['excellent']}/{len(numeric)}"], 'subtitle': ['90 分及以上']})).mark_text(fontSize=25, fontWeight=700, color='#233950', dy=-6).encode(text='label:N')
            sub = alt.Chart(pd.DataFrame({'label': ['90 分及以上']})).mark_text(fontSize=10, color='#7b899c', dy=20).encode(text='label:N')
            st.altair_chart(chart_style(alt.layer(donut, label, sub).properties(height=235)), use_container_width=True)
    if detailed and not summary['numeric'].empty:
        with st.container(border=True):
            section('COURSE PERFORMANCE', '课程成绩对比')
            data = summary['numeric'].sort_values('score', ascending=False)
            chart = alt.Chart(data).mark_bar(cornerRadiusEnd=4, height=14).encode(x=alt.X('score:Q', title='统计分数', scale=alt.Scale(domain=[0, 100])), y=alt.Y('course_name:N', sort='-x', title=None, axis=alt.Axis(labelLimit=240)), color=alt.Color('course_type:N', scale=alt.Scale(range=PALETTE), title='课程性质'), tooltip=[alt.Tooltip('course_name:N', title='课程'), alt.Tooltip('grade:N', title='原始成绩'), alt.Tooltip('score:Q', title='统计分数'), alt.Tooltip('credits:Q', title='统计学分')]).properties(height=max(200, len(data) * 29))
            st.altair_chart(chart_style(chart), use_container_width=True)


def activity_dashboard(todos, projects, algorithms, research, applications):
    section('BEYOND THE CLASSROOM', '成长，不止于课堂')
    cols = st.columns(4)
    metrics = [('待完成事项', int((todos.status.fillna('待办') != '已完成').sum())), ('工程项目', len(projects)), ('已掌握算法', int((algorithms.status == '已掌握').sum())), ('科研任务', len(research))]
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)
    st.write('')
    left, right = st.columns([1.45, 1])
    with left, st.container(border=True):
        section('PROJECT & LEARNING', '实践进度')
        for title, frame, completed in [('工程交付', projects, ['已部署', '已归档']), ('算法掌握', algorithms, ['已掌握']), ('科研推进', research, ['已完成'])]:
            field = 'stage' if 'stage' in frame else 'status'
            done = int(frame[field].isin(completed).sum())
            st.progress(done / len(frame) if len(frame) else 0, text=f'{title}　{done} / {len(frame)}')
        st.caption('进度按各模块标记为完成的记录统计。')
    with right, st.container(border=True):
        section('COMING UP NEXT', '近期截止')
        upcoming = []
        for frame, label, field in [(research, '科研', 'task_name'), (applications, '升学', 'university')]:
            for _, row in frame.iterrows():
                if row.get('status', row.get('stage')) in ('已完成', '已结束', '已拿 Offer'):
                    continue
                deadline = pd.to_datetime(row['deadline'], errors='coerce')
                if pd.notna(deadline) and deadline.date() <= today() + timedelta(days=14):
                    upcoming.append((deadline.date(), label, str(row[field])))
        for deadline, label, title in sorted(upcoming)[:6]:
            days = (deadline - today()).days
            timing = f'已逾期 {-days} 天' if days < 0 else f'{days} 天后截止'
            st.markdown(f'<div class="wb-task"><span class="wb-tag {"wb-alert" if days < 0 else ""}">{escape(label)}</span> <strong>{escape(title)}</strong><small>{deadline} · {timing}</small></div>', unsafe_allow_html=True)
        if not upcoming:
            st.markdown('<div class="wb-empty">日程从容，专注当下。<br>未来两周暂无截止事项</div>', unsafe_allow_html=True)
