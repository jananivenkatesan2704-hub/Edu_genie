# EduGenie – Gemini Powered Learning Assistant

A dark, responsive AI learning app: **Ask AI**, **Explain Concept**, **Generate Quiz**, **Learning Path** and **Summarize**.
Python FastAPI backend + Google Gemini (`google-genai`) + plain HTML/CSS/JS. No Node.js, React or database.

## Structure
```
EduGenie/
├── backend/        main.py, requirements.txt
├── frontend/       index.html, style.css, script.js
├── .env.example
├── .gitignore
└── README.md
```

## Setup
1. Get a free API key at https://aistudio.google.com/apikey
2. From the `EduGenie/` folder, create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```
3. Create your `.env`:
   ```bash
   cp .env.example .env             # Windows: copy .env.example .env
   ```
   Then edit `.env`:
   ```
   GEMINI_API_KEY=your_real_key
   GEMINI_MODEL=gemini-2.5-flash
   ```

## Run
From the `EduGenie/` folder (the project root):
```bash
uvicorn backend.main:app --reload
```
Open http://127.0.0.1:8000. Interactive API docs: http://127.0.0.1:8000/docs

## API
| Method | Path | Body |
|---|---|---|
| GET | `/api/health` | – |
| POST | `/api/ask` | `{"question": "..."}` |
| POST | `/api/explain` | `{"concept": "..."}` |
| POST | `/api/quiz` | `{"topic": "...", "num_questions": 3\|5\|7\|10, "difficulty": "Easy\|Medium\|Hard"}` |
| POST | `/api/learning-path` | `{"topic": "...", "level": "Beginner\|Intermediate\|Advanced", "duration": "8 weeks"}` |
| POST | `/api/summarize` | `{"text": "..."}` |

Every POST returns `{"result": "<markdown>", "model": "..."}`.

## Security
The API key is read only on the server from `.env` and is never sent to the browser. `.env` is git-ignored.

## Troubleshooting
- **Red dot in the header / "GEMINI_API_KEY is not set"**: check `.env` is in the project root, then restart the server.
- **401 error**: the key is invalid. **429 error**: rate limit reached; wait and retry.
- **`ModuleNotFoundError: backend`**: run `uvicorn` from the project root, not from inside `backend/`.
