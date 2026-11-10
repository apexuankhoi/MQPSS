"""
Unit Tests for Multilevel Queue, Dynamic Aging & Preemptive Scheduling
"""

from datetime import datetime, timedelta
import pytest
from backend.app.models.schemas import (
    Patient, Doctor, ESILevel, AVPUConsciousness,
    VitalSigns, PatientStatus, DoctorStatus, TriageClassification
)
from backend.app.algorithms.queues import (
    PreemptivePriorityQueue, ScoredPriorityQueue,
    RoundRobinQueue, FCFSQueue, OutpatientDiversionQueue
)
from backend.app.algorithms.aging import run_dynamic_aging_cycle
from backend.app.algorithms.dispatcher import HospitalDispatcher
from backend.app.services.scheduler_service import SchedulerService

def create_sample_patient(pid: str, esi: ESILevel, score: float, wait_mins: float = 0.0) -> Patient:
    vitals = VitalSigns(
        heart_rate=80, systolic_bp=120, diastolic_bp=80,
        respiratory_rate=16, spo2=98.0, temperature=37.0, pain_scale=3
    )
    triage_info = TriageClassification(
        esi_level=esi, is_rule_based=True, confidence=1.0, explanations=["Test case"]
    )
    return Patient(
        patient_id=pid,
        full_name=f"Bệnh nhân {pid}",
        age=30,
        gender="male",
        chief_complaint="Khám thử nghiệm",
        consciousness=AVPUConsciousness.ALERT,
        vitals=vitals,
        original_esi=esi,
        current_esi=esi,
        triage_info=triage_info,
        arrival_time=datetime.now() - timedelta(minutes=wait_mins),
        current_queue=esi.value,
        status=PatientStatus.WAITING,
        waiting_time_minutes=wait_mins,
        priority_score=score
    )

def test_queues_basic_operations():
    """Kiểm tra hoạt động cơ bản của cả 5 hàng đợi"""
    q1 = PreemptivePriorityQueue()
    q2 = ScoredPriorityQueue()
    q3 = RoundRobinQueue(quantum_minutes=30.0)
    q4 = FCFSQueue()
    q5 = OutpatientDiversionQueue()

    p1 = create_sample_patient("P1", ESILevel.LEVEL_1, 95.0)
    p2_low = create_sample_patient("P2_LOW", ESILevel.LEVEL_2, 60.0)
    p2_high = create_sample_patient("P2_HIGH", ESILevel.LEVEL_2, 90.0)
    p3 = create_sample_patient("P3", ESILevel.LEVEL_3, 50.0)
    p4 = create_sample_patient("P4", ESILevel.LEVEL_4, 25.0)
    p5 = create_sample_patient("P5", ESILevel.LEVEL_5, 10.0)

    # Queue 1
    q1.enqueue(p1)
    assert len(q1) == 1
    assert q1.dequeue().patient_id == "P1"

    # Queue 2: Max-Heap theo priority_score
    q2.enqueue(p2_low)
    q2.enqueue(p2_high)
    assert len(q2) == 2
    # p2_high có điểm 90.0 phải được lấy ra TRƯỚC p2_low có điểm 60.0
    popped = q2.dequeue()
    assert popped.patient_id == "P2_HIGH"

    # Queue 3: Round Robin
    q3.enqueue(p3)
    assert len(q3) == 1
    assert q3.dequeue().patient_id == "P3"

    # Queue 4: FCFS
    q4.enqueue(p4)
    assert len(q4) == 1
    assert q4.dequeue().patient_id == "P4"

    # Queue 5: Diversion
    q5.enqueue(p5)
    assert p5.status == PatientStatus.TRANSFERRED

def test_dynamic_aging_promotion():
    """Kiểm tra cơ chế Dynamic Aging thăng hạng bệnh nhân chờ quá ngưỡng an toàn"""
    q4 = FCFSQueue()
    q3 = RoundRobinQueue()
    q2 = ScoredPriorityQueue()

    # Bệnh nhân P4_STARVED đã chờ 100 phút ở Queue 4 (vượt ngưỡng 90p)
    p4_starved = create_sample_patient("P4_STARVED", ESILevel.LEVEL_4, 25.0, wait_mins=100.0)
    # Bệnh nhân P4_FRESH chỉ mới chờ 10 phút
    p4_fresh = create_sample_patient("P4_FRESH", ESILevel.LEVEL_4, 25.0, wait_mins=10.0)
    q4.enqueue(p4_starved)
    q4.enqueue(p4_fresh)

    # Bệnh nhân P3_STARVED đã chờ 50 phút ở Queue 3 (vượt ngưỡng 45p)
    p3_starved = create_sample_patient("P3_STARVED", ESILevel.LEVEL_3, 50.0, wait_mins=50.0)
    q3.enqueue(p3_starved)

    now = datetime.now()
    promotions = run_dynamic_aging_cycle(q4, q3, q2, now)

    assert len(promotions) == 2
    
    # P4_STARVED phải được thăng lên Queue 3
    assert len(q4) == 1 # Chỉ còn P4_FRESH
    assert any(p.patient_id == "P4_STARVED" for p in q3.get_all())
    
    # P3_STARVED phải được thăng lên Queue 2
    assert any(p.patient_id == "P3_STARVED" for p in q2.get_all())

def test_preemption_logic():
    """
    Kiểm tra cơ chế ngắt quyền (Preemption):
    Khi có ca ESI-1 nguy kịch vào viện mà tất cả bác sĩ đều bận,
    bác sĩ đang khám ca ESI-4 sẽ bị ngắt để cấp cứu ca ESI-1 ngay lập tức.
    """
    doc1 = Doctor(doctor_id="DOC-1", full_name="Bác sĩ 1", status=DoctorStatus.BUSY, current_patient_id="P_MILD")
    dispatcher = HospitalDispatcher([doc1])
    
    q3 = RoundRobinQueue()
    q4 = FCFSQueue()
    
    p_mild = create_sample_patient("P_MILD", ESILevel.LEVEL_4, 20.0)
    active = {"P_MILD": p_mild}
    
    esi1_patient = create_sample_patient("P_CRITICAL", ESILevel.LEVEL_1, 100.0)

    # Gọi hàm xử lý preemption
    assigned_doc, preempted = dispatcher.handle_preemption_for_esi1(
        esi1_patient=esi1_patient,
        q3=q3,
        q4=q4,
        active_treatments=active
    )

    # Bác sĩ 1 phải được gán cho ca ESI-1
    assert assigned_doc.doctor_id == "DOC-1"
    assert assigned_doc.current_patient_id == "P_CRITICAL"
    assert esi1_patient.status == PatientStatus.IN_TREATMENT
    
    # Ca nhẹ bị ngắt phải được trả về đầu hàng đợi 4
    assert preempted.patient_id == "P_MILD"
    assert len(q4) == 1
    assert q4.peek().patient_id == "P_MILD"

def test_dispatcher_load_balancing():
    """Kiểm tra điều phối cân bằng tải giữa các bác sĩ"""
    doc_busy = Doctor(doctor_id="D1", full_name="BS Bận", status=DoctorStatus.AVAILABLE, patients_treated_count=10)
    doc_free = Doctor(doctor_id="D2", full_name="BS Rảnh", status=DoctorStatus.AVAILABLE, patients_treated_count=2)
    
    dispatcher = HospitalDispatcher([doc_busy, doc_free])
    chosen = dispatcher.get_available_doctor()
    
    # Phải chọn bác sĩ có ít ca hơn để cân bằng tải
    assert chosen.doctor_id == "D2"

