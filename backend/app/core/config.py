"""
Application Configuration & Priority Scheduling Parameters
MQPSS - Multilevel Queue Priority Scheduling System for Emergency Triage
GVHD: ThS. Lê Văn Phong | Năm học: 2026-2027
"""

import os
from pydantic import BaseModel

class PriorityWeights(BaseModel):
    w1_esi: float = 0.35           # Trọng số mức độ nguy kịch ESI
    w2_waiting_time: float = 0.25  # Trọng số thời gian đã chờ
    w3_vitals: float = 0.20        # Trọng số bất thường sinh hiệu
    w4_age: float = 0.10           # Trọng số tuổi ưu tiên (trẻ nhỏ / người già)
    w5_comorbidity: float = 0.10   # Trọng số bệnh lý nền

class AgingThresholds(BaseModel):
    # Ngưỡng thời gian chờ (phút) để thăng hạng (Dynamic Aging)
    esi4_to_esi3_minutes: float = 90.0  # ESI-4 chờ quá 90p -> lên ESI-3
    esi3_to_esi2_minutes: float = 45.0  # ESI-3 chờ quá 45p -> lên ESI-2
    esi2_warning_minutes: float = 15.0  # ESI-2 chờ quá 15p -> Báo động đỏ
    aging_check_interval_seconds: int = 10 # Chu kỳ quét aging trong real-time

class Settings(BaseModel):
    PROJECT_NAME: str = "MQPSS - Hospital Emergency Triage & Multilevel Scheduling"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Priority & Scheduling Config
    WEIGHTS: PriorityWeights = PriorityWeights()
    AGING: AgingThresholds = AgingThresholds()
    
    # Quantum Round Robin cho Hàng đợi 3 (phút)
    RR_QUANTUM_MINUTES: float = 30.0

    # Default Doctor Capacity
    DEFAULT_DOCTORS_COUNT: int = 5

settings = Settings()

