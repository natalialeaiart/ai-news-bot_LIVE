import os
import telebot
import feedparser
import html
import re

# === Настройки ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")
ARCHIVE_CHANNEL_ID = os.getenv("ARCHIVE_CHANNEL_ID")  # Например: -1001234567890

# === Инициализация ===
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# === Список сайтов (AI/нейросети) ===
SITES = [
    'https://feeds.bbci.co.uk/news/technology/rss.xml',
    'https://www.deeplearning.ai/the-batch/tag/news/feed/',
    'https://venturebeat.com/category/ai/feed/',
    'https://syncedreview.com/feed/',
    'https://www.wired.com/',
    'https://www.technologyreview.com/feed/',
    'https://feeds.arstechnica.com/arstechnica/technology-lab',
    'https://habr.com/ru/rss/interesting/',
    'https://rb.ru/feeds/',
    'https://vc.ru/rss/all'
]

# === Ключевые слова для фильтрации ===
KEYWORDS = [
    "ai", "neural", "machine learning", "deep learning", "llm", "chatgpt", "openai",
    "generative", "artificial intelligence", "gpt", "sora", "midjourney", "krea",
    "automation", "robot", "autonomous", "genai", "ml", "vision"
]

# === Получение опубликованных ссылок из канала-архива ===
def get_posted_urls_from_archive():
    posted = set()
    try:
        messages = bot.get_chat_history(ARCHIVE_CHANNEL_ID, limit=100)
        for msg in messages:
            urls = re.findall(r'(https?://\S+)', msg.text or '')
            posted.update(urls)
    except Exception as e:
        print(f"Ошибка чтения архива: {e}")
    return posted

# === Функции ===
def fetch_rss(url):
    feed = feedparser.parse(url)
    print(f"Найдено статей: {len(feed.entries)}")
    return feed.entries

def clean_text(text):
    text = html.unescape(text)
    text = re.sub(r'[\u0000-\u001F\u007F-\u009F]', '', text)
    return text.encode("utf-16", "surrogatepass").decode("utf-16")

def is_relevant(title):
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in KEYWORDS)

def create_post(title, link):
    safe_title = clean_text(title)
    return f"\U0001F4C8 *{safe_title}*\n\n[Читать статью]({link})"

def run_bot():
    posted_urls = get_posted_urls_from_archive()
    for site in SITES:
        print(f"Проверяю: {site}")
        entries = fetch_rss(site)
        for entry in entries[:3]:
            url = entry.link
            title = entry.title

            if url in posted_urls or not is_relevant(title):
                continue

            post = create_post(title, url)
            try:
                print("\nГотовый пост:\n", post)
                bot.send_message(CHANNEL_USERNAME, post, parse_mode="Markdown", disable_web_page_preview=False)
                bot.send_message(ARCHIVE_CHANNEL_ID, url)  # сохраняем ссылку в архивный канал
                print(f"Опубликовано: {title}")
            except Exception as e:
                print(f"Ошибка отправки в Telegram: {e}")

# === Запуск бота ===
if __name__ == '__main__':
    run_bot()
