import vk_api
from datetime import datetime, timedelta
import json
import logging
from typing import List, Dict

class VKParser:
    def __init__(self, vk_config, filter_config, app_config):
        self.vk = self._init_vk_session(vk_config)
        self.filter_config = filter_config
        self.app_config = app_config
        self.state = self._load_state()
        self.logger = logging.getLogger(self.__class__.__name__)

    def _init_vk_session(self, config):
        session = vk_api.VkApi(token=config['access_token'])
        return session.get_api()

    def _load_state(self) -> Dict:
        try:
            with open(self.app_config['state_file'], 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_state(self):
        with open(self.app_config['state_file'], 'w') as f:
            json.dump(self.state, f)

    def _is_valid_post(self, post: Dict) -> bool:
        # Проверка возраста поста
        post_age = datetime.now() - datetime.fromtimestamp(post['date'])
        if post_age > timedelta(days=self.filter_config['max_age_days']):
            return False
        
        # Проверка длины текста
        text = post.get('text', '')
        if len(text) < self.filter_config['min_text_length']:
            return False
            
        # Фильтрация по ключевым словам
        text_lower = text.lower()
        if any(kw.lower() in text_lower for kw in self.filter_config['keywords']):
            if not any(excl.lower() in text_lower for excl in self.filter_config['exclude_words']):
                return True
        return False

    def get_new_posts(self, group_id: int) -> List[Dict]:
        self.logger.info(f"Проверка группы {group_id}")
        try:
            response = self.vk.wall.get(
                owner_id=group_id,
                count=self.app_config['max_posts_per_check'],
                filter='owner',
                v=VK_CONFIG['api_version']
            )
        except Exception as e:
            self.logger.error(f"Ошибка VK API: {e}")
            return []

        new_posts = []
        for post in response['items']:
            if self._is_valid_post(post):
                post_data = self._format_post(post)
                new_posts.append(post_data)

        if new_posts:
            self.state[str(group_id)] = new_posts[0]['date']
            self._save_state()
            
        return new_posts

    def _format_post(self, post: Dict) -> Dict:
        return {
            'id': f"{post['owner_id']}_{post['id']}",
            'text': post.get('text', ''),
            'date': post['date'],
            'url': f"https://vk.com/wall{post['owner_id']}_{post['id']}",
            'attachments': self._get_attachments(post)
        }

    def _get_attachments(self, post: Dict) -> List[str]:
        # Реализация обработки вложений
        # ...
