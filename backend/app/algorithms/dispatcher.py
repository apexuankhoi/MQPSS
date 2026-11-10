"""
Dispatcher & Resource Allocation with Preemption and Load Balancing
Allocates emergency department doctors/beds to queued patients.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
from backend.app.models.schemas import Doctor, Patient, DoctorStatus, PatientStatus, ESILevel
from backend.app.algorithms.queues import (
    PreemptivePriorityQueue, ScoredPriorityQueue, RoundRobinQueue, FCFSQueue
)

class HospitalDispatcher:
    def __init__(self, doctors: List[Doctor]):
        self.doctors: Dict[str, Doctor] = {d.doctor_id: d for d in doctors}
        # Lưu các ca bị preempt (tạm dừng) để tiếp tục sau
        self.preempted_patients: Dict[str, Patient] = {}

    def get_available_doctor(self) -> Optional[Doctor]:
        """
        Load Balancing: Chọn bác sĩ đang RẢNH có số ca đã khám ít nhất (Least-Loaded)
        """
        available = [d for d in self.doctors.values() if d.status == DoctorStatus.AVAILABLE]
        if not available:
            return None
        # Sắp xếp theo số ca đã xử lý tăng dần, sau đó theo tổng thời gian khám
        available.sort(key=lambda d: (d.patients_treated_count, d.total_treatment_minutes))
        return available[0]

    def dispatch_next_patient(
        self,
        q1: PreemptivePriorityQueue,
        q2: ScoredPriorityQueue,
        q3: RoundRobinQueue,
        q4: FCFSQueue,
        target_doctor: Optional[Doctor] = None
    ) -> Optional[Tuple[Doctor, Patient]]:
        """
        Điều phối bệnh nhân tiếp theo theo thứ tự ưu tiên tuyệt đối:
        Queue 1 > Queue 2 > Queue 3 > Queue 4
        """
        doc = target_doctor or self.get_available_doctor()
        if not doc:
            return None

        # 1. Quét Queue 1 (Ưu tiên tuyệt đối)
        patient = q1.dequeue()
        if not patient:
            # 2. Quét Queue 2
            patient = q2.dequeue()
        if not patient:
            # 3. Quét Queue 3
            patient = q3.dequeue()
        if not patient:
            # 4. Quét Queue 4
            patient = q4.dequeue()

        if not patient:
            return None

        # Gán ca cho bác sĩ
        doc.status = DoctorStatus.BUSY
        doc.current_patient_id = patient.patient_id
        
        patient.status = PatientStatus.IN_TREATMENT
        patient.assigned_doctor_id = doc.doctor_id
        patient.treatment_start_time = datetime.now()

        return doc, patient

    def handle_preemption_for_esi1(
        self,
        esi1_patient: Patient,
        q3: RoundRobinQueue,
        q4: FCFSQueue,
        active_treatments: Dict[str, Patient]
    ) -> Tuple[Doctor, Optional[Patient]]:
        """
        Cơ chế ngắt quyền (Preemption) khi có ca ESI-1 nguy kịch:
        Nếu không còn bác sĩ rảnh, tạm ngắt bác sĩ đang điều trị ca nhẹ nhất (Queue 4 hoặc 3)
        để ưu tiên cấp cứu tức thì.
        """
        # Nếu có bác sĩ rảnh -> nhận ngay không cần ngắt
        avail = self.get_available_doctor()
        if avail:
            avail.status = DoctorStatus.BUSY
            avail.current_patient_id = esi1_patient.patient_id
            esi1_patient.status = PatientStatus.IN_TREATMENT
            esi1_patient.assigned_doctor_id = avail.doctor_id
            esi1_patient.treatment_start_time = datetime.now()
            return avail, None

        # Không còn bác sĩ rảnh: Tìm bác sĩ đang khám ca có ESI nhẹ nhất (ưu tiên ngắt ca ESI-4, sau đó ESI-3)
        preemptable_candidates = []
        for doc_id, doc in self.doctors.items():
            if doc.status == DoctorStatus.BUSY and doc.current_patient_id:
                p = active_treatments.get(doc.current_patient_id)
                if p and p.current_esi in (ESILevel.LEVEL_4, ESILevel.LEVEL_3):
                    preemptable_candidates.append((p.current_esi.value, doc, p))

        if preemptable_candidates:
            # Sắp xếp để ngắt ca nhẹ nhất (ESI value lớn nhất: ESI-4 > ESI-3)
            preemptable_candidates.sort(key=lambda x: -x[0])
            _, target_doc, preempted_patient = preemptable_candidates[0]

            # Ngắt ca nhẹ: Đưa trở lại đầu hàng đợi tương ứng
            preempted_patient.status = PatientStatus.WAITING
            preempted_patient.assigned_doctor_id = None
            if preempted_patient.current_esi == ESILevel.LEVEL_4:
                q4._list.insert(0, preempted_patient)
            else:
                q3._deque.appendleft(preempted_patient)

            # Gán bác sĩ vừa ngắt cho ca ESI-1
            target_doc.current_patient_id = esi1_patient.patient_id
            esi1_patient.status = PatientStatus.IN_TREATMENT
            esi1_patient.assigned_doctor_id = target_doc.doctor_id
            esi1_patient.treatment_start_time = datetime.now()

            return target_doc, preempted_patient

        # Trường hợp ngoại lệ: Tất cả bác sĩ đều đang xử lý ca ESI-1 hoặc ESI-2 -> Không ngắt, chờ slot gần nhất
        first_doc = list(self.doctors.values())[0]
        return first_doc, None

