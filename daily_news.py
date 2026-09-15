import os
import feedparser
import datetime
import smtplib
import ollama
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 1. CONFIGURATION & SETTINGS
# ==========================================

# Email Settings — fill in your own values before running.
# NOTE: this file is meant for your local/private copy only. If you keep a
# separate copy for GitHub, replace these with placeholder values there
# before publishing (see README).
# Fine-tuning note: for Gmail, SENDER_PASSWORD must be an App Password
# (https://myaccount.google.com/apppasswords), not your normal account
# password — Gmail rejects normal passwords over SMTP.
SENDER_EMAIL = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"
RECIPIENTS = ["recipient1@example.com", "recipient2@example.com"]

# Language the AI summaries/translations are written in.
# Default is Vietnamese — change this to any language the model supports,
# e.g. "English", "French", "Japanese".
# Fine-tuning note: translation quality for less common languages may be
# weaker than for English/Vietnamese — test on one source before running
# the full digest after changing this.
TARGET_LANGUAGE = "Vietnamese"

# How many recent articles to pull from each source.
# Fine-tuning note: raising this may need a larger num_ctx (see below) so
# the AI doesn't run out of context window and truncate its output.
ARTICLES_PER_SOURCE = 5


SOURCES = {
    "VnExpresstg": "https://vnexpress.net/rss/the-gioi.rss",
    #"VnExpresskd": "https://vnexpress.net/rss/kinh-doanh.rss",
    "VnExpress": "https://vnexpress.net/rss/khoa-hoc-cong-nghe.rss",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "TechCrunch": "https://techcrunch.com/feed/",
    "Sciencedaily": "https://www.sciencedaily.com/rss/all.xml",
    #"CNN": "http://rss.cnn.com/rss/edition.rss",
    #"BBC News": "http://feeds.bbci.co.uk/news/rss.xml",
    "The New York Times": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "CNBC": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    #"Buenos Aires Times": "https://www.batimes.com.ar/feed",
    "Times of Israel": "https://news.google.com/rss/search?q=site:timesofisrael.com&hl=en-US&gl=US&ceid=US:en",
    "Al Jazeera (Trung Đông)": "https://www.aljazeera.com/xml/rss/all.xml",
    #"BBC News (Anh)": "http://feeds.bbci.co.uk/news/rss.xml",
    "The Guardian (Anh)": "https://www.theguardian.com/world/rss",
    #"Sky News (Anh)": "https://feeds.skynews.com/feeds/rss/world.xml",
    "France 24 (Pháp)": "https://www.france24.com/en/rss",
    #"Deutsche Welle (Đức)": "https://rss.dw.com/rdf/rss-en-world",
    #"Euronews (Châu Âu)": "https://www.euronews.com/rss",
    "SCMP (Trung Quốc)": "https://www.scmp.com/rss/91/feed",
    "The Times of India": "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms"

}


# ==========================================
# 2 & 3. FETCH AND SUMMARIZE NEWS ONE BY ONE
# ==========================================
print("Fetching articles and asking the AI to summarize each source...")

final_ai_summary = ""
email_links_section = ""

for source_name, feed_url in SOURCES.items():
    print(f"-> Processing: {source_name}...")
    # Fine-tuning note: RSS feeds can change format or go down without
    # notice. feedparser won't crash the script on a bad feed — that source
    # will just come back with 0 entries and an empty summary.
    feed = feedparser.parse(feed_url)
    
    source_articles_text = ""
    email_links_section += f"{source_name}\n"
    
    # No date filter — just take the first 5 entries from the RSS feed
    for i, entry in enumerate(feed.entries[:ARTICLES_PER_SOURCE], 1):
        
        # Parse the date just to print it nicely
        parsed_date = getattr(entry, 'published_parsed', getattr(entry, 'updated_parsed', None))
        if parsed_date:
            article_date = datetime.datetime.fromtimestamp(time.mktime(parsed_date))

            if article_date.year < datetime.datetime.now().year:
                continue
                
            formatted_date = article_date.strftime("%d/%m/%Y")
        else:
            formatted_date = "Date unknown"
            
        title = getattr(entry, 'title', 'No Title')
        summary = getattr(entry, 'summary', 'No Summary available')
        link = getattr(entry, 'link', '#')
        
        # Build the text the AI will read (title + date, then content)
        source_articles_text += f"Article {i} - Title: {title} ({formatted_date})\nContent: {summary}\n\n"
        
        # Save the link for the end of the digest
        email_links_section += f"{i}. {link}\n"
    
    email_links_section += "\n"

    # Instruct the AI to follow the exact output format we want
    # Fine-tuning note: Ollama must already be running locally with the
    # 'gemma2' model pulled (`ollama pull gemma2`), otherwise this call fails.
    prompt = f"""You are a professional news editor. Read the articles below from a single news source, then summarize and translate each one into {TARGET_LANGUAGE}, following this structure: source name, article title translated into {TARGET_LANGUAGE}, and a summary of each article in {TARGET_LANGUAGE} (about 700 words per article). Do not write anything other than the summaries.

{source_name}
{source_articles_text}

Result:"""

    response = ollama.chat(
        model='gemma2', 
            messages=[
            {'role': 'user', 'content': prompt} # Keep this as the variable carrying the article content
    ], 
            options={
            # Fine-tuning notes:
            # - num_gpu: how many model layers to push onto the GPU. 999 tries
            #   to push as many as possible; if your machine has no/limited
            #   GPU VRAM, Ollama falls back to CPU automatically (just slower,
            #   not an error).
            # - num_ctx: the context window. 4096 may truncate input if you
            #   raise ARTICLES_PER_SOURCE (below) or the feeds return longer
            #   summaries. Raise to 8192+ if you see truncated/incomplete
            #   AI output.
            'num_gpu': 999,
            'num_ctx': 4096
    }
)

    # Add this source's summary to the overall digest (with a blank line between sources)
    final_ai_summary += response['message']['content'].strip() + "\n\n"

# ==========================================
# 4. ASSEMBLE THE EMAIL AND SEND IT
# ==========================================
final_email_body = f"DAILY AI NEWS DIGEST - {datetime.date.today()}\n"
# Combine AI Summary with Direct Links
final_email_body += "="*50 + "\n\n"
final_email_body += final_ai_summary.strip() + "\n\n"
final_email_body += "="*50 + "\n\n"
final_email_body += email_links_section

# Save locally to backup file (relative "output" folder instead of a personal Windows path)
date_str = datetime.datetime.now().strftime("%Y-%m-%d")
os.makedirs("output", exist_ok=True)
backup_file = f"output/Summary_{date_str}.txt"
with open(backup_file, "w", encoding="utf-8") as f:
    f.write(final_email_body)

msg = MIMEMultipart()
msg['From'] = SENDER_EMAIL
msg['To'] = ", ".join(RECIPIENTS)
msg['Subject'] = f"Daily AI News Digest ({datetime.date.today()})"

msg.attach(MIMEText(final_email_body, 'plain', 'utf-8'))

try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(SENDER_EMAIL, RECIPIENTS, msg.as_string())
    server.quit()
    print("Email sent successfully!")
except Exception as e:
    print(f"Failed to send email: {e}")
print("\nDigest complete!")
