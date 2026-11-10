# 🌟 TUẦN ĐẶC BIỆT (Tuần 4): Thiết Kế & Xây Dựng Toàn Diện Giao Diện Người Dùng (UI/UX Clinical Frontend)

> **Giai đoạn:** Tuần Chuyên Biệt Frontend Y Tế Khẩn Cấp (Dedicated Frontend Design & Engineering)  
> **Thời gian dự kiến:** Tuần 4  
> **Trọng tâm:** Xây dựng hệ thống Design System y tế chuyên nghiệp, thiết kế và hoàn thiện toàn bộ các màn hình giao diện (Tiếp đón Triage, Bảng điều phối 5 hàng đợi Real-time, Trạm Bác sĩ, và Dashboard Giám sát Khoa cấp cứu).

---

## 1. 🎯 Mục Tiêu Cốt Lõi (Objectives)
1. Xây dựng **Hệ thống Thiết kế Y tế (Clinical Design System & Tokens)** đạt chuẩn tiếp cận **WCAG 2.1 AA**, tối ưu hóa thị giác cho môi trường phòng cấp cứu căng thẳng (High-stress Clinical Ergonomics).
2. Phát triển trọn vẹn **4 màn hình tương tác chuyên sâu**:
   * **Màn hình 1 — Trạm Tiếp Đón & Phân Loại (Triage Intake Desk):** Tối ưu hóa nhập liệu siêu tốc với phím tắt, tự động cảnh báo sinh hiệu bất thường và khung AI giải thích (Explainable AI Cards).
   * **Màn hình 2 — Bảng Điều Phối Hàng Đợi Trực Quan Đa Tầng (Live Multilevel Queue Board):** Hiệu ứng Kanban 5 cột tương tác cao, đồng hồ đếm ngược thời gian an toàn, hiệu ứng rung lắc/nhấp nháy khi ca ESI-1 xuất hiện và hoạt ảnh mượt mà khi bệnh nhân được thăng hạng (Aging Transition Animation).
   * **Màn hình 3 — Trạm Bác Sĩ Cấp Cứu (Doctor Workstation):** Không gian làm việc tập trung cao độ để bác sĩ gọi ca kế tiếp, theo dõi diễn tiến lâm sàng, ra lệnh xét nghiệm (I/O Wait) và hoàn tất ca.
   * **Màn hình 4 — Bảng Giám Sát Công Suất & Cảnh Báo Ùn Ứ (ED Capacity & Executive Dashboard):** Biểu đồ thời gian thực về tải trọng khoa, thời gian chờ trung bình, năng suất bác sĩ và cảnh báo quá tải đỏ.
3. Tích hợp trọn vẹn **Hiệu ứng Âm thanh & Báo động Thị giác (Audio-Visual Emergency Alerts)** chuẩn y tế cho các tình huống khẩn cấp mức độ 1 và mức độ 2.
4. Tối ưu hóa hiển thị Responsive trên cả màn hình lớn trung tâm (Large Wall Monitor), máy tính để bàn y tá và máy tính bảng di động (Triage Tablet).

---

## 2. 🧭 Hướng Đi Chiến Lược (Strategy & Direction)
* **Quy chuẩn Màu sắc Lâm sàng Quốc tế (ESI Palette Standard):**
  * **ESI-1 (Đỏ `#EF4444` / Crimson):** Nguy kịch tức thì — Báo động nhấp nháy (pulsing animation) + âm thanh còi cấp cứu.
  * **ESI-2 (Cam `#F97316` / Amber-Orange):** Rất cấp — Viền phát sáng, đồng hồ đếm ngược 15 phút.
  * **ESI-3 (Vàng `#F59E0B` / Warning Yellow):** Cấp tính — Đồng hồ đếm ngược 60 phút.
  * **ESI-4 (Xanh lá `#10B981` / Emerald Green):** Ít cấp — Giao diện êm dịu, thông tin gọn gàng.
  * **ESI-5 (Ghi xám `#64748B` / Slate):** Không cấp — Thẻ tối giản, chỉ dẫn chuyển phòng khám.
* **Ergonomics & Tối giản Thao tác (Zero-Friction UX):**
  * Trong phòng cấp cứu, mỗi giây đều quý giá. Y tá không dùng chuột quá nhiều: hỗ trợ bộ **Phím tắt Bàn phím (Keyboard Shortcuts: `F1` - `F5` gán nhanh ESI, `Ctrl+Enter` gửi ca, `Space` gọi ca kế tiếp)**.
  * Form nhập sinh hiệu có cơ chế phát hiện lỗi thông minh (ví dụ: gõ nhịp tim 300 hoặc huyết áp 40 sẽ hiển thị cảnh báo đỏ xác nhận lại).
* **Trạng thái Hoạt ảnh Động (State Transitions & Micro-interactions):**
  * Khi cơ chế Dynamic Aging nâng cấp bệnh nhân từ Hàng đợi 4 lên Hàng đợi 3, thẻ bệnh nhân phải có animation bay mượt mà giữa 2 cột kèm badge thông báo *"Thăng hạng do chờ > 90 phút"*.

---

## 3. 📋 Danh Sách Công Việc Cần Hoàn Thành (Task Checklist)

### 3.1. Thiết Lập Design System, Theme & Component Tokens
- [ ] Xây dựng bộ Design Tokens trong Tailwind CSS (`tailwind.config.js`):
  * Màu sắc ngữ nghĩa ESI (`color-esi-1` đến `color-esi-5`).
  * Trạng thái lâm sàng: Đang chờ, Đang khám, Chờ cận lâm sàng (Lab/X-ray), Đã xuất viện.
- [ ] Thiết lập chế độ **Clinical Dark Mode / High-Contrast Mode** giúp giảm mỏi mắt cho kíp trực đêm và màn hình theo dõi liên tục 24/7.
- [ ] Xây dựng thư viện Base Components dùng chung (shadcn/ui hoặc Radix UI):
  * `VitalSignBadge`: Hiển thị chỉ số sinh hiệu (SpO2, Mạch, HA) kèm màu cảnh báo trạng thái sinh tồn.
  * `PatientCard`: Thẻ bệnh nhân đa thông tin (Mã, Tuổi, Triệu chứng chính, Điểm Priority Score, Đồng hồ đếm ngược).
  * `CountdownTimer`: Bộ đếm ngược thời gian chờ tối đa an toàn (chuyển sang màu đỏ nhấp nháy khi quá hạn).
  * `EmergencyAlertBanner`: Thanh báo động khẩn cấp toàn màn hình khi có ca ESI-1.

### 3.2. Màn Hình 1 — Trạm Tiếp Đón & Phân Loại Triage (Triage Intake Screen)
- [ ] Xây dựng Form nhập liệu nhanh (Triage Intake Form):
  * Nhập thông tin hành chính: Họ tên/Mã BN, Tuổi, Giới tính, Đối tượng ưu tiên (Trẻ em, Phụ nữ mang thai, Người già).
  * Nhập chỉ số sinh hiệu: Nhịp tim, Huyết áp (Tâm thu/Tâm trương), Nhịp thở, SpO2, Nhiệt độ, Thang đau (VAS 0–10).
  * Đánh giá mức độ tri giác AVPU (Alert, Voice, Pain, Unresponsive).
- [ ] Tích hợp **AI Triage Suggestion Panel**:
  * Khi y tá nhập xong các chỉ số, card gợi ý AI tự động hiển thị mức ESI khuyến nghị.
  * Thẻ **Explainable AI**: Hiển thị gạch đầu dòng rõ ràng lý do gợi ý (ví dụ: *"SpO2 = 88% < 90% cảnh báo suy hô hấp"*).
  * Nút **Chấp Nhận** (`Enter`) hoặc **Ghi Đè Thủ Công (Override Modal)** cho phép y tá chọn ESI khác kèm nhập lý do lâm sàng.

### 3.3. Màn Hình 2 — Bảng Hàng Đợi 5 Tầng Trực Quan (Live Multilevel Queue Board)
- [ ] Xây dựng giao diện dạng 5 cột Kanban tương ứng với 5 Queue:
  * Cột 1 (ESI-1 - Hồi sức lập tức)
  * Cột 2 (ESI-2 - Cấp cứu rất cấp)
  * Cột 3 (ESI-3 - Cấp cứu thường)
  * Cột 4 (ESI-4 - Can thiệp nhẹ)
  * Cột 5 (ESI-5 - Hướng dẫn chuyển ngoại trú)
- [ ] Hiển thị Header mỗi cột: Số lượng ca đang chờ, Thời gian chờ bình quân, Ngưỡng cảnh báo.
- [ ] Lập trình hiệu ứng hoạt ảnh động (Framer Motion / CSS Transition):
  * Animation chuyển cột khi bệnh nhân được Dynamic Aging thăng hạng.
  * Thẻ bệnh nhân ESI-1 xuất hiện kèm hiệu ứng xung đỏ (Pulse ring) và âm thanh *Ding-Ding* cảnh báo.
- [ ] Bộ lọc và tìm kiếm nhanh: Lọc theo thời gian chờ, tìm theo mã bệnh nhân, lọc theo khoa/bác sĩ.

### 3.4. Màn Hình 3 — Trạm Làm Việc Bác Sĩ (Doctor Station)
- [ ] Thiết kế khu vực tiếp nhận bệnh nhân:
  * Nút to nổi bật: **"Tiếp Nhận Ca Tiếp Theo" (Call Next Patient)** — nhấn phím Space để kích hoạt.
  * Hiển thị bảng tóm tắt bệnh nhân đang khám: Sinh hiệu chi tiết, triệu chứng chính, tiền sử bệnh án.
- [ ] Thanh điều khiển hành động y lệnh nhanh (Quick Action Toolbar):
  * Nút **"Chỉ định Cận Lâm Sàng"** (X-quang, CT, Xét nghiệm máu) $\rightarrow$ chuyển bệnh nhân vào hàng chờ I/O Wait.
  * Nút **"Bệnh nhân trở lại có kết quả"** $\rightarrow$ tiếp tục xử lý.
  * Nút **"Chuyển phòng mổ / ICU"** hoặc **"Kê đơn & Cho về"**.
- [ ] Đồng hồ bấm giờ thời gian điều trị thực tế (Treatment Duration Timer).

### 3.5. Màn Hình 4 — Bảng Giám Sát Công Suất & Cảnh Báo Ùn Ứ (ED Overview Dashboard)
- [ ] Thiết kế thanh chỉ số đo lường trung tâm (KPI Summary Cards):
  * Tổng số ca tiếp nhận trong ngày.
  * Thời gian chờ trung bình toàn khoa vs Thời gian chờ ca nguy kịch.
  * Tỷ lệ bệnh nhân quá hạn an toàn (Starvation Rate Meter).
  * Công suất sử dụng buồng bệnh / Bác sĩ trực (% Utilization).
- [ ] Biểu đồ trực quan hóa (Recharts / Chart.js):
  * Biểu đồ cột phân bổ bệnh nhân theo 5 cấp độ ESI.
  * Biểu đồ đường thể hiện tải lượng bệnh nhân theo khung giờ (Rush-hour Trend).
  * Gauge đo mức độ rủi ro quá tải (Low - Normal - Critical Congestion Alert).

---

## 4. 📦 Kết Quả Đầu Ra Nghiệm Thu (Deliverables / DoD)
1. Thư mục mã nguồn Frontend (`frontend/`) hoàn chỉnh, cấu trúc module rõ ràng, không lỗi build (`npm run build` thành công 100%).
2. Giao diện trực quan, thẩm mỹ chuẩn y tế, phản hồi nhanh nhạy, hỗ trợ Dark/Light mode và phím tắt thao tác.
3. Toàn bộ 4 màn hình kết nối mượt mà với REST API và WebSocket Backend từ Tuần 3.
4. Video quay màn hình hoặc Demo tương tác kịch bản hoàn chỉnh: Y tá nhập ca $\rightarrow$ AI gợi ý ESI $\rightarrow$ Thấy thẻ xuất hiện trên bảng Kanban $\rightarrow$ Hiệu ứng Aging thăng cấp $\rightarrow$ Bác sĩ gọi khám $\rightarrow$ Cảnh báo âm thanh khi ca ESI-1 xuất hiện.

---

## 5. ⚠️ Rủi Ro Kỹ Thuật & Giải Pháp (Risks & Mitigation)
| Rủi Ro | Mức Độ | Giải Pháp Phòng Ngừa |
| :--- | :---: | :--- |
| Giao diện quá nhiều animation gây giật lag khi số lượng bệnh nhân lớn | Trung bình | Tắt các hiệu ứng phức tạp trên các danh sách dài; chỉ giữ animation cho các sự kiện trọng yếu (ESI-1, Aging nhảy cột). |
| Trình duyệt chặn âm thanh cảnh báo tự động (Autoplay Policy) | Trung bình | Yêu cầu người dùng bấm nút "Bật Báo Động Âm Thanh" (Enable Audio Alerts) ngay khi mở ứng dụng ở đầu ca trực. |
| Y tá nhập nhầm thông số sinh hiệu trong lúc vội vã | Cao | Đặt dải giá trị validation lâm sàng (Hard validation) chặn các giá trị phi lý tính và yêu cầu xác nhận 2 bước với ca nguy kịch. |
