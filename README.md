# AI Smart Reader — Django + Ollama (Free Local AI)

Features:
- User registration, login, logout, and per-user data isolation
- PDF upload and personal document library
- Browser PDF reader with text selection, page navigation, zoom, and reading progress
- **Local AI** for explain, examples, summaries, and questions using Ollama on your computer
- Notes, bookmarks, highlights, and reading progress saved per user/document
- Responsive interface and Django admin

## 1. Install Ollama

1. Download and install Ollama for Windows: https://ollama.com/download
2. Open PowerShell and download the default model:

```powershell
ollama pull llama3.2:3b
```

If your laptop has limited RAM, use the smaller model instead:

```powershell
ollama pull llama3.2:1b
```

If you use the 1B model, update `OLLAMA_MODEL=llama3.2:1b` in `.env`.
Ollama should be running locally at `http://127.0.0.1:11434`.

## 2. Set up the Django project on Windows

Run these commands from the folder that contains `manage.py`:

```powershell
py -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

If your virtual environment already exists and is active, do not recreate it; run only the install command if needed, then migrate and run the server.

Open http://127.0.0.1:8000/ and use Explain, Examples, Summarize, or Ask AI in the PDF reader. The first AI request can take a little longer while Ollama loads the model. No OpenAI API key or per-request cloud API payment is needed for the local Ollama mode.

## Configuration

In `.env`:

```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2:3b
```

For a smaller model, use `OLLAMA_MODEL=llama3.2:1b` after running `ollama pull llama3.2:1b`.

Optional: to use the paid OpenAI API instead, set `AI_PROVIDER=openai` and provide `OPENAI_API_KEY` and `OPENAI_MODEL`. Ollama is the default provider.

## Troubleshooting

- **Cannot connect to Ollama:** Open the Ollama app, then check in PowerShell with `ollama --version` and `ollama list`.
- **Model not found:** Run `ollama pull llama3.2:3b` (or the model name set in `.env`).
- **Slow response / laptop has limited RAM:** Use `llama3.2:1b` and change `OLLAMA_MODEL` in `.env`.
- **Port changed:** Set `OLLAMA_BASE_URL` to your Ollama server URL.

Uploaded documents are private to their owner. Local development uses SQLite and local media storage. Before public deployment, configure a strong `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`, HTTPS, secure storage, and a production database. Do not commit `.env` or API keys to GitHub.
