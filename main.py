import logging
import time
from vk_parser import VKParser
from notifier import Notifier
from config import (
    VK_CONFIG,
    TELEGRAM_CONFIG,
    FILTER_CONFIG,
    APP_CONFIG,
    MESSAGE_CONFIG
)

def setup_logging():
    logging.basicConfig(
        level=APP_CONFIG['log_level'],
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('vk_monitor.log'),
            logging.StreamHandler()
        ]
    )

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    parser = VKParser(
        vk_config=VK_CONFIG,
        filter_config=FILTER_CONFIG,
        app_config=APP_CONFIG
    )
    
    notifier = Notifier(
        vk_config=VK_CONFIG,
        telegram_config=TELEGRAM_CONFIG,
        message_config=MESSAGE_CONFIG
    )

    logger.info("Сервис мониторинга запущен")
    
    while True:
        try:
            for group_id in VK_CONFIG['source_groups']:
                posts = parser.get_new_posts(group_id)
                for post in posts:
                    notifier.send_all(post)
                    time.sleep(1)
                    
            time.sleep(APP_CONFIG['check_interval'])
            
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
