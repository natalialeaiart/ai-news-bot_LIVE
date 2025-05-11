import os
import telebot
import feedparser
import html
import re
import time
import random
from datetime import datetime, timedelta

# === Настройки ===

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# === Список сайтов ===

SITES = [ # Англоязычные источники 'https://feeds.bbci.co.uk/news/technology/rss.xml', 'https://www.deeplearning.ai/the-batch/feed/', 'https://venturebeat.com/feed/', 'https://syncedreview.com/feed/', 'https://feeds.arstechnica.com/arstechnica/technology-lab', 'https://techcrunch.com/feed/', 'https://www.artificialintelligence-news.com/feed/', 'https://www.geeky-gadgets.com/feed/',

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

KEYWORDS = [ # Английские "chatgpt", "gpt", "gpt-4", "gpt-5", "sora", "gemini", "grok", "bard", "claude", "pi", "llm", "midjourney", "dall·e", "stable diffusion", "sdxl", "runway", "runway ml", "runway gen", "runway release", "openai sora", "sora video", "pika", "kaiber", "kling ai", "flux", "krea", "leonardo ai", "dreamina", "suno ai", "haiper", "ideogram", "dreambooth", "consistency", "consistent character", "style transfer", "image generation", "video generation", "gen-ai", "ai generated", "ai fashion", "ai art", "ai avatar", "ai animation", "auto-gpt", "agentgpt", "babyagi", "langchain", "hugginggpt", "superagi", "generative agent", "virtual assistant", "ai assistant", "ai agent", "microsoft copilot", "github copilot", "duet ai", "notion ai", "character ai", "replika", "n8n", "make", "integromat", "10web", "mixo", "framer ai", "durable", "unicorn platform", "bookmark aida", "uizard", "ai website", "ai builder", "ai update", "ai release", "new ai", "new ai model", "ai model launch", "new ai platform", "new generator", "ai tool release", "next-gen ai", "ai suite", "gpt update", "midjourney v6", "sora preview", "dreambooth", "lora", "controlnet", "fine-tuning", "textual inversion", "custom model", "one-shot learning", "training character", "stylegan", "nerf", "deepfake", "personal ai", "ai tuning", "ai nft", "generated nft", "ai art nft", "monetize ai art", "sell ai art", "nft platform", "mint nft", "digital art nft", "ai fashion design", "create fashion ai", "monetize ai", "earn with ai", "ai services", "ai business",

# Русские
"gpt", "нейросеть", "искусственный интеллект", "большая языковая модель", "llm", "новая нейросеть", "запуск нейросети",
"новая платформа ии", "новый генератор", "релиз инструмента ии", "ии следующего поколения", "набор инструментов ии",
"ai видео", "ai фото", "ai мода", "ai стиль", "генерация изображений", "генерация видео", "обновление gpt", "обновление нейросети",
"релиз нейросети", "файнтюнинг", "dreambooth", "consistent character", "персонаж ai", "фон нейросеть", "обучение на фото",
"ai ассистент", "автоагент", "генеративный агент", "сайт на нейросети", "генерация сайта", "без кода", "ноу код", "n8n", "make",
"создание сайта ai", "ai генератор контента",
"ai nft", "сгенерированный nft", "ai арт nft", "монетизация ai арт", "продать ai арт", "платформа nft", "минт nft", "цифровой арт nft",
"дизайн одежды ai", "создание моды ai", "монетизация ии", "заработок с помощью ии", "ai услуги", "ai бизнес"

]

# === Функции ===

def fetch_rss(url): feed = feedparser.parse(url) print(f"Найдено статей на сайте: {len(feed.entries)}") return feed.entries

def clean_text(text): text = html.unescape(text) text = re.sub(r'[\u0000-\u001F\u007F-\u009F]', '', text) return text.encode("utf-16", "surrogatepass").decode("utf-16")

def is_relevant(entry): title = entry.title if 'title' in entry else '' description = entry.get('description', '') summary = entry.get('summary', '') content = '' if 'content' in entry and isinstance(entry.content, list): content = ' '.join([c.value for c in entry.content if 'value' in c]) text = (title + ' ' + description + ' ' + summary + ' ' + content).lower() return any(keyword in text for keyword in KEYWORDS)

def is_fresh(entry): if hasattr(entry, 'published_parsed') and entry.published_parsed: published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed)) print(f"⏰ Время публикации: {published_time} UTC") return published_time >= datetime.utcnow() - timedelta(days=1) else: print("❗ Не удалось определить дату публикации — считаем статью старой.") return False

def create_post(title, link): safe_title = clean_text(title) return f"\U0001F4C8 {safe_title}\n\nЧитать статью"

def run_bot(): all_entries = [] for site in SITES: print(f"\nПроверяю сайт: {site}") entries = fetch_rss(site) for entry in entries[:100]: if is_fresh(entry) and is_relevant(entry): all_entries.append(entry)

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

if name == 'main': run_bot()

