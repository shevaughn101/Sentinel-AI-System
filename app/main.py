from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from sqlmodel import Session, select
from app.auth import get_current_officer
from app.config import settings
from app.database import create_db_and_tables, get_session, engine
from app.llm import ProviderRateLimited, generate_answer
from app.models import Incident, Officer, Photo
from app.quota import finish_quota, reserve_quota, usage_summary
from app.retrieval import hybrid_search
from app.schemas import IncidentPublic, PhotoPublic, RAGQueryRequest, RAGQueryResponse, UsagePublic
from app.security import authorized_incidents, get_authorized_incident, get_authorized_photo
from app.seed import seed_demo_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        seed_demo_data(session)
    yield

app = FastAPI(title="Sentinel Civic Response API", version="0.2.0",
              description="SQLModel-backed jurisdiction-aware RAG prototype with fictional data.",
              lifespan=lifespan)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        seed_demo_data(session)
    yield

# Add these 3 lines right here so pytest initializes the database on import:
create_db_and_tables()
with Session(engine) as session:
    seed_demo_data(session)
def current_officer(session: Session = Depends(get_session),
                    x_dev_officer_id: int | None = Header(default=None, alias="X-Dev-Officer-ID")):
    return get_current_officer(session, x_dev_officer_id)

def incident_public(session: Session, incident: Incident):
    photos = session.exec(select(Photo).where(Photo.incident_id == incident.incident_id)).all()
    return IncidentPublic(
        incident_id=incident.incident_id, incident_date=incident.incident_date.isoformat(),
        parish=incident.parish, incident_type=incident.incident_type,
        description=incident.description, photo_ids=[p.photo_id for p in photos if p.photo_id is not None]
    )

@app.get("/health")
def health():
    return {"status": "ok", "llm": "groq" if settings.groq_api_key else "local-demo"}

@app.get("/officers/me")
def me(officer: Officer = Depends(current_officer)):
    return {"officer_id": officer.officer_id, "name": officer.name, "parish": officer.parish, "role": officer.role}

@app.get("/incidents", response_model=list[IncidentPublic])
def list_incidents(days: int = Query(default=20, ge=1, le=365),
                   session: Session = Depends(get_session),
                   officer: Officer = Depends(current_officer)):
    return [incident_public(session, x) for x in authorized_incidents(session, officer, days)]

@app.get("/incidents/{incident_id}", response_model=IncidentPublic)
def incident_detail(incident_id: int, session: Session = Depends(get_session),
                    officer: Officer = Depends(current_officer)):
    return incident_public(session, get_authorized_incident(session, officer, incident_id))

@app.get("/media/{photo_id}", response_model=PhotoPublic)
def media_detail(photo_id: int, session: Session = Depends(get_session),
                 officer: Officer = Depends(current_officer)):
    p = get_authorized_photo(session, officer, photo_id)
    # Metadata only. Production must stream the private file after re-authorizing.
    return PhotoPublic(photo_id=p.photo_id, incident_id=p.incident_id, caption=p.caption)

@app.get("/usage/me", response_model=UsagePublic)
def my_usage(session: Session = Depends(get_session), officer: Officer = Depends(current_officer)):
    return usage_summary(session, officer)

@app.post("/rag/query", response_model=RAGQueryResponse)
def rag_query(request: RAGQueryRequest, session: Session = Depends(get_session),
              officer: Officer = Depends(current_officer)):
    matches = hybrid_search(session, request.question, officer, request.days, settings.retrieval_chunks)
    evidence, seen = [], set()
    for incident, text, score in matches:
        if incident.incident_id not in seen:
            seen.add(incident.incident_id)
            evidence.append({"incident_id": incident.incident_id,
                "incident_date": incident.incident_date.date().isoformat(),
                "incident_type": incident.incident_type, "evidence": text, "score": round(score, 4)})
    preflight = request.question + "\n" + "\n".join(
        f"{x['incident_id']} {x['incident_date']} {x['incident_type']} {x['evidence']}" for x in evidence)
    reservation = reserve_quota(session, officer, preflight, settings.groq_model)
    try:
        answer = generate_answer(request.question, officer.parish, evidence)
    except ProviderRateLimited:
        finish_quota(session, reservation, "failed")
        raise HTTPException(status_code=429, detail={
            "code": "PROVIDER_RATE_LIMITED",
            "message": "The LLM provider's current rate limit has been reached; your app quota may still be available.",
            "action": "Wait for the provider's reset and check your provider dashboard."
        })
    except Exception:
        finish_quota(session, reservation, "failed")
        raise HTTPException(status_code=502, detail={"code": "LLM_PROVIDER_ERROR", "message": "The LLM provider could not complete this request."})
    finish_quota(session, reservation, "success", answer.input_tokens, answer.output_tokens)
    records = []
    for e in evidence:
        incident = session.get(Incident, e["incident_id"])
        if incident and incident.parish == officer.parish:
            records.append(incident_public(session, incident))
    return RAGQueryResponse(answer=answer.answer, parish_scope=officer.parish,
        days=request.days, incidents=records, evidence_incident_ids=[x["incident_id"] for x in evidence],
        provider=answer.provider, model=answer.model, usage=usage_summary(session, officer))
