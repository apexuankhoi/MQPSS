# 📅 Tuần 3: Scheduler Core, Backend API & WebSocket Engine

> **Giai đoạn:** Phát triển Toàn diện Backend & Lập lịch Cốt lõi (Core Engine & Backend API)  
> **Thời gian dự kiến:** Tuần 3  
> **Trọng tâm:** Lập trình cấu trúc 5 hàng đợi đa mức (Multilevel Queue), cơ chế Dynamic Aging chống Starvation, bộ điều phối bác sĩ (Dispatcher), và đóng gói thành hệ thống REST API + WebSocket Server sẵn sàng phục vụ Frontend.

---

## 1. 🎯 Mục Tiêu Cốt Lõi (Objectives)
1. Hiện thực hóa chính xác cấu trúc dữ liệu cho **5 hàng đợi độc lập**:
   * **Queue 1 (ESI-1):** Hàng đợi ưu tiên ngắt quyền (Preemptive Priority).
   * **Queue 2 (ESI-2):** Hàng đợi ưu tiên theo điểm số (Priority Queue với Min/Max Heap).
   * **Queue 3 (ESI-3):** Hàng đợi xoay vòng (Round Robin với Time Quantum = 30 phút).
   * **Queue 4 (ESI-4):** Hàng đợi đến trước phục vụ trước (FCFS tiêu chuẩn).
   * **Queue 5 (ESI-5):** Luồng điều hướng chuyển viện ngoại trú.
2. Xây dựng **Background Aging Worker** định kỳ quét hàng đợi để tự động thăng hạng ưu tiên, loại bỏ triệt để hiện tượng đói tài nguyên (**Starvation**).
3. Lập trình bộ điều phối (**Dispatcher & Resource Allocator**) thông minh: phân bổ bệnh nhân cho bác sĩ/phòng khám khả dụng theo tải cân bằng (Load Balancing).
4. Xây dựng toàn bộ hệ thống **RESTful API** và **WebSocket Event Broadcaster** (FastAPI) để cung cấp bộ dữ liệu chuẩn (API Contract / Swagger UI) sẵn sàng cho Tuần 4 thiết kế Frontend.

---

## 2. 🧭 Hướng Đi Chiến Lược (Strategy & Direction)
* **Contract-First Development:** Đóng gói toàn bộ API endpoints và WebSocket message schemas chuẩn (`/docs` Swagger), giúp tầng Frontend ở Tuần 4 có thể tích hợp ngay lập tức hoặc mock dữ liệu mà không bị phụ thuộc luồng code.
* **Tách biệt Core Logic và Web Layer:** Thuật toán Multilevel Queue được đóng gói thành service độc lập, nhận `PatientState` và trả về `SchedulingDecision`, đảm bảo testable 100%.
* **Xử lý bất đồng bộ & An toàn dữ liệu (Async & Thread Safety):** Dùng Mutex Lock để đảm bảo tính atomic khi nhiều bác sĩ cùng gọi lệnh nhận bệnh nhân (dispatch) cùng một thời điểm.

---

## 3. 📋 Danh Sách Công Việc Cần Hoàn Thành (Task Checklist)

### 3.1. Cài Đặt 5 Hàng Đợi & Lõi Thuật Toán (Scheduler Core)
- [ ] Xây dựng lớp `BaseQueue` và các lớp con:
  * `PreemptivePriorityQueue` (Queue 1): Xử lý ca ESI-1 lập tức.
  * `ScoredPriorityQueue` (Queue 2): Dùng `heapq` theo `priority_score`.
  * `RoundRobinQueue` (Queue 3): Dùng `collections.deque` với slice quantum 30 phút.
  * `FCFSQueue` (Queue 4): First Come First Served nghiêm ngặt.
  * `OutpatientDiversionQueue` (Queue 5): Điều hướng chuyển tuyến.
- [ ] Cài đặt logic **Dynamic Aging Worker**: Quét định kỳ (mỗi 60s), tự động thăng hạng ESI-4 $\rightarrow$ ESI-3 sau 90 phút và ESI-3 $\rightarrow$ ESI-2 sau 45 phút.
- [ ] Cài đặt **Dispatcher**: Thuật toán tự động ghép bệnh nhân ưu tiên cao nhất với bác sĩ đang có khối lượng công việc thấp nhất (Least Loaded Doctor).

### 3.2. Xây Dựng Hệ Thống REST API (FastAPI)
- [ ] Module Tiếp nhận & Phân loại:
  * `POST /api/v1/patients/intake`: Nhập sinh hiệu, gọi Triage Engine $\rightarrow$ đưa vào hàng đợi.
  * `POST /api/v1/triage/override`: Ghi đè kết quả phân loại từ y tá.
- [ ] Module Thao tác Hàng đợi:
  * `GET /api/v1/queues`: Lấy snapshot danh sách 5 hàng đợi theo thời gian thực.
  * `GET /api/v1/queues/stats`: Thống kê số lượng bệnh nhân, thời gian chờ trung bình mỗi queue.
- [ ] Module Trạm Bác sĩ:
  * `POST /api/v1/doctors/{id}/call-next`: Lấy bệnh nhân tiếp theo theo thuật toán định thời.
  * `POST /api/v1/patients/{id}/finish`: Hoàn tất ca khám và giải phóng bác sĩ.
  * `POST /api/v1/patients/{id}/send-to-lab`: Đưa bệnh nhân vào trạng thái chờ cận lâm sàng (I/O Wait).

### 3.3. Xây Dựng WebSocket Server
- [ ] Cài đặt `ConnectionManager` quản lý kết nối WebSocket tập trung.
- [ ] Định nghĩa các gói tin phát sóng thời gian thực:
  * `QUEUE_UPDATED`: Khi có ca mới, ca thăng hạng hoặc ca rời hàng chờ.
  * `PATIENT_CALLED`: Khi bác sĩ tiếp nhận bệnh nhân.
  * `EMERGENCY_ALARM`: Báo động đỏ toàn viện khi có ca ESI-1 nhập viện.

### 3.4. Kiểm Thử Backend & API Verification
- [ ] Viết Unit Test & Integration Test cho 5 hàng đợi và API endpoints (`pytest`).
- [ ] Kiểm thử kịch bản Aging: Chờ vượt ngưỡng $\rightarrow$ tự động nhảy queue.
- [ ] Kiểm thử tải và tranh chấp đồng thời (Concurrency Test) với 50 requests gọi nhận bệnh nhân cùng lúc.

---

## 4. 📦 Kết Quả Đầu Ra Nghiệm Thu (Deliverables / DoD)
1. Thư viện lõi `SchedulerEngine` hoạt động chính xác theo đúng lý thuyết Multilevel Queue.
2. Toàn bộ API endpoints RESTful và WebSocket server chạy thông suốt trên FastAPI.
3. Tài liệu OpenAPI/Swagger UI hoàn chỉnh tại `http://localhost:8000/docs`, đầy đủ ví dụ request/response schema.
4. Bộ test suite Backend đạt tỷ lệ pass 100%.

---

## 5. ⚠️ Rủi Ro Kỹ Thuật & Giải Pháp (Risks & Mitigation)
| Rủi Ro | Mức Độ | Giải Pháp Phòng Ngừa |
| :--- | :---: | :--- |
| Race Condition khi nhiều bác sĩ bấm "Tiếp nhận" cùng lúc dẫn đến nhận trùng bệnh nhân | Cao | Dùng `asyncio.Lock` ở tầng Service để khóa tài nguyên hàng đợi trong microsecond thực thi lệnh dispatch. |
| API schema thay đổi làm vỡ kết nối khi làm Frontend ở tuần sau | Trung bình | Đóng băng API Contract và xuất file `openapi.json` làm mốc tham chiếu chuẩn cho Tuần 4. |
