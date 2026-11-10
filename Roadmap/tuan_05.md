# 📅 Tuần 5: Mô Phỏng Sự Kiện Rời Rạc (DES), Đánh Giá Benchmark & Hoàn Thiện Báo Cáo

> **Giai đoạn:** Thực nghiệm Khoa học, Đóng gói & Báo cáo Nghiệm thu (Simulation, Benchmark & Delivery)  
> **Thời gian dự kiến:** Tuần 5  
> **Trọng tâm:** Xây dựng mô hình mô phỏng sự kiện rời rạc (Discrete Event Simulation - DES), thực hiện Benchmark so sánh thuật toán đề xuất với các giải thuật truyền thống, đóng gói Docker Compose và hoàn thiện tài liệu báo cáo khoa học gửi GVHD ThS. Lê Văn Phong.

---

## 1. 🎯 Mục Tiêu Cốt Lõi (Objectives)
1. Xây dựng môi trường mô phỏng sự kiện rời rạc (**Discrete Event Simulation - DES**) bằng thư viện `SimPy` trong Python để giả lập hàng nghìn ca cấp cứu trong điều kiện thực tế (giờ cao điểm, dịch bệnh, thảm họa).
2. Thực hiện **Benchmark đối đầu** giữa 3 giải thuật:
   * **Giải thuật 1 (Cơ sở truyền thống):** FCFS thuần túy (Ai đến trước khám trước).
   * **Giải thuật 2 (Ưu tiên tĩnh không Aging):** Pure Priority Scheduling (Rất dễ gây đói tài nguyên - Starvation cho ca nhẹ).
   * **Giải thuật 3 (Đề tài đề xuất - MQPSS):** Multilevel Queue kết hợp Dynamic Aging và Preemption.
3. Thu thập dữ liệu định lượng, tính toán các chỉ số KPI then chốt và trực quan hóa bằng biểu đồ khoa học:
   * Thời gian chờ trung bình (**Average Waiting Time**) theo từng mức ESI.
   * Tỷ lệ bệnh nhân bị bỏ rơi quá hạn an toàn (**Starvation Rate**).
   * Năng suất xử lý của khoa (**Throughput - bệnh nhân/giờ**).
   * Tỷ lệ đảo ngược ưu tiên (**Priority Inversion Rate**).
4. Đóng gói toàn bộ hệ thống bằng Docker Compose để có thể khởi chạy chỉ bằng 1 câu lệnh duy nhất.
5. Soạn thảo báo cáo nghiệm thu hoàn chỉnh và slide thuyết trình bảo vệ đề tài.

---

## 2. 🧭 Hướng Đi Chiến Lược (Strategy & Direction)
* **Chứng minh bằng số liệu thực nghiệm định lượng:** Điểm khác biệt lớn nhất giữa một ứng dụng web tầm thường và một nghiên cứu khoa học chất lượng là **số liệu thực nghiệm**. Phải chứng minh được bằng biểu đồ và p-value rằng thuật toán MQPSS giảm thiểu tối đa ca tử vong do chờ đợi mà không làm vỡ trận ở các ca nhẹ.
* **Mô phỏng bám sát thực tế y tế:**
  * Luồng bệnh nhân đến tuân theo phân phối Poisson ($\lambda$ thay đổi theo giờ: ban ngày đông, đêm vắng, có xung đột biến khi xảy ra tai nạn liên hoàn).
  * Thời gian khám của bác sĩ tuân theo phân phối Log-normal hoặc Erlang tùy theo mức độ nặng ESI.
* **Tính tái lập cao (Reproducibility):** Mọi thí nghiệm mô phỏng phải có `random_seed` cố định để GVHD hoặc hội đồng phản biện có thể chạy lại và ra đúng kết quả đối chứng.

---

## 3. 📋 Danh Sách Công Việc Cần Hoàn Thành (Task Checklist)

### 3.1. Xây Dựng Engine Mô Phỏng (SimPy Simulation)
- [ ] Lập trình mô hình mô phỏng sự kiện rời rạc (`simulations/des_simulator.py`):
  * Thực thể: `PatientGenerator`, `HospitalEnvironment`, `DoctorPool`, `TriageDesk`.
  * Cơ chế sinh ngẫu nhiên: Phân phối Poisson cho dòng đến, phân phối Log-normal cho thời gian khám.
  * Giả lập các kịch bản:
    * Kịch bản A: Ngày làm việc bình thường (Normal Load: 200 bệnh nhân/ngày, 5 bác sĩ).
    * Kịch bản B: Giờ cao điểm / Quá tải đột biến (Peak Load: 600 bệnh nhân/ngày, 5 bác sĩ).
    * Kịch bản C: Thảm họa hàng loạt (Mass Casualty: 50 ca ESI-1 và ESI-2 tràn vào cùng lúc).

### 3.2. Chạy Thí Nghiệm Benchmark Đối Đầu
- [ ] Chạy mô phỏng 1,000+ ca bệnh qua lần lượt 3 thuật toán:
  * Chạy thuật toán 1: FCFS thuần.
  * Chạy thuật toán 2: Priority thuần (không Aging).
  * Chạy thuật toán 3: Multilevel Queue + Dynamic Aging (MQPSS).
- [ ] Thu thập dữ liệu thống kê:
  * Thời gian chờ của từng bệnh nhân từ lúc vào viện đến khi gặp bác sĩ.
  * Số lượng bệnh nhân ESI-3 và ESI-4 phải chờ vượt quá thời gian tối đa khuyến cáo (ESI-3 > 60p, ESI-4 > 120p).
  * Thời gian đáp ứng cho ca ESI-1 (phải tiến dần về 0 phút).

### 3.3. Xử Lý Số Liệu & Vẽ Đồ Thị Khoa Học
- [ ] Viết script phân tích thống kê và vẽ biểu đồ (`simulations/plot_benchmark_results.py`):
  * Biểu đồ cột: So sánh thời gian chờ trung bình của 3 thuật toán theo từng ESI 1–5.
  * Biểu đồ đường (Line chart): Sự biến thiên của Starvation Rate theo tải trọng bệnh nhân.
  * Biểu đồ hộp (Boxplot): Độ phân tán thời gian chờ đợi.
- [ ] Xuất bảng tổng hợp kết quả (Metrics Summary Table) phục vụ chèn trực tiếp vào báo cáo.

### 3.4. Đóng Gói Hệ Thống (Deployment & Packaging)
- [ ] Viết `Dockerfile` tối ưu cho Backend FastAPI và Frontend React.
- [ ] Viết file `docker-compose.yml` tích hợp trọn vẹn:
  * Backend API + WebSocket Service.
  * Frontend Web App.
  * PostgreSQL Database (kèm file SQL seed dữ liệu ban đầu).
  * Redis Cache/Queue.
- [ ] Viết tài liệu hướng dẫn chạy nhanh (`README.md`): hướng dẫn cài đặt trong 3 bước (`docker-compose up -d`).

### 3.5. Viết Báo Cáo Tổng Kết & Soạn Slide Thuyết Trình
- [ ] Soạn thảo báo cáo kỹ thuật hoàn chỉnh:
  * Phần 1: Giới thiệu & Đặt vấn đề y tế khẩn cấp.
  * Phần 2: Cơ sở lý thuyết (ESI Triage & CPU Scheduling Concepts).
  * Phần 3: Thiết kế mô hình toán học & Thuật toán Multilevel Queue có Aging.
  * Phần 4: Kiến trúc hệ thống phần mềm & Giao diện Dashboard.
  * Phần 5: Kết quả thực nghiệm mô phỏng & Đánh giá Benchmark.
  * Phần 6: Kết luận, Đóng góp khoa học & Hướng phát triển mở rộng.
- [ ] Thiết kế slide thuyết trình báo cáo đề tài (15–20 slides súc tích, trực quan, nhấn mạnh vào demo và kết quả benchmark).

---

## 4. 📦 Kết Quả Đầu Ra Nghiệm Thu (Deliverables / DoD)
1. Thư mục mã nguồn mô phỏng `simulations/` với mã nguồn SimPy hoàn chỉnh và các biểu đồ PNG độ phân giải cao.
2. File `docker-compose.yml` khởi chạy toàn bộ hệ thống trơn tru chỉ với một lệnh.
3. Bản báo cáo khoa học định dạng PDF/Markdown hoàn chỉnh, chi tiết, chỉn chu.
4. Bộ slide thuyết trình báo cáo tiến độ và kết quả trước GVHD ThS. Lê Văn Phong.

---

## 5. ⚠️ Rủi Ro Kỹ Thuật & Giải Pháp (Risks & Mitigation)
| Rủi Ro | Mức Độ | Giải Pháp Phòng Ngừa |
| :--- | :---: | :--- |
| Kết quả mô phỏng không cho thấy sự vượt trội rõ rệt do thông số ban đầu chưa sát thực tế | Trung bình | Tinh chỉnh lại tỷ lệ phân bổ thời gian khám y tế sát với các công bố của hiệp hội cấp cứu (AHRQ / ACEP); tăng quy mô mẫu lên 5,000 ca để hội tụ quy luật số lớn. |
| Môi trường Docker bị xung đột port hoặc build chậm | Thấp | Sử dụng multi-stage build cho Dockerfile và thiết lập port mapping linh hoạt qua file `.env`. |
