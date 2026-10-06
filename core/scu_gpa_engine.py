def calculate_single_gpa(score: float) -> float:
    """根据分数返回对应的 4.0 制单科绩点"""
    if score >= 90: return 4.0
    elif score >= 85: return 3.7
    elif score >= 80: return 3.3
    elif score >= 76: return 3.0
    elif score >= 73: return 2.7
    elif score >= 70: return 2.3
    elif score >= 66: return 2.0
    elif score >= 63: return 1.7
    elif score >= 61: return 1.3
    elif score >= 60: return 1.0
    else: return 0.0

def process_academic_metrics(df):
    """
    接收成绩 DataFrame，统一计算总加权、必修加权与对应绩点。
    返回包含整体与必修指标的字典，供前端直接渲染。
    """
    if df.empty:
        return None
        
    df['credits'] = df['credits'].astype(float)
    df['grade'] = df['grade'].astype(float)
    df['gpa'] = df['grade'].apply(calculate_single_gpa)
    
    metrics = {}
    
    # 全部课程指标
    total_credits = df['credits'].sum()
    if total_credits > 0:
        metrics['overall_avg'] = (df['grade'] * df['credits']).sum() / total_credits
        metrics['overall_gpa'] = (df['gpa'] * df['credits']).sum() / total_credits
    else:
        metrics['overall_avg'] = metrics['overall_gpa'] = 0.0
    metrics['total_credits'] = total_credits
    
    # 必修课程指标
    req_df = df[df['course_type'] == '必修']
    req_credits = req_df['credits'].sum()
    if req_credits > 0:
        metrics['req_avg'] = (req_df['grade'] * req_df['credits']).sum() / req_credits
        metrics['req_gpa'] = (req_df['gpa'] * req_df['credits']).sum() / req_credits
    else:
        metrics['req_avg'] = metrics['req_gpa'] = 0.0
    metrics['req_credits'] = req_credits
    
    return metrics