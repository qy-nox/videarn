import json
import firebase_admin
from firebase_admin import auth, credentials
from app.core.config import get_settings

def verify_firebase_token(id_token: str) -> dict:
    settings = get_settings()
    if not firebase_admin._apps:
        if settings.firebase_service_account_json:
            firebase_admin.initialize_app(credentials.Certificate(json.loads(settings.firebase_service_account_json)))
        else:
            firebase_admin.initialize_app(options={"projectId": settings.firebase_project_id})
    return auth.verify_id_token(id_token)
