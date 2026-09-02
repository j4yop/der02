# Deploying der02

The project ships with two UIs and three deploy targets.

| UI | Tech | Best deploy target |
|---|---|---|
| `streamlit_app.py` | Streamlit | [Streamlit Community Cloud](https://share.streamlit.io) (free) |
| `app.py` + `public/index.html` | FastAPI + static HTML/JS | [Vercel](https://vercel.com) (free) |
| Library only (`src/der02/`) | Python | PyPI (`pip install der02`) |

## Vercel (recommended for a public web demo)

The FastAPI backend (`app.py`) + static frontend (`public/index.html`)
deploys to Vercel in one click. Vercel auto-detects the FastAPI
`app` instance and serves the `public/` directory as static files.

**Setup (5 minutes):**

1. Go to <https://vercel.com/signup> and create an account.
2. Click **Add New Project** → import `j4yop/der02` from GitHub.
3. Vercel auto-detects the Python framework. Confirm:
   - **Framework Preset:** FastAPI
   - **Build Command:** (leave blank, Vercel auto-detects)
   - **Output Directory:** (leave blank, Vercel uses the project root)
4. Click **Deploy**.

The first build takes 2–3 minutes (installs `requirements.txt` and
compiles the FastAPI function). After that, every push to `main`
triggers a redeploy.

**What you'll get:**

- `https://<your-project>.vercel.app/` — the static HTML frontend.
- `https://<your-project>.vercel.app/api/health` — JSON health check.
- `https://<your-project>.vercel.app/docs` — FastAPI's auto-generated
  interactive API documentation (try the endpoints in the browser).
- `https://<your-project>.vercel.app/api/fuels` — JSON list of fuels.
- `https://<your-project>.vercel.app/api/zones` (POST) — compute zones.

**What Vercel reads:**

- `app.py` — FastAPI entrypoint. Vercel auto-detects the `app` instance.
  via `[tool.vercel] entrypoint = "api:app"` in `pyproject.toml`.
- `public/` — static files served at the matching URL paths.
- `requirements.txt` — Python deps (FastAPI, pydantic, uvicorn, der02 deps).
- `pyproject.toml` — alt dependency declaration (Vercel reads this too).
- `vercel.json` — function config (maxDuration, excludeFiles).

**Manual steps you need to do:**

1. **Create a Vercel account** at <https://vercel.com/signup>.
2. **Connect your GitHub account** so Vercel can import `j4yop/der02`.
3. **Click "Deploy"** on the import page.
4. **Wait for the first build** to finish (~2–3 min).
5. **Open the URL** Vercel gives you.

I cannot do these steps for you (Vercel requires browser-based
authentication and your account). Everything else (the FastAPI
backend, the static frontend, the vercel.json config) is already
committed and ready to deploy.

**Free tier limits (Vercel Hobby):**

- 100 GB-hours of function execution per month
- 100 GB egress per month
- 10s max function execution time (default; we set 60s in
  `vercel.json` which requires Pro — for Hobby, 10s is enough for
  a typical compute)

If a single request takes >10s, the function times out. For der02,
that means very high-resolution grids (50 m over a 5 km box → ~10,000
nodes, which can take 5–8s in cold-start conditions). The default
100 m resolution over a 4 km box is well under 10s.

## Streamlit Community Cloud (alternative)

If you'd rather use the Streamlit UI, see the previous deployment
instructions. The Streamlit app uses WebSockets and persistent state
which Vercel doesn't support.

## Docker (for self-hosting)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Then deploy to Render.com, Fly.io, Railway, or any VPS.

## Verifying the deploy

After deploying:

- `GET /` returns the HTML frontend.
- `GET /api/health` returns `{"status": "ok", "version": "0.2.0"}`.
- `GET /docs` shows the FastAPI interactive docs.
- The frontend sliders should compute zones and render the map.

## CI status

The repo has a GitHub Actions CI (`.github/workflows/ci.yml`) that
runs `pytest` and `ruff` on every push/PR. Vercel ignores CI
failures (deploy happens anyway) but you can require CI to pass
via branch protection rules.
