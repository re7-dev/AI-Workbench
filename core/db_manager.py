import os
from pathlib import Path
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Text, Float, Date, select, inspect, text
from core.auth import require_access

metadata = MetaData()
FIELDS = {
    'grades': [('course_name', Text), ('credits', Float), ('grade', Text), ('course_type', Text)],
    'projects': [('project_name', Text), ('tech_stack', Text), ('status', Text), ('repo_url', Text)],
    'algorithms': [('title', Text), ('difficulty', Text), ('tags', Text), ('status', Text), ('review_count', Integer)],
    'research_tasks': [('task_name', Text), ('stage', Text), ('deadline', Date), ('notes', Text)],
    'career_applications': [('university', Text), ('program', Text), ('target_ielts', Float), ('status', Text), ('deadline', Date)],
    'sys_todos': [('content', Text), ('status', Text)],
}
TABLES = {name: Table(name, metadata, Column('id', Integer, primary_key=True), *[Column(key, kind) for key, kind in fields]) for name, fields in FIELDS.items()}


@st.cache_resource
def get_engine():
    uri = os.environ.get('WORKBENCH_DB_URI')
    if not uri:
        try:
            uri = st.secrets.get('DB_URI')
        except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
            pass
    if not uri:
        uri = 'sqlite:///' + str(Path(__file__).resolve().parents[1] / 'workbench.db')
    if uri.startswith('postgres://'):
        uri = uri.replace('postgres://', 'postgresql://', 1)
    return create_engine(uri, pool_pre_ping=True, connect_args={'connect_timeout': 10} if uri.startswith('postgresql') else {})


@st.cache_resource
def init_database():
    engine = get_engine()
    metadata.create_all(engine)
    with engine.begin() as conn:
        columns = {column['name'] for column in inspect(conn).get_columns('sys_todos')}
        if 'status' not in columns:
            conn.execute(text("ALTER TABLE sys_todos ADD COLUMN status TEXT DEFAULT '待办'"))
    return True


def read_records(name):
    require_access()
    with get_engine().connect() as conn:
        return pd.read_sql(select(TABLES[name]).order_by(TABLES[name].c.id.desc()), conn)


def save_record(name, values, record_id=None):
    require_access(admin=True)
    table = TABLES[name]
    if not values or not set(values) <= set(table.c.keys()) - {'id'}:
        raise ValueError('无效字段')
    with get_engine().begin() as conn:
        if record_id is None:
            conn.execute(table.insert().values(**values))
        else:
            conn.execute(table.update().where(table.c.id == int(record_id)).values(**values))


def delete_record(name, record_id):
    require_access(admin=True)
    table = TABLES[name]
    with get_engine().begin() as conn:
        conn.execute(table.delete().where(table.c.id == int(record_id)))
