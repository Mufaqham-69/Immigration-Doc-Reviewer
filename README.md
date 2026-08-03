# Casefile — Immigration Document & Visa Eligibility Reviewer

Concept 7 from your catalog, built out. An immigration law firm uploads client
documents (passports, I-797 notices, employment letters, degree certificates...),
the agent OCRs and classifies each one, cross-references the full set against
the visa category's requirements, and hands the attorney a one-page briefing:
a timeline, a flagged checklist, and a plain-language summary — not a legal
opinion, a head start on the manual review.

## What's actually here

- **Backend** (`/backend`) — FastAPI + Celery/Redis + Postgres. The agent
  pipeline lives in `app/services/`:
  - `extraction.py` — OCR + structured field extraction per document
  - `eligibility_engine.py` — cross-references extracted fields against
    `app/visa_rules/rules.py`, runs deterministic checks (missing docs,
    expired documents, low-confidence extractions), then uses the LLM only
    to write the timeline narrative and attorney briefing. **This split
    matters** — rules engine for anything that must never hallucinate,
    LLM for synthesis only.
  - `app/core/llm_router.py` — provider-agnostic LLM client (Mistral +
    Gemini). Every other 20-concept build reuses this file unchanged.
- **Frontend** (`/frontend`) — Next.js 14 + Tailwind. Landing/pricing pages,
  auth, a case dashboard, and the case detail view with the briefing.
- **Billing** — Stripe Checkout + webhook, gates document processing behind
  an active subscription (`app/api/deps.py::require_active_subscription`).
- **Docker Compose** — one command brings up Postgres, Redis, the API, the
  Celery worker, and the frontend together.

## Running it locally

1. `cp backend/.env.example backend/.env` and fill in:
   - `MISTRAL_API_KEY` — free tier at https://console.mistral.ai (used first;
     it's EU-hosted, which matters for passports/personal documents)
   - `GOOGLE_API_KEY` — free tier at https://aistudio.google.com (fallback)
   - Leave Stripe keys blank to start — signup/cases/uploads all work without
     billing configured; only `require_active_subscription` routes need it,
     and new orgs start in `trialing` so they're not blocked immediately.
2. `cp frontend/.env.example frontend/.env`
3. `docker compose up --build`
4. Frontend at `http://localhost:3000`, API docs at `http://localhost:8000/docs`

Without Docker: run Postgres + Redis yourself, then in `/backend`:
`pip install -r requirements.txt`, `uvicorn app.main:app --reload`, and in a
second terminal `celery -A app.workers.celery_app worker --loglevel=info`.
In `/frontend`: `npm install && npm run dev`.

## Wiring up Stripe (when you're ready to charge)

1. Create a $100/month recurring price in the Stripe dashboard, put its ID
   in `STRIPE_PRICE_ID_STANDARD`.
2. Point a webhook at `https://your-api-domain/api/billing/webhook` for
   `checkout.session.completed`, `customer.subscription.updated`, and
   `customer.subscription.deleted`. Put the signing secret in
   `STRIPE_WEBHOOK_SECRET`.
3. The frontend's "Start free" flow creates an account first; add a
   "Add billing" button that calls `api.createCheckoutSession()` and
   redirects to `checkout_url` once you want to convert trial orgs.

## Deploying (zero/near-zero cost to start)

- **Frontend** → Vercel. Point it at `/frontend`, set `NEXT_PUBLIC_API_URL`
  to your deployed API URL.
- **API + worker** → Railway or Render, free tier. Two services from the
  same repo: one running the Dockerfile's default `uvicorn` command, one
  overriding the command to `celery -A app.workers.celery_app worker`.
  Both need the same `.env` values, plus `DATABASE_URL`/`REDIS_URL` pointed
  at whatever Postgres/Redis add-on you provision there (Railway gives you
  both as one-click add-ons on the free tier).
- **File storage** — local disk works until you have more than one API
  instance. `app/services/storage.py` is the only file to touch when you
  move to S3/Cloudflare R2 — nothing else references the filesystem
  directly.

## Before your first real client's documents touch this

This is a working MVP, not a compliance-audited legal-document handler.
Before onboarding a paying firm:
- Add Alembic migrations (the app currently does `create_all` on startup —
  fine for one dev, not for schema changes against real data)
- Add encryption at rest for the uploads volume/bucket — these are passports
  and immigration records
- Add a data retention / deletion policy and put it in your ToS — this is
  the reason Mistral (EU-hosted) is the default provider over Gemini
- Add virus/malware scanning on upload before documents hit the OCR pipeline
- Add audit logging on who viewed/downloaded which document (law firms will
  ask about this in due diligence)
- Get real attorney feedback on 5-10 pilot cases before charging anyone —
  the `visa_rules/rules.py` rule packs are a starting point, not vetted by
  an actual immigration attorney yet

## Adapting this skeleton to the other 19 concepts

Everything in `app/core/`, `app/api/routes/auth.py`, `app/api/routes/billing.py`,
and the Docker/deploy setup is concept-agnostic — reuse it as-is. What
changes per concept is small and localized:

| File | What changes for a new concept |
|---|---|
| `app/db/models.py` | Swap `Case`/`Document`/`Flag` for that concept's entities (e.g. for the RFP Responder: `RFP`, `Question`, `DraftAnswer`) |
| `app/schemas/*.py` | New Pydantic schema for that concept's structured output — this is where most of your actual design work goes |
| `app/services/extraction.py` equivalent | Same OCR/extraction pattern, different prompt + schema |
| `app/services/eligibility_engine.py` equivalent | Same "deterministic checks + LLM synthesis" pattern, different rules |
| `app/visa_rules/rules.py` equivalent | Whatever domain rule pack that concept needs (pricing tables, compliance checklists, material cost databases) |
| `app/core/llm_router.py` | Change `DEFAULT_LLM_PROVIDER` / add a provider if that concept's doc recommends Groq or Cerebras instead |
| Frontend pages | Swap the case-detail view's content, keep auth/dashboard/pricing shells |

Concepts 1 (RFP Responder) and 6 (Construction Takeoff) are the next-closest
fits to this exact pattern — same "ingest documents → extract structured
data → cross-reference against a rule set → synthesize a summary" shape.
Concept 9 (Async Standup Agent) and Concept 10 (Review Responder) are
webhook-triggered rather than upload-triggered, so they'd replace the
`documents.py` upload route with a webhook receiver but keep everything else.
