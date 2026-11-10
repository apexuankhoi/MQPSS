# 📅 Tuần 2: Xây Dựng AI Triage Engine & Module Phân Loại Lâm Sàng (ESI Classifier)

> **Giai đoạn:** Phát triển Bộ máy Phân loại Thông minh (AI Triage Engine)  
> **Thời gian dự kiến:** Tuần 2  
> **Trọng tâm:** Huấn luyện / xây dựng thuật toán phân loại ESI 1–5 kết hợp Rule-based y tế và Machine Learning có khả năng giải thích (Explainable AI).

---

## 1. 🎯 Mục Tiêu Cốt Lõi (Objectives)
1. Xây dựng tập dữ liệu lâm sàng mẫu chuẩn hóa (sử dụng trích xuất từ MIMIC-IV ED hoặc bộ dữ liệu sinh tự động bám sát ca lâm sàng thực tế).
2. Xây dựng module **AI Triage Engine** hai lớp:
   * **Lớp 1 (Safety Rule-based Filter):** Kiểm tra ngay các dấu hiệu đe dọa tính mạng (Red Flags) để gắn ESI-1 hoặc ESI-2 lập tức.
   * **Lớp 2 (Machine Learning Classifier):** Phân loại ESI-3, ESI-4, ESI-5 dựa trên triệu chứng, sinh hiệu, độ tuổi và nhu cầu cận lâm sàng.
3. Thiết lập tính năng **Explainable AI (XAI)**: Mỗi quyết định phân loại phải trả về lý do cụ thể cho y bác sĩ (ví dụ: *"Gán ESI-2 do SpO2 88% và mạch nhanh 130 bpm"*).
4. Cung cấp API phân loại có hỗ trợ cơ chế **Y tá / Bác sĩ Override** (ghi đè thủ công khi có đánh giá lâm sàng trực tiếp).

---

## 2. 🧭 Hướng Đi Chiến Lược (Strategy & Direction)
* **An toàn người bệnh là trên hết (Safety First):** Không để mô hình "Black Box" Machine Learning tự ý quyết định ca nguy kịch. Các ca ngưng thở, hôn mê, sốc bắt buộc phải qua Rule-based cứng để gán ESI-1 ngay lập tức trong 0.01 giây.
* **Mô hình hóa nhu cầu cận lâm sàng (Resource-based Decision):** Theo chuẩn ESI v4:
  * ESI-1: Cần hồi sức lập tức.
  * ESI-2: Tình trạng nguy cơ cao hoặc lú lẫn/đau dữ dội.
  * ESI-3: Cần $\ge 2$ loại xét nghiệm/chẩn đoán hình ảnh.
  * ESI-4: Cần 1 loại xét nghiệm (ví dụ X-quang hoặc khâu vết thương).
  * ESI-5: Không cần xét nghiệm (chỉ cần kê đơn hoặc khám ngoài).
* **Kiểm thử diện rộng bằng Scenario-based Testing:** Viết bộ test suite bao phủ tối thiểu 50 ca bệnh giả định từ nhẹ đến kịch phát.

---

## 3. 📋 Danh Sách Công Việc Cần Hoàn Thành (Task Checklist)

### 3.1. Chuẩn Bị & Tiền Xử Lý Dữ Liệu
- [ ] Xây dựng script sinh dữ liệu giả lập chuẩn y tế (`scripts/generate_synthetic_patients.py`) hoặc parse tập dữ liệu MIMIC-IV ED.
- [ ] Chuẩn hóa các trường thông tin đầu vào:
  * Sinh hiệu: `heart_rate`, `systolic_bp`, `diastolic_bp`, `respiratory_rate`, `spo2`, `temperature`, `pain_scale` (0–10).
  * Nhân khẩu học & bệnh sử: `age`, `gender`, `is_pregnant`, `comorbidities` (danh sách bệnh nền).
  * Triệu chứng chính: `chief_complaint`, `consciousness_level` (AVPU scale: Alert, Voice, Pain, Unresponsive).
- [ ] Phân chia tập Train/Test (80/20) và đánh giá độ mất cân bằng lớp (Class Imbalance - do ESI-1 thường chiếm tỷ lệ rất nhỏ).

### 3.2. Xây Dựng Thuật Toán Phân Loại (Triage Engine)
- [ ] **Xây dựng Safety Rule-based System:**
  * Nếu Unresponsive hoặc ngưng thở/ngưng tim $\rightarrow$ **ESI-1**.
  * Nếu SpO2 $< 90\%$ hoặc Shock Index $> 1.0$ hoặc đau ngực kiểu mạch vành $\rightarrow$ **ESI-2**.
- [ ] **Xây dựng Model Machine Learning (Scikit-Learn):**
  * Thử nghiệm Decision Tree và Random Forest Classifier để giữ được tính minh bạch logic.
  * Trích xuất Feature Importance để phục vụ giải thích quyết định.
- [ ] **Tích hợp Explainability Module:**
  * Trả về output JSON có trường `explanations`: danh sách các yếu tố khiến bệnh nhân bị nâng hoặc hạ mức ESI.

### 3.3. Xây Dựng Triage Service & API
- [ ] Viết `TriageService` độc lập trong thư mục `app/services/triage_service.py`.
- [ ] Viết endpoint FastAPI:
  * `POST /api/v1/triage/classify`: Tiếp nhận thông số bệnh nhân $\rightarrow$ trả về ESI Level gợi ý + giải thích.
  * `POST /api/v1/triage/override`: Y tá xác nhận hoặc điều chỉnh ESI kèm lý do ghi đè (lưu audit log).

### 3.4. Kiểm Thử & Đánh Giá Chất Lượng Phân Loại
- [ ] Viết bộ Unit Test (`tests/test_triage_engine.py`) cho toàn bộ các ca kiểm thử biên (Edge cases).
- [ ] Đánh giá độ chính xác mô hình: Precision, Recall, F1-Score (đặc biệt theo dõi chỉ số Under-triage Rate — tỷ lệ đoán bệnh nặng thành nhẹ, phải $< 5\%$).

---

## 4. 📦 Kết Quả Đầu Ra Nghiệm Thu (Deliverables / DoD)
1. Module `TriageService` chạy ổn định, có model ML đã được huấn luyện và lưu trữ (`models/triage_model.joblib`).
2. Bộ API FastAPI `/api/v1/triage/*` hoạt động và có tài liệu Swagger UI (`/docs`).
3. Bộ unit test tự động đạt tỷ lệ pass 100% cho 50+ kịch bản bệnh nhân mẫu.
4. Báo cáo đánh giá hiệu năng mô hình (Accuracy, F1-score, Under-triage / Over-triage rates).

---

## 5. ⚠️ Rủi Ro Kỹ Thuật & Giải Pháp (Risks & Mitigation)
| Rủi Ro | Mức Độ | Giải Pháp Phòng Ngừa |
| :--- | :---: | :--- |
| Under-triage (phân loại nhầm ca nặng thành ca nhẹ) gây nguy hiểm tính mạng | Cực cao | Ưu tiên Rule-based chốt chặn trước; cấu hình loss function phạt nặng lỗi under-triage hơn over-triage. |
| Dữ liệu mất cân bằng nghiêm trọng (ESI-1 rất hiếm so với ESI-3, ESI-4) | Cao | Áp dụng kỹ thuật SMOTE hoặc gán trọng số class weight (`class_weight='balanced'`) trong mô hình ML. |
