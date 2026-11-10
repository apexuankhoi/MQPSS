"""
Multilevel Queue Scheduling Algorithms for Hospital Emergency Department
Implements 5 Distinct Queues conforming to OS Scheduling Theory
"""

import heapq
from collections import deque
from typing import List, Optional
from datetime import datetime
from backend.app.models.schemas import Patient, ESILevel, PatientStatus

class BaseQueue:
    """Interface cơ sở cho các tầng hàng đợi"""
    def __init__(self, queue_id: int, name: str):
        self.queue_id = queue_id
        self.name = name

    def enqueue(self, patient: Patient) -> None:
        raise NotImplementedError

    def dequeue(self) -> Optional[Patient]:
        raise NotImplementedError

    def peek(self) -> Optional[Patient]:
        raise NotImplementedError

    def remove(self, patient_id: str) -> Optional[Patient]:
        raise NotImplementedError

    def get_all(self) -> List[Patient]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError


class PreemptivePriorityQueue(BaseQueue):
    """
    HÀNG ĐỢI 1 (ESI-1: Đỏ - Nguy kịch tức thì)
    Thuật toán: Preemptive Priority với FCFS nội bộ
    Đặc điểm: Luôn được phục vụ trước mọi hàng đợi khác, có quyền ngắt (preempt) tài nguyên bác sĩ
    """
    def __init__(self):
        super().__init__(1, "Queue 1: ESI-1 Preemptive Priority")
        self._items: List[Patient] = []

    def enqueue(self, patient: Patient) -> None:
        patient.current_queue = 1
        patient.current_esi = ESILevel.LEVEL_1
        self._items.append(patient)

    def dequeue(self) -> Optional[Patient]:
        if not self._items:
            return None
        return self._items.pop(0) # FCFS cho các ca ESI-1 cùng lúc

    def peek(self) -> Optional[Patient]:
        return self._items[0] if self._items else None

    def remove(self, patient_id: str) -> Optional[Patient]:
        for i, p in enumerate(self._items):
            if p.patient_id == patient_id:
                return self._items.pop(i)
        return None

    def get_all(self) -> List[Patient]:
        return list(self._items)

    def __len__(self) -> int:
        return len(self._items)


class ScoredPriorityQueue(BaseQueue):
    """
    HÀNG ĐỢI 2 (ESI-2: Cam - Rất cấp, chờ < 15 phút)
    Thuật toán: Priority Scheduling dùng Max-Heap dựa trên `priority_score`
    Bệnh nhân có điểm ưu tiên cao nhất luôn được đưa lên đầu hàng đợi.
    """
    def __init__(self):
        super().__init__(2, "Queue 2: ESI-2 Priority Heap")
        self._heap: List[tuple[float, int, Patient]] = []
        self._counter: int = 0  # Tie-breaker khi điểm số bằng nhau

    def enqueue(self, patient: Patient) -> None:
        patient.current_queue = 2
        patient.current_esi = ESILevel.LEVEL_2
        self._counter += 1
        # Python heapq là min-heap -> Lưu -priority_score để thành max-heap
        heapq.heappush(self._heap, (-patient.priority_score, self._counter, patient))

    def dequeue(self) -> Optional[Patient]:
        if not self._heap:
            return None
        _, _, patient = heapq.heappop(self._heap)
        return patient

    def peek(self) -> Optional[Patient]:
        return self._heap[0][2] if self._heap else None

    def remove(self, patient_id: str) -> Optional[Patient]:
        for i, (_, _, p) in enumerate(self._heap):
            if p.patient_id == patient_id:
                item = self._heap.pop(i)
                heapq.heapify(self._heap)
                return item[2]
        return None

    def re_heapify(self) -> None:
        """Cập nhật lại heap sau khi điểm số priority_score thay đổi"""
        current_patients = [p for _, _, p in self._heap]
        self._heap.clear()
        for p in current_patients:
            self._counter += 1
            heapq.heappush(self._heap, (-p.priority_score, self._counter, p))

    def get_all(self) -> List[Patient]:
        # Trả về danh sách sắp xếp theo thứ tự ưu tiên giảm dần
        sorted_items = sorted(self._heap, key=lambda x: x[0])
        return [p for _, _, p in sorted_items]

    def __len__(self) -> int:
        return len(self._heap)


class RoundRobinQueue(BaseQueue):
    """
    HÀNG ĐỢI 3 (ESI-3: Vàng - Cấp tính, chờ < 60 phút)
    Thuật toán: Round Robin (RR) với Time Quantum = 30 phút
    Phù hợp cho các ca cần đa xét nghiệm / chẩn đoán hình ảnh:
    Sau 1 quantum khám sơ bộ, bệnh nhân ra chờ cận lâm sàng rồi quay lại nhận lát thời gian tiếp.
    """
    def __init__(self, quantum_minutes: float = 30.0):
        super().__init__(3, "Queue 3: ESI-3 Round Robin")
        self.quantum_minutes = quantum_minutes
        self._deque: deque[Patient] = deque()

    def enqueue(self, patient: Patient) -> None:
        patient.current_queue = 3
        patient.current_esi = ESILevel.LEVEL_3
        self._deque.append(patient)

    def dequeue(self) -> Optional[Patient]:
        if not self._deque:
            return None
        return self._deque.popleft()

    def peek(self) -> Optional[Patient]:
        return self._deque[0] if self._deque else None

    def remove(self, patient_id: str) -> Optional[Patient]:
        for p in self._deque:
            if p.patient_id == patient_id:
                self._deque.remove(p)
                return p
        return None

    def get_all(self) -> List[Patient]:
        return list(self._deque)

    def __len__(self) -> int:
        return len(self._deque)


class FCFSQueue(BaseQueue):
    """
    HÀNG ĐỢI 4 (ESI-4: Xanh lá - Ít cấp, chờ < 120 phút)
    Thuật toán: First Come First Served (FCFS)
    Đến trước phục vụ trước nghiêm ngặt theo thời điểm tiếp nhận.
    """
    def __init__(self):
        super().__init__(4, "Queue 4: ESI-4 First Come First Served")
        self._list: List[Patient] = []

    def enqueue(self, patient: Patient) -> None:
        patient.current_queue = 4
        patient.current_esi = ESILevel.LEVEL_4
        self._list.append(patient)

    def dequeue(self) -> Optional[Patient]:
        if not self._list:
            return None
        return self._list.pop(0)

    def peek(self) -> Optional[Patient]:
        return self._list[0] if self._list else None

    def remove(self, patient_id: str) -> Optional[Patient]:
        for i, p in enumerate(self._list):
            if p.patient_id == patient_id:
                return self._list.pop(i)
        return None

    def get_all(self) -> List[Patient]:
        return list(self._list)

    def __len__(self) -> int:
        return len(self._list)


class OutpatientDiversionQueue(BaseQueue):
    """
    HÀNG ĐỢI 5 (ESI-5: Trắng/Ghi - Không cấp tính)
    Thuật toán: Chuyển tuyến điều phối (Diversion) sang phòng khám ngoại trú
    Không chiếm tài nguyên giường/bác sĩ của khoa Cấp cứu.
    """
    def __init__(self):
        super().__init__(5, "Queue 5: ESI-5 Outpatient Diversion")
        self._diverted: List[Patient] = []

    def enqueue(self, patient: Patient) -> None:
        patient.current_queue = 5
        patient.current_esi = ESILevel.LEVEL_5
        patient.status = PatientStatus.TRANSFERRED
        self._diverted.append(patient)

    def dequeue(self) -> Optional[Patient]:
        if not self._diverted:
            return None
        return self._diverted.pop(0)

    def peek(self) -> Optional[Patient]:
        return self._diverted[0] if self._diverted else None

    def remove(self, patient_id: str) -> Optional[Patient]:
        for i, p in enumerate(self._diverted):
            if p.patient_id == patient_id:
                return self._diverted.pop(i)
        return None

    def get_all(self) -> List[Patient]:
        return list(self._diverted)

    def __len__(self) -> int:
        return len(self._diverted)

