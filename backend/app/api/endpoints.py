"""
RESTful Endpoints for MQPSS Emergency Triage & Queue Scheduling
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List
from backend.app.models.schemas import (
    PatientIntakeRequest, TriageOverrideRequest, Patient, Doctor
)
from backend.app.services.scheduler_service import scheduler_service
from backend.app.services.triage_service import triage_service
from backend.app.core.websocket_manager import ws_manager

router = APIRouter()

@router.get("/patients/{patient_id}", response_model=Dict[str, Any])
def get_patient_detail(patient_id: str):
    """Lấy chi tiết hồ sơ bệnh nhân, sinh hiệu và giải thích AI"""
    patient = scheduler_service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Không tìm thấy bệnh nhân")
    return {"status": "SUCCESS", "patient": patient.model_dump()}

@router.post("/reset", response_model=Dict[str, Any])
async def reset_queues(bg_tasks: BackgroundTasks):
    """Reset sạch dữ liệu hàng đợi và giải phóng toàn bộ bác sĩ"""
    scheduler_service.reset_system()
    bg_tasks.add_task(ws_manager.broadcast, "SYSTEM_RESET", {
        "snapshot": scheduler_service.get_snapshot()
    })
    return {"status": "RESET_SUCCESS", "message": "Đã làm sạch toàn bộ hàng đợi"}

@router.get("/export/csv")
def export_csv_report():
    """Xuất danh sách dữ liệu bệnh nhân dưới định dạng CSV"""
    from fastapi.responses import Response
    snapshot = scheduler_service.get_snapshot()
    all_p = (
        snapshot["queue_1"] + snapshot["queue_2"] +
        snapshot["queue_3"] + snapshot["queue_4"] +
        snapshot["queue_5"] + snapshot["active_treatments"]
    )
    lines = ["Mã BN,Họ Tên,Tuổi,Giới Tính,ESI Gốc,ESI Hiện Tại,Thời Gian Chờ (phút),Điểm Ưu Tiên,Triệu Chứng Chính,SpO2,Mạch,HA Tâm Thu,Trạng Thái"]
    for p in all_p:
        v = p.get("vitals", {})
        line = f'{p.get("patient_id")},"{p.get("full_name")}",{p.get("age")},{p.get("gender")},{p.get("original_esi")},{p.get("current_esi")},{p.get("waiting_time_minutes")},{p.get("priority_score")},"{p.get("chief_complaint")}",{v.get("spo2")},{v.get("heart_rate")},{v.get("systolic_bp")},{p.get("status")}'
        lines.append(line)
    csv_content = "\ufeff" + "\n".join(lines) # UTF-8 with BOM for Excel
    return Response(content=csv_content, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=danh_sach_benh_nhan_cap_cuu.csv"})

@router.post("/patients/intake", response_model=Dict[str, Any])
async def intake_patient(req: PatientIntakeRequest, bg_tasks: BackgroundTasks):
    """Tiếp đón bệnh nhân mới, AI phân loại ESI và đưa vào hàng đợi"""
    patient = scheduler_service.admit_patient(req)
    
    # Broadcast event real-time
    event_type = "EMERGENCY_ALARM_ESI1" if patient.current_esi.value == 1 else "PATIENT_ADMITTED"
    bg_tasks.add_task(ws_manager.broadcast, event_type, {
        "patient": patient.model_dump(),
        "snapshot": scheduler_service.get_snapshot()
    })
    
    return {
        "status": "SUCCESS",
        "message": f"Bệnh nhân {patient.full_name} đã được phân loại ESI-{patient.current_esi.value}",
        "patient": patient.model_dump()
    }

@router.get("/queues", response_model=Dict[str, Any])
def get_all_queues():
    """Lấy snapshot toàn bộ 5 hàng đợi và danh sách bác sĩ"""
    return scheduler_service.get_snapshot()

@router.get("/queues/stats", response_model=Dict[str, Any])
def get_queue_statistics():
    """Lấy số liệu KPI thống kê hàng đợi"""
    return scheduler_service.get_stats().model_dump()

@router.post("/doctors/{doctor_id}/call-next", response_model=Dict[str, Any])
async def doctor_call_next(doctor_id: str, bg_tasks: BackgroundTasks):
    """Bác sĩ gọi bệnh nhân ưu tiên cao nhất tiếp theo"""
    patient = scheduler_service.call_next_patient(doctor_id)
    if not patient:
        return {"status": "EMPTY", "message": "Không có bệnh nhân nào trong hàng chờ hoặc bác sĩ đang bận"}
    
    bg_tasks.add_task(ws_manager.broadcast, "PATIENT_DISPATCHED", {
        "doctor_id": doctor_id,
        "patient": patient.model_dump(),
        "snapshot": scheduler_service.get_snapshot()
    })
    
    return {
        "status": "DISPATCHED",
        "doctor_id": doctor_id,
        "patient": patient.model_dump()
    }

@router.post("/patients/{patient_id}/finish", response_model=Dict[str, Any])
async def finish_patient_treatment(patient_id: str, bg_tasks: BackgroundTasks):
    """Hoàn tất điều trị ca bệnh, giải phóng bác sĩ"""
    patient = scheduler_service.finish_treatment(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Không tìm thấy bệnh nhân đang điều trị")
    
    bg_tasks.add_task(ws_manager.broadcast, "TREATMENT_FINISHED", {
        "patient_id": patient_id,
        "snapshot": scheduler_service.get_snapshot()
    })
    
    return {"status": "FINISHED", "patient": patient.model_dump()}

@router.post("/patients/{patient_id}/send-to-lab", response_model=Dict[str, Any])
async def send_patient_to_lab(patient_id: str, bg_tasks: BackgroundTasks):
    """Chuyển bệnh nhân sang chờ cận lâm sàng (I/O Wait), giải phóng bác sĩ"""
    patient = scheduler_service.send_to_lab(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Không tìm thấy ca bệnh")
    
    bg_tasks.add_task(ws_manager.broadcast, "PATIENT_SENT_TO_LAB", {
        "patient_id": patient_id,
        "snapshot": scheduler_service.get_snapshot()
    })
    
    return {"status": "LAB_WAIT", "patient": patient.model_dump()}

@router.post("/patients/{patient_id}/lab-return", response_model=Dict[str, Any])
async def return_patient_from_lab(patient_id: str, bg_tasks: BackgroundTasks):
    """Bệnh nhân nhận kết quả cận lâm sàng, trở lại Queue 2"""
    patient = scheduler_service.return_from_lab(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Không tìm thấy ca trong phòng cận lâm sàng")
    
    bg_tasks.add_task(ws_manager.broadcast, "LAB_RETURNED", {
        "patient": patient.model_dump(),
        "snapshot": scheduler_service.get_snapshot()
    })
    
    return {"status": "RETURNED_TO_QUEUE", "patient": patient.model_dump()}

@router.post("/aging/trigger", response_model=Dict[str, Any])
async def trigger_aging(bg_tasks: BackgroundTasks):
    """Kích hoạt quét Dynamic Aging thủ công"""
    promotions = scheduler_service.run_aging()
    if promotions:
        bg_tasks.add_task(ws_manager.broadcast, "AGING_PROMOTIONS", {
            "promotions": promotions,
            "snapshot": scheduler_service.get_snapshot()
        })
    return {"status": "AGING_CHECKED", "promotions_count": len(promotions), "promotions": promotions}

@router.post("/triage/override", response_model=Dict[str, Any])
def override_triage(req: TriageOverrideRequest):
    """Y tá / Bác sĩ override mức ESI thủ công kèm lý do"""
    return triage_service.override_triage(req)

@router.post("/demo/seed", response_model=Dict[str, Any])
async def seed_demo_patients(bg_tasks: BackgroundTasks):
    """Nạp 8 ca lâm sàng mẫu đủ các cấp độ ESI để test nhanh hệ thống"""
    from backend.app.models.schemas import VitalSigns, AVPUConsciousness
    
    demo_cases = [
        # Ca 1: ESI-1 Nguy kịch (Sốc tim)
        PatientIntakeRequest(
            patient_id="BN-0101", full_name="Nguyễn Văn Hùng", age=68, gender="male",
            chief_complaint="Đột ngột ngưng thở, tím tái sau đau ngực", consciousness=AVPUConsciousness.UNRESPONSIVE,
            vitals=VitalSigns(heart_rate=32, systolic_bp=55, diastolic_bp=30, respiratory_rate=6, spo2=68.0, temperature=35.8, pain_scale=0),
            comorbidities=["tim_mach", "tang_huyet_ap"]
        ),
        # Ca 2: ESI-2 Rất cấp (Suy hô hấp cấp / SpO2 86%)
        PatientIntakeRequest(
            patient_id="BN-0102", full_name="Trần Thị Lan", age=72, gender="female",
            chief_complaint="Khó thở dữ dội, co kéo cơ hô hấp", consciousness=AVPUConsciousness.ALERT,
            vitals=VitalSigns(heart_rate=128, systolic_bp=150, diastolic_bp=90, respiratory_rate=32, spo2=86.0, temperature=38.2, pain_scale=5),
            comorbidities=["copd"]
        ),
        # Ca 3: ESI-2 Đau ngực kịch phát (Nghi NMCT)
        PatientIntakeRequest(
            patient_id="BN-0103", full_name="Lê Minh Trí", age=58, gender="male",
            chief_complaint="Đau ngực sau xương ức lan vai trái, vã mồ hôi", consciousness=AVPUConsciousness.ALERT,
            vitals=VitalSigns(heart_rate=105, systolic_bp=165, diastolic_bp=95, respiratory_rate=22, spo2=95.0, temperature=37.0, pain_scale=9),
            comorbidities=["tang_huyet_ap", "tieu_duong"]
        ),
        # Ca 4: ESI-3 Đau bụng cấp (Cần máu + CT)
        PatientIntakeRequest(
            patient_id="BN-0104", full_name="Võ Thanh Bình", age=41, gender="male",
            chief_complaint="Đau quặn bụng quanh rốn kèm nôn liên tục", consciousness=AVPUConsciousness.ALERT,
            vitals=VitalSigns(heart_rate=92, systolic_bp=125, diastolic_bp=80, respiratory_rate=18, spo2=98.0, temperature=38.6, pain_scale=7),
            comorbidities=[]
        ),
        # Ca 5: ESI-3 Sốt cao kéo dài
        PatientIntakeRequest(
            patient_id="BN-0105", full_name="Phạm Mai Anh", age=29, gender="female",
            chief_complaint="Sốt cao 39.2 độ, đau mỏi toàn thân 3 ngày", consciousness=AVPUConsciousness.ALERT,
            vitals=VitalSigns(heart_rate=96, systolic_bp=110, diastolic_bp=70, respiratory_rate=20, spo2=98.0, temperature=39.2, pain_scale=4),
            comorbidities=[]
        ),
        # Ca 6: ESI-4 Chấn thương ngón tay (Cần 1 X-quang)
        PatientIntakeRequest(
            patient_id="BN-0106", full_name="Đặng Tuấn Kiệt", age=19, gender="male",
            chief_complaint="Gãy xương ngón trỏ tay phải sau ngã xe", consciousness=AVPUConsciousness.ALERT,
            vitals=VitalSigns(heart_rate=78, systolic_bp=118, diastolic_bp=75, respiratory_rate=16, spo2=99.0, temperature=36.8, pain_scale=5),
            comorbidities=[]
        ),
        # Ca 7: ESI-4 Vết thương rách da
        PatientIntakeRequest(
            patient_id="BN-0107", full_name="Hoàng Thị Thảo", age=33, gender="female",
            chief_complaint="Vết rách cẳng tay dài 4cm do mảnh kính cứa", consciousness=AVPUConsciousness.ALERT,
            vitals=VitalSigns(heart_rate=80, systolic_bp=115, diastolic_bp=75, respiratory_rate=16, spo2=99.0, temperature=37.0, pain_scale=4),
            comorbidities=[]
        ),
        # Ca 8: ESI-5 Khám tái khám / Xin thuốc
        PatientIntakeRequest(
            patient_id="BN-0108", full_name="Ngô Văn Nam", age=45, gender="male",
            chief_complaint="Hết thuốc huyết áp, đến tái khám và xin toa thuốc", consciousness=AVPUConsciousness.ALERT,
            vitals=VitalSigns(heart_rate=72, systolic_bp=125, diastolic_bp=80, respiratory_rate=16, spo2=99.0, temperature=36.6, pain_scale=0),
            comorbidities=["tang_huyet_ap"]
        )
    ]
    
    admitted = []
    for case in demo_cases:
        p = scheduler_service.admit_patient(case)
        admitted.append(p.model_dump())

    bg_tasks.add_task(ws_manager.broadcast, "DEMO_SEEDED", {
        "snapshot": scheduler_service.get_snapshot()
    })
    
    return {
        "status": "SEEDED",
        "count": len(admitted),
        "snapshot": scheduler_service.get_snapshot()
    }

@router.post("/simulation/fast-forward-time", response_model=Dict[str, Any])
async def fast_forward_simulation_time(bg_tasks: BackgroundTasks, minutes: float = 30.0):
    """Tua nhanh thời gian chờ của các bệnh nhân thêm `minutes` phút và tự động kích hoạt aging"""
    promotions = scheduler_service.fast_forward_time(minutes)
    bg_tasks.add_task(ws_manager.broadcast, "TIME_FAST_FORWARDED", {
        "minutes": minutes,
        "promotions": promotions,
        "snapshot": scheduler_service.get_snapshot()
    })
    return {
        "status": "TIME_ADVANCED",
        "minutes_added": minutes,
        "promotions_count": len(promotions),
        "promotions": promotions,
        "snapshot": scheduler_service.get_snapshot()
    }

@router.post("/simulation/mass-casualty-surge", response_model=Dict[str, Any])
async def trigger_mass_casualty_surge(bg_tasks: BackgroundTasks):
    """Mô phỏng thảm họa hàng loạt (MCI) kích hoạt báo động đỏ và preemption"""
    patients = scheduler_service.trigger_mass_casualty_incident()
    bg_tasks.add_task(ws_manager.broadcast, "EMERGENCY_ALARM_ESI1", {
        "mci": True,
        "patients": [p.model_dump() for p in patients],
        "snapshot": scheduler_service.get_snapshot()
    })
    return {
        "status": "MCI_TRIGGERED",
        "admitted_count": len(patients),
        "snapshot": scheduler_service.get_snapshot()
    }

