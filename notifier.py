import requests
from vk_api.utils import get_random_id
import logging

class Notifier:
    def __init__(self, vk_config, telegram_config, message_config):
        self.vk_config = vk_config
        self.telegram_config = telegram_config
        self.message_config = message_config
        self.logger = logging.getLogger(self.__class__.__name__)

    def send_all(self, post):
        self.send_to_vk(post)
        if self.telegram_config['enable']:
            self.send_to_telegram(post)

    def send_to_vk(self, post):
        try:
            message = self._prepare_message(post, 'vk')
            self.vk.wall.post(
                owner_id=self.vk_config['target_group'],
                message=message,
                attachments=','.join(post['attachments']),
                random_id=get_random_id()
            )
            self.logger.info(f"Отправлено в VK: {post['id']}")
        except Exception as e:
            self.logger.error(f"Ошибка VK: {e}")

    def send_to_telegram(self, post):
        try:
            message = self._prepare_message(post, 'telegram')
            url = f"https://api.telegram.org/bot{self.telegram_config['bot_token']}/sendMessage"
            response = requests.post(url, json={
                'chat_id': self.telegram_config['chat_id'],
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': False
            })
            response.raise_for_status()
        except Exception as e:
            self.logger.error(f"Ошибка Telegram: {e}")

    def _prepare_message(self, post, platform):
        template = self.message_config[platform]['template']
        return template.format(
            text=post['text'][:self.message_config[platform]['max_length']],
            url=post['url']
        )
