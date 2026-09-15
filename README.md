# Daily News AI Digest

An AI-powered news aggregation tool that collects articles from multiple RSS
feeds, summarizes them, and translates the summaries into another language
using a local AI model (via [Ollama](https://ollama.com)) — Vietnamese by
default, but configurable to any language the model supports. The digest is
emailed automatically and keeps direct links back to every original article.

## What it does

1. Fetches the latest articles from a configurable list of RSS feeds
   (international and Vietnamese news, tech, and science sources).
2. Sends each source's articles to a local Ollama model, which summarizes and
   translates them into the configured target language (Vietnamese by
   default).
3. Assembles a single daily digest with the AI summaries followed by a
   section of direct links to every original article.
4. Saves a local backup copy of the digest and emails it to a list of
   recipients.

## Features

- Works with any RSS/Atom feed — just add an entry to the `SOURCES`
  dictionary in `daily_news.py`.
- Runs entirely with a local LLM through Ollama — no article content is sent
  to a third-party API.
- Always includes the original source name and article link, so readers can
  verify the AI summary against the source.
- Email credentials and recipients are set as plain variables at the top of
  `daily_news.py`, kept out of the published copy of this repo (see
  Configuration below).

## Technologies used

- Python 3.10+
- [feedparser](https://pypi.org/project/feedparser/) — RSS/Atom parsing
- [Ollama](https://ollama.com) Python client — local LLM inference
- `smtplib` (standard library) — sending email over SMTP

## Requirements

Before running the script, make sure you have the following installed:

1. **Python 3.10 or newer** — [download here](https://www.python.org/downloads/)
2. **Ollama** — [download here](https://ollama.com/download), then pull a
   model to use (the default configuration uses `gemma2`):
   ```bash
   ollama pull gemma2
   ```
   Ollama needs to be running in the background whenever you run the script.
3. **Python packages** listed in `requirements.txt` — installed via `pip` in
   the Installation step below.
4. **An email account that supports SMTP** to send the digest (the defaults
   are set up for Gmail with an App Password — no extra software needed,
   just an account).

## Installation

```bash
git clone https://github.com/phongtt2st/daily-news-ai.git
cd daily-news-ai
pip install -r requirements.txt
```

(See the Requirements section above for what needs to be installed first.)

## Configuration

Open `daily_news.py` and fill in the settings near the top of the file:

```python
SENDER_EMAIL = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"
RECIPIENTS = ["recipient1@example.com", "recipient2@example.com"]
```

- `SENDER_EMAIL` / `SENDER_PASSWORD` — the account the digest is sent from.
  For Gmail, generate an App Password at
  <https://myaccount.google.com/apppasswords> — do not use your regular
  account password.
- `RECIPIENTS` — the list of addresses that receive the digest.

**Keeping your credentials private:** this repository's copy of
`daily_news.py` intentionally contains placeholder values, not real
credentials. If you keep a separate local copy with your real
`SENDER_EMAIL`/`SENDER_PASSWORD` to actually run the script, make sure that
copy is never committed or pushed to GitHub — only publish a copy with the
placeholder values shown above.

(Optional) Edit the `SOURCES` dictionary further down in `daily_news.py` to
add, remove, or reorder RSS feeds, or change `ARTICLES_PER_SOURCE` to pull
more or fewer articles per feed.

## Running

```bash
python daily_news.py
```

This fetches the configured feeds, generates the AI digest, saves a copy in
the `output/` folder, and emails it to the addresses in `RECIPIENTS`. To run
it automatically every day, schedule it with `cron` (Linux/macOS) or Task
Scheduler (Windows).

Example cron entry to run every morning at 7 AM:

```
0 7 * * * cd /path/to/daily-news-ai && /usr/bin/python3 daily_news.py
```

## Configuring the AI model

The script calls a locally running Ollama server, so no API key is required.
Any model available in Ollama can be used by changing the `model=` value in
the `ollama.chat(...)` call inside `daily_news.py` — just make sure it's
pulled first (`ollama pull <model>`). Larger models produce better
summaries/translations but are slower and need more memory/GPU resources;
the `num_gpu` and `num_ctx` options passed to `ollama.chat(...)` can be
adjusted to match your hardware.

### Customizing how the AI summarizes/translates

**Output language:** set `TARGET_LANGUAGE` near the top of `daily_news.py`.
It defaults to `"Vietnamese"`, but can be changed to any language the model
supports, e.g. `"English"`, `"French"`, `"Japanese"`.

The rest of the instruction sent to the model — how long each summary should
be, what structure to follow — is defined in the `prompt` variable inside
the loop that processes each source. Edit that text directly to change the
AI's behavior further, for example:

- Shorten or lengthen the requested summary length (currently ~700 words per
  article)
- Ask for a different structure (e.g. bullet points instead of paragraphs)

No other code changes are needed — the rest of the script just sends
whatever text is in `prompt` to the model and uses the reply as-is.

## Fine-tuning notes

A few settings are worth checking before you rely on this daily:

- **Ollama must be running** locally, with the model in `model=` already
  pulled (`ollama pull gemma2` by default), before the script is run —
  otherwise the AI call fails.
- **`ARTICLES_PER_SOURCE`** (default `5`) controls how many articles are
  pulled per feed. Raising it may need a larger `num_ctx` (below) so the
  model doesn't run out of context and truncate its output.
- **`num_ctx`** (default `4096`) is the model's context window. If you see
  truncated or incomplete AI output — especially after raising
  `ARTICLES_PER_SOURCE` — raise this to `8192` or higher.
- **`num_gpu`** (default `999`) tries to push as many model layers as
  possible onto the GPU. If your machine has no or limited GPU VRAM, Ollama
  falls back to CPU automatically — this just makes it slower, not an error.
- **`TARGET_LANGUAGE`**: translation quality for less common languages may
  be weaker than for English/Vietnamese. Test on one source before running
  the full digest after changing it.
- **Gmail App Password**: `SENDER_PASSWORD` must be an
  [App Password](https://myaccount.google.com/apppasswords), not your normal
  Gmail password — Gmail rejects normal passwords over SMTP.
- **RSS feed reliability**: feeds can change format or go down without
  notice. The script won't crash on a bad feed — that source just comes back
  with an empty summary for that run.

## Limitations & known issues

- AI-generated summaries and translations may contain errors or omissions —
  always refer to the linked original article for the full, verified text.
- Only the `summary`/`description` field from each RSS feed is used as input
  for summarization; feeds that provide short or empty summaries will
  produce lower-quality output.
- This project only aggregates and links to original articles — it does not
  redistribute full copyrighted article text.
- Email sending currently supports basic SMTP with STARTTLS (e.g. Gmail App
  Passwords); OAuth2-based providers are not yet supported.

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for
details.
