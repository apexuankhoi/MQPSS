# 📅 Tuần 1: Nghiên Cứu Lý Thuyết, Mô Hình Toán Học & Thiết Kế Kiến Trúc Hệ Thống

> **Giai đoạn:** Khởi động & Nền tảng (Foundation & Architecture Design)  
> **Thời gian dự kiến:** Tuần 1  
> **Trọng tâm:** Chuẩn hóa quy tắc Triage ESI, xây dựng mô hình lập lịch đa mức và chốt kiến trúc hệ thống.

---

## 1. 🎯 Mục Tiêu Cốt Lõi (Objectives)
1. Thấu hiểu sâu sắc cơ chế phân loại bệnh nhân cấp cứu theo thang **Emergency Severity Index (ESI v4)**.
2. Thiết lập công thức toán học tính điểm ưu tiên đa biến (**Priority Score Formula**) tích hợp các yếu tố lâm sàng.
3. Hoàn thiện thiết kế kiến trúc 5 tầng hàng đợi (**Multilevel Queue**) và đặc tả cơ chế Preemption, Dynamic Aging.
4. Thiết kế cấu trúc dữ liệu, sơ đồ cơ sở dữ liệu (**Database Schema**) và luồng xử lý tổng thể (**Dataflow Pipeline**).
5. Chuẩn bị môi trường lập trình chuẩn (Python, Git, Docker, cấu trúc thư mục repo).

---

## 2. 🧭 Hướng Đi Chiến Lược (Strategy & Direction)
* **Tiếp cận liên ngành chuẩn xác:** Không chỉ code theo cảm tính, mà phải căn cứ vào tài liệu y khoa chuẩn ESI (AHRQ) kết hợp với lý thuyết định thời CPU (Silberschatz OS Concept).
* **Mô hình hóa toán học trước khi viết mã:** Mọi quy tắc ưu tiên và thăng cấp (Aging) cần có công thức tường minh, tham số hóa ($w_1, w_2, \dots$) để sau này dễ dàng tinh chỉnh (tune) trong quá trình mô phỏng thực nghiệm.
* **Tách bạch rõ ranh giới các module:** Phân tách rành mạch giữa:
  * Module phân loại lâm sàng (Triage Engine).
  * Module điều phối tài nguyên (Scheduler/Dispatcher).
  * Module hiển thị và giám sát (Dashboard).

---

## 3. 📋 Danh Sách Công Việc Cần Hoàn Thành (Task Checklist)

### 3.1. Nghiên Cứu Tài Liệu & Nghiệp Vụ Y Tế
- [ ] Đọc và tổng hợp tài liệu chuẩn phân loại ESI (5 mức: ESI-1 đến ESI-5).
- [ ] Xác định các ngưỡng sinh hiệu nguy hiểm (Danger Vital Signs: SpO2 < 90%, Huyết áp tâm thu < 90 hoặc > 180 mmHg, Mạch > 120 hoặc < 50 bpm, Thở > 30 hoặc < 10 l/p).
- [ ] Phân tích các yếu tố nguy cơ bổ trợ: độ tuổi (sơ sinh, người già > 65 tuổi), bệnh lý nền (tim mạch, COPD, đái tháo đường).

### 3.2. Thiết Kế Mô Hình Toán Học & Thuật Toán
- [ ] **Đặc tả công thức Priority Score tổng quát:**
  $$\text{Priority\_Score} = w_1 \cdot \text{ESI} + w_2 \cdot \text{Wait\_Time} + w_3 \cdot \text{Vital\_Score} + w_4 \cdot \text{Age\_Factor} + w_5 \cdot \text{Comorbidity}$$
- [ ] **Thiết kế cơ chế Dynamic Aging:**
  * Xác định hàm tăng trưởng độ ưu tiên theo thời gian chờ (Linear vs Exponential Aging).
  * Ngưỡng thăng hạng queue: ESI-4 $\rightarrow$ ESI-3 sau 90 phút; ESI-3 $\rightarrow$ ESI-2 sau 45 phút.
- [ ] **Đặc tả cơ chế Preemption:**
  * Định nghĩa hành vi hệ thống khi có ca ESI-1 vào cấp cứu ngay (cơ chế phân bổ bác sĩ rảnh kế tiếp hoặc ngắt can thiệp không nguy kịch).

### 3.3. Thiết Kế Hệ Thống & Cơ Sở Dữ Liệu
- [ ] Vẽ sơ đồ kiến trúc tổng thể (Architecture Diagram), sơ đồ luồng dữ liệu (Data Flow Diagram - DFD).
- [ ] Thiết kế Database Schema (PostgreSQL):
  * Bảng `patients` (hồ sơ bệnh nhân, thông tin nhân khẩu học).
  * Bảng `triage_records` (thời điểm nhập, triệu chứng, sinh hiệu, ESI dự đoán, ESI do y tá duyệt).
  * Bảng `queues_history` (lịch sử vào queue, thời điểm thăng hạng, thời điểm tiếp nhận).
  * Bảng `doctors_resources` (danh sách bác sĩ, chuyên khoa, trạng thái sẵn sàng, ca đang phụ trách).
- [ ] Thiết kế In-Memory Data Structure cho Redis: cấu trúc Sorted Set / Lists để quản lý 5 hàng đợi theo thời gian thực.

### 3.4. Thiết Lập Môi Trường Dự Án (Project Setup)
- [ ] Khởi tạo cấu trúc thư mục chuẩn cho backend (`app/core`, `app/api`, `app/models`, `app/services`, `app/algorithms`).
- [ ] Tạo file cấu hình `docker-compose.yml` (PostgreSQL, Redis, Adminer/PGAdmin).
- [ ] Cấu hình `requirements.txt` / `pyproject.toml` (FastAPI, Pydantic, SQLAlchemy, Redis-py, SimPy, Scikit-learn, Pytest).

---

## 4. 📦 Kết Quả Đầu Ra Nghiệm Thu (Deliverables / DoD)
1. Tài liệu đặc tả kỹ thuật toán học & thuật toán định thời (`docs/spec_scheduling_algorithm.md`).
2. Sơ đồ Database ERD (file ảnh/mermaid) và mã nguồn migration khởi tạo bảng (`alembic` hoặc SQL script).
3. Môi trường Docker Compose chạy được PostgreSQL và Redis local sẵn sàng cho tuần 2.
4. Repo có khung sườn source code hoàn chỉnh, cấu hình linter/formatter sẵn sàng.

---

## 5. ⚠️ Rủi Ro Kỹ Thuật & Giải Pháp (Risks & Mitigation)
| Rủi Ro | Mức Độ | Giải Pháp Phòng Ngừa |
| :--- | :---: | :--- |
| Trọng số $w_1 \dots w_5$ ban đầu đặt theo cảm tính gây lệch thứ tự ưu tiên | Trung bình | Thiết lập file config biến động (dynamic config) để có thể chỉnh trọng số linh hoạt trong các vòng test. |
| Cơ chế Preemption trong thực tế y tế không giống OS (bác sĩ không ngắt ngang mổ xẻ được) | Cao | Phải định nghĩa lại Preemption: ưu tiên tối thượng ở khâu nhận ca kế tiếp (Next Available Resource Dispatching) và báo động kíp trực cấp cứu đặc biệt. |
