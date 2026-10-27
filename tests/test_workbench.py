import os
from pathlib import Path
import time
import pytest
import pandas as pd
from streamlit.testing.v1 import AppTest
from core.auth import hash_password, verify_password

ROOT = Path(__file__).resolve().parents[1]
HASH = hash_password('test-password-only')
USERS = {'admin': {'role': 'admin', 'password_hash': HASH}, 'viewer': {'role': 'viewer', 'password_hash': HASH}}


@pytest.fixture(autouse=True)
def database(tmp_path, monkeypatch):
    monkeypatch.setenv('WORKBENCH_DB_URI', f'sqlite:///{tmp_path / "test.db"}')
    from core.db_manager import get_engine, init_database
    get_engine.clear()
    init_database.clear()
    yield
    get_engine().dispose()
    get_engine.clear()
    init_database.clear()


def app(file='app.py', user=None):
    at = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=20)
    at.secrets['auth'] = {'users': USERS}
    if user:
        at.session_state['_identity'] = {'username': user, 'issued': time.time(), 'version': HASH}
    at.run()
    if file != 'app.py':
        at.switch_page(file).run()
    assert not at.exception
    return at


def test_password():
    assert verify_password('test-password-only', HASH)
    assert not verify_password('wrong', HASH)
    assert not verify_password('x', 'broken')
    assert hash_password('same') != hash_password('same')


@pytest.mark.parametrize('file', ['app.py'] + [f'pages/{p.name}' for p in (ROOT / 'pages').glob('*.py')])
def test_direct_page_requires_login(file):
    at = app(file)
    assert [x.label for x in at.text_input] == ['账号', '密码']
    assert not at.dataframe


@pytest.mark.parametrize('user', ['admin', 'viewer'])
@pytest.mark.parametrize('file', ['app.py'] + [f'pages/{p.name}' for p in (ROOT / 'pages').glob('*.py')])
def test_authenticated_pages(file, user):
    at = app(file, user)
    labels = [b.label for b in at.button]
    if user == 'viewer':
        assert '保存记录' not in labels
        assert '删除记录' not in labels
        assert '🚀 发送 API 请求' not in labels
        assert '导出筛选结果 CSV' not in [b.label for b in at.get('download_button')]


def test_login_and_logout():
    at = app()
    at.text_input[0].set_value('viewer')
    at.text_input[1].set_value('test-password-only')
    at.button[0].click().run()
    assert not at.exception
    assert at.title[0].value == '🌌 工作空间'
    at.sidebar.button[0].click().run()
    assert [x.label for x in at.text_input] == ['账号', '密码']


def test_wrong_password():
    at = app()
    at.text_input[0].set_value('admin')
    at.text_input[1].set_value('wrong')
    at.button[0].click().run()
    assert at.error[0].value == '账号或密码错误。'
    assert not at.dataframe


def test_admin_crud_and_viewer_denial(monkeypatch):
    from core import auth
    from core.db_manager import init_database, save_record, read_records, delete_record
    init_database()
    monkeypatch.setattr(auth, 'role', lambda: 'admin')
    save_record('sys_todos', {'content': "SQL ' quotation", 'status': '待办'})
    record = int(read_records('sys_todos').iloc[0].id)
    save_record('sys_todos', {'status': '已完成'}, record)
    assert read_records('sys_todos').iloc[0].status == '已完成'
    monkeypatch.setattr(auth, 'role', lambda: 'viewer')
    with pytest.raises(PermissionError):
        save_record('sys_todos', {'content': 'forbidden'})
    with pytest.raises(PermissionError):
        delete_record('sys_todos', record)
    assert len(read_records('sys_todos')) == 1
    monkeypatch.setattr(auth, 'role', lambda: None)
    with pytest.raises(PermissionError):
        read_records('sys_todos')
    monkeypatch.setattr(auth, 'role', lambda: 'admin')
    delete_record('sys_todos', record)
    assert read_records('sys_todos').empty


def test_ui_create_todo():
    at = app(user='admin')
    next(x for x in at.text_input if x.label == '待办内容 *').set_value('测试待办')
    next(x for x in at.button if x.label == '保存记录').click().run()
    assert not at.exception
    assert '测试待办' in at.dataframe[0].value.to_string()


def test_grade_metrics_handle_letters():
    from core.scu_gpa_engine import process_academic_metrics
    data = pd.DataFrame({'grade': ['A', '90', '80'], 'credits': [3, 2, 2], 'course_type': ['必修'] * 3})
    result = process_academic_metrics(data)
    assert result['overall_avg'] == 85
    assert data.grade.iloc[0] == 'A'


def test_legacy_todo_migration():
    from core.db_manager import get_engine, init_database
    with get_engine().begin() as conn:
        conn.exec_driver_sql('CREATE TABLE sys_todos (id INTEGER PRIMARY KEY, content TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
        conn.exec_driver_sql("INSERT INTO sys_todos (content) VALUES ('existing')")
    init_database()
    init_database.clear()
    init_database()
    with get_engine().connect() as conn:
        row = conn.exec_driver_sql('SELECT content, status FROM sys_todos').one()
        assert row == ('existing', '待办')


def test_validation():
    from core.ui import validate
    with pytest.raises(ValueError):
        validate('projects', dict(project_name='x', tech_stack='', status='开发中', repo_url='javascript:alert(1)'))
    with pytest.raises(ValueError):
        validate('grades', dict(course_name='x', credits=1, grade='101', course_type='必修'))


@pytest.mark.parametrize('name,values', [
    ('grades', dict(course_name='数学', credits=2.0, grade='A', course_type='必修')),
    ('projects', dict(project_name='测试工程', tech_stack='Python', status='开发中', repo_url='https://github.com/re7-dev/AI-Workbench')),
    ('algorithms', dict(title='两数之和', difficulty='简单', tags='哈希', status='需复习', review_count=2)),
    ('research_tasks', dict(task_name='论文阅读', stage='文献调研', deadline=__import__('datetime').date(2026, 10, 1), notes='笔记')),
    ('career_applications', dict(university='测试学校', program='AI', target_ielts=6.5, status='材料准备', deadline=__import__('datetime').date(2026, 11, 1))),
])
def test_populated_pages(name, values, monkeypatch):
    from core import auth
    from core.db_manager import init_database, save_record
    init_database()
    with monkeypatch.context() as context:
        context.setattr(auth, 'role', lambda: 'admin')
        save_record(name, values)
    files = dict(grades='1_academics.py', projects='2_projects.py', algorithms='3_algorithms.py', research_tasks='4_research_hub.py', career_applications='5_career_path.py')
    at = app('pages/' + files[name], 'admin')
    assert len(at.dataframe[0].value) == 1
    at = app('app.py', 'viewer')
    assert not at.exception


def test_expired_session():
    at = AppTest.from_file(str(ROOT / 'app.py'))
    at.secrets['auth'] = {'users': USERS}
    at.session_state['_identity'] = dict(username='admin', issued=time.time() - 9 * 3600, version=HASH)
    at.run()
    assert not at.exception
    assert at.text_input[0].label == '账号'


def test_changed_password_invalidates_session():
    at = AppTest.from_file(str(ROOT / 'app.py'))
    at.secrets['auth'] = {'users': USERS}
    at.session_state['_identity'] = dict(username='admin', issued=time.time(), version='old-hash')
    at.run()
    assert at.text_input[0].label == '账号'


def test_model_denies_viewer(monkeypatch):
    from core import auth
    from core.llm_client import call_llm_api
    monkeypatch.setattr(auth, 'role', lambda: 'viewer')
    with pytest.raises(PermissionError):
        call_llm_api('https://example.com', 'secret', 'model', 'prompt')


def test_model_denies_private_network(monkeypatch):
    import socket
    from core.llm_client import validate_api_url
    monkeypatch.setattr(socket, 'getaddrinfo', lambda *a, **kw: [(2, 1, 6, '', ('127.0.0.1', 443))])
    with pytest.raises(ValueError):
        validate_api_url('https://example.com/v1')
    with pytest.raises(ValueError):
        validate_api_url('http://example.com/v1')
