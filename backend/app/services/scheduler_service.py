"""
Central Scheduler Service for Hospital Emergency Department
Coordinates Queues, Aging, Dispatcher, and Triage Engine
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from backend.app.models.schemas import (
    Patient, Doctor, PatientIntakeRequest, ESILevel,
    DoctorStatus, PatientStatus, QueueStats, TriageOverrideRequest
)
from backend.app.algorithms.queues import (
    PreemptivePriorityQueue, ScoredPriorityQueue,
    RoundRobinQueue, FCFSQueue, OutpatientDiversionQueue
)
from backend.app.algorithms.dispatcher import HospitalDispatcher
from backend.app.algorithms.aging import run_dynamic_aging_cycle
from backend.app.core.priority_math import compute_overall_priority_score
from backend.app.services.triage_service import triage_service

class SchedulerService:
    def __init__(self, num_doctors: int = 5):
        # 5 Hàng đợi độc lập
        self.q1 = PreemptivePriorityQueue()
        self.q2 = ScoredPriorityQueue()
        self.q3 = RoundRobinQueue()
        self.q4 = FCFSQueue()
        self.q5 = OutpatientDiversionQueue()

        # Danh sách bệnh nhân đang được điều trị và đang ở cận lâm sàng
        self.active_treatments: Dict[str, Patient] = {}
        self.lab_wait_patients: Dict[str, Patient] = {}
        self.discharged_patients: List[Patient] = []
        self.all_patients_index: Dict[str, Patient] = {}

        # Khởi tạo bác sĩ kíp trực cấp cứu
        initial_doctors = [
            Doctor(doctor_id="BS-01", full_name="BS.CKI Nguyễn Quốc Hưng", specialty="Cấp cứu tim mạch"),
            Doctor(doctor_id="BS-02", full_name="ThS.BS Trần Mai Phương", specialty="Cấp cứu thần kinh"),
            Doctor(doctor_id="BS-03", full_name="BS. Lê Minh Tuấn", specialty="Hồi sức cấp cứu"),
            Doctor(doctor_id="BS-04", full_name="BS. Phạm Thu Thảo", specialty="Chấn thương chỉnh hình"),
            Doctor(doctor_id="BS-05", full_name="BS. Đỗ Quang Huy", specialty="Cấp cứu nhi khoa")
        ]
        self.dispatcher = HospitalDispatcher(initial_doctors[:num_doctors])

    def get_patient(self, patient_id: str) -> Optional[Patient]:
        """Tra cứu chi tiết bệnh nhân theo mã ID"""
        return self.all_patients_index.get(patient_id)

    def reset_system(self):
        """Khởi tạo lại toàn bộ trạng thái hệ thống"""
        self.q1._items.clear()
        self.q2._heap.clear()
        self.q3._deque.clear()
        self.q4._list.clear()
        self.q5._diverted.clear()
        self.active_treatments.clear()
        self.lab_wait_patients.clear()
        self.discharged_patients.clear()
        self.all_patients_index.clear()
        for doc in self.dispatcher.doctors.values():
            doc.status = DoctorStatus.AVAILABLE
            doc.current_patient_id = None
            doc.patients_treated_count = 0
            doc.total_treatment_minutes = 0.0

    def admit_patient(self, req: PatientIntakeRequest) -> Patient:
        """Tiếp đón bệnh nhân, phân loại ESI và đưa vào hàng đợi tương ứng"""
        triage_res = triage_service.classify_patient(req)
        
        # Tính điểm ưu tiên ban đầu
        initial_score = compute_overall_priority_score(
            esi_level=triage_res.esi_level,
            waiting_minutes=0.0,
            vitals=req.vitals,
            consciousness=req.consciousness,
            age=req.age,
            comorbidities=req.comorbidities
        )

        patient = Patient(
            patient_id=req.patient_id,
            full_name=req.full_name,
            age=req.age,
            gender=req.gender,
            is_pregnant=req.is_pregnant,
            chief_complaint=req.chief_complaint,
            consciousness=req.consciousness,
            vitals=req.vitals,
            comorbidities=req.comorbidities,
            original_esi=triage_res.esi_level,
            current_esi=triage_res.esi_level,
            triage_info=triage_res,
            arrival_time=datetime.now(),
            current_queue=triage_res.esi_level.value,
            status=PatientStatus.WAITING,
            waiting_time_minutes=0.0,
            priority_score=initial_score,
            estimated_burst_time_minutes=req.estimated_burst_time_minutes
        )

        self.all_patients_index[patient.patient_id] = patient

        # Đưa vào hàng đợi phù hợp
        if patient.current_esi == ESILevel.LEVEL_1:
            # Ca ESI-1: Kiểm tra Preemption ngay lập tức
            doc, preempted = self.dispatcher.handle_preemption_for_esi1(
                esi1_patient=patient,
                q3=self.q3,
                q4=self.q4,
                active_treatments=self.active_treatments
            )
            self.active_treatments[patient.patient_id] = patient
            if preempted and preempted.patient_id in self.active_treatments:
                del self.active_treatments[preempted.patient_id]
        elif patient.current_esi == ESILevel.LEVEL_2:
            self.q2.enqueue(patient)
        elif patient.current_esi == ESILevel.LEVEL_3:
            self.q3.enqueue(patient)
        elif patient.current_esi == ESILevel.LEVEL_4:
            self.q4.enqueue(patient)
        else: # LEVEL_5
            self.q5.enqueue(patient)

        return patient

    def call_next_patient(self, doctor_id: str) -> Optional[Patient]:
        """Bác sĩ bấm 'Tiếp nhận bệnh nhân kế tiếp'"""
        doc = self.dispatcher.doctors.get(doctor_id)
        if not doc:
            return None

        # Nếu bác sĩ đang bận ca cũ, không cho nhận thêm
        if doc.status == DoctorStatus.BUSY and doc.current_patient_id:
            return None

        dispatched = self.dispatcher.dispatch_next_patient(
            q1=self.q1,
            q2=self.q2,
            q3=self.q3,
            q4=self.q4,
            target_doctor=doc
        )
        if dispatched:
            _, patient = dispatched
            self.active_treatments[patient.patient_id] = patient
            return patient
        return None

    def finish_treatment(self, patient_id: str) -> Optional[Patient]:
        """Bác sĩ hoàn tất điều trị ca bệnh"""
        patient = self.active_treatments.get(patient_id)
        if not patient:
            return None

        patient.status = PatientStatus.DISCHARGED
        patient.treatment_end_time = datetime.now()
        
        # Giải phóng bác sĩ
        if patient.assigned_doctor_id:
            doc = self.dispatcher.doctors.get(patient.assigned_doctor_id)
            if doc:
                doc.status = DoctorStatus.AVAILABLE
                doc.current_patient_id = None
                doc.patients_treated_count += 1
                if patient.treatment_start_time:
                    dur = (patient.treatment_end_time - patient.treatment_start_time).total_seconds() / 60.0
                    doc.total_treatment_minutes += dur

        del self.active_treatments[patient_id]
        self.discharged_patients.append(patient)
        return patient

    def send_to_lab(self, patient_id: str) -> Optional[Patient]:
        """Chuyển bệnh nhân sang chờ cận lâm sàng (I/O Wait), giải phóng bác sĩ"""
        patient = self.active_treatments.get(patient_id)
        if not patient:
            return None

        patient.status = PatientStatus.LAB_WAIT
        
        # Giải phóng bác sĩ để nhận ca khác trong lúc chờ kết quả
        if patient.assigned_doctor_id:
            doc = self.dispatcher.doctors.get(patient.assigned_doctor_id)
            if doc:
                doc.status = DoctorStatus.AVAILABLE
                doc.current_patient_id = None

        del self.active_treatments[patient_id]
        self.lab_wait_patients[patient_id] = patient
        return patient

    def return_from_lab(self, patient_id: str) -> Optional[Patient]:
        """Bệnh nhân có kết quả cận lâm sàng, trở lại hàng chờ khám"""
        patient = self.lab_wait_patients.get(patient_id)
        if not patient:
            return None

        patient.status = PatientStatus.WAITING
        del self.lab_wait_patients[patient_id]

        # Ca đã có kết quả cận lâm sàng được đưa vào Hàng đợi 2 (Ưu tiên đọc kết quả)
        patient.current_esi = ESILevel.LEVEL_2
        self.q2.enqueue(patient)
        return patient

    def run_aging(self, current_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Thực thi chu kỳ Dynamic Aging chống Starvation"""
        t = current_time or datetime.now()
        promotions = run_dynamic_aging_cycle(self.q4, self.q3, self.q2, t)
        return promotions

    def get_snapshot(self) -> Dict[str, Any]:
        """Lấy toàn bộ trạng thái hiện tại của hệ thống"""
        now = datetime.now()
        # Cập nhật thời gian chờ
        for q in [self.q1, self.q2, self.q3, self.q4]:
            for p in q.get_all():
                p.waiting_time_minutes = round((now - p.arrival_time).total_seconds() / 60.0, 1)

        return {
            "queue_1": [p.model_dump() for p in self.q1.get_all()],
            "queue_2": [p.model_dump() for p in self.q2.get_all()],
            "queue_3": [p.model_dump() for p in self.q3.get_all()],
            "queue_4": [p.model_dump() for p in self.q4.get_all()],
            "queue_5": [p.model_dump() for p in self.q5.get_all()],
            "active_treatments": [p.model_dump() for p in self.active_treatments.values()],
            "lab_wait": [p.model_dump() for p in self.lab_wait_patients.values()],
            "doctors": [d.model_dump() for d in self.dispatcher.doctors.values()],
            "stats": self.get_stats().model_dump(),
            "timestamp": now.isoformat()
        }

    def get_stats(self) -> QueueStats:
        now = datetime.now()
        all_waiting = (
            self.q1.get_all() + self.q2.get_all() +
            self.q3.get_all() + self.q4.get_all()
        )
        total_wait_mins = sum((now - p.arrival_time).total_seconds() / 60.0 for p in all_waiting)
        avg_wait = total_wait_mins / len(all_waiting) if all_waiting else 0.0

        # Đếm các ca nguy cơ starvation: ESI-3 chờ > 40p hoặc ESI-4 chờ > 80p
        starvation_count = sum(
            1 for p in all_waiting
            if (p.current_esi == ESILevel.LEVEL_3 and (now - p.arrival_time).total_seconds() / 60.0 > 40) or
               (p.current_esi == ESILevel.LEVEL_4 and (now - p.arrival_time).total_seconds() / 60.0 > 80)
        )

        active_docs = sum(1 for d in self.dispatcher.doctors.values() if d.status == DoctorStatus.BUSY)

        return QueueStats(
            queue_1_count=len(self.q1),
            queue_2_count=len(self.q2),
            queue_3_count=len(self.q3),
            queue_4_count=len(self.q4),
            queue_5_count=len(self.q5),
            total_waiting=len(all_waiting),
            active_doctors=active_docs,
            avg_waiting_time_minutes=round(avg_wait, 1),
            starvation_risk_count=starvation_count
        )

    def fast_forward_time(self, minutes: float = 30.0) -> List[Dict[str, Any]]:
        """Tua nhanh thời gian chờ của toàn bộ bệnh nhân để kiểm thử Dynamic Aging"""
        from datetime import timedelta
        delta = timedelta(minutes=minutes)
        for q in [self.q1, self.q2, self.q3, self.q4, self.q5]:
            for p in q.get_all():
                p.arrival_time -= delta
                p.waiting_time_minutes += minutes
        # Sau khi tua, tự động kích hoạt aging cycle
        promotions = self.run_aging()
        return promotions

    def trigger_mass_casualty_incident(self) -> List[Patient]:
        """Mô phỏng thảm họa hàng loạt (Mass Casualty Incident - MCI) để kiểm thử quá tải và ngắt tài nguyên"""
        import random
        from backend.app.models.schemas import PatientIntakeRequest, VitalSigns, AVPUConsciousness
        
        mci_cases = [
            PatientIntakeRequest(
                patient_id=f"MCI-{random.randint(100, 999)}",
                full_name="Nạn Nhân TNGT 01 (Sốc Chấn Thương)",
                age=26, gender="male",
                consciousness=AVPUConsciousness.PAIN,
                chief_complaint="Đa chấn thương do tai nạn liên hoàn, vỡ xương chậu, sốc mất máu",
                vitals=VitalSigns(heart_rate=145, systolic_bp=70, diastolic_bp=40, respiratory_rate=32, spo2=87.0, temperature=35.9, pain_scale=9),
                comorbidities=[]
            ),
            PatientIntakeRequest(
                patient_id=f"MCI-{random.randint(100, 999)}",
                full_name="Nạn Nhân TNGT 02 (Ngưng Thở)",
                age=52, gender="female",
                consciousness=AVPUConsciousness.UNRESPONSIVE,
                chief_complaint="Hôn mê sâu, chấn thương sọ não hở, ngưng thở gián đoạn",
                vitals=VitalSigns(heart_rate=38, systolic_bp=50, diastolic_bp=25, respiratory_rate=4, spo2=58.0, temperature=35.2, pain_scale=0),
                comorbidities=["tang_huyet_ap"]
            ),
            PatientIntakeRequest(
                patient_id=f"MCI-{random.randint(100, 999)}",
                full_name="Nạn Nhân TNGT 03 (Tràn Khí Màng Phổi)",
                age=34, gender="male",
                consciousness=AVPUConsciousness.ALERT,
                chief_complaint="Khó thở tím tái, chấn thương ngực kín, tràn khí màng phổi áp lực",
                vitals=VitalSigns(heart_rate=130, systolic_bp=100, diastolic_bp=60, respiratory_rate=36, spo2=83.0, temperature=37.0, pain_scale=8),
                comorbidities=[]
            ),
            PatientIntakeRequest(
                patient_id=f"MCI-{random.randint(100, 999)}",
                full_name="Nạn Nhân TNGT 04 (Vết Thương Rách)",
                age=21, gender="male",
                consciousness=AVPUConsciousness.ALERT,
                chief_complaint="Rách da đầu và cẳng tay chảy máu, xây xát nhiều nơi",
                vitals=VitalSigns(heart_rate=86, systolic_bp=118, diastolic_bp=76, respiratory_rate=18, spo2=99.0, temperature=36.8, pain_scale=5),
                comorbidities=[]
            )
        ]
        admitted = []
        for case in mci_cases:
            p = self.admit_patient(case)
            admitted.append(p)
        return admitted

scheduler_service = SchedulerService()

