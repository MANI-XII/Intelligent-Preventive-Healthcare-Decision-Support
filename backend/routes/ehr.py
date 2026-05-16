from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import User
from backend.utils.auth import get_current_user

router = APIRouter(prefix="/ehr", tags=["ehr"])


@router.get("/records")
def get_ehr_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mock EHR integration - returns simulated medical records"""
    # In a real implementation, this would connect to HL7 FHIR API or hospital database

    mock_ehr_data = {
        "patient_id": current_user.user_id,
        "medical_history": {
            "conditions": [
                {
                    "condition": "Hypertension",
                    "onset_date": "2020-03-15",
                    "status": "active",
                    "severity": "moderate"
                },
                {
                    "condition": "Type 2 Diabetes",
                    "onset_date": "2021-07-22",
                    "status": "active",
                    "severity": "mild"
                }
            ],
            "medications": [
                {
                    "name": "Metformin",
                    "dosage": "500mg twice daily",
                    "start_date": "2021-07-22",
                    "status": "active"
                },
                {
                    "name": "Lisinopril",
                    "dosage": "10mg daily",
                    "start_date": "2020-03-15",
                    "status": "active"
                }
            ],
            "allergies": [
                {
                    "allergen": "Penicillin",
                    "reaction": "Rash",
                    "severity": "moderate"
                }
            ],
            "lab_results": [
                {
                    "test": "HbA1c",
                    "value": "7.2%",
                    "date": "2024-01-15",
                    "reference_range": "4.0-5.6%"
                },
                {
                    "test": "Blood Pressure",
                    "value": "140/90 mmHg",
                    "date": "2024-01-15",
                    "reference_range": "<120/80 mmHg"
                }
            ]
        },
        "last_updated": "2024-01-15T10:30:00Z",
        "source": "Mock Hospital EHR System"
    }

    return {"ok": True, "data": mock_ehr_data}


@router.post("/sync")
def sync_ehr_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sync EHR data with user profile"""
    # In real implementation, this would update user profile with EHR data

    # For now, just return success
    return {"ok": True, "message": "EHR data synced successfully"}