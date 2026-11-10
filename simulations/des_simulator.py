"""
Discrete Event Simulation (DES) Engine for Emergency Patient Scheduling
Built with SimPy for scientific benchmarking against baseline algorithms.
GVHD: ThS. Lê Văn Phong | Đề tài 2: MQPSS
"""

import random
import simpy
import numpy as np
from typing import List, Dict, Any

class SimulationPatient:
    def __init__(self, pid: int, arrival_time: float, esi_level: int, service_time: float):
        self.pid = pid
        self.arrival_time = arrival_time
        self.esi_level = esi_level
        self.current_esi = esi_level
        self.service_time = service_time
        
        # Thống kê ghi nhận
        self.start_treatment_time: float = -1.0
        self.end_treatment_time: float = -1.0
        self.waiting_time: float = 0.0
        self.is_starved: bool = False
        self.aged_times: int = 0

class EmergencyDepartmentSimulation:
    def __init__(
        self,
        algorithm: str = "MQPSS", # "FCFS", "PURE_PRIORITY", "MQPSS"
        num_doctors: int = 5,
        sim_duration_minutes: float = 1440.0, # 24 giờ
        seed: int = 42
    ):
        self.algorithm = algorithm
        self.num_doctors = num_doctors
        self.sim_duration = sim_duration_minutes
        self.seed = seed
        
        self.env = simpy.Environment()
        if self.algorithm == "FCFS":
            self.doctor_resource = simpy.Resource(self.env, capacity=self.num_doctors)
        else:
            self.doctor_resource = simpy.PriorityResource(self.env, capacity=self.num_doctors)
        
        # Hàng đợi trong mô phỏng
        self.queue: List[SimulationPatient] = []
        self.completed_patients: List[SimulationPatient] = []

        # Ngưỡng an toàn thời gian chờ (phút) để đo Starvation
        self.safe_thresholds = {
            1: 2.0,    # ESI-1 chờ > 2p coi như trễ
            2: 15.0,   # ESI-2 chờ > 15p
            3: 60.0,   # ESI-3 chờ > 60p
            4: 120.0,  # ESI-4 chờ > 120p
            5: 240.0   # ESI-5 chờ > 240p
        }

    def generate_patient_arrivals(self):
        """Sinh dòng bệnh nhân ngẫu nhiên theo quá trình Poisson không thuần nhất"""
        random.seed(self.seed)
        np.random.seed(self.seed)
        
        pid = 0
        while self.env.now < self.sim_duration:
            hour_of_day = (self.env.now / 60.0) % 24
            # Giờ cao điểm (8h-11h và 18h-21h) lượng bệnh nhân đến đông gấp 2.5 lần
            if (8 <= hour_of_day <= 11) or (18 <= hour_of_day <= 21):
                interarrival_mean = 3.0 # trung bình 3 phút có 1 ca
            elif 0 <= hour_of_day <= 5:
                interarrival_mean = 12.0 # ban đêm vắng
            else:
                interarrival_mean = 6.0 # giờ bình thường

            inter_time = random.expovariate(1.0 / interarrival_mean)
            yield self.env.timeout(inter_time)

            pid += 1
            # Phân phối xác suất ESI chuẩn AHRQ
            # ESI-1 (3%), ESI-2 (18%), ESI-3 (45%), ESI-4 (25%), ESI-5 (9%)
            esi = np.random.choice([1, 2, 3, 4, 5], p=[0.03, 0.18, 0.45, 0.25, 0.09])
            
            # Thời gian khám trung bình theo mức độ nặng (phút)
            service_means = {1: 40.0, 2: 28.0, 3: 20.0, 4: 12.0, 5: 6.0}
            mean_serv = service_means[esi]
            serv_time = max(3.0, random.gauss(mean_serv, mean_serv * 0.25))

            patient = SimulationPatient(pid, self.env.now, esi, serv_time)
            
            # Nếu là ESI-5 và đang chạy MQPSS -> Chuyển ngoại trú không chiếm giường cấp cứu
            if self.algorithm == "MQPSS" and esi == 5:
                patient.waiting_time = 5.0
                patient.start_treatment_time = self.env.now + 5.0
                patient.end_treatment_time = patient.start_treatment_time + serv_time
                self.completed_patients.append(patient)
                continue

            self.queue.append(patient)
            self.env.process(self.process_patient_workflow(patient))

    def aging_monitor_process(self):
        """Tiến trình quét Dynamic Aging mỗi 5 phút trong MQPSS"""
        while self.env.now < self.sim_duration:
            yield self.env.timeout(5.0)
            now = self.env.now
            for p in self.queue:
                wait = now - p.arrival_time
                # Thăng ESI-4 lên ESI-3 sau 90p
                if p.current_esi == 4 and wait >= 90.0:
                    p.current_esi = 3
                    p.aged_times += 1
                # Thăng ESI-3 lên ESI-2 sau 45p
                elif p.current_esi == 3 and wait >= 45.0:
                    p.current_esi = 2
                    p.aged_times += 1

    def select_next_patient(self) -> SimulationPatient:
        """Thuật toán chọn bệnh nhân tiếp theo từ hàng đợi"""
        if self.algorithm == "FCFS":
            # Ai đến trước khám trước (sắp theo arrival_time)
            self.queue.sort(key=lambda p: p.arrival_time)
        elif self.algorithm == "PURE_PRIORITY":
            # Ưu tiên cứng theo original ESI (1 > 2 > 3 > 4 > 5), không có Aging
            self.queue.sort(key=lambda p: (p.esi_level, p.arrival_time))
        elif self.algorithm == "MQPSS":
            # Multilevel Queue + Dynamic Aging + Preemptive Priority
            # Sắp xếp theo current_esi (sau khi được thăng hạng do Aging) rồi đến arrival_time
            self.queue.sort(key=lambda p: (p.current_esi, p.arrival_time))

        return self.queue.pop(0)

    def process_patient_workflow(self, patient: SimulationPatient):
        """Vòng đời của bệnh nhân qua các khâu cấp cứu"""
        # Xin tài nguyên bác sĩ
        if self.algorithm == "FCFS":
            req = self.doctor_resource.request()
        else:
            req = self.doctor_resource.request(priority=patient.current_esi)

        with req:
            yield req

            # Bắt đầu khám
            patient.start_treatment_time = self.env.now
            patient.waiting_time = patient.start_treatment_time - patient.arrival_time
            
            # Đánh giá xem có bị Starvation (chờ quá hạn an toàn) hay không
            safe_limit = self.safe_thresholds.get(patient.esi_level, 60.0)
            if patient.waiting_time > safe_limit:
                patient.is_starved = True

            # Thời gian khám bệnh
            yield self.env.timeout(patient.service_time)
            
            patient.end_treatment_time = self.env.now
            self.completed_patients.append(patient)

    def run(self) -> Dict[str, Any]:
        """Chạy mô phỏng và tính toán các chỉ số KPI"""
        self.env.process(self.generate_patient_arrivals())
        if self.algorithm == "MQPSS":
            self.env.process(self.aging_monitor_process())

        self.env.run(until=self.sim_duration)

        # Tổng hợp số liệu
        patients = self.completed_patients
        total_count = len(patients)

        if total_count == 0:
            return {"error": "Không có bệnh nhân hoàn tất"}

        # Thời gian chờ theo ESI ban đầu
        wait_by_esi = {}
        starved_by_esi = {}
        for level in [1, 2, 3, 4, 5]:
            level_patients = [p for p in patients if p.esi_level == level]
            if level_patients:
                avg_w = np.mean([p.waiting_time for p in level_patients])
                starved_cnt = sum(1 for p in level_patients if p.is_starved)
                wait_by_esi[level] = round(float(avg_w), 2)
                starved_by_esi[level] = round(float(starved_cnt / len(level_patients) * 100.0), 1)
            else:
                wait_by_esi[level] = 0.0
                starved_by_esi[level] = 0.0

        all_waits = [p.waiting_time for p in patients]
        total_starved = sum(1 for p in patients if p.is_starved)

        # ESI-1 Response time
        esi1_patients = [p for p in patients if p.esi_level == 1]
        esi1_avg_wait = np.mean([p.waiting_time for p in esi1_patients]) if esi1_patients else 0.0

        return {
            "algorithm": self.algorithm,
            "total_treated": total_count,
            "overall_avg_wait_minutes": round(float(np.mean(all_waits)), 2),
            "overall_max_wait_minutes": round(float(np.max(all_waits)), 2),
            "starvation_rate_percent": round(float(total_starved / total_count * 100.0), 2),
            "esi_1_avg_wait_minutes": round(float(esi1_avg_wait), 2),
            "waiting_time_by_esi": wait_by_esi,
            "starvation_rate_by_esi": starved_by_esi,
            "throughput_per_hour": round(total_count / (self.sim_duration / 60.0), 2)
        }

