import os
import telebot
import feedparser
import html
import re
import time
import random
from datetime import datetime, timedelta
import email.utils

# === Настройки ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL1_USERNAME = os.getenv("CHANNEL1_USERNAME")  # Канал для генерации контента
CHANNEL2_USERNAME = os.getenv("CHANNEL2_USERNAME")  # Канал для автоматизации
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# === Список сайтов ===
SITES = [
    # Англоязычные источники
    'https://feeds.bbci.co.uk/news/technology/rss.xml',
    'https://www.deeplearning.ai/the-batch/feed/',
    'https://venturebeat.com/feed/',
    'https://syncedreview.com/feed/',
    'https://feeds.arstechnica.com/arstechnica/technology-lab',
    'https://techcrunch.com/feed/',
    'https://artificialintelligence-news.com/feed/',
    'https://www.geeky-gadgets.com/feed/',

    # Русскоязычные источники
    'https://habr.com/ru/rss/interesting/',
    'https://habr.com/ru/rss/hub/artificial_intelligence/',
    'https://neurohive.io/ru/feed/',
    'https://rb.ru/feeds/tag/ai/',
    'https://vc.ru/rss/all',
    'https://hi-tech.mail.ru/rss/all/',
    'https://skillbox.ru/media/rss.xml',
    'https://letaibe.media/feed/'
]

# Импорт ключевых слов для каждого канала
from keywords_channel1 import KEYWORDS_CHANNEL1
from keywords_channel2 import KEYWORDS_CHANNEL2

# === Функции ===

def fetch_rss(url):
    """Получает и парсит RSS-ленту с указанного URL."""
    feed = feedparser.parse(url)
    print(f"Найдено статей на сайте {url}: {len(feed.entries)}")
    
    # Выводим информацию о первой статье для диагностики
    if feed.entries and len(feed.entries) > 0:
        entry = feed.entries[0]
        print(f"Пример статьи с {url}:")
        print(f"  Заголовок: {entry.title if 'title' in entry else 'Нет заголовка'}")
        print(f"  Доступные поля даты:")
        for field in ['published', 'published_parsed', 'updated', 'updated_parsed']:
            if hasattr(entry, field):
                print(f"    {field}: {getattr(entry, field)}")
    
    return feed.entries

def clean_text(text):
    """Очищает текст от HTML-сущностей и невидимых символов."""
    text = html.unescape(text)
    text = re.sub(r'[\u0000-\u001F\u007F-\u009F]', '', text)
    return text.encode("utf-16", "surrogatepass").decode("utf-16")

def is_relevant_for_channel(entry, channel_keywords):
    """Проверяет, содержит ли статья ключевые слова для конкретного канала."""
    title = entry.title if 'title' in entry else ''
    description = entry.get('description', '')
    summary = entry.get('summary', '')
    content = ''

    if 'content' in entry and isinstance(entry.content, list):
        content = ' '.join([c.value for c in entry.content if 'value' in c])

    text = (title + ' ' + description + ' ' + summary + ' ' + content).lower()
    return any(keyword.lower() in text for keyword in channel_keywords)

def parse_date_string(date_str):
    """Пытается распарсить строку даты в различных форматах."""
    try:
        # RFC 2822 формат (наиболее распространенный в RSS)
        return email.utils.parsedate_to_datetime(date_str)
    except:
        pass
    
    # Пробуем различные форматы дат
    date_formats = [
        "%a, %d %b %Y %H:%M:%S %z",      # RFC 822 / RFC 1123
        "%a, %d %b %Y %H:%M:%S %Z",      # Вариация RFC 822 с текстовой временной зоной
        "%Y-%m-%dT%H:%M:%S%z",           # ISO 8601
        "%Y-%m-%dT%H:%M:%SZ",            # ISO 8601 (UTC)
        "%Y-%m-%dT%H:%M:%S.%f%z",        # ISO 8601 с миллисекундами
        "%Y-%m-%dT%H:%M:%S.%fZ",         # ISO 8601 с миллисекундами (UTC)
        "%Y-%m-%d %H:%M:%S",             # Простой формат
        "%d %b %Y %H:%M:%S",             # Еще один распространенный формат
        "%d %b %Y",                      # Только дата
        "%Y-%m-%d"                       # Только дата (ISO)
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    
    return None

def is_fresh(entry):
    """
    Проверяет, является ли статья свежей (опубликованной в течение последних 24 часов).
    Использует различные поля даты и форматы для максимальной совместимости.
    """
    # Проверяем published_parsed (стандартное поле)
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        try:
            published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed))
            print(f"⏰ Время публикации (published_parsed): {published_time} UTC")
            return published_time >= datetime.utcnow() - timedelta(days=1)
        except Exception as e:
            print(f"❗ Ошибка при обработке published_parsed: {e}")
    
    # Проверяем updated_parsed (альтернативное поле)
    if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
        try:
            updated_time = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
            print(f"⏰ Время обновления (updated_parsed): {updated_time} UTC")
            return updated_time >= datetime.utcnow() - timedelta(days=1)
        except Exception as e:
            print(f"❗ Ошибка при обработке updated_parsed: {e}")
    
    # Проверяем строковые поля published или updated
    date_str = None
    if hasattr(entry, 'published'):
        date_str = entry.published
        print(f"⏰ Строка даты публикации: {date_str}")
    elif hasattr(entry, 'updated'):
        date_str = entry.updated
        print(f"⏰ Строка даты обновления: {date_str}")
    
    if date_str:
        date_obj = parse_date_string(date_str)
        if date_obj:
            print(f"⏰ Распарсенная дата: {date_obj} UTC")
            return date_obj >= datetime.utcnow() - timedelta(days=1)
    
    # Если не удалось определить дату, проверяем поле pubDate (часто используется)
    if hasattr(entry, 'pubDate'):
        date_str = entry.pubDate
        print(f"⏰ Строка pubDate: {date_str}")
        date_obj = parse_date_string(date_str)
        if date_obj:
            print(f"⏰ Распарсенная дата из pubDate: {date_obj} UTC")
            return date_obj >= datetime.utcnow() - timedelta(days=1)
    
    # Если не удалось определить дату, считаем статью свежей
    # Это можно изменить на False, если вы хотите более строгую фильтрацию
    print("❗ Не удалось определить дату публикации — считаем статью СВЕЖЕЙ")
    return True

def create_post(title, link):
    """Создает текст поста для Telegram."""
    safe_title = clean_text(title)
    return f"\U0001F4C8 *{safe_title}*\n\n[Читать статью]({link})"

def process_entries_for_channel(entries, channel_keywords, channel_username, max_posts=20):
    """Обрабатывает и публикует статьи для конкретного канала."""
    relevant_entries = []
    
    for entry in entries:
        if is_fresh(entry) and is_relevant_for_channel(entry, channel_keywords):
            relevant_entries.append(entry)
    
    print(f"\nВсего подходящих статей для канала {channel_username}: {len(relevant_entries)}")
    random.shuffle(relevant_entries)
    count = 0
    
    for entry in relevant_entries:
        if count >= max_posts:
            break
            
        url = entry.link
        title = entry.title
        post = create_post(title, url)
        
        try:
            print(f"\nГотовый пост для канала {channel_username}:\n{post}")
            bot.send_message(channel_username, post, parse_mode="Markdown", disable_web_page_preview=False)
            print(f"✅ Опубликовано в {channel_username}: {title}")
            count += 1
            time.sleep(1)
        except Exception as e:
            print(f"❗ Ошибка отправки в Telegram: {e}\nПост: {post}")
    
    return count

def run_bot():
    """Основная функция бота."""
    all_entries = []
    
    for site in SITES:
        print(f"\nПроверяю сайт: {site}")
        entries = fetch_rss(site)
        all_entries.extend(entries[:100])  # Ограничиваем до 100 статей с каждого сайта
    
    # Обработка для первого канала (генерация контента)
    if CHANNEL1_USERNAME:
        print("\n=== Обработка для канала генерации контента ===")
        channel1_count = process_entries_for_channel(all_entries, KEYWORDS_CHANNEL1, CHANNEL1_USERNAME)
        print(f"Опубликовано статей в канале {CHANNEL1_USERNAME}: {channel1_count}")
    else:
        print("\n⚠️ Канал для генерации контента не настроен (CHANNEL1_USERNAME)")
    
    # Обработка для второго канала (автоматизация)
    if CHANNEL2_USERNAME:
        print("\n=== Обработка для канала автоматизации ===")
        channel2_count = process_entries_for_channel(all_entries, KEYWORDS_CHANNEL2, CHANNEL2_USERNAME)
        print(f"Опубликовано статей в канале {CHANNEL2_USERNAME}: {channel2_count}")
    else:
        print("\n⚠️ Канал для автоматизации не настроен (CHANNEL2_USERNAME)")

if __name__ == '__main__':
    run_bot()
