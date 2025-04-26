import os
import telebot
import feedparser
import html
import re

# === Настройки ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")

# === Инициализация ===
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# === Список сайтов (AI/нейросети) ===
SITES = [
    'https://feeds.bbci.co.uk/news/technology/rss.xml',
    'https://www.deeplearning.ai/the-batch/tag/news/feed/',
    'https://venturebeat.com/category/ai/feed/',
    'https://syncedreview.com/feed/',
    'https://www.wired.com/feed/',
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

# === Работа с файлами опубликованных ссылок ===
POSTED_URLS_FILE = "posted_urls.txt"

def load_posted_urls():
    if not os.path.exists(POSTED_URLS_FILE):
        return set()
    with open(POSTED_URLS_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)

def save_posted_url(url):
    with open(POSTED_URLS_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

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
    posted_urls = load_posted_urls()
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
                save_posted_url(url)
                print(f"✅ Опубликовано: {title}")
            except Exception as e:
                print(f"❗ Ошибка отправки в Telegram: {e}")

# === Старт ===
if __name__ == '__main__':
    run_bot()
