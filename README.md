# Taniksha Datar — Portfolio

Personal portfolio with a built-in **multi-agent assistant**. The site is a normal, fully readable portfolio; the
"Ask my agent" section lets visitors ask questions or paste a job description for a cited, honest fit check.

```
frontend/  (repo root)   React + Vite + Tailwind v4   → Render static site
backend/                 FastAPI + LangGraph           → Render
content/portfolio.json   single source of truth for the site AND the agent
```

## The agent

```
router ──question──▶ retriever ──▶ answerer ─────┐
   │ ──job_fit────▶ extractor ──▶ fit_analyst ───┼─▶ citation_check ─▶ response
   │ ──contact────▶ contact_drafter ─────────────┤
   └ ──off_topic──▶ guardrail ───────────────────┘
```

- **Router** classifies the message (structured output) and picks a specialist.
- **Retriever** runs BM25 over chunks of `content/portfolio.json`; every chunk id is a DOM id on the page.
- **Answerer** streams a grounded answer with inline `[chunk-id]` citations, and abstains when unsupported.
- **Extractor → Fit analyst** pulls requirements from a job description, retrieves evidence per requirement and
  rates each as strong / partial / gap.
- **Citation check** is deterministic: it strips citations that don't point at retrieved context and downgrades
  fit claims left without evidence.
- Node start/finish events stream to the browser over SSE, which animates the graph and the trace.

Without an API key the backend runs in **demo mode**, a rule-based stand-in for the model, so everything works
locally and in tests.

## Run locally

```bash
# frontend
npm install
npm run dev                       # http://localhost:5173

# backend (in another terminal)
cd backend
uv venv --python 3.11 .venv && uv pip install --python .venv -r requirements.txt pytest httpx
cp .env.example .env              # add OPENROUTER_API_KEY, or leave empty for demo mode
.venv/Scripts/python -m uvicorn app.main:app --reload --env-file .env   # http://localhost:8000
.venv/Scripts/python -m pytest -q # graph tests + retrieval regression suite
```

(On macOS/Linux use `.venv/bin/python`.)

## Deploy (free, all on Render)

`render.yaml` is a Render Blueprint that creates both services:

- **taniksha-portfolio**: static site (the React app) served from Render's CDN; never sleeps.
- **taniksha-portfolio-agent**: the FastAPI agent; free instances sleep after ~15 idle minutes and take about a
  minute to wake (the site shows Nimbus "waking up" meanwhile).

1. Render → **New → Blueprint** → pick this repo.
2. Fill in `GROQ_API_KEY` (primary, free: https://console.groq.com/keys) and `OPENROUTER_API_KEY` (automatic backup).
   Set `ALLOWED_ORIGINS` to `*` for the first deploy.
3. Once both are live, set the agent's `ALLOWED_ORIGINS` to the static site's URL
   (e.g. `https://taniksha-portfolio.onrender.com`).

The site's `VITE_AGENT_URL` is filled in automatically from the agent service. Every push to `main` redeploys both.
Rate limits (`RATE_LIMIT_PER_IP`, `RATE_LIMIT_DAILY`) keep usage inside the free model quotas.

## Editing content

Edit `content/portfolio.json`; the site and the agent both read it. Put your resume at `public/resume.pdf`.
