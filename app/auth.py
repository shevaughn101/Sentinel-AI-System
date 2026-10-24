from fastapi import HTTPException
from sqlmodel import Session, select
from app.models import Officer

def get_current_officer(session: Session, dev_officer_id: int | None) -> Officer:
    if dev_officer_id is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    officer = session.exec(select(Officer).where(
        Officer.officer_id == dev_officer_id, Officer.active == True
    )).first()
    if officer is None:
        raise HTTPException(status_code=401, detail="Invalid development identity")
    return officer
