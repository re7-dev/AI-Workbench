"""Academic statistics preserve original grades and exclude unweighted courses."""
import io
import math
import pandas as pd

GRADE_LEVELS = {'A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'F', '优秀', '良好', '中等', '及格', '不及格', '通过', '不通过'}
LETTER_POINTS = {'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0, 'B-': 2.7, 'C+': 2.3, 'C': 2.0, 'C-': 1.7, 'D+': 1.3, 'D': 1.0, 'F': 0.0}
GRADE_FIELDS = ('course_name', 'credits', 'grade', 'course_type', 'semester', 'course_code')


def validate_grade(row):
    if not str(row.get('course_name', '')).strip():
        raise ValueError('课程名称不能为空')
    credits = float(row.get('credits', -1))
    if not math.isfinite(credits) or not 0 <= credits <= 100:
        raise ValueError('学分必须在 0–100 之间')
    grade = str(row.get('grade', '')).strip().upper()
    if grade not in GRADE_LEVELS:
        try:
            score = float(grade)
        except ValueError:
            raise ValueError('成绩请输入 0–100 的分数或有效等级')
        if not math.isfinite(score) or not 0 <= score <= 100:
            raise ValueError('成绩请输入 0–100 的分数或有效等级')
    if row.get('course_type') not in ('必修', '选修', '任选', '实践'):
        raise ValueError('课程性质须为必修、选修、任选或实践')
    if any(len(str(row.get(key, ''))) > 500 for key in GRADE_FIELDS):
        raise ValueError('课程字段过长')


def parse_grade_csv(content):
    if len(content) > 2_000_000:
        raise ValueError('文件大小不能超过 2 MB')
    try:
        frame = pd.read_csv(io.BytesIO(content), dtype=str, keep_default_na=False, encoding='utf-8-sig')
    except (ValueError, UnicodeError):
        raise ValueError('请上传 UTF-8 编码的 CSV 文件')
    if not {'course_name', 'credits', 'grade', 'course_type'} <= set(frame.columns):
        raise ValueError('CSV 缺少课程名称、学分、成绩或课程性质字段，请参考模板')
    if frame.empty or len(frame) > 1000:
        raise ValueError('每次请导入 1–1000 门课程')
    rows = []
    for index, source in frame.iterrows():
        row = {key: str(source.get(key, '')).strip() for key in GRADE_FIELDS}
        try:
            row['credits'] = float(row['credits'])
            validate_grade(row)
        except (ValueError, TypeError) as exc:
            raise ValueError(f'第 {index + 2} 行：{exc}') from None
        rows.append(row)
    return rows


def academic_summary(frame):
    data = frame.copy()
    data['credits'] = pd.to_numeric(data['credits'], errors='coerce').fillna(0).astype(float)
    data['source_credits'] = data['credits']
    names = data.get('course_name', pd.Series('', index=data.index)).astype(str)
    policy = names.str.contains('形势与政策|形策', regex=True, na=False)
    data.loc[policy, 'credits'] = 0.25
    data['score'] = pd.to_numeric(data['grade'], errors='coerce').astype(float)
    data.loc[data.grade.astype(str).str.upper().eq('A-'), 'score'] = 85.0
    from core.scu_gpa_engine import calculate_single_gpa
    data['grade_point'] = data.score.apply(lambda score: calculate_single_gpa(score) if pd.notna(score) and 0 <= score <= 100 else float('nan'))
    letters = data.grade.astype(str).str.strip().str.upper().map(LETTER_POINTS)
    data['grade_point'] = letters.combine_first(data.grade_point)
    gpa_courses = data[data.grade_point.notna() & data.credits.gt(0)]
    required_gpa_courses = gpa_courses[gpa_courses.course_type == '必修']
    numeric = data[data.score.between(0, 100)].copy()
    weighted = numeric[numeric.credits > 0]
    denominator = weighted.credits.sum()
    passed = data.score.ge(60) | data.grade.astype(str).str.upper().isin(GRADE_LEVELS - {'F', '不及格', '不通过'})
    required = weighted[weighted.course_type == '必修']
    return {
        'courses': len(data), 'credits': float(data.credits.sum()), 'source_credits': float(data.source_credits.sum()),
        'earned_credits': float(data.loc[passed, 'credits'].sum()),
        'average': float((weighted.score * weighted.credits).sum() / denominator) if denominator else None,
        'required_average': float((required.score * required.credits).sum() / required.credits.sum()) if required.credits.sum() else None,
        'gpa': float((gpa_courses.grade_point * gpa_courses.credits).sum() / gpa_courses.credits.sum()) if gpa_courses.credits.sum() else None,
        'required_gpa': float((required_gpa_courses.grade_point * required_gpa_courses.credits).sum() / required_gpa_courses.credits.sum()) if required_gpa_courses.credits.sum() else None,
        'excellent': int(numeric.score.ge(90).sum()), 'numeric_courses': len(numeric),
        'level_courses': int((data.score.isna()).sum()), 'weighted_credits': float(denominator),
        'numeric': numeric, 'weighted': weighted, 'all': data,
    }


def semester_summary(frame):
    data = frame.copy()
    if 'semester' not in data:
        data['semester'] = ''
    data['semester'] = data['semester'].fillna('').replace('', '未标注学期')
    rows = []
    for semester, group in data.groupby('semester'):
        summary = academic_summary(group)
        rows.append({'学期': semester, '课程数': len(group), '已获学分': summary['earned_credits'], '加权均分': summary['average']})
    return pd.DataFrame(rows, columns=['学期', '课程数', '已获学分', '加权均分']).sort_values('学期', key=lambda col: col.map(lambda value: value.replace('秋', '0').replace('春', '1')))
