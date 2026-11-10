# 🖥️ ĐỀ CƯƠNG SLIDE THUYẾT TRÌNH BẢO VỆ ĐỀ TÀI (20 SLIDES)
## Ứng Dụng Thuật Toán Multilevel Queue & Priority Scheduling Trong Hệ Thống Phân Loại Bệnh Nhân Cấp Cứu (Triage) — MQPSS
* **GVHD:** ThS. Lê Văn Phong | **Thời gian trình bày:** 15 - 20 phút

---

### SLIDE 1: Trang Tiêu Đề
* **Tên đề tài:** Ứng Dụng Thuật Toán Multilevel Queue & Priority Scheduling Trong Hệ Thống Phân Loại Bệnh Nhân Cấp Cứu (Triage)
* **Tên viết tắt:** MQPSS (*Multilevel Queue Priority Scheduling System*)
* **GVHD:** ThS. Lê Văn Phong
* **Năm học:** 2026 – 2027

---

### SLIDE 2: Thực Trạng & Nghịch Lý Khoa Cấp Cứu
* Khoa Cấp Cứu: Nơi ranh giới sinh tử chỉ tính bằng phút.
* 3 bài toán nan giải:
  1. Quá tải đột biến giờ cao điểm.
  2. Ca nguy kịch (ngưng tim, sốc) bị trễ nợ thời gian vàng cấp cứu.
  3. Bệnh nhân nhẹ chen lấn hoặc bị bỏ quên kéo dài gây bức xúc.

---

### SLIDE 3: Hạn Chế Của Các Phương Pháp Hiện Tại
* **FCFS (Đến trước khám trước):** Sai lầm nghiêm trọng trong y tế — người đau ngực phải chờ sau người đứt tay nhẹ.
* **Ưu tiên tĩnh (Pure Priority):** Luôn đón ca nặng $\rightarrow$ Ca nhẹ bị hoãn vô thời hạn (*Starvation*).
* **Quyết định thủ công bằng mắt thường:** Dễ sai sót, thiếu minh bạch, phụ thuộc chủ quan của điều dưỡng.

---

### SLIDE 4: Ý Tưởng Liên Ngành Đột Phá
* Cầu nối giữa: **Khoa học Máy tính (Lý thuyết Hệ Điều Hành)** $\leftrightarrow$ **Y học Cấp cứu**.
* Ánh xạ lập lịch CPU sang lập lịch tiếp nhận bệnh nhân:
  * *Process* $\rightarrow$ Bệnh nhân
  * *CPU Burst Time* $\rightarrow$ Thời gian điều trị ước tính
  * *Priority Level* $\rightarrow$ Mức độ nguy kịch ESI (1–5)
  * *Preemption* $\rightarrow$ Dừng ca nhẹ để ép tim ca ngừng tuần hoàn
  * *Aging* $\rightarrow$ Tự động thăng hạng người đã chờ quá lâu

---

### SLIDE 5: Chuẩn Phân Loại ESI v4 (Emergency Severity Index)
* **Level 1 (Đỏ):** Nguy kịch tức thì $\rightarrow$ Vào phòng hồi sức ngay (0 phút).
* **Level 2 (Cam):** Rất cấp, rủi ro cao $\rightarrow$ Chờ $< 15$ phút.
* **Level 3 (Vàng):** Cấp tính, cần $\ge 2$ cận lâm sàng $\rightarrow$ Chờ $< 60$ phút.
* **Level 4 (Xanh):** Ít cấp, cần 1 cận lâm sàng $\rightarrow$ Chờ $< 120$ phút.
* **Level 5 (Ghi):** Không cấp $\rightarrow$ Hướng dẫn chuyển ngoại trú.

---

### SLIDE 6: Mô Hình Toán Học Tính Điểm Ưu Tiên (Priority Score)
$$S_{\text{overall}} = w_1 S_{\text{ESI}} + w_2 S_{\text{Wait}} + w_3 S_{\text{Vitals}} + w_4 S_{\text{Age}} + w_5 S_{\text{Comorbidity}}$$
* $w_1 = 0.35$ (Mức độ ESI)
* $w_2 = 0.25$ (Thời gian đã chờ)
* $w_3 = 0.20$ (Bất thường sinh hiệu: SpO2, Shock Index, Mạch, HA)
* $w_4 = 0.10$ (Hệ số tuổi: Trẻ sơ sinh & Người già $>80$ tuổi)
* $w_5 = 0.10$ (Bệnh nền: Tim mạch, Đột quỵ, COPD)

---

### SLIDE 7: Bộ Máy AI Triage Hai Lớp (Explainable AI Engine)
* **Lớp 1 — Safety Rule-Based:** Chốt chặn an toàn tuyệt đối.
  * Hôn mê (AVPU = 'U'), ngưng thở, SpO2 $< 90\%$, Shock Index $\ge 1.05 \rightarrow$ ESI-1 hoặc ESI-2 ngay lập tức trong 0.01s.
* **Lớp 2 — Machine Learning (Random Forest):** Phân loại ESI 3, 4, 5 dựa trên nhu cầu cận lâm sàng.
* **Minh bạch (XAI):** Trả về danh sách lý do cụ thể cho y bác sĩ. Hỗ trợ Nurse Override ghi đè thủ công.

---

### SLIDE 8: Cấu Trúc 5 Hàng Đợi Đa Mức (Multilevel Queue)
1. **Queue 1 (ESI-1):** Preemptive Priority, FCFS nội bộ.
2. **Queue 2 (ESI-2):** Max-Heap theo Priority Score ($O(\log N)$).
3. **Queue 3 (ESI-3):** Round Robin (Quantum = 30 phút).
4. **Queue 4 (ESI-4):** First Come First Served ($O(1)$).
5. **Queue 5 (ESI-5):** Outpatient Diversion (Chuyển tuyến khám ngoài).

---

### SLIDE 9: Cơ Chế Dynamic Aging Chống Đói Tài Nguyên (Anti-Starvation)
* Thuật toán quét nền định kỳ:
  * Bệnh nhân Queue 4 chờ $> 90$ phút $\rightarrow$ Thăng hạng lên Queue 3.
  * Bệnh nhân Queue 3 chờ $> 45$ phút $\rightarrow$ Thăng hạng lên Queue 2.
* Nguyên tắc **Anti-thrashing**: Tối đa 1 bậc thăng hạng / chu kỳ.
* Kết quả: Triệt tiêu tình trạng bệnh nhân nhẹ bị lãng quên trong góc phòng chờ.

---

### SLIDE 10: Cơ Chế Preemption & Cân Bằng Tải Bác Sĩ (Dispatcher)
* **Preemption:** Khi ca ESI-1 vào và tất cả bác sĩ đều bận:
  * Tạm ngắt bác sĩ đang xử lý ca nhẹ nhất (Queue 4/3).
  * Ca nhẹ được đưa về đầu hàng đợi để khám tiếp ngay sau đó.
  * Ca ESI-1 được cấp cứu ngay lập tức.
* **Least-Loaded Dispatcher:** Gán bệnh nhân cho bác sĩ có số ca đã xử lý ít nhất.

---

### SLIDE 11: Kiến Trúc Công Nghệ Hệ Thống (Tech Stack)
* **Backend:** Python + FastAPI (Bất đồng bộ tốc độ cao).
* **Thuật toán lõi:** `heapq`, `collections.deque`, Scikit-learn, SimPy.
* **Realtime:** WebSocket Event Manager (phát sóng biến động hàng đợi & còi báo động).
* **Frontend:** Tailwind CSS, Lucide Icons, Chart.js (Clinical Ergonomics, Dark Mode).
* **Đóng gói:** Docker & Docker Compose (1 lệnh khởi chạy).

---

### SLIDE 12: Màn Hình 1 — Trạm Tiếp Đón Triage Siêu Tốc
* Form nhập liệu tối ưu hóa cho môi trường khẩn trương (`Ctrl+Enter`).
* Cảnh báo tự động khi sinh hiệu vượt ngưỡng nguy kịch.
* Khung AI Triage Preview kèm lý do giải thích rõ ràng.
* Nút Ghi đè ESI kèm lưu vết kiểm toán (Audit Trail).

---

### SLIDE 13: Màn Hình 2 — Bảng 5 Hàng Đợi Live Kanban
* Trực quan hóa 5 cột màu chuẩn ESI quốc tế (Đỏ, Cam, Vàng, Xanh, Ghi).
* Thẻ bệnh nhân hiển thị điểm Priority Score, thời gian đã chờ.
* Badge động đánh dấu ca được thăng hạng do Aging (`Aged +1`).
* Báo động thị giác nhấp nháy đỏ khi ca ESI-1 xuất hiện.

---

### SLIDE 14: Màn Hình 3 — Trạm Làm Việc Bác Sĩ
* Bác sĩ bấm "Gọi Ca Kế Tiếp" $\rightarrow$ Dispatcher tự động chọn bệnh nhân tối ưu.
* Luồng quản lý Cận lâm sàng (I/O Wait Pool):
  * Chuyển bệnh nhân đi chụp X-quang/Xét nghiệm $\rightarrow$ Bác sĩ rảnh nhận ca khác.
  * Bệnh nhân có kết quả $\rightarrow$ Ưu tiên quay lại Queue 2.

---

### SLIDE 15: Màn Hình 4 — Dashboard Giám Sát Công Suất Viện
* 4 Đồng hồ chỉ số: Tổng ca chờ, Thời gian chờ TB, Bác sĩ trực, Ca rủi ro Starvation.
* Biểu đồ phân bổ tỷ lệ ESI và biểu đồ cân bằng tải giữa các bác sĩ.
* Cập nhật thời gian thực không cần tải lại trang nhờ WebSocket.

---

### SLIDE 16: Thực Nghiệm Mô Phỏng Sự Kiện Rời Rạc (SimPy DES)
* Thiết kế mô phỏng 48 giờ liên tục.
* 527 lượt bệnh nhân theo phân phối Poisson ngẫu nhiên (2 đợt giờ cao điểm sáng - tối).
* So sánh đối đầu giữa 3 giải thuật trên **CÙNG 1 TẬP DỮ LIỆU ĐẦU VÀO** (`seed = 42`):
  1. FCFS truyền thống
  2. Pure Priority (Không Aging)
  3. MQPSS (Thuật toán đề xuất)

---

### SLIDE 17: Kết Quả Benchmark — Thời Gian Chờ Ca Nguy Kịch ESI-1
* **FCFS:** Chờ **24.88 phút** $\rightarrow$ Quá thời gian vàng, 72.2% ca nguy kịch bị trễ!
* **Pure Priority:** Chờ **3.14 phút**.
* **MQPSS:** Chờ **3.02 phút** $\rightarrow$ **Giảm 87.9% thời gian chờ so với FCFS**, đảm bảo tiếp cận hồi sức tức thì!

---

### SLIDE 18: Kết Quả Benchmark — Tỷ Lệ Đói Tài Nguyên (Starvation)
* **Pure Priority:** Thời gian chờ tối đa lên tới **292.9 phút (~5 giờ)** do ca nhẹ bị chèn ép.
* **MQPSS:**
  * Dynamic Aging kéo thời gian chờ tối đa xuống còn **197.6 phút (giảm 32.5%)**.
  * Tỷ lệ Starvation toàn viện đạt mức **thấp nhất trong 3 thuật toán (12.52%)**.
  * ESI-5 giảm 90.5% thời gian chờ nhờ điều chuyển ngoại trú.

---

### SLIDE 19: Kiểm Thử Toàn Diện (Testing & Verification)
* 15/15 Automated Unit & Integration Tests đạt **100% PASS**:
  * Kiểm thử phân loại ESI lâm sàng & Red Flags.
  * Kiểm thử Max-Heap và thứ tự ưu tiên.
  * Kiểm thử cơ chế Preemption ngắt ca nhẹ.
  * Kiểm thử Dynamic Aging chống cascade thrashing.
  * Kiểm thử End-to-End REST API & WebSocket.

---

### SLIDE 20: Kết Luận & Lời Cảm Ơn
* **Kết luận:** Đề tài đã xây dựng thành công giải pháp MQPSS giải quyết trọn vẹn bài toán cứu sống ca nguy kịch mà không bỏ rơi ca nhẹ.
* **Đóng góp:** Ánh xạ khoa học máy tính vào y học thực tiễn, có đầy đủ phần mềm chạy thực tế, mã nguồn chuẩn hóa, và bằng chứng mô phỏng định lượng.
* **Lời cảm ơn:** Xin trân trọng cảm ơn GVHD ThS. Lê Văn Phong đã định hướng và góp ý quý báu cho đề tài!
* **Q & A:** Xin mời thầy và hội đồng đặt câu hỏi.

