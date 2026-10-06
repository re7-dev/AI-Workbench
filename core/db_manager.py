import sqlite3
import os

# 将数据库文件生成在项目根目录
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'workbench.db')

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_database():
    """初始化系统所需的全部专业数据表"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. 学业档案表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_name TEXT NOT NULL,
                credits REAL NOT NULL,
                grade TEXT NOT NULL,
                course_type TEXT NOT NULL
            )
        ''')
        
        # 2. 算法题库表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS algorithms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                difficulty TEXT,
                tags TEXT,
                status TEXT,
                review_count INTEGER DEFAULT 0
            )
        ''')
        
        # 3. 工程资产表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                tech_stack TEXT,
                status TEXT,
                repo_url TEXT
            )
        ''')
        
        # 4. 科研大创看板表 (追踪多模态 AI 等课题)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                stage TEXT NOT NULL,
                deadline DATE,
                notes TEXT
            )
        ''')
        
        # 5. 升学网申时间轴表 (追踪港新欧澳院校申请)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS career_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                university TEXT NOT NULL,
                program TEXT NOT NULL,
                target_ielts REAL,
                status TEXT,
                deadline DATE
            )
        ''')
        
        # 6. 系统动态待办表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sys_todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()