from typing import List, Dict, Any
from django.contrib.auth.models import User
from sleep_tracking_app.models import UserData, SleepStatistics, SleepRecord


def get_test_scenarios_from_db(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Берём последние N пользователей с данными по сну
    и собираем сценарии вида:
    {
      "id": "<user_id>:<date>",
      "description": "...",
      "user_data": UserData,
      "sleep_stats": SleepStatistics,
      "sleep_record": SleepRecord
    }
    """
    scenarios: List[Dict[str, Any]] = []

    # Берём последних активных пользователей с UserData
    users = (
        User.objects
        .filter(user_data__isnull=False)
        .order_by("-date_joined")[:limit]
    )

    for user in users:
        try:
            user_data = user.user_data  # OneToOne
        except UserData.DoesNotExist:
            continue

        # последняя статистика сна
        stat = (
            SleepStatistics.objects
            .filter(user=user)
            .order_by("-date")
            .first()
        )
        if not stat:
            continue

        # ближайшая запись сна по дате
        record = (
            SleepRecord.objects
            .filter(user=user, sleep_date_time__date=stat.date)
            .order_by("-sleep_date_time")
            .first()
        )
        if not record:
            continue

        scenarios.append({
            "id": f"user_{user.id}_{stat.date.isoformat()}",
            "description": f"Пользователь {user.id}, дата {stat.date}",
            "user_data": user_data,
            "sleep_stats": stat,
            "sleep_record": record,
        })

    return scenarios
