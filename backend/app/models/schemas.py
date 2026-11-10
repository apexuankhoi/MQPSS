"""
Data Models & Schemas for Emergency Triage & Queue Management
"""

from enum import Enum
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class ESILevel(int, Enum):
    LEVEL_1 = 1  # Đỏ: Nguy kịch tức thì (Resuscitation)
    LEVEL_2 = 2  # Cam: Rất cấp (Emergent)
    LEVEL_3 = 3  # Vàng: Cấp tính (Urgent)
    LEVEL_4 = 4  # Xanh: Ít cấp (Less Urgent)
    LEVEL_5 = 5  # Trắng/Ghi: Không cấp (Non-urgent)

class AVPUConsciousness(str, Enum):
    ALERT = "A"          # Tỉnh táo
    VOICE = "V"          # Đáp ứng lời nói
    PAIN = "P"           # Đáp ứng kích thích đau
    UNRESPONSIVE = "U"   # Hôn mê, không đáp ứng (ESI-1)

class DoctorStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    OFF_DUTY = "OFF_DUTY"

class PatientStatus(str, Enum):
    WAITING = "WAITING"
    IN_TREATMENT = "IN_TREATMENT"
    LAB_WAIT = "LAB_WAIT"     # Chờ cận lâm sàng (I/O Wait)
    DISCHARGED = "DISCHARGED"
    TRANSFERRED = "TRANSFERRED"

class VitalSigns(BaseModel):
    heart_rate: int = Field(..., ge=0, le=280, description="Nhịp tim (nhịp/phút)")
    systolic_bp: int = Field(..., ge=0, le=260, description="Huyết áp tâm thu (mmHg)")
    diastolic_bp: int = Field(..., ge=0, le=160, description="Huyết áp tâm trương (mmHg)")
    respiratory_rate: int = Field(..., ge=0, le=60, description="Nhịp thở (lần/phút)")
    spo2: float = Field(..., ge=0.0, le=100.0, description="Độ bão hòa oxy SpO2 (%)")
    temperature: float = Field(..., ge=25.0, le=44.0, description="Nhiệt độ cơ thể (°C)")
    pain_scale: int = Field(0, ge=0, le=10, description="Thang điểm đau VAS (0-10)")

class PatientIntakeRequest(BaseModel):
    patient_id: str
    full_name: str
    age: int = Field(..., ge=0, le=125)
    gender: str = "other"  # male, female, other
    is_pregnant: bool = False
    chief_complaint: str
    consciousness: AVPUConsciousness = AVPUConsciousness.ALERT
    vitals: VitalSigns
    comorbidities: List[str] = Field(default_factory=list) # e.g. ["diabetes", "hypertension", "copd"]
    estimated_burst_time_minutes: float = Field(25.0, ge=5.0, le=180.0)

class TriageClassification(BaseModel):
    esi_level: ESILevel
    is_rule_based: bool
    confidence: float
    explanations: List[str]
    triage_time: datetime = Field(default_factory=datetime.now)

class TriageOverrideRequest(BaseModel):
    patient_id: str
    new_esi_level: ESILevel
    reason: str
    staff_name: str

class Patient(BaseModel):
    patient_id: str
    full_name: str
    age: int
    gender: str
    is_pregnant: bool = False
    chief_complaint: str
    consciousness: AVPUConsciousness
    vitals: VitalSigns
    comorbidities: List[str] = Field(default_factory=list)
    
    # Triage State
    original_esi: ESILevel
    current_esi: ESILevel
    triage_info: TriageClassification
    
    # Timing & Queue State
    arrival_time: datetime = Field(default_factory=datetime.now)
    current_queue: int # 1, 2, 3, 4, 5
    status: PatientStatus = PatientStatus.WAITING
    waiting_time_minutes: float = 0.0
    priority_score: float = 0.0
    estimated_burst_time_minutes: float = 25.0
    
    # Doctor handling
    assigned_doctor_id: Optional[str] = None
    treatment_start_time: Optional[datetime] = None
    treatment_end_time: Optional[datetime] = None
    aged_count: int = 0  # Số lần được thăng hạng do Aging

class Doctor(BaseModel):
    doctor_id: str
    full_name: str
    specialty: str = "Cấp cứu đa khoa"
    status: DoctorStatus = DoctorStatus.AVAILABLE
    current_patient_id: Optional[str] = None
    patients_treated_count: int = 0
    total_treatment_minutes: float = 0.0

class QueueStats(BaseModel):
    queue_1_count: int = 0
    queue_2_count: int = 0
    queue_3_count: int = 0
    queue_4_count: int = 0
    queue_5_count: int = 0
    total_waiting: int = 0
    active_doctors: int = 0
    avg_waiting_time_minutes: float = 0.0
    starvation_risk_count: int = 0
