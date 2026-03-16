# AI Web Security Scanner API

AI Web Security Scanner API is a portfolio-grade Python backend that scans a target URL for common HTTP security headers and returns a frontend-friendly report.

## Why This Project Exists

This project is designed as a practical backend sample for a security-focused product. It demonstrates:

- FastAPI-based API design
- clear separation between routes, services, models, and scoring logic
- safe outbound HTTP access with `httpx`
- environment-driven deployment setup for frontend integration
- a clean base for a future AI-generated security report feature

There is no database yet, and there is no AI integration yet by design.

## What It Does

- accepts `POST /scan` with a target URL
- validates input and blocks localhost-style targets
- fetches remote headers using `HEAD` first and `GET` as fallback
- analyzes six common security headers
- returns a score, rank, per-header report, and missing header list
- exposes `GET /health` for runtime checks

## Local Setup

Requirements:

- Python 3.11+

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the API locally:

```bash
uvicorn app.main:app --reload
```

The API will typically be available at `http://127.0.0.1:8000`.

## Run Tests

```bash
python3 -m pytest
```

## Environment Variables

`ALLOWED_ORIGINS`

- comma-separated list of browser origins allowed to call this API
- example:

```bash
ALLOWED_ORIGINS=https://your-frontend.netlify.app,http://localhost:5173
```

If you deploy a Netlify frontend, include its production origin here.

## Netlify Frontend Integration

The Netlify frontend is expected to call this backend directly over HTTPS.

Example browser request flow:

- frontend origin: `https://your-frontend.netlify.app`
- backend origin: `https://your-vercel-backend.vercel.app`
- backend `ALLOWED_ORIGINS` should include the Netlify frontend origin

Example fetch call from the frontend:

```js
await fetch("https://your-vercel-backend.vercel.app/scan", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    url: "https://example.com",
  }),
});
```

## Error Response Shape

Validation errors return `400`:

```json
{
  "error": {
    "code": "invalid_request",
    "message": "Request validation failed.",
    "details": [
      {
        "field": "url",
        "message": "Value error, URL scheme must be http or https."
      }
    ]
  }
}
```

Upstream fetch failures return `502`:

```json
{
  "error": {
    "code": "upstream_request_failed",
    "message": "Unable to retrieve security headers from the target URL."
  }
}
```

## Example curl Requests

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Scan a URL:

```bash
curl -X POST http://127.0.0.1:8000/scan \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
```

## Vercel Deployment Note

This repository includes:

- `api/index.py` as the Vercel ASGI entrypoint
- `vercel.json` for routing all requests to that entrypoint

On Vercel, set `ALLOWED_ORIGINS` to your Netlify frontend origin and deploy the repository as a Python project.
