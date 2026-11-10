"""
Dynamic Aging Algorithm for Multilevel Queue (Anti-Starvation Mechanism)
Automatically escalates waiting patients to higher priority queues when thresholds expire.
"""

from datetime import datetime
from typing import List, Dict, Any
from backend.app.algorithms.queues import (
    ScoredPriorityQueue, RoundRobinQueue, FCFSQueue
)
from backend.app.core.config import settings
from backend.app.core.priority_math import compute_overall_priority_score
from backend.app.models.schemas import ESILevel

def run_dynamic_aging_cycle(
    q4: FCFSQueue,
    q3: RoundRobinQueue,
    q2: ScoredPriorityQueue,
    current_time: datetime,
    thresholds = settings.AGING
) -> List[Dict[str, Any]]:
    """
    Quét toàn bộ hàng đợi cấp 4 và 3 để thăng cấp tự động (Dynamic Aging)
    Trả về danh sách các sự kiện thăng hạng để gửi broadcast WebSocket.
    """
    promotions: List[Dict[str, Any]] = []
    promoted_patient_ids = set()

    # 1. Quét Hàng đợi 4 (ESI-4 -> ESI-3)
    # Ngưỡng: chờ quá 90 phút (hoặc cấu hình)
    q4_patients = q4.get_all()
    for p in q4_patients:
        wait_mins = (current_time - p.arrival_time).total_seconds() / 60.0
        p.waiting_time_minutes = round(wait_mins, 2)
        
        if wait_mins >= thresholds.esi4_to_esi3_minutes:
            removed = q4.remove(p.patient_id)
            if removed:
                removed.aged_count += 1
                removed.current_esi = ESILevel.LEVEL_3
                # Tính lại điểm ưu tiên mới
                removed.priority_score = compute_overall_priority_score(
                    esi_level=ESILevel.LEVEL_3,
                    waiting_minutes=wait_mins,
                    vitals=removed.vitals,
                    consciousness=removed.consciousness,
                    age=removed.age,
                    comorbidities=removed.comorbidities
                )
                q3.enqueue(removed)
                promoted_patient_ids.add(removed.patient_id)
                promotions.append({
                    "patient_id": removed.patient_id,
                    "patient_name": removed.full_name,
                    "from_queue": 4,
                    "to_queue": 3,
                    "wait_minutes": round(wait_mins, 1),
                    "reason": f"Chờ {round(wait_mins, 1)} phút (vượt ngưỡng {thresholds.esi4_to_esi3_minutes}p) -> Thăng hạng lên ESI-3"
                })

    # 2. Quét Hàng đợi 3 (ESI-3 -> ESI-2)
    # Ngưỡng: chờ quá 45 phút (hoặc cấu hình)
    # Lưu ý: Không thăng hạng kép cho bệnh nhân vừa được nâng từ Q4 lên Q3 trong cùng chu kỳ
    q3_patients = q3.get_all()
    for p in q3_patients:
        if p.patient_id in promoted_patient_ids:
            continue

        wait_mins = (current_time - p.arrival_time).total_seconds() / 60.0
        p.waiting_time_minutes = round(wait_mins, 2)
        
        if wait_mins >= thresholds.esi3_to_esi2_minutes:
            removed = q3.remove(p.patient_id)
            if removed:
                removed.aged_count += 1
                removed.current_esi = ESILevel.LEVEL_2
                # Tính lại điểm ưu tiên mới
                removed.priority_score = compute_overall_priority_score(
                    esi_level=ESILevel.LEVEL_2,
                    waiting_minutes=wait_mins,
                    vitals=removed.vitals,
                    consciousness=removed.consciousness,
                    age=removed.age,
                    comorbidities=removed.comorbidities
                )
                q2.enqueue(removed)
                promoted_patient_ids.add(removed.patient_id)
                promotions.append({
                    "patient_id": removed.patient_id,
                    "patient_name": removed.full_name,
                    "from_queue": 3,
                    "to_queue": 2,
                    "wait_minutes": round(wait_mins, 1),
                    "reason": f"Chờ {round(wait_mins, 1)} phút (vượt ngưỡng {thresholds.esi3_to_esi2_minutes}p) -> Thăng hạng lên ESI-2 (Cấp cứu khẩn)"
                })

    # 3. Cập nhật thời gian chờ và re-heapify Hàng đợi 2
    q2_patients = q2.get_all()
    for p in q2_patients:
        wait_mins = (current_time - p.arrival_time).total_seconds() / 60.0
        p.waiting_time_minutes = round(wait_mins, 2)
        p.priority_score = compute_overall_priority_score(
            esi_level=ESILevel.LEVEL_2,
            waiting_minutes=wait_mins,
            vitals=p.vitals,
            consciousness=p.consciousness,
            age=p.age,
            comorbidities=p.comorbidities
        )
    q2.re_heapify()

    return promotions
