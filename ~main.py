import vk_api
import requests
from vk_api.utils import get_random_id
from datetime import datetime, timedelta
import time
import json
import logging
import re
import os
from typing import List, Dict

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vk_parser.log'),
        logging.StreamHandler()
    ]
)

# Конфигурация (заполните своими данными)
CONFIG = {
    "source_groups": [-12345678, -87654321],  # ID исходных групп (с минусом)
    "target_group": -11111111,               # ID целевой группы
    "access_token": "ваш_токен_vk",          # VK API токен
    "telegram_token": "ваш_токен_telegram",  # Telegram Bot Token
    "telegram_chat_id": "ваш_chat_id",       # ID чата в Telegram
    "interval": 300,                        # Интервал проверки (секунды)
    "keywords": ["важное", "новость", "акция"], # Ключевые слова для фильтра
    "max_text_length": 100,                  # Макс. длина текста в сообщении
    "include_reposts": True,                 # Включать репосты
    "include_media": True,                   # Включать медиавложения
    "media_types": ["photo", "video", "doc"] # Типы медиавложений
}

# Файлы для хранения состояния
STATE_FILE = "last_processed.json"
POSTS_CACHE_FILE = "posts_cache.json"

def get_vk_session():
    """Инициализация сессии VK"""
    return vk_api.VkApi(token=CONFIG['access_token'])

def load_json_file(filename: str, default: dict) -> dict:
    """Загрузка данных из JSON файла"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def save_json_file(filename: str, data: dict):
    """Сохранение данных в JSON файл"""
    with open(filename, 'w') as f:
        json.dump(data, f)

class VKParser:
    def __init__(self):
        self.vk = get_vk_session().get_api()
        self.state = load_json_file(STATE_FILE, {})
        self.posts_cache = load_json_file(POSTS_CACHE_FILE, {})
        
    def _get_media_attachments(self, post: dict) -> List[str]:
        """Извлечение медиавложений из поста"""
        if not CONFIG['include_media'] or 'attachments' not in post:
            return []
        
        attachments = []
        for attach in post['attachments']:
            if attach['type'] in CONFIG['media_types']:
                media = attach[attach['type']]
                # Для фото берем последнее изображение с максимальным размером
                if attach['type'] == 'photo':
                    url = max(
                        media['sizes'], 
                        key=lambda x: x['width'] + x['height']
                    )['url']
                elif attach['type'] == 'video':
                    url = f"video{media['owner_id']}_{media['id']}_{media['access_key']}"
                elif attach['type'] == 'doc':
                    url = media['url']
                attachments.append(f"{attach['type']}{url}")
        return attachments

    def _process_reposts(self, post: dict) -> dict:
        """Обработка репостов"""
        if 'copy_history' in post and CONFIG['include_reposts']:
            original = post['copy_history'][0]
            return {
                **original,
                'reposter_id': post['owner_id']
            }
        return post

    def _check_keywords(self, text: str) -> bool:
        """Проверка на наличие ключевых слов"""
        if not CONFIG['keywords']:
            return True
        text = text.lower()
        return any(keyword.lower() in text for keyword in CONFIG['keywords'])

    def get_new_posts(self, group_id: int) -> List[dict]:
        """Получение новых постов из группы"""
        last_ts = self.state.get(str(group_id), 0)
        
        try:
            response = self.vk.wall.get(
                owner_id=group_id,
                count=20,
                filter='owner'
            )
        except vk_api.exceptions.ApiError as e:
            logging.error(f"Ошибка VK API: {e}")
            return []

        new_posts = []
        for item in response['items']:
            # Проверка времени публикации
            post_time = datetime.fromtimestamp(item['date'])
            if post_time < datetime.now() - timedelta(days=2):
                continue
                
            # Проверка на дубликаты
            post_id = f"{item['owner_id']}_{item['id']}"
            if post_id in self.posts_cache:
                continue
                
            # Обработка репостов
            processed_post = self._process_reposts(item)
            
            # Фильтрация по ключевым словам
            if not self._check_keywords(processed_post.get('text', '')):
                continue
                
            # Сбор информации о посте
            post_data = {
                'id': post_id,
                'text': processed_post.get('text', ''),
                'date': item['date'],
                'url': f"https://vk.com/wall{post_id}",
                'attachments': self._get_media_attachments(processed_post),
                'is_repost': 'reposter_id' in processed_post
            }
            
            new_posts.append(post_data)
            self.posts_cache[post_id] = post_data['date']
            
        if new_posts:
            self.state[str(group_id)] = new_posts[0]['date']
            save_json_file(STATE_FILE, self.state)
            save_json_file(POSTS_CACHE_FILE, self.posts_cache)
            
        return new_posts

class Notifier:
    @staticmethod
    def send_to_vk(post: dict):
        """Отправка поста в VK"""
        vk = get_vk_session().get_api()
        message = Notifier._prepare_message(post)
        
        try:
            vk.wall.post(
                owner_id=CONFIG['target_group'],
                message=message,
                attachments=','.join(post['attachments']),
                random_id=get_random_id()
            )
            logging.info(f"Отправлен пост в VK: {post['id']}")
        except Exception as e:
            logging.error(f"Ошибка отправки в VK: {e}")

    @staticmethod
    def send_to_telegram(post: dict):
        """Отправка уведомления в Telegram"""
        message = Notifier._prepare_message(post)
        url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/sendMessage"
        
        payload = {
            'chat_id': CONFIG['telegram_chat_id'],
            'text': message,
            'disable_web_page_preview': not bool(post['attachments'])
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            logging.info(f"Отправлено в Telegram: {post['id']}")
        except Exception as e:
            logging.error(f"Ошибка отправки в Telegram: {e}")

    @staticmethod
    def _prepare_message(post: dict) -> str:
        """Форматирование сообщения"""
        text = re.sub(r'\n{3,}', '\n\n', post['text'].strip())
        if len(text) > CONFIG['max_text_length']:
            text = text[:CONFIG['max_text_length']] + "..."
            
        message = [
            "📢 Новый пост!" + (" (Репост)" if post['is_repost'] else ""),
            text,
            f"🔗 Читать полностью: {post['url']}"
        ]
        return '\n'.join(message)

def main():
    parser = VKParser()
    notifier = Notifier()
    
    logging.info("Сервис мониторинга ВК запущен")
    
    while True:
        try:
            for group_id in CONFIG['source_groups']:
                posts = parser.get_new_posts(group_id)
                for post in reversed(posts):
                    notifier.send_to_vk(post)
                    notifier.send_to_telegram(post)
                    time.sleep(1)
                    
            time.sleep(CONFIG['interval'])
            
        except Exception as e:
            logging.error(f"Критическая ошибка: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
