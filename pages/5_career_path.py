import streamlit as st
import pandas as pd
from core.db_manager import get_connection
from datetime import date

st.set_page_config(page_title="Career Path", page_icon="✈️")
st.title("✈️ 境外升学与网申规划")
st.markdown("高效追踪各院校网申 Deadline 与材料准备进度。")

with st.expander("➕ 添加目标院校", expanded=False):
    with st.form("uni_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        uni = col1.text_input("目标院校", placeholder="如：NUS, NTU, IC, UCL")
        prog = col2.text_input("专业项目", placeholder="如：MSc in AI / CS")
        
        col3, col4, col5 = st.columns([1, 1, 1])
        ielts = col3.number_input("雅思/托福目标", min_value=0.0, step=0.5, value=6.5)
        status = col4.selectbox("当前进度", ["选校调研中", "准备材料 (CV/PS)", "网申已提交", "等待 Offer", "已录取"])
        ddl = col5.date_input("网申截止日期")
        
        if st.form_submit_button("加入院校库"):
            if uni and prog:
                with get_connection() as conn:
                    conn.execute("INSERT INTO career_applications (university, program, target_ielts, status, deadline) VALUES (?, ?, ?, ?, ?)",
                                 (uni, prog, ielts, status, ddl))
                    conn.commit()
                st.success(f"《{uni}》添加成功！")
                st.rerun()

st.divider()

with get_connection() as conn:
    df = pd.read_sql_query("SELECT id, university as 目标院校, program as 申请项目, target_ielts as 语言要求, status as 当前状态, deadline as 截止日期 FROM career_applications", conn)

if not df.empty:
    st.subheader("🏫 网申 Deadline 追踪")
    
    # 实用功能：自动计算距离 Deadline 还有多少天
    today = date.today()
    
    for _, row in df.iterrows():
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            c1.markdown(f"**{row['目标院校']}** | {row['申请项目']}")
            
            # 计算倒计时状态
            try:
                ddl_date = pd.to_datetime(row['截止日期']).date()
                days_left = (ddl_date - today).days
                if days_left < 0:
                    countdown_text = "🚨 已截止"
                elif days_left <= 30:
                    countdown_text = f"🔥 仅剩 {days_left} 天"
                else:
                    countdown_text = f"⏳ 还有 {days_left} 天"
            except:
                countdown_text = "未知"

            c2.markdown(f"📅 Deadline: {row['截止日期']} ({countdown_text})")
            c3.markdown(f"📌 进度: {row['当前状态']}")
            
            # 删除按钮
            if c4.button("🗑️", key=f"del_uni_{row['id']}"):
                with get_connection() as conn:
                    conn.execute("DELETE FROM career_applications WHERE id=?", (row['id'],))
                    conn.commit()
                st.rerun()
else:
    st.info("尚未添加目标院校，开始建立你的升学档案吧！")