# "access_token": fa132b59fa132b59fa132b59f2f93b5354ffa13fa132b599d896d868516ee65b047c800,
# "target_group": -52983821

import os
from pathlib import Path

# Пути к файлам данных
BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(exist_ok=True)

# Конфигурация VK
VK_CONFIG = {
    "source_groups": [-12345678, -87654321],  # ID групп (с минусом)
    "target_group": -229818247,                # ID целевой группы
    "access_token": "fa132b59fa132b59fa132b59f2f93b5354ffa13fa132b599d896d868516ee65b047c800",           # Токен от VK (требуемые права: wall, groups)
# "access_token": vk1.a.IAprfX-XZJ8AHgXXIZ3JLTcOy4sHXhR4q3Lzsv7HZJXnK-TUoPDttCZHMJ2_47ZxXo6SHXfPOPprUenPf7LzM9GJSxILcE1Yl8UaVErl0mlrDS2vk0WVGicVyeIRNhK99yWFAJK2rd1KgKEmBzzbXat010MM1ws3vVeV4AlnL0hiJkbrIfBBB03eDeTYXSyMPjCCUHGt6hoTDA4N9L6SfA,   # Токен от VK (требуемые права: wall, groups)
    "api_version": "5.199"                    # Версия VK API
}

# Конфигурация Telegram
#TELEGRAM_CONFIG = {
#    "enable": True,                           # Включить уведомления в Telegram
#    "bot_token": "ваш_telegram_token",        # Токен бота от @BotFather
#    "chat_id": "ваш_chat_id",                 # ID чата/канала
#    "max_retries": 3                          # Попытки отправки
#}

# Параметры фильтрации
FILTER_CONFIG = {
    "keywords": ["*"],        # Ключевые слова для фильтра
    "exclude_words": ["*"],             # Слова для исключения
    "max_age_days": 2,                        # Макс. возраст поста
    "include_reposts": False,                 # Включать репосты
    "min_text_length": 30                     # Мин. длина текста
}

# Настройки приложения
APP_CONFIG = {
    "check_interval": 300,                    # Интервал проверки (секунд)
    "max_posts_per_check": 10,                # Макс. постов за проверку
    "log_level": "INFO",                      # Уровень логирования
    "state_file": DATA_DIR / "last_processed.json",
    "cache_file": DATA_DIR / "posts_cache.json"
}

# Настройки сообщений
MESSAGE_CONFIG = {
    "vk": {
        "max_length": 2000,                   # Макс. длина поста ВКонтакте
        "template": "📌 Новый пост!\n{text}\n\n🔗 {url}"
    },
#    "telegram": {
#        "max_length": 1024,
#        "template": "🚨 Новое обновление!\n\n{text}\n\n➡️ Читать полностью: {url}"
#    }
}
