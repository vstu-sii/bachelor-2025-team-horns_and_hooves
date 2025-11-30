from django.urls import path, include

# import debug_toolbar
from .tasks import send_reminder_email
from .views import home, register, user_update, sleep_statistics_show, \
    profile, CustomPasswordResetView, CustomPasswordResetDoneView, CustomPasswordResetConfirmView, \
    CustomPasswordResetCompleteView, sleep_records_from_csv, custom_logout, sleep_history, sleep_fragmentation, \
    sleep_chronotype

urlpatterns = [
    path('send_reminder_email/', send_reminder_email, name='send_reminder_email'),

    path('', home, name='home'),

    path('user-update', user_update, name='user_update'),

    path('sleep-records-from-csv/', sleep_records_from_csv, name='sleep_records_from_csv'),
    path('profile/', profile, name='profile'),
    path('sleep-statistics-show/', sleep_statistics_show, name='sleep_statistics_show'),
    path('register/', register, name='register'),
    path('logout/', custom_logout, name='custom_logout'),

    path('sleep-history/', sleep_history, name='sleep_history'),
    path('sleep-fragmentation/', sleep_fragmentation, name='sleep_fragmentation'),

    path('sleep-chronotype/', sleep_chronotype, name='sleep_chronotype'),

    path('custom-password-reset-confirm/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(),
         name='custom_password_reset_confirm'),
    path('custom-password-reset-done/', CustomPasswordResetDoneView.as_view(), name='custom_password_reset_done'),
    path('custom-password-reset/', CustomPasswordResetView.as_view(), name='custom_password_reset'),
    path('custom-password-complete/', CustomPasswordResetCompleteView.as_view(), name='custom_password_reset_complete'),

    # path('__debug__/', include(debug_toolbar.urls)),
]
