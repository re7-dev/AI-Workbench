import pandas as pd


def calculate_single_gpa(score):
    for threshold, value in [(90,4.0),(85,3.7),(80,3.3),(76,3.0),(73,2.7),(70,2.3),(66,2.0),(63,1.7),(61,1.3),(60,1.0)]:
        if score >= threshold:
            return value
    return 0.0


def process_academic_metrics(df):
    data = df.copy()
    data['grade'] = pd.to_numeric(data['grade'], errors='coerce')
    data['credits'] = pd.to_numeric(data['credits'], errors='coerce')
    data = data[data.grade.between(0, 100) & (data.credits > 0)]
    if data.empty:
        return None
    metrics = {'total_credits': data.credits.sum()}
    for prefix, subset in [('overall', data), ('req', data[data.course_type == '必修'])]:
        credits = subset.credits.sum()
        metrics[f'{prefix}_avg'] = (subset.grade * subset.credits).sum() / credits if credits else 0
        metrics[f'{prefix}_gpa'] = (subset.grade.apply(calculate_single_gpa) * subset.credits).sum() / credits if credits else 0
    metrics['req_credits'] = data.loc[data.course_type == '必修', 'credits'].sum()
    return metrics
