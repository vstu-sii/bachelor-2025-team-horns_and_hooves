# sleepproject/settings_ci.py
from .settings import *
import tempfile
import os

# ===== БАЗА ДАННЫХ =====
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# ===== ХРАНИЛИЩЕ ФАЙЛОВ =====
TEMP_DIR = tempfile.gettempdir()
MEDIA_ROOT = os.path.join(TEMP_DIR, 'test_media')
MEDIA_URL = '/media/'
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# ===== КЭШИРОВАНИЕ =====
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache-location',
        'OPTIONS': {
            'MAX_ENTRIES': 10000,
        }
    }
}

# ===== CELERY - СИНХРОННЫЙ РЕЖИМ =====
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'

# ===== СЕССИИ =====
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# ===== УСКОРЕНИЕ ТЕСТОВ =====
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# ===== МИГРАЦИИ =====
MIGRATION_MODULES = {}

# ===== DEBUG И ЛОГИРОВАНИЕ =====
DEBUG = False

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
}

# ===== ОТКЛЮЧАЕМ DEBUG_TOOLBAR =====
DEBUG_TOOLBAR_CONFIG = {
    'IS_RUNNING_TESTS': True,
    'SHOW_TOOLBAR_CALLBACK': lambda r: False,
}

# Фильтруем Debug Toolbar из INSTALLED_APPS
INSTALLED_APPS = [app for app in INSTALLED_APPS if 'debug_toolbar' not in app]

# Фильтруем Debug Toolbar middleware
MIDDLEWARE = [m for m in MIDDLEWARE if 'debug_toolbar' not in m]
