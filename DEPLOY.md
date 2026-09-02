# Deploying der02

## Recommended: Streamlit Community Cloud (free)

Streamlit Community Cloud is the official free hosting for Streamlit apps
and supports this project out of the box.

**Setup (5 minutes):**

1. Go to <https://share.streamlit.io> and sign in with the GitHub
   account that owns `j4yop/der02`.
2. Click **New app**.
3. Repository: `j4yop/der02`
4. Branch: `main`
5. Main file path: `app.py`
6. App URL: pick a subdomain (e.g. `der02-threat-zones`)
7. Click **Deploy**.

The first build takes 1–2 minutes (installs `requirements.txt` and starts
the Streamlit server). After that, every push to `main` triggers a
redeploy automatically.

**What the platform reads:**

- `requirements.txt` — pinned Python deps.
- `.streamlit/config.toml` — theme + server config.
- `app.py` — entry point.
- `packages.txt` (optional, system deps — not needed for this app).

**Secrets:** None required for der02.

## Why not Vercel?

Vercel supports Python via serverless functions (FastAPI, Flask,
Django) but **does not officially support Streamlit**. Streamlit uses
WebSockets and long-lived state, which don't fit the serverless
function model. If you specifically need Vercel, the path is:

1. Rewrite `app.py` as a FastAPI app that serves a static HTML/JS
   frontend.
2. Replace `streamlit-folium` with a plain Leaflet frontend.
3. Reimplement the slider state via URL query params + a JSON API.

This is a substantial rewrite. **Streamlit Community Cloud is the
right choice for this app.**

## Alternative: Docker to any PaaS

If you need private hosting, the standard pattern is:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Push to a registry (Docker Hub, GHCR) and deploy to:

- **Render.com** — free tier for static + web services, supports Docker.
- **Fly.io** — free allowance, supports `fly launch` for Streamlit.
- **Railway.app** — pay-as-you-go, simple Docker deploy.
- **Hetzner / DigitalOcean / any VPS** — full control, $5–10/month.

## Verifying the deploy

After deploying to Streamlit Community Cloud:

1. Open the app URL.
2. Default scenario (1000 m³ propane, no wind) should show three
   bands around the source.
3. Move the wind speed slider to 15 m/s — zones should elongate
   downwind.
4. Click **Download map HTML** and verify the file opens in a browser
   with a working map.

## CI status

The repo has a GitHub Actions CI (`.github/workflows/ci.yml`) that runs
`pytest` and `ruff` on every push. The Streamlit Community Cloud
build is independent of CI; CI failures won't block a deploy.

## Custom domain

Streamlit Community Cloud supports custom domains on paid plans.
Otherwise, the app is hosted at `<subdomain>.streamlit.app`.
