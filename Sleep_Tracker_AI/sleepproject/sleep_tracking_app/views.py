import json
import os
from typing import Optional
import uuid

from cursor_pagination import CursorPaginator

from django.views.decorators.cache import cache_page
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetCompleteView, PasswordResetView
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.utils import timezone
from django.core.files.storage import FileSystemStorage

from .sleep_statistic import get_sleep_phases_pie_data, get_heart_rate_bell_curve_data, chronotype_assessment, \
    sleep_regularity, get_sleep_efficiency_trend, get_sleep_duration_trend, avg_sleep_duration

from .tasks import import_sleep_records, sleep_recommended
from sleepproject.settings import MEDIA_ROOT

from .forms import UserRegistrationForm, UserDataForm, UserInfoUpdateForm, \
    CSVImportForm
from .models import SleepRecord, SleepStatistics, UserData

# Create your views here.
# python-benedict

today = timezone.now()


def home(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'home.html')


def register(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        user_data_form = UserDataForm(request.POST)
        if user_form.is_valid() and user_data_form.is_valid():
            user = user_form.save()
            user_data = user_data_form.save(commit=False)
            user_data.user = user
            user_data.save()
            return redirect('home')
    else:
        user_form = UserRegistrationForm()
        user_data_form = UserDataForm()
    return render(request, 'registration/register.html', {'user_form': user_form, 'user_data_form': user_data_form})


@login_required
def custom_logout(request: HttpRequest) -> HttpResponse:
    # Выход из текущей учетной записи
    logout(request)
    # Перенаправление на главную страницу
    return redirect('home')


@login_required
def user_update(request: HttpRequest) -> HttpResponse:
    user = request.user

    user_data = UserData.objects.get(user=user)

    if request.method == 'POST':
        form = UserInfoUpdateForm(request.POST, instance=user)
        user_data_form = UserDataForm(request.POST, instance=user_data)

        if form.is_valid() and user_data_form.is_valid():
            user = form.save()
            user_data = user_data_form.save(commit=False)
            user_data.user = user
            user_data.save()
            return redirect('profile')
    else:
        form = UserInfoUpdateForm(instance=user)
        user_data_form = UserDataForm(instance=user_data)

    context = {
        'form': form,
        'user_data_form': user_data_form,
    }

    return render(request, 'update_user.html', context)


@login_required
def profile(request: HttpRequest) -> HttpResponse:
    user = request.user
    user_data = UserData.objects.get(user=user)
    context = {
        'user': user,
        'user_data': user_data,
    }
    return render(request, 'web/profile.html', context)


@login_required
def sleep_records_from_csv(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        csv_file = request.FILES['csv_file']
        fs = FileSystemStorage(location=os.path.join(MEDIA_ROOT, 'tmp'))
        unique_filename = f'{uuid.uuid4()}_{csv_file.name}'
        filename = fs.save(unique_filename, csv_file)
        tmp_path = fs.path(filename)

        # запускаем Celery‑таску
        task = import_sleep_records.delay(request.user.id, tmp_path)

        return JsonResponse({'task_id': task.id})

    return render(request, 'sleep_records_from_csv.html', {'form': CSVImportForm()})


@login_required
def sleep_statistics_show(request: HttpRequest) -> HttpResponse:
    user = request.user
    user_data = get_object_or_404(UserData, user=request.user)

    sleep_statistics_list = SleepStatistics.objects.only('id', 'user', 'recommended', 'sleep_calories_burned',
                                                    'sleep_efficiency', 'sleep_phases').filter(user=user).order_by(
        '-date')

    sleep_statistics = sleep_statistics_list.first() if sleep_statistics_list else None

    # Получаем записи сна за 7 дней с сортировкой по убыванию даты
    sleep_records = list(SleepRecord.get_last_sleep_records(user=user))


    last_record = sleep_records[0] if sleep_records else None

    rec = None
    task_id = None

    if sleep_statistics and not sleep_statistics.recommended and not request.GET.get("poll"):
        # Создаём задачу Celery, если ещё нет рекомендации
        task = sleep_recommended.delay(
            user_data_id=user_data.id,
            sleep_statistics_id=[s.id for s in sleep_statistics_list],
            sleep_record_id=[r.id for r in sleep_records]
        )
        task_id = task.id
    else:
        rec = sleep_statistics.recommended if sleep_statistics else None

    # Пагинация
    page_size = int(request.GET.get('page_size', 7))
    qs = SleepRecord.get_delta_days_sleep_records(user)

    paginator = CursorPaginator(qs, ordering=('-sleep_date_time', '-id'))

    after = request.GET.get('after')
    before = request.GET.get('before')

    if before:
        page = paginator.page(last=page_size, before=before)
    else:
        page = paginator.page(first=page_size, after=after)

    # Курсоры для ответа
    next_cursor: Optional[str] = paginator.cursor(page[-1]) if page and page.has_next else None
    prev_cursor: Optional[str] = paginator.cursor(page[0]) if page and page.has_previous else None

    # Подготовка данных для графика
    graph_data = get_sleep_duration_trend(page)

    # Метрики
    metric = {
        'chronotype': chronotype_assessment(sleep_records=sleep_records) if sleep_records else {},
        'sleep_regularity': sleep_regularity(sleep_records=sleep_records) if sleep_records else {},
        'avg_sleep_duration': avg_sleep_duration(page) if page else 0,
        'calories_burned': getattr(sleep_statistics, 'sleep_calories_burned', 0),
        'sleep_efficiency': round(getattr(sleep_statistics, 'sleep_efficiency', 0), 2),
    }

    # Подготовка plot_data
    first_date = graph_data['dates'][0] if graph_data.get('dates') else 0
    last_date = graph_data['dates'][-1] if graph_data.get('dates') else 0

    phases = get_sleep_phases_pie_data(sleep_statistics)
    heart_rate = get_heart_rate_bell_curve_data(last_record)

    plot_data = {
        'phases': phases,
        'graph_data': graph_data,
        'heart_rate': heart_rate,
        'first_date': first_date,
        'last_date': last_date,
    }

    # AJAX-ответ
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        rec = sleep_statistics.recommended if sleep_statistics else None
        return JsonResponse({
            'has_next': page.has_next,
            'has_previous': page.has_previous,
            'next_cursor': next_cursor,
            'prev_cursor': prev_cursor,
            'graph_data': graph_data,
            'first_date': first_date,
            'last_date': last_date,
            'metric': metric,
            'rec': rec,
            'task_id': task_id

        })

    # Передаём контекст
    context = {
        'page': page,
        'graph_data': graph_data,
        'metric': metric,
        'plot_data': plot_data,
        'page_size': page_size,
        'rec': rec,
        'task_id': task_id,
        'next_cursor': next_cursor,
        'prev_cursor': prev_cursor,

    }

    return render(request, 'sleep_statistic/sleep_statistics_show.html', context)


@login_required
@cache_page(60 * 15)
def sleep_history(request: HttpRequest) -> HttpResponse:
    user = request.user

    page_size = int(request.GET.get('page_size', 7))

    qs = SleepStatistics.get_delta_days_sleep_statistics(user)

    paginator = CursorPaginator(qs, ordering=('-date', '-id'))

    # Получаем курсоры из GET
    after = request.GET.get('after')  # ссылка на следующий блок (страница вперёд)
    before = request.GET.get('before')  # ссылка на предыдущий блок (страница назад)

    if before:
        # Если есть курсор before, то получаем предыдущую страницу
        page = paginator.page(last=page_size, before=before)
    else:
        # Если курсора before нет, то получаем первую страницу
        page = paginator.page(first=page_size, after=after)

    next_cursor: Optional[str] = paginator.cursor(page[-1]) if page and page.has_next else None
    prev_cursor: Optional[str] = paginator.cursor(page[0]) if page and page.has_previous else None

    # Преобразуем в JSON для графика
    graph_data_json = get_sleep_efficiency_trend(page)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Если запрос AJAX, возвращаем только HTML таблицы и курсоры
        return JsonResponse({

            'has_next': page.has_next,
            'has_previous': page.has_previous,
            'next_cursor': next_cursor,
            'prev_cursor': prev_cursor,
            'graph_data_json': graph_data_json,
        })

    context = {

        'has_next': page.has_next,
        'has_previous': page.has_previous,
        'next_cursor': next_cursor,
        'prev_cursor': prev_cursor,
        'graph_data_json': json.dumps(graph_data_json),
        'page_size': page_size,

    }

    return render(request, 'sleep_statistic/sleep_history.html', context)


@login_required
def sleep_fragmentation(request: HttpRequest) -> HttpResponse:
    return render(request, 'sleep_statistic/sleep_fragmentation.html')


@login_required
def sleep_chronotype(request: HttpRequest) -> HttpResponse:
    return render(request, 'sleep_statistic/sleep_chronotype.html')


class CustomPasswordResetView(PasswordResetView):
    template_name = 'system/user_password_reset.html'
    email_template_name = 'system/password_reset_email.html'
    success_url = reverse_lazy('custom_password_reset_done')


class CustomPasswordResetDoneView(TemplateView):
    template_name = 'system/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'system/password_reset_confirm.html'
    success_url = reverse_lazy('custom_password_reset_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'system/password_reset_complete.html'

# taskkill /F /IM celery.exe
