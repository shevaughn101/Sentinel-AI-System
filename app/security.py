from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlmodel import Session, select
from app.models import Incident, Officer, Photo, ReportChunk

def authorized_incidents(session: Session, officer: Officer, days: int):
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    return list(session.exec(select(Incident).where(
        Incident.parish == officer.parish,
        Incident.incident_date >= start,
        Incident.incident_date <= now
    ).order_by(Incident.incident_date.desc())).all())

def get_authorized_incident(session: Session, officer: Officer, incident_id: int):
    incident = session.get(Incident, incident_id)
    if incident is None or incident.parish != officer.parish:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

def get_authorized_photo(session: Session, officer: Officer, photo_id: int):
    photo = session.get(Photo, photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")
    get_authorized_incident(session, officer, photo.incident_id)
    return photo

def authorized_chunks(session: Session, officer: Officer, days: int):
    ids = [i.incident_id for i in authorized_incidents(session, officer, days)]
    if not ids:
        return []
    return list(session.exec(select(ReportChunk).where(
        ReportChunk.parish == officer.parish,
        ReportChunk.incident_id.in_(ids)
    )).all())
