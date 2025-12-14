let charts = {};

function renderChart(containerId, data, seriesName, dataKey, type_diagram) {
    if (charts[containerId]) {
        charts[containerId].destroy(); // Удаляем предыдущий график, если он существует
    }

    let color;
    switch (seriesName) {
        case 'Латентность':
            color = '#667eea'; // Ярко-красный
            break;
        case 'Эффективность':
            color = '#10b981'; // Бирюзовый
            break;
        case 'Фрагментация':
            color = '#f6d365'; // Голубой
            break;
        case 'Сожженные калории':
            color = '#ff5e62'; // Зеленовато-голубой
            break;
        default:
    }

    charts[containerId] = Highcharts.chart(containerId, {
        credits: {enabled: false},
        colors: [color],
        chart: {type: type_diagram},
        title: {text: `Тренд ${seriesName}`},
        xAxis: {categories: data.dates},
        yAxis: {title: {text: 'Значение'}},
        series: [{
            name: seriesName,
            data: data[dataKey]
        }]
    });
}

function loadPage(params) {
    // Добавляем page_size в каждый AJAX-запрос
    params.page_size = currentPageSize;

    $.ajax({
        url: sleepHistoryAjaxUrl,
        method: 'GET',
        data: params,
        headers: {'X-Requested-With': 'XMLHttpRequest'},
        cache: false,
        success: function (response) {


            // Обновляем графики
            if (response.graph_data_json) {
                const data = response.graph_data_json;
                renderChart('graph-Latency', data, 'Латентность', 'latency_minutes', 'column');
                renderChart('graph-Efficiency', data, 'Эффективность', 'sleep_efficiency', 'line');
                renderChart('graph-Fragmentation', data, 'Фрагментация', 'sleep_fragmentation_index', 'line');
                renderChart('graph-Calories', data, 'Сожженные калории', 'sleep_calories_burned', 'line');
            } else {
                console.warn('Нет данных для графиков в ответе');
            }

            // Обновляем пагинацию
            const pag = $('#pagination');
            pag.empty(); // Очищаем пагинацию

            if (response.has_previous && response.prev_cursor) {
                pag.append(`<a href="#" id="prev-btn" class="btn-hero btn-hero--sm btn-hero--muted" data-cursor="${response.prev_cursor}"> <i class="bi bi-arrow-left"></i></a>`);
            }
            if (response.has_next && response.next_cursor) {
                pag.append(`<a href="#" id="next-btn" class="btn-hero btn-hero--sm btn-hero--muted" data-cursor="${response.next_cursor}">  <i class="bi bi-arrow-right"></i> </a>`);
            }

            // Перепривязываем обработчики
            bindNavigationEvents();
        },
        error: function (xhr, status, error) {
            console.error('Ошибка при загрузке данных:', error);

        }
    });
}

function bindNavigationEvents() {
    // Отменяем предыдущие обработчики чтобы не дублировались
    $(document).off('click', '#prev-btn');
    $(document).off('click', '#next-btn');
    $(document).off('click', '.mode-btn');

    // Привязываем новые обработчики
    $(document).on('click', '#prev-btn', function (e) {
        e.preventDefault();
        const cursor = $(this).data('cursor');
        if (cursor) loadPage({before: cursor});
    });

    $(document).on('click', '#next-btn', function (e) {
        e.preventDefault();
        const cursor = $(this).data('cursor');
        if (cursor) loadPage({after: cursor});
    });

    // Обработчик для кнопок режимов
    $(document).on('click', '.mode-btn', function (e) {
        e.preventDefault();
        const mode = $(this).data('mode');
        const newPageSize = (mode === 'week') ? 7 : 30;

        if (newPageSize !== currentPageSize) {
            currentPageSize = newPageSize;

            // Обновляем активный класс на кнопках
            $('.mode-btn').removeClass('active');
            $(this).addClass('active');

            // Сбрасываем пагинацию и загружаем первую страницу с новым page_size
            loadPage({});  // Без курсоров — первая страница
        }
    });
}

$(document).ready(function () {
    // Инициализация графиков с начальными данными
    const data = initialGraphData;
    renderChart('graph-Latency', data, 'Латентность', 'latency_minutes', 'column');
    renderChart('graph-Efficiency', data, 'Эффективность', 'sleep_efficiency', 'line');
    renderChart('graph-Fragmentation', data, 'Фрагментация', 'sleep_fragmentation_index', 'line');
    renderChart('graph-Calories', data, 'Сожженные калории', 'sleep_calories_burned', 'line');
    bindNavigationEvents();
});