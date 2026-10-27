import os
from pathlib import Path
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Text, Float, Date, select, inspect, text
from core.auth import require_access

metadata = MetaData()
FIELDS = {
    'grades': [('course_name', Text), ('credits', Float), ('grade', Text), ('course_type', Text), ('semester', Text), ('course_code', Text)],
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
        grade_columns = {column['name'] for column in inspect(conn).get_columns('grades')}
        for name in ('semester', 'course_code'):
            if name not in grade_columns:
                conn.execute(text(f'ALTER TABLE grades ADD COLUMN {name} TEXT'))
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


def import_grades(records):
    """All-or-nothing import; identical reuploads are harmless, conflicts are explicit."""
    require_access(admin=True)
    from core.academics import validate_grade
    for row in records:
        validate_grade(row)
    table = TABLES['grades']
    inserted = skipped = 0
    with get_engine().begin() as conn:
        if conn.dialect.name == 'postgresql':
            conn.execute(text('LOCK TABLE grades IN SHARE ROW EXCLUSIVE MODE'))
        existing = [dict(row) for row in conn.execute(select(table)).mappings()]
        for row in records:
            matches = [old for old in existing if
                       (old.get('semester') or '') == row.get('semester', '') and
                       ((row.get('course_code') and old.get('course_code') == row['course_code']) or old['course_name'] == row['course_name'])]
            if matches:
                if any(all(str(old.get(key) or '') == str(value or '') for key, value in row.items()) for old in matches):
                    skipped += 1
                    continue
                raise ValueError(f"课程「{row['course_name']}」存在不同记录，请先在编辑区核对")
            conn.execute(table.insert().values(**row))
            existing.append(row.copy())
            inserted += 1
    return inserted, skipped
