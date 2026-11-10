"""
End-to-End Integration Tests for FastAPI Endpoints & Static Files
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_root_serves_frontend():
    """Kiểm tra endpoint GET / phục vụ giao diện HTML Dashboard"""
    response = client.get("/")
    assert response.status_code == 200
    assert "MQPSS" in response.text
    assert "Hệ Thống Phân Loại & Lập Lịch Bệnh Nhân Cấp Cứu" in response.text

def test_api_demo_seed_and_dispatch_flow():
    """
    Kiểm tra luồng trọn vẹn:
    1. Nạp ca mẫu qua /demo/seed
    2. Kiểm tra hàng đợi có bệnh nhân
    3. Bác sĩ gọi nhận ca tiếp theo
    4. Hoàn tất ca bệnh
    """
    # 1. Seed demo
    seed_res = client.post("/api/v1/demo/seed")
    assert seed_res.status_code == 200
    assert seed_res.json()["status"] == "SEEDED"
    
    # 2. Get queues snapshot
    q_res = client.get("/api/v1/queues")
    assert q_res.status_code == 200
    snapshot = q_res.json()
    assert snapshot["stats"]["total_waiting"] >= 5

    # 3. Doctor BS-02 calls next patient
    call_res = client.post("/api/v1/doctors/BS-02/call-next")
    assert call_res.status_code == 200
    call_data = call_res.json()
    assert call_data["status"] == "DISPATCHED"
    dispatched_pid = call_data["patient"]["patient_id"]

    # 4. Finish treatment
    fin_res = client.post(f"/api/v1/patients/{dispatched_pid}/finish")
    assert fin_res.status_code == 200
    assert fin_res.json()["status"] == "FINISHED"

def test_api_trigger_aging():
    """Kiểm tra gọi trigger dynamic aging qua API"""
    res = client.post("/api/v1/aging/trigger")
    assert res.status_code == 200
    assert "promotions_count" in res.json()

def test_api_simulation_fast_forward_and_mci():
    """Kiểm tra chức năng tua nhanh thời gian và kích hoạt thảm họa hàng loạt"""
    # 1. Tua nhanh thời gian thêm 35 phút
    ff_res = client.post("/api/v1/simulation/fast-forward-time?minutes=35.0")
    assert ff_res.status_code == 200
    assert ff_res.json()["status"] == "TIME_ADVANCED"
    assert ff_res.json()["minutes_added"] == 35.0

    # 2. Kích hoạt Mass Casualty Surge
    mci_res = client.post("/api/v1/simulation/mass-casualty-surge")
    assert mci_res.status_code == 200
    assert mci_res.json()["status"] == "MCI_TRIGGERED"
    assert mci_res.json()["admitted_count"] == 4

