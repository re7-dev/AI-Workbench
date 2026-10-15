import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
import pandas as pd

# 从云端保险箱 (Secrets) 安全读取数据库钥匙
DB_URI = st.secrets["DB_URI"]

# 【核心修复 1】使用缓存装饰器，保证整个应用生命周期内只有一个底层引擎，避免重复创建
@st.cache_resource
def get_engine():
    # 【核心修复 2】引入 NullPool 禁用连接池。
    # 这样每次查询完，Python 垃圾回收时会自动释放真实连接，彻底杜绝 QueuePool 溢出！
    return create_engine(DB_URI, poolclass=NullPool)

engine = get_engine()

def get_connection():
    """返回云端连接对象，用完自动销毁不占资源"""
    return engine.connect()

def init_database():
    """初始化云端 PostgreSQL 数据库的标准表结构"""
    with engine.begin() as conn:
        conn.exec_driver_sql('''
            CREATE TABLE IF NOT EXISTS grades (
                id SERIAL PRIMARY KEY,
                course_name TEXT NOT NULL,
                credits REAL NOT NULL,
                grade TEXT NOT NULL,
                course_type TEXT NOT NULL
            )
        ''')
        
        conn.exec_driver_sql('''
            CREATE TABLE IF NOT EXISTS algorithms (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                difficulty TEXT,
                tags TEXT,
                status TEXT,
                review_count INTEGER DEFAULT 0
            )
        ''')
        
        conn.exec_driver_sql('''
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                project_name TEXT NOT NULL,
                tech_stack TEXT,
                status TEXT,
                repo_url TEXT
            )
        ''')
        
        conn.exec_driver_sql('''
            CREATE TABLE IF NOT EXISTS research_tasks (
                id SERIAL PRIMARY KEY,
                task_name TEXT NOT NULL,
                stage TEXT NOT NULL,
                deadline DATE,
                notes TEXT
            )
        ''')
        
        conn.exec_driver_sql('''
            CREATE TABLE IF NOT EXISTS career_applications (
                id SERIAL PRIMARY KEY,
                university TEXT NOT NULL,
                program TEXT NOT NULL,
                target_ielts REAL,
                status TEXT,
                deadline DATE
            )
        ''')
        
        conn.exec_driver_sql('''
            CREATE TABLE IF NOT EXISTS sys_todos (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')