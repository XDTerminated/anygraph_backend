# AnyGraph Backend

## Installation

```bash
uv sync
```

## Docker

```bash
docker build -t anygraph-executor:latest docker/
```

## Environment Variables

Create `.env`:

```env
NEONDB_URL=postgresql://...
GEMINI_API_KEY=...
```

- **Neon DB**: https://neon.tech
- **Gemini**: https://aistudio.google.com/apikey

## Run

```bash
uv run fastapi dev src/main.py
```
