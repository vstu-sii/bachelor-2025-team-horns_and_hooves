Dropzone.options.csvDropzone = {
    paramName: 'csv_file',
    maxFiles: 13,
    parallelUploads: 3,
    acceptedFiles: '.csv',
    autoProcessQueue: true,

    init: function () {
        const progressBarWrapper = document.getElementById('progress-bar-wrapper');
        const errorElement = document.getElementById('file-type-error');
        const dzInstance = this;  // Сохраняем ссылку на экземпляр Dropzone


        // Обработчик добавления файла
        this.on('addedfile', function (file) {
            errorElement.style.display = 'none';

            // Проверка расширения файла
            const extension = file.name.split('.').pop().toLowerCase();
            if (extension !== 'csv') {
                errorElement.style.display = 'block';
                dzInstance.removeFile(file);  // Используем сохраненную ссылку
                return false;  // Блокируем обработку файла
            }
        });

        this.on('success', function (file, response) {
            const taskId = response.task_id;
            const taskProgress = document.getElementById('tasks-progress');

            taskProgress.style.display = 'block';
            const fileName = file.name.length > 10 ? file.name.substring(0, 10) + '...' : file.name;

            // Создаём контейнер для каждого таска
            const wrapper = document.createElement('div');
            wrapper.id = `progress-${taskId}`;
            wrapper.innerHTML = `
              <div class="progress-wrapper">
                <div id="bar-${taskId}" class="progress-bar" style="background-color: #69a9ef; width: 0;"></div>
              </div>
              <div id="msg-${taskId}">Ожидание...</div>
            `;
            taskProgress.appendChild(wrapper);

            const progressUrl = `/celery-progress/${taskId}/`;

            CeleryProgressBar.initProgressBar(progressUrl, {
                progressBarId: `bar-${taskId}`,        // ваш id бара
                progressBarMessageId: `msg-${taskId}`,    // ваш id сообщения
                pollInterval: 500,

                onSuccess: function () {
                    document.getElementById(`msg-${taskId}`).textContent = `Загрузка файла ${fileName} завершена`;
                     setTimeout(() => window.location.reload(), 10000);
                },
                onError: function () {
                    document.getElementById(`msg-${taskId}`).textContent = `Ошибка при загрузке файла ${fileName}`;
                    setTimeout(() => window.location.reload(), 5000);
                }
            });
        });


        this.on('error', function (file, errorMessage) {
            progressBarWrapper.style.display = 'none';

            // Показываем кастомную ошибку для неподдерживаемых типов
            if (errorMessage.includes('You can\'t upload files of this type')) {
                errorElement.style.opacity = '0';
                errorElement.style.display = 'block';
                errorElement.style.transition = 'opacity 0.5s';
                setTimeout(() => {
                    errorElement.style.opacity = '1';
                    setTimeout(() => {
                        errorElement.style.opacity = '0';
                        setTimeout(() => {
                            errorElement.style.display = 'none';
                        }, 500);
                    }, 1000);
                }, 10);
                this.removeFile(file);
            } else {
                alert('Ошибка при загрузке: ' + errorMessage);
            }
        }.bind(this));
    }
};