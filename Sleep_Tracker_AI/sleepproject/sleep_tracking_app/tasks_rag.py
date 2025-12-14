from celery import shared_task
from sleep_tracking_app.rag.rag_service import RagService

@shared_task(bind=True)
def enhance_recommendation_task(self, gemini_response: str, user_data: dict):
    svc = RagService()
    return svc.enhance(gemini_response, user_data)
