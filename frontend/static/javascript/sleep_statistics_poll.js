function pollRecommendations() {
    const recommendationBlock = $('#recommendation-block');

    $.ajax({
        url: window.location.href, // текущий URL
        method: 'GET',
        headers: {'X-Requested-With': 'XMLHttpRequest'},
        data: {poll: true},
        success: function(response) {
            if (response.rec) {
                recommendationBlock.html(`
                    <div>${response.rec.replace(/\n/g, '<br>')}</div>
                    <div class="mt-3">
                        Эффективность вашего сна составляет <strong>${response.metric.sleep_efficiency}%</strong>
                    </div>`);
            } else {
                // повторяем через 5 секунд, пока Celery не закончит
                setTimeout(pollRecommendations, 5000);
            }
        },
        error: function() {
            console.error('Ошибка при загрузке данных:', error);
        }
    });
}

$(document).ready(function() {
    // запускаем только если блок рекомендаций пустой или task_id есть
    if ($('#recommendation-block').length && $('#recommendation-block').text().includes("Рекомендации обрабатываются")) {
        pollRecommendations();
    }
});
