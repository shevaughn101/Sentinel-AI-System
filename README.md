# Sentinel Civic Response API — Stage 1

A learning starter for a jurisdiction-aware FastAPI incident-search/RAG backend.
All records are fictional. This stage is an executable security-focused prototype,
not a production law-enforcement system.

## Requirements
- Python 3.11+
- Install packages: `pip install -r requirements.txt`
- Run: `uvicorn app.main:app --reload`
- Tests: `pytest -q`
- API docs: http://127.0.0.1:8000/docs

## Development authentication warning
This starter uses `X-Dev-Officer-ID` to select a fictional officer. This is ONLY
for local development and tests. It is not authentication. Never deploy this
mechanism. Stage 2 should replace it with verified signed access tokens and
load the officer's current parish assignment from the database.

## Project structure
- `app/main.py`: FastAPI routes and dependency wiring.
- `app/auth.py`: development-only identity dependency.
- `app/data.py`: fictional officers, incidents, and photo metadata.
- `app/schemas.py`: request/response validation.
- `app/security.py`: jurisdiction checks and secure incident/photo lookup.
- `app/retrieval.py`: hybrid retrieval interface; this stage uses a deterministic
  lexical fallback so it runs without external services.
- `app/rag.py`: answer assembly grounded in retrieved records; model provider is
  intentionally not connected yet.
- `tests/test_security.py`: regression tests for cross-parish access attempts.

## Security design
1. The client never chooses the effective parish filter.
2. The authenticated identity determines the officer's parish.
3. Incident retrieval filters by parish before matching query terms.
4. Photo retrieval first checks access to the parent incident.
5. Responses only include records from the authorized parish.
6. RAG evidence is built only from the already-filtered retrieval results.

## Example
Manchester officer:
```bash
curl -H "X-Dev-Officer-ID: 101" \
  -H "Content-Type: application/json" \
  -d '{"question":"rain incidents in the last 20 days","days":20}' \
  http://127.0.0.1:8000/rag/query
```

Clarendon officer:
```bash
curl -H "X-Dev-Officer-ID: 202" \
  -H "Content-Type: application/json" \
  -d '{"question":"DUI incidents","days":20}' \
  http://127.0.0.1:8000/rag/query
```

`parish` is deliberately not a field in the request schema. Sending an extra
parish field is rejected rather than trusted.

## Next implementation stages
1. Replace development identity with JWT/OIDC authentication.
2. Move officers/incidents/media to PostgreSQL using SQLAlchemy.
3. Add PostgreSQL row-level security as defense in depth.
4. Add pgvector embeddings and hybrid SQL + vector retrieval.
5. Store photos in private object storage and issue short-lived authorized access.
6. Add audit events, rate limits, retention policies, and security review.
7. Connect a model provider only after authorization filtering is proven by tests.

## Important production safeguards
- Use least-privilege database roles and deny access by default.
- Enforce authorization for every endpoint, including exports and media.
- Re-check access before serving each photo; do not expose public object URLs.
- Do not put unauthorized records into the LLM context, prompts, caches, or logs.
- Treat retrieved report text as untrusted data, not as instructions to the model.
- Log access decisions without unnecessarily logging sensitive report content.
- Define date/timezone semantics and validate incident classification.
