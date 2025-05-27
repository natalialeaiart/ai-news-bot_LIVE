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
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# === Список сайтов ===
SITES = [
    # Англоязычные источники
    'https://deeplearning.ai/the-batch/feed/',
    'https://syncedreview.com/feed/',
    'https://feeds.arstechnica.com/arstechnica/technology-lab', # Наблюдайте за ней
    'https://artificialintelligence-news.com/feed/',

    # Русскоязычные источники
    'https://habr.com/ru/rss/hub/artificial_intelligence/',
    'https://neurohive.io/ru/feed/',
    'https://rb.ru/feeds/tag/ai/',
    'https://letaibe.media/feed/' # Наблюдайте за ней
]

# === Ключевые слова для фильтрации ===
KEYWORDS = [
    # Английские
    "chatgpt", "gpt", "gpt-4", "gpt-5", "sora", "gemini", "grok", "bard", "claude", "pi", "llm",
    "midjourney", "dall·e", "stable diffusion", "sdxl", "runway", "runway ml", "runway gen",
    "openai sora", "sora video", "pika", "kaiber", "kling ai", "flux", "krea", "leonardo ai",
    "ideogram", "dreambooth", "consistency", "consistent character", "style transfer",
    "image generation", "video generation", "gen-ai", "ai generated", "ai fashion", "ai art",
    "ai photo", "ai video", "ai avatar", "ai animation", "ai style", "ai background",
    "auto-gpt", "agentgpt", "babyagi", "langchain", "hugginggpt", "superagi",
    "generative agent", "virtual assistant", "ai assistant", "ai agent",
    "microsoft copilot", "github copilot", "duet ai", "notion ai", "character ai", "replika",
    "n8n", "make", "integromat", "10web", "mixo", "framer ai", "durable",
    "unicorn platform", "bookmark aida", "uizard", "ai website", "ai builder",
    "ai update", "ai release", "ai beta", "ai feature", "ai launch", "ai news",
    "gpt update", "midjourney v6", "sora preview", "runway release",
    "dreambooth", "lora", "controlnet", "fine-tuning", "textual inversion",
    "custom model", "one-shot learning", "training character", "stylegan", "nerf", "deepfake",
    "personal ai", "ai tuning",
    "new ai model", "ai model launch", "new ai platform", "new generator", "ai tool release",
    "next-gen ai", "ai suite",
    "ai nft", "generated nft", "ai art nft", "monetize ai art", "sell ai art", "nft platform",
    "mint nft", "digital art nft",
    "ai fashion design", "create fashion ai",
    "monetize ai", "earn with ai", "ai services", "ai business",

    # Русские
    "gpt", "нейросеть", "искусственный интеллект", "большая языковая модель", "llm",
    "ai видео", "ai фото", "ai мода", "ai стиль", "генерация изображений", "генерация видео",
    "обновление gpt", "обновление нейросети", "релиз нейросети", "файнтюнинг",
    "dreambooth", "consistent character", "персонаж ai", "фон нейросеть",
    "обучение на фото", "ai ассистент", "автоагент", "генеративный агент",
    "сайт на нейросети", "генерация сайта", "без кода", "ноу код",
    "создание сайта ai", "ai генератор контента",
    "новая нейросеть", "запуск нейросети", "новая платформа ии", "новый генератор",
    "релиз инструмента ии", "ии следующего поколения", "набор инструментов ии",
    "сгенерированный nft", "ai арт nft", "монетизация ai арт", "продать ai арт",
    "платформа nft", "минт nft", "цифровой арт nft",
    "дизайн одежды ai", "создание моды ai",
    "монетизация ии", "заработок с помощью ии", "ai услуги", "ai бизнес"
]

# === Функции ===

def fetch_rss(url):
    """Получает и парсит RSS-ленту с указанного URL."""
    feed = feedparser.parse(url)
    print(f"Найдено статей на сайте: {len(feed.entries)}")
    
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

def is_relevant(entry):
    """Проверяет, содержит ли статья ключевые слова."""
    title = entry.title if 'title' in entry else ''
    description = entry.get('description', '')
    summary = entry.get('summary', '')
    content = ''

    if 'content' in entry and isinstance(entry.content, list):
        content = ' '.join([c.value for c in entry.content if 'value' in c])

    text = (title + ' ' + description + ' ' + summary + ' ' + content).lower()
    return any(keyword in text for keyword in KEYWORDS)

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

def run_bot():
    """Основная функция бота."""
    all_entries = []

    for site in SITES:
        print(f"\nПроверяю сайт: {site}")
        entries = fetch_rss(site)
        for entry in entries[:100]:
            if is_fresh(entry) and is_relevant(entry):
                all_entries.append(entry)

    print(f"\nВсего подходящих статей: {len(all_entries)}")
    random.shuffle(all_entries)
    count = 0

    for entry in all_entries:
        if count >= 35:
            break

        url = entry.link
        title = entry.title
        post = create_post(title, url)

        try:
            print("\nГотовый пост:\n", post)
            bot.send_message(CHANNEL_USERNAME, post, parse_mode="Markdown", disable_web_page_preview=False)
            print(f"✅ Опубликовано: {title}")
            count += 1
            time.sleep(1)
        except Exception as e:
            print(f"❗ Ошибка отправки в Telegram: {e}\nПост: {post}")

if __name__ == '__main__':
    run_bot()
