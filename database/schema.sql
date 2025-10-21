-- Создание таблицы для пользователей и их данных
CREATE TABLE user_data (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    date_of_birth DATE NOT NULL,
    weight FLOAT CHECK (weight >= 10),
    gender SMALLINT CHECK (gender IN (0, 1)),
    height SMALLINT CHECK (height >= 10),
    active BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES auth_user(id)
);

-- Создание таблицы для записей сна
CREATE TABLE sleep_record (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    sleep_date_time TIMESTAMP WITH TIME ZONE NOT NULL,
    sleep_rem_duration SMALLINT CHECK (sleep_rem_duration >= 0 AND sleep_rem_duration <= 1440),
    has_rem BOOLEAN DEFAULT FALSE,
    min_hr SMALLINT,
    device_bedtime TIMESTAMP WITH TIME ZONE,
    sleep_deep_duration SMALLINT CHECK (sleep_deep_duration >= 0 AND sleep_deep_duration <= 1440),
    wake_up_time TIMESTAMP WITH TIME ZONE,
    bedtime TIMESTAMP WITH TIME ZONE,
    awake_count SMALLINT,
    duration SMALLINT,
    max_hr SMALLINT,
    sleep_awake_duration SMALLINT,
    avg_hr DECIMAL(5,2),
    sleep_light_duration SMALLINT CHECK (sleep_light_duration >= 0 AND sleep_light_duration <= 1440),
    device_wake_up_time TIMESTAMP WITH TIME ZONE,
    UNIQUE (user_id, sleep_date_time),
    FOREIGN KEY (user_id) REFERENCES auth_user(id)
);

-- Создание индекса для быстрого поиска по пользователю и времени сна
CREATE INDEX idx_sleep_record_user_sleep_date_time ON sleep_record(user_id, sleep_date_time);

-- Создание таблицы для записей пульса ночью
CREATE TABLE night_heart_rate_entry (
    id INTEGER PRIMARY KEY,
    record_id INTEGER NOT NULL,
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    bpm SMALLINT CHECK (bpm >= 0 AND bpm <= 300),
    FOREIGN KEY (record_id) REFERENCES sleep_record(id)
);

-- Создание таблицы для сегментов сна
CREATE TABLE sleep_segment (
    id INTEGER PRIMARY KEY,
    record_id INTEGER NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    state SMALLINT CHECK (state IN (2, 3, 4, 5)),  -- 2: Light, 3: Deep, 4: REM, 5: Awake
    FOREIGN KEY (record_id) REFERENCES sleep_record(id)
);

-- Создание таблицы для статистики сна
CREATE TABLE sleep_statistics (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    latency_minutes FLOAT,
    sleep_efficiency FLOAT,
    sleep_phases JSONB,
    sleep_fragmentation_index FLOAT,
    sleep_calories_burned FLOAT,
    date DATE NOT NULL,
    sleep_quality FLOAT,
    recommended TEXT,
    FOREIGN KEY (user_id) REFERENCES auth_user(id)
);

-- Создание индекса для быстрого поиска статистики по пользователю и дате
CREATE INDEX idx_sleep_statistics_user_date ON sleep_statistics(user_id, date);
