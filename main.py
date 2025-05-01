import os
import telebot
import feedparser
import html
import re
import time
from datetime import datetime, timedelta

# === Настройки ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")

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
    'https://www.artificialintelligence-news.com/feed/',
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

# === Ключевые слова для фильтрации ===
KEYWORDS = [
    # Английские ключевые слова
    "ai", "runway", "artificial intelligence", "ai tool", "machine learning", "deep learning", "llm",
    "chatgpt", "openai", "gpt", "sora", "midjourney", "krea", "kling", "veo", "wan",
    "automation", "robot", "autonomous", "genai", "vision", "updates", "ai agents",
    "n8n", "make", "ai fashion", "ai video", "ai image", "ai challenge", "ai challenges",
    "ai trend", "ai trends", "image generation", "video generation", "new ai", 
    "ai movie", "ai exhibition",
    
    # Русские ключевые слова
    "искусственный интеллект", "нейросеть", "нейросети", "машинное обучение", "глубокое обучение",
    "автоматизация", "робот", "автономный", "ии агент", "генеративный искусственный интеллект",
    "обновления искусственного интеллекта", "агенты ии", "ai мода", "видео ии", "изображение ии", "челлендж ии",
    "конкурс ai", "видео генерация", "генерации картинок", "ии фотостоки", "новая нейросеть", "тренды ии",
    "ии ассистент", "ai агент", "ai ассистент", "ии инструмент", "ии фильм", "ии выставка", 
]

# === Функции ===

def fetch_rss(url):
    feed = feedparser.parse(url)
    print(f"Найдено статей на сайте: {len(feed.entries)}")
    return feed.entries

def clean_text(text):
    text = html.unescape(text)
    text = re.sub(r'[\u0000-\u001F\u007F-\u009F]', '', text)
    return text.encode("utf-16", "surrogatepass").decode("utf-16")

def is_relevant(entry):
    title = entry.title if 'title' in entry else ''
    description = entry.get('description', '')
    text = (title + ' ' + description).lower()
    return any(keyword in text for keyword in KEYWORDS)

def is_fresh(entry):
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed))
        print(f"⏰ Время публикации: {published_time} UTC")
        return published_time >= datetime.utcnow() - timedelta(days=1)
    else:
        print("❗ Не удалось определить дату публикации — считаем статью старой.")
    return False

def create_post(title, link):
    safe_title = clean_text(title)
    return f"\U0001F4C8 *{safe_title}*\n\n[Читать статью]({link})"

def run_bot():
    for site in SITES:
        print(f"\nПроверяю сайт: {site}")
        entries = fetch_rss(site)
        for entry in entries[:60]:  # максимум 60 новостей с одного сайта
            url = entry.link
            title = entry.title

            if not is_fresh(entry):
                print(f"⏭️ Пропущено (старое): {title}")
                continue

            if not is_relevant(entry):
                print(f"⚠️ Пропущено (не по теме): {title}")
                continue

            post = create_post(title, url)
            try:
                print("\nГотовый пост:\n", post)
                bot.send_message(CHANNEL_USERNAME, post, parse_mode="Markdown", disable_web_page_preview=False)
                print(f"✅ Опубликовано: {title}")
            except Exception as e:
                print(f"❗ Ошибка отправки в Telegram: {e}")

if __name__ == '__main__':
    run_bot()
