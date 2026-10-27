from datetime import date
import pandas as pd
import pytest
from core.academics import academic_summary, semester_summary, parse_grade_csv


def records():
    return [
        dict(course_name='编程实战', credits=1.0, grade='A-', course_type='必修', semester='2025-2026学年春', course_code='01'),
        dict(course_name='形势与政策-1', credits=0.0, grade='87', course_type='必修', semester='2025-2026学年秋', course_code='02'),
        dict(course_name='数学', credits=2.0, grade='90', course_type='必修', semester='2025-2026学年秋', course_code='03'),
    ]


def test_personal_weighting_policy_preserves_source():
    data = pd.DataFrame(records())
    summary = academic_summary(data)
    assert summary['credits'] == 3.25
    assert summary['source_credits'] == 3
    assert summary['average'] == pytest.approx((85 + 87 * .25 + 90 * 2) / 3.25)
    assert data.grade.iloc[0] == 'A-'
    assert data.credits.iloc[1] == 0
    assert summary['excellent'] == 1


def test_semester_order():
    data = pd.DataFrame(records())
    result = semester_summary(data)
    assert result['学期'].tolist() == ['2025-2026学年秋', '2025-2026学年春']
    assert result['已获学分'].tolist() == [2.25, 1]


def test_csv_preserves_zero_and_letter_grade():
    rows = parse_grade_csv(pd.DataFrame(records()).to_csv(index=False).encode())
    assert rows[0]['grade'] == 'A-'
    assert rows[1]['credits'] == 0
    assert rows[0]['course_code'] == '01'


@pytest.mark.parametrize('content', [b'bad,header\n1,2\n', b'course_name,credits,grade,course_type\nx,2,nan,required\n', b'course_name,credits,grade,course_type\nx,-1,90,required\n'])
def test_bad_csv_rejected(content):
    with pytest.raises(ValueError):
        parse_grade_csv(content)


def test_import_is_idempotent_and_transactional(tmp_path, monkeypatch):
    from core import auth
    from core.db_manager import get_engine, init_database, import_grades, read_records
    monkeypatch.setenv('WORKBENCH_DB_URI', f'sqlite:///{tmp_path / "import.db"}')
    get_engine.clear()
    init_database.clear()
    monkeypatch.setattr(auth, 'role', lambda: 'admin')
    init_database()
    assert import_grades(records()) == (3, 0)
    assert import_grades(records()) == (0, 3)
    conflict = dict(records()[0], grade='90')
    new = dict(records()[2], course_name='另一门课', course_code='04')
    with pytest.raises(ValueError):
        import_grades([new, conflict])
    assert len(read_records('grades')) == 3
    monkeypatch.setattr(auth, 'role', lambda: 'viewer')
    with pytest.raises(PermissionError):
        import_grades(records())
    get_engine().dispose()
    get_engine.clear()
    init_database.clear()


def test_migration_preserves_existing_grades(tmp_path, monkeypatch):
    from core.db_manager import get_engine, init_database
    monkeypatch.setenv('WORKBENCH_DB_URI', f'sqlite:///{tmp_path / "legacy.db"}')
    get_engine.clear()
    init_database.clear()
    with get_engine().begin() as conn:
        conn.exec_driver_sql('CREATE TABLE grades (id INTEGER PRIMARY KEY, course_name TEXT, credits REAL, grade TEXT, course_type TEXT)')
        conn.exec_driver_sql("INSERT INTO grades VALUES (1,'legacy',2,'90','必修')")
    init_database()
    with get_engine().connect() as conn:
        result = conn.exec_driver_sql('SELECT course_name, grade, semester FROM grades').one()
        assert result == ('legacy', '90', None)
    get_engine().dispose()
    get_engine.clear()
    init_database.clear()
