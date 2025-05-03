import os
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-very-secret-key-here'
    CSV_FILE = 'patient_data.csv'
    BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    PUBLIC_FIELDS = ["patient_id", "name", "created_at"]
    PRIVATE_FIELDS = [
        "age", "gender", "blood_group", "diagnosis",
        "prescribed_meds", "generic_alternatives",
        "dosages", "allergies", "notes"
    ]
SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'