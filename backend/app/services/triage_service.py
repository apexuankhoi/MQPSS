"""
Clinical Triage Service — Emergency Severity Index (ESI v4)
Two-layer hybrid: Deterministic Safety Rules + Explainable ML Classifier
"""

import re
from typing import List, Tuple
from datetime import datetime
from backend.app.models.schemas import (
    ESILevel, AVPUConsciousness, VitalSigns,
    PatientIntakeRequest, TriageClassification, TriageOverrideRequest
)
from backend.app.services.ml_triage_model import get_or_train_model

class TriageService:
    def __init__(self):
        self.ml_model = get_or_train_model()
        self.override_audit_logs = []

    def classify_patient(self, request: PatientIntakeRequest) -> TriageClassification:
        """
        Quy trình phân loại 2 lớp chuẩn ESI v4:
        1. Kiểm tra dấu hiệu đe dọa sinh mạng tức thì (ESI-1)
        2. Kiểm tra dấu hiệu rủi ro cao / đau dữ dội / sinh hiệu nguy kịch (ESI-2)
        3. Phân loại ESI-3, ESI-4, ESI-5 bằng Machine Learning kết hợp đánh giá nhu cầu cận lâm sàng
        """
        v = request.vitals
        complaint = request.chief_complaint.lower()
        explanations: List[str] = []

        # ==================== LỚP 1A: CHỐT CHẶN NGUY KỊCH (ESI-1) ====================
        if request.consciousness == AVPUConsciousness.UNRESPONSIVE:
            explanations.append("Bệnh nhân hôn mê, không đáp ứng (AVPU = 'U') — Đe dọa sinh mạng tức thì.")
            return TriageClassification(
                esi_level=ESILevel.LEVEL_1,
                is_rule_based=True,
                confidence=1.0,
                explanations=explanations
            )

        cardiac_arrest_keywords = ["ngung tim", "ngưng tim", "ngung tho", "ngưng thở", "ngat tho", "ngạt thở", "soc phan ve", "sốc phản vệ"]
        if any(kw in complaint for kw in cardiac_arrest_keywords):
            explanations.append(f"Triệu chứng kịch phát: '{request.chief_complaint}' — Cần hồi sức tim phổi ngay.")
            return TriageClassification(
                esi_level=ESILevel.LEVEL_1,
                is_rule_based=True,
                confidence=1.0,
                explanations=explanations
            )

        if v.systolic_bp < 65 or (v.heart_rate < 35 and v.systolic_bp < 80):
            explanations.append(f"Huyết áp tụt nghiêm trọng ({v.systolic_bp} mmHg) — Nguy cơ trụy mạch/tử vong.")
            return TriageClassification(
                esi_level=ESILevel.LEVEL_1,
                is_rule_based=True,
                confidence=1.0,
                explanations=explanations
            )

        # ==================== LỚP 1B: RỦI RO CAO / RẤT CẤP (ESI-2) ====================
        is_esi_2 = False
        
        # Chỉ số SpO2 suy hô hấp
        if v.spo2 < 90.0:
            explanations.append(f"SpO2 hạ thấp đáng báo động ({v.spo2}%) < 90% — Suy hô hấp cấp.")
            is_esi_2 = True

        # Chỉ số sốc Shock Index
        shock_index = v.heart_rate / max(v.systolic_bp, 1)
        if shock_index >= 1.05:
            explanations.append(f"Chỉ số sốc (Shock Index = {shock_index:.2f} >= 1.05) — Cảnh báo sốc tuần hoàn.")
            is_esi_2 = True

        # Nhịp tim quá nhanh hoặc quá chậm
        if v.heart_rate > 145:
            explanations.append(f"Nhịp tim nhanh kịch phát ({v.heart_rate} bpm > 145).")
            is_esi_2 = True
        elif v.heart_rate < 45:
            explanations.append(f"Nhịp tim chậm nguy hiểm ({v.heart_rate} bpm < 45).")
            is_esi_2 = True

        # Đau ngực nghi nhồi máu cơ tim hoặc dấu hiệu đột quỵ
        emergent_keywords = [
            "dau nguc", "đau ngực", "kho tho", "khó thở", "tai bien", "tai biến", 
            "yeu nua nguoi", "yếu nửa người", "meo mieng", "méo miệng", "non ra mau", "nôn ra máu"
        ]
        if any(kw in complaint for kw in emergent_keywords):
            explanations.append(f"Bệnh cảnh nghi ngờ biến cố tim mạch/mạch máu não: '{request.chief_complaint}'.")
            is_esi_2 = True

        # Đau dữ dội
        if v.pain_scale >= 9:
            explanations.append(f"Mức độ đau kịch liệt ({v.pain_scale}/10 điểm VAS).")
            is_esi_2 = True

        # Trẻ sơ sinh sốt cao
        if request.age <= 1 and v.temperature >= 38.5:
            explanations.append(f"Trẻ nhũ nhi ({request.age} tuổi) sốt cao {v.temperature}°C — Nguy cơ nhiễm khuẩn huyết.")
            is_esi_2 = True

        if is_esi_2:
            return TriageClassification(
                esi_level=ESILevel.LEVEL_2,
                is_rule_based=True,
                confidence=0.95,
                explanations=explanations
            )

        # ==================== LỚP 2: MACHINE LEARNING & RESOURCE ESTIMATION ====================
        # Dự đoán số lượng tài nguyên cận lâm sàng cần thiết (Resources)
        estimated_resources = self._estimate_resources(complaint, v, request.comorbidities)
        
        # Vector đặc trưng đưa vào model ML: [age, hr, sbp, dbp, rr, spo2, temp, pain, comorb_count, resources]
        features = [[
            request.age,
            v.heart_rate,
            v.systolic_bp,
            v.diastolic_bp,
            v.respiratory_rate,
            v.spo2,
            v.temperature,
            v.pain_scale,
            len(request.comorbidities),
            estimated_resources
        ]]

        try:
            pred_level_int = int(self.ml_model.predict(features)[0])
            pred_esi = ESILevel(pred_level_int)
            probs = self.ml_model.predict_proba(features)[0]
            confidence = float(max(probs))
        except Exception:
            # Fallback heuristic logic nếu ML có vấn đề
            if estimated_resources >= 2:
                pred_esi = ESILevel.LEVEL_3
            elif estimated_resources == 1:
                pred_esi = ESILevel.LEVEL_4
            else:
                pred_esi = ESILevel.LEVEL_5
            confidence = 0.88

        # Sinh lời giải thích minh bạch (Explainable AI)
        if pred_esi == ESILevel.LEVEL_3:
            explanations.append(f"Dự kiến cần đa xét nghiệm/can thiệp (ước tính {estimated_resources} dịch vụ CLS: máu, chẩn đoán hình ảnh).")
            if v.pain_scale >= 6:
                explanations.append(f"Thang điểm đau mức độ vừa-nặng ({v.pain_scale}/10).")
            if len(request.comorbidities) > 0:
                explanations.append(f"Có kèm {len(request.comorbidities)} bệnh lý nền cần theo dõi.")
        elif pred_esi == ESILevel.LEVEL_4:
            explanations.append("Dự kiến chỉ cần 1 xét nghiệm/thủ thuật đơn giản (ví dụ X-quang hoặc tiểu phẫu khâu).")
            explanations.append("Dấu hiệu sinh tồn ổn định, không có rối loạn huyết động.")
        else: # LEVEL_5
            explanations.append("Không cần thực hiện xét nghiệm cận lâm sàng tại phòng cấp cứu.")
            explanations.append("Tình trạng nhẹ, hướng dẫn chuyển khám chuyên khoa ngoại trú.")

        return TriageClassification(
            esi_level=pred_esi,
            is_rule_based=False,
            confidence=round(confidence, 2),
            explanations=explanations
        )

    def _estimate_resources(self, complaint: str, vitals: VitalSigns, comorbidities: list) -> int:
        """Ước tính số nguồn lực chẩn đoán / can thiệp (0, 1, hoặc >=2)"""
        # Các triệu chứng thường cần >= 2 dịch vụ CLS (xét nghiệm máu + ECG/X-quang/CT)
        multi_resource_kw = [
            "sot", "sốt", "dau bung", "đau bụng", "chong mat", "chóng mặt", 
            "non", "nôn", "tieu chay", "tiêu chảy", "kho tho nhe", "khó thở nhẹ"
        ]
        # Các triệu chứng thường chỉ cần 1 dịch vụ (X-quang chi, khâu, thay băng)
        single_resource_kw = [
            "gay tay", "gãy tay", "gay chan", "gãy chân", "trat khop", "trật khớp",
            "rach da", "rách da", "chay mau nhe", "chảy máu nhẹ", "bong gan", "bong gân"
        ]

        if any(kw in complaint for kw in multi_resource_kw) or len(comorbidities) >= 2 or vitals.temperature >= 38.2:
            return 2
        elif any(kw in complaint for kw in single_resource_kw) or vitals.pain_scale >= 5:
            return 1
        else:
            return 0

    def override_triage(self, req: TriageOverrideRequest) -> dict:
        """Ghi nhận yêu cầu can thiệp thủ công từ nhân viên y tế (Override Audit)"""
        log_entry = {
            "patient_id": req.patient_id,
            "new_esi_level": req.new_esi_level.value,
            "reason": req.reason,
            "staff_name": req.staff_name,
            "timestamp": datetime.now().isoformat()
        }
        self.override_audit_logs.append(log_entry)
        return {"status": "SUCCESS", "message": f"Đã cập nhật ESI thành Level {req.new_esi_level.value}", "audit": log_entry}

triage_service = TriageService()

