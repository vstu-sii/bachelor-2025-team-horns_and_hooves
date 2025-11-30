from django.contrib import admin


from .models import SleepRecord, SleepStatistics, UserData


# Register your models here.
class UserDataAdmin(admin.ModelAdmin):
    search_fields = ['user_name', 'weight', 'gender', 'height', 'active']

    def user_name(self, obj):
        return obj.user.username


class SleepRecordAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'sleep_date_time', 'sleep_deep_duration', 'sleep_light_duration']
    list_filter = ['user']
    search_fields = ['user', 'sleep_date_time', 'sleep_deep_duration', 'sleep_light_duration']

    def user_name(self, obj):
        return obj.user.username


class SleepStatisticsAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'sleep_duration', 'sleep_quality', 'health_impact', 'date', 'calories_burned']
    list_filter = ['user', 'sleep_duration', 'sleep_quality']
    search_fields = ['user', 'sleep_duration', 'sleep_quality']

    def delete_model(self, request, obj):
        # Удаляем все записи SleepStatistics, связанные с удаляемым пользователем
        SleepStatistics.objects.filter(user=obj.user).delete()

    def user_name(self, obj):
        return obj.user.username


admin.site.register(UserData, UserDataAdmin)
admin.site.register(SleepRecord, SleepRecordAdmin)
admin.site.register(SleepStatistics, SleepStatisticsAdmin)
