from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


SmokingHistory = Literal["never", "former", "current"]
StressLevel = Literal["low", "moderate", "high"]
DietType = Literal["balanced", "high-carb", "high-fat", "low-sugar", "vegetarian", "other"]
WorkType = Literal["sedentary", "active", "mixed"]


class PredictRequest(BaseModel):
    gender: Literal["Male", "Female", "Other"]
    age: int = Field(..., ge=0, le=120)
    bmi: float = Field(..., ge=10.0, le=60.0)
    blood_glucose_level: float = Field(..., ge=50.0, le=400.0)
    hba1c_level: float = Field(..., ge=3.0, le=14.0)
    smoking_history: SmokingHistory
    hypertension: int = Field(..., ge=0, le=1)
    heart_disease: int = Field(..., ge=0, le=1)
    activity_level: Literal["low", "moderate", "high"] = Field(default="moderate")
    sleep_hours: float = Field(..., ge=0.0, le=24.0)
    stress_level: StressLevel = Field(default="moderate")
    diet_type: DietType = Field(default="balanced")
    work_type: WorkType = Field(default="mixed")
    blood_pressure: str | None = None


class SimulateRequest(PredictRequest):
    simulate_bmi: float | None = Field(None, ge=10.0, le=60.0)
    simulate_smoking_history: SmokingHistory | None = None
    simulate_blood_glucose_level: float | None = Field(None, ge=50.0, le=400.0)
    simulate_activity_level: Literal["low", "moderate", "high"] | None = None
    simulate_sleep_hours: float | None = Field(None, ge=0.0, le=24.0)


class HealthRecordCreateRequest(PredictRequest):
    notes: str | None = None


class HealthRecordResponse(BaseModel):
    id: int
    created_at: datetime
    recorded_at: datetime
    gender: Literal["Male", "Female", "Other"]
    age: int
    bmi: float
    blood_glucose_level: float
    hba1c_level: float
    smoking_history: SmokingHistory
    hypertension: int
    heart_disease: int
    activity_level: Literal["low", "moderate", "high"]
    sleep_hours: float
    stress_level: StressLevel
    diet_type: DietType
    work_type: WorkType
    blood_pressure: str | None = None
    notes: str | None = None


class PredictionHistorySummary(BaseModel):
    id: int
    created_at: datetime
    diabetes_risk: float
    diabetes_risk_level: str
    heart_risk_level: str
    overall_health_score: float
    bmi_status: str
    risk_breakdown: dict


class PredictionHistoryPoint(BaseModel):
    created_at: datetime
    diabetes_risk: float
    heart_disease_risk: float
    hypertension_risk: float
    overall_health_score: float


class TaskCreateRequest(BaseModel):
    task_date: date = Field(default_factory=date.today)
    title: str = Field(..., min_length=2, max_length=255)
    notes: str | None = Field(None, max_length=2000)
    completed: bool = False


class TaskUpdateRequest(BaseModel):
    task_id: int
    completed: bool
    notes: str | None = Field(None, max_length=2000)


class TaskRescheduleRequest(BaseModel):
    target_date: date | None = None


class ReportQuery(BaseModel):
    # If not provided, uses the latest prediction for that user.
    prediction_id: int | None = None


class ProgressQuery(BaseModel):
    pass


class ApiResponse(BaseModel):
    ok: bool = True
    data: Any
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class SignupRequest(BaseModel):
    user_id: str = Field(..., min_length=3, max_length=128, description="Email address")
    password: str = Field(..., min_length=8, max_length=255)


class LoginRequest(BaseModel):
    user_id: str = Field(..., min_length=3, max_length=128, description="Email address")
    password: str = Field(..., min_length=8, max_length=255)


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str


class MeResponse(BaseModel):
    user_id: str


class ProfileResponse(BaseModel):
    user_id: str
    full_name: str | None = None
    date_of_birth: date | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    locale: str = "en"
    medical_history: dict = Field(default_factory=dict)


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(None, max_length=255)
    date_of_birth: date | None = None
    height_cm: float | None = Field(None, ge=0.0, le=300.0)
    weight_kg: float | None = Field(None, ge=0.0, le=500.0)
    locale: str | None = Field(None, max_length=32)
    medical_history: dict | None = None


class DeviceReadingCreateRequest(BaseModel):
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field(default="manual", max_length=64)
    heart_rate_bpm: float | None = Field(None, ge=0.0, le=300.0)
    steps: int | None = Field(None, ge=0, le=300000)
    sleep_minutes: int | None = Field(None, ge=0, le=24 * 60)
    payload: dict = Field(default_factory=dict)


class AlertResponse(BaseModel):
    id: int
    created_at: datetime
    severity: str
    category: str
    title: str
    message: str
    acknowledged: bool
    meta: dict = Field(default_factory=dict)


class AlertAckRequest(BaseModel):
    alert_id: int
    acknowledged: bool = True


class GoalCreateRequest(BaseModel):
    goal_type: str = Field(..., max_length=64)
    target_value: float
    deadline: date | None = None
    notes: str | None = Field(None, max_length=2000)


class GoalUpdateRequest(BaseModel):
    goal_id: int
    target_value: float | None = None
    deadline: date | None = None
    status: str | None = Field(None, max_length=16)
    progress_value: float | None = None
    notes: str | None = Field(None, max_length=2000)


class BehaviorLogCreateRequest(BaseModel):
    category: str = Field(..., max_length=64)
    value: dict = Field(default_factory=dict)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    reply: str
    suggested_actions: list[str] = Field(default_factory=list)
