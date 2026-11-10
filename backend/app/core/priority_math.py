"""
Mathematical Modeling & Priority Scoring Engine for MQPSS
Calculates multi-attribute dynamic priority scores.
"""

from backend.app.core.config import settings
from backend.app.models.schemas import ESILevel, VitalSigns, AVPUConsciousness

def compute_vital_signs_score(vitals: VitalSigns, consciousness: AVPUConsciousness) -> float:
    """Tính điểm bất thường sinh hiệu (0 - 100)"""
    score = 0.0
    
    # 1. Hôn mê / Giảm tri giác (Unresponsive / Pain response)
    if consciousness == AVPUConsciousness.UNRESPONSIVE:
        return 100.0
    elif consciousness == AVPUConsciousness.PAIN:
        score += 50.0
    elif consciousness == AVPUConsciousness.VOICE:
        score += 25.0

    # 2. SpO2 (Thiếu oxy máu)
    if vitals.spo2 < 88.0:
        score += 45.0
    elif vitals.spo2 < 92.0:
        score += 30.0
    elif vitals.spo2 < 95.0:
        score += 15.0

    # 3. Chỉ số sốc Shock Index = Heart Rate / Systolic BP
    shock_index = vitals.heart_rate / max(vitals.systolic_bp, 1)
    if shock_index >= 1.0:
        score += 35.0  # Dấu hiệu sốc mất máu hoặc sốc nhiễm trùng
    elif shock_index >= 0.8:
        score += 20.0

    # 4. Nhịp tim bất thường
    if vitals.heart_rate > 140 or vitals.heart_rate < 45:
        score += 25.0
    elif vitals.heart_rate > 115 or vitals.heart_rate < 55:
        score += 15.0

    # 5. Nhịp thở bất thường
    if vitals.respiratory_rate > 32 or vitals.respiratory_rate < 10:
        score += 25.0
    elif vitals.respiratory_rate > 24:
        score += 15.0

    # 6. Thang điểm đau cấp (VAS)
    if vitals.pain_scale >= 8:
        score += 20.0
    elif vitals.pain_scale >= 5:
        score += 10.0

    # 7. Sốt cao co giật / Hạ thân nhiệt
    if vitals.temperature >= 39.5 or vitals.temperature <= 35.0:
        score += 15.0

    return min(100.0, score)

def compute_age_factor_score(age: int) -> float:
    """Tính điểm hệ số tuổi ưu tiên (0 - 100)"""
    if age < 1:
        return 100.0   # Trẻ sơ sinh cực kỳ dễ chuyển biến xấu
    elif age <= 5:
        return 75.0    # Trẻ dưới 5 tuổi
    elif age >= 80:
        return 90.0    # Người rất cao tuổi
    elif age >= 65:
        return 65.0    # Người cao tuổi
    elif age <= 12:
        return 45.0    # Thiếu nhi
    else:
        return 20.0    # Người trưởng thành

def compute_comorbidity_score(comorbidities: list[str]) -> float:
    """Tính điểm bệnh lý nền (0 - 100)"""
    high_risk_diseases = {
        "heart_disease": 30.0,
        "tim_mach": 30.0,
        "stroke": 35.0,
        "tai_bien": 35.0,
        "copd": 25.0,
        "hen_suyen": 25.0,
        "diabetes": 20.0,
        "tieu_duong": 20.0,
        "chronic_kidney": 25.0,
        "suy_than": 25.0,
        "hypertension": 15.0,
        "tang_huyet_ap": 15.0,
        "cancer": 25.0,
        "ung_thu": 25.0
    }
    score = 0.0
    for c in comorbidities:
        norm = c.lower().strip().replace(" ", "_")
        for key, val in high_risk_diseases.items():
            if key in norm:
                score += val
                break
    return min(100.0, score)

def compute_waiting_time_score(waiting_minutes: float, esi_level: ESILevel) -> float:
    """Tính điểm tăng tốc theo thời gian chờ dựa trên ngưỡng an toàn ESI (0 - 100)"""
    # Ngưỡng thời gian an toàn theo ESI v4
    safe_thresholds = {
        ESILevel.LEVEL_1: 0.1,    # Phải vào ngay
        ESILevel.LEVEL_2: 15.0,   # Chờ < 15p
        ESILevel.LEVEL_3: 60.0,   # Chờ < 60p
        ESILevel.LEVEL_4: 120.0,  # Chờ < 120p
        ESILevel.LEVEL_5: 240.0   # Chờ < 240p
    }
    threshold = safe_thresholds.get(esi_level, 60.0)
    ratio = waiting_minutes / max(threshold, 0.1)
    # Tăng dần theo hàm căn bậc hai để phản ứng sớm, đạt 100 khi chạm ngưỡng
    score = min(100.0, (ratio ** 0.8) * 100.0)
    return score

def compute_overall_priority_score(
    esi_level: ESILevel,
    waiting_minutes: float,
    vitals: VitalSigns,
    consciousness: AVPUConsciousness,
    age: int,
    comorbidities: list[str],
    weights = settings.WEIGHTS
) -> float:
    """
    Công thức tổng hợp Priority Score đa biến (0 - 100)
    Priority = w1*S_ESI + w2*S_Wait + w3*S_Vitals + w4*S_Age + w5*S_Comorbidity
    """
    # 1. Điểm ESI nền tảng
    esi_base_scores = {
        ESILevel.LEVEL_1: 100.0,
        ESILevel.LEVEL_2: 80.0,
        ESILevel.LEVEL_3: 50.0,
        ESILevel.LEVEL_4: 25.0,
        ESILevel.LEVEL_5: 10.0
    }
    s_esi = esi_base_scores.get(esi_level, 50.0)
    
    # 2. Điểm thời gian chờ
    s_wait = compute_waiting_time_score(waiting_minutes, esi_level)
    
    # 3. Điểm sinh hiệu
    s_vitals = compute_vital_signs_score(vitals, consciousness)
    
    # 4. Điểm tuổi
    s_age = compute_age_factor_score(age)
    
    # 5. Điểm bệnh lý nền
    s_comorbidity = compute_comorbidity_score(comorbidities)
    
    # Tổng hợp theo trọng số
    total_score = (
        weights.w1_esi * s_esi +
        weights.w2_waiting_time * s_wait +
        weights.w3_vitals * s_vitals +
        weights.w4_age * s_age +
        weights.w5_comorbidity * s_comorbidity
    )
    return round(total_score, 2)

