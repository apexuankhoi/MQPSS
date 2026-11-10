"""
Machine Learning Classifier for ESI Triage (Levels 3, 4, 5)
Uses Decision Tree / Random Forest for high interpretability.
"""

import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier

MODEL_PATH = os.path.join(os.path.dirname(__file__), "triage_rf_model.joblib")

def generate_synthetic_training_data(n_samples: int = 1200):
    """
    Sinh dữ liệu huấn luyện giả lập bám sát phân phối lâm sàng ESI v4
    Features: [age, hr, sbp, dbp, rr, spo2, temp, pain, num_comorbidities, estimated_resources]
    Target: ESI Level (3, 4, 5)
    """
    np.random.seed(42)
    X = []
    y = []

    for _ in range(n_samples):
        # Chọn ngẫu nhiên loại ca (Level 3, 4, hoặc 5)
        level = np.random.choice([3, 4, 5], p=[0.50, 0.35, 0.15])
        
        if level == 3:
            # ESI-3: Cần nhiều cận lâm sàng (máu + xquang/ct), sinh hiệu thường ở mức cảnh báo nhẹ
            age = np.random.randint(18, 80)
            hr = np.random.randint(85, 120)
            sbp = np.random.randint(110, 160)
            dbp = np.random.randint(70, 95)
            rr = np.random.randint(16, 26)
            spo2 = np.random.uniform(92.0, 97.0)
            temp = np.random.uniform(37.0, 39.0)
            pain = np.random.randint(4, 9)
            comorb = np.random.randint(1, 4)
            resources = np.random.randint(2, 5) # >= 2 resources
        elif level == 4:
            # ESI-4: Chỉ cần 1 cận lâm sàng (ví dụ X-quang gãy xương ngón tay, khâu vết thương)
            age = np.random.randint(10, 65)
            hr = np.random.randint(65, 95)
            sbp = np.random.randint(105, 135)
            dbp = np.random.randint(65, 85)
            rr = np.random.randint(14, 20)
            spo2 = np.random.uniform(96.0, 100.0)
            temp = np.random.uniform(36.5, 37.5)
            pain = np.random.randint(2, 6)
            comorb = np.random.randint(0, 2)
            resources = 1 # exactly 1 resource
        else: # level 5
            # ESI-5: Khám thường, kê đơn hoặc tái khám, không cần cận lâm sàng phức tạp
            age = np.random.randint(15, 60)
            hr = np.random.randint(60, 85)
            sbp = np.random.randint(110, 130)
            dbp = np.random.randint(70, 80)
            rr = np.random.randint(12, 18)
            spo2 = np.random.uniform(98.0, 100.0)
            temp = np.random.uniform(36.5, 37.2)
            pain = np.random.randint(0, 3)
            comorb = 0
            resources = 0 # 0 resources

        features = [age, hr, sbp, dbp, rr, spo2, temp, pain, comorb, resources]
        X.append(features)
        y.append(level)

    return np.array(X), np.array(y)

def get_or_train_model():
    """Tải model đã huấn luyện hoặc huấn luyện mới nếu chưa có"""
    if os.path.exists(MODEL_PATH):
        try:
            return joblib.load(MODEL_PATH)
        except Exception:
            pass

    X_train, y_train = generate_synthetic_training_data(1500)
    model = RandomForestClassifier(n_estimators=50, max_depth=6, random_state=42)
    model.fit(X_train, y_train)
    joblib.dump(model, MODEL_PATH)
    return model

