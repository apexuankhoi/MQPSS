"""
Unit Tests for AI Triage Engine & Mathematical Priority Scoring
"""

import pytest
from backend.app.models.schemas import (
    ESILevel, AVPUConsciousness, VitalSigns,
    PatientIntakeRequest, TriageOverrideRequest
)
from backend.app.core.priority_math import (
    compute_vital_signs_score, compute_age_factor_score,
    compute_waiting_time_score, compute_overall_priority_score
)
from backend.app.services.triage_service import triage_service

def test_esi_1_unresponsive():
    """Ca hôn mê bất tỉnh phải được phân loại ESI-1 ngay lập tức"""
    vitals = VitalSigns(
        heart_rate=40, systolic_bp=60, diastolic_bp=30,
        respiratory_rate=8, spo2=75.0, temperature=35.5, pain_scale=0
    )
    req = PatientIntakeRequest(
        patient_id="BN-001",
        full_name="Nguyễn Văn A",
        age=55,
        chief_complaint="Hôn mê sau tai nạn giao thông",
        consciousness=AVPUConsciousness.UNRESPONSIVE,
        vitals=vitals
    )
    result = triage_service.classify_patient(req)
    assert result.esi_level == ESILevel.LEVEL_1
    assert result.is_rule_based is True
    assert result.confidence == 1.0
    assert any("hôn mê" in exp.lower() for exp in result.explanations)

def test_esi_1_cardiac_arrest_keyword():
    """Ca có triệu chứng ngưng thở/ngưng tim phải gán ESI-1"""
    vitals = VitalSigns(
        heart_rate=0, systolic_bp=40, diastolic_bp=20,
        respiratory_rate=0, spo2=50.0, temperature=36.0, pain_scale=0
    )
    req = PatientIntakeRequest(
        patient_id="BN-002",
        full_name="Trần Văn B",
        age=62,
        chief_complaint="Đột ngột ngưng tim tại nhà",
        consciousness=AVPUConsciousness.PAIN,
        vitals=vitals
    )
    result = triage_service.classify_patient(req)
    assert result.esi_level == ESILevel.LEVEL_1

def test_esi_2_hypoxia():
    """Ca SpO2 < 90% phải gán ESI-2 do suy hô hấp cấp"""
    vitals = VitalSigns(
        heart_rate=110, systolic_bp=125, diastolic_bp=80,
        respiratory_rate=28, spo2=87.0, temperature=37.2, pain_scale=4
    )
    req = PatientIntakeRequest(
        patient_id="BN-003",
        full_name="Lê Thị C",
        age=48,
        chief_complaint="Khó thở nhiều, mệt lả",
        consciousness=AVPUConsciousness.ALERT,
        vitals=vitals
    )
    result = triage_service.classify_patient(req)
    assert result.esi_level == ESILevel.LEVEL_2
    assert result.is_rule_based is True
    assert any("spo2" in exp.lower() for exp in result.explanations)

def test_esi_2_shock_index():
    """Ca mạch 130, huyết áp 100 (Shock Index = 1.3) phải gán ESI-2"""
    vitals = VitalSigns(
        heart_rate=130, systolic_bp=100, diastolic_bp=60,
        respiratory_rate=22, spo2=96.0, temperature=38.0, pain_scale=6
    )
    req = PatientIntakeRequest(
        patient_id="BN-004",
        full_name="Phạm Văn D",
        age=35,
        chief_complaint="Đau bụng quặn, nghi xuất huyết tiêu hóa",
        consciousness=AVPUConsciousness.ALERT,
        vitals=vitals
    )
    result = triage_service.classify_patient(req)
    assert result.esi_level == ESILevel.LEVEL_2

def test_esi_3_multi_resource():
    """Ca đau bụng sốt cần xét nghiệm máu + siêu âm -> ESI-3"""
    vitals = VitalSigns(
        heart_rate=88, systolic_bp=120, diastolic_bp=80,
        respiratory_rate=18, spo2=98.0, temperature=38.4, pain_scale=6
    )
    req = PatientIntakeRequest(
        patient_id="BN-005",
        full_name="Hoàng Thị E",
        age=30,
        chief_complaint="Đau bụng hố chậu phải kèm sốt 2 ngày",
        consciousness=AVPUConsciousness.ALERT,
        vitals=vitals,
        comorbidities=["viêm dạ dày"]
    )
    result = triage_service.classify_patient(req)
    assert result.esi_level == ESILevel.LEVEL_3

def test_esi_4_single_resource():
    """Ca bong gân gãy ngón chỉ cần 1 X-quang -> ESI-4"""
    vitals = VitalSigns(
        heart_rate=76, systolic_bp=115, diastolic_bp=75,
        respiratory_rate=16, spo2=99.0, temperature=36.8, pain_scale=4
    )
    req = PatientIntakeRequest(
        patient_id="BN-006",
        full_name="Đặng Văn F",
        age=22,
        chief_complaint="Bong gân cổ chân sau đá bóng",
        consciousness=AVPUConsciousness.ALERT,
        vitals=vitals
    )
    result = triage_service.classify_patient(req)
    assert result.esi_level == ESILevel.LEVEL_4

def test_priority_score_ordering():
    """Ca ESI-1 phải có điểm ưu tiên cao hơn ESI-4"""
    vitals_critical = VitalSigns(
        heart_rate=135, systolic_bp=75, diastolic_bp=45,
        respiratory_rate=30, spo2=84.0, temperature=36.0, pain_scale=8
    )
    score_critical = compute_overall_priority_score(
        esi_level=ESILevel.LEVEL_1,
        waiting_minutes=5.0,
        vitals=vitals_critical,
        consciousness=AVPUConsciousness.VOICE,
        age=75,
        comorbidities=["tai_bien", "tieu_duong"]
    )

    vitals_stable = VitalSigns(
        heart_rate=72, systolic_bp=120, diastolic_bp=80,
        respiratory_rate=16, spo2=99.0, temperature=36.8, pain_scale=2
    )
    score_stable = compute_overall_priority_score(
        esi_level=ESILevel.LEVEL_4,
        waiting_minutes=5.0,
        vitals=vitals_stable,
        consciousness=AVPUConsciousness.ALERT,
        age=25,
        comorbidities=[]
    )

    assert score_critical > score_stable
    assert score_critical >= 75.0

def test_triage_override():
    """Y tá có thể override thủ công và lưu vào audit log"""
    req = TriageOverrideRequest(
        patient_id="BN-005",
        new_esi_level=ESILevel.LEVEL_2,
        reason="Bệnh nhân có vẻ mặt nhiễm trùng nhiễm độc nặng, mạch nảy yếu",
        staff_name="Điều dưỡng Hương"
    )
    resp = triage_service.override_triage(req)
    assert resp["status"] == "SUCCESS"
    assert resp["audit"]["staff_name"] == "Điều dưỡng Hương"

