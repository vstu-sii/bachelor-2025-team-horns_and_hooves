// Получение данных для графика
/*document.addEventListener("DOMContentLoaded", () => {
    var graphPhaseData = JSON.parse(document.getElementById('graphPhaseChart').value);
    var graphDurationQualityData = JSON.parse(document.getElementById('graphDurationQualityChart').value);
    var graphSleepDeepFastData = JSON.parse(document.getElementById('graphSleepDeepFastChart').value);
    var graphQualityData = JSON.parse(document.getElementById('graphQualityChart').value);

    // График для graphPhaseData
    Highcharts.chart('graph-Phase-Chart', {
        credits: {
            enabled: false
        },
        chart: {
            type: 'line'
        },
        title: {
            text: 'Общее время сна (часы)'
        },
        xAxis: {
            categories: graphPhaseData.dates
        },
        yAxis: {
            title: {
                text: 'Продолжительность сна'
            }
        },
        series: [{
            name: 'Продолжительность сна',
            data: graphPhaseData.sleep_duration,
        }]
    });

    // График для graphDurationQualityData
    Highcharts.chart('graph-Duration-QualityChart', {
        credits: {
            enabled: false
        },
        chart: {
            type: 'column'
        },
        title: {
            text: 'Зависимость продолжительности и качестве сна'
        },
        xAxis: {
            categories: graphDurationQualityData.dates
        },
        yAxis: [{
            title: {
                text: 'Продолжительность сна (часы)'
            }
        }, {
            title: {
                text: 'Качество сна (%)'
            },
            opposite: true
        }],
        series: [{
            name: 'Продолжительность сна (часы)',
            data: graphDurationQualityData.sleep_duration,
            yAxis: 0
        }, {
            name: 'Качество сна',
            data: graphDurationQualityData.sleep_quality,
            yAxis: 1
        }]
    });

    // График для graphSleepDeepFastData
    Highcharts.chart('graph-Sleep-DeepFastChart', {
        credits: {
            enabled: false
        },
        chart: {
            type: 'column'
        },
        title: {
            text: 'Зависимость глубокой и лёгкой фазы сна (часы)'
        },
        xAxis: {
            categories: graphSleepDeepFastData.dates
        },
        yAxis: {
            title: {
                text: 'Продолжительность сна (часы)'
            }
        },
        series: [{
            name: 'Фаза глубоко сна (часы)',
            data: graphSleepDeepFastData.deep_sleep_duration
        }, {
            name: 'Фаза лёгкого сна (часы)',
            data: graphSleepDeepFastData.fast_sleep_duration
        }]
    });

    // График для graphQualityData
    Highcharts.chart('graph-Quality-Chart', {
        credits: {
            enabled: false
        },
        chart: {
            type: 'line'
        },
        title: {
            text: 'Качество сна (%)'
        },
        xAxis: {
            categories: graphQualityData.dates
        },
        yAxis: {
            title: {
                text: 'Качество сна (%)'
            }
        },
        series: [{
            name: 'Качество сна (%)',
            data: graphQualityData.sleep_quality
        }]
    });
});
*/
let charts = {};

function VariableRadius(containerId, data) {
    charts[containerId] = Highcharts.chart(containerId, {
        credits: {enabled: false},

        chart: {type: 'variablepie'},
        title: {text: `Фазы сна`},

        series: [{
            innerSize: '20%',
            borderRadius: 5,
            name: 'Фаза сна',
            data: data,
            colors: [
                '#64bff7',
                '#8053d5',
                '#45c454',
                '#ffad61',


            ],
            tooltip: {
                // Убираем headerFormat, указываем только pointFormat
                headerFormat: '',
                pointFormat: '<strong>{point.name}</strong>: {point.y}%'
            }
        }]
    });
}


function DurationLiner(containerId, data, seriesName, dataKey) {
    if (charts[containerId]) {
        charts[containerId].destroy(); // Удаляем предыдущий график, если он существует
    }

    charts[containerId] = Highcharts.chart(containerId, {
        credits: {enabled: false},
        chart: {type: 'line'},
        colors: ['#10b981'],
        title: {text: `${seriesName}`},
        xAxis: {categories: data.dates},
        yAxis: {title: {text: 'Значение, мин'}},
        series: [{
            name: 'Продолжительность сна',
            data: data[dataKey]
        }]
    });
}

function loadPage(params) {
    // Добавляем page_size в каждый AJAX-запрос
    params.page_size = currentPageSize;


    $.ajax({
        url: sleepRecordAJAXUrl,
        method: 'GET',
        data: params,
        headers: {'X-Requested-With': 'XMLHttpRequest'},
        cache: false,
        success: function (response) {

            // Обновляем графики
            if (response.graph_data) {
                const data = response.graph_data;
                DurationLiner('graph-Duration', data, 'Продолжительность сна', 'sleep_duration');

            }

            // Обновляем заголовок
            const titleElement = $('#sleep-graph-title');
            if (response.first_date && response.last_date) {
                titleElement.text(`Тенденции и статистика вашего сна с ${response.first_date} по ${response.last_date}`);
            }


            // Обновляем текст о количестве записей
            const countElement = $('#count_sleep');
            countElement.text(`Здесь отображается, сколько вы спали каждый день за последние ${currentPageSize} суток.`);

            // Обновляем текст о средней продолжительности сна
            const avgDurationElement = $('#avg_duration');
            avgDurationElement.text(`${response.metric.avg_sleep_duration} часов.`);

            // Обновляем пагинацию
            const pag = $('#pagination');
            pag.empty(); // Очищаем пагинацию

            if (response.has_previous && response.prev_cursor) {
                pag.append(`<a href="#" id="prev-btn" class="btn btn-sm btn-outline-secondary" data-cursor="${response.prev_cursor}"> <i class="bi bi-chevron-left"></i></a>`);
            }
            if (response.has_next && response.next_cursor) {
                pag.append(`<a href="#" id="next-btn" class="btn btn-sm btn-outline-secondary" data-cursor="${response.next_cursor}"> <i class="bi bi-chevron-right"></i></a>`);
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


function BPMGraph(containerId, heartRateData) {
    const bpmValues = heartRateData.bpm.map(Number);

    // Используем индекс к
    const points = bpmValues.map((v, i) => ({
        x: v,
        y: i + 1,
        name: heartRateData.date ? heartRateData.date[i] : ''
    }));

    Highcharts.chart(containerId, {
        credits: {enabled: false},

        chart: {zoomType: 'x'},
        title: {text: 'Распределение пульса'},

        xAxis: [{
            title: {text: 'Пульс (уд/мин)'},
            alignTicks: true,
            gridLineWidth: 0
        }],

        yAxis: [
            {
                title: {text: '№ измерения'},
                gridLineWidth: 0,
            },
            {
                title: {text: 'Плотность вероятности'},
                opposite: true
            }
        ],

        plotOptions: {
            bellcurve: {
                color: '#8053d5',
                fillColor: 'rgba(128, 83, 213, 0.1)',
                lineWidth: 2,
                tooltip: {
                    headerFormat: '',
                    pointFormat: 'Плотность: <b>{point.y:.4f}</b>',

                }
            },
            scatter: {
                marker: {radius: 3, symbol: 'circle'},
                color: '#ff5e62',
                tooltip: {pointFormat: 'Пульс: <b>{point.x}</b> уд/мин<br/>Время: {point.name}'}
            }
        },

        series: [
            {
                name: 'base-bpm',
                type: 'scatter',
                data: bpmValues,
                visible: false,
                showInLegend: false,
                enableMouseTracking: false
            },
            {
                name: 'Замеры пульса',
                type: 'scatter',
                yAxis: 0,
                data: points
            },
            {
                name: 'Колоколообразная кривая',
                type: 'bellcurve',
                baseSeries: 0,
                xAxis: 0,
                yAxis: 1,
                zIndex: -1
            }
        ]
    });
}



$(document).ready(function () {
    // Инициализация графиков с начальными данными
    const data = initialGraphData;
    VariableRadius('graph-Phase', data.phases);
    DurationLiner('graph-Duration', data.graph_data, 'Продолжительность сна', 'sleep_duration');
    BPMGraph('graph-BPM', data.heart_rate);
    bindNavigationEvents();
});