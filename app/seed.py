from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select
from app.models import Officer, Incident, Photo, ReportChunk

def seed_demo_data(session: Session):
    if session.exec(select(Officer)).first():
        return
    session.add_all([
        Officer(officer_id=101, name="Officer A (fictional)", parish="Manchester"),
        Officer(officer_id=202, name="Officer B (fictional)", parish="Clarendon"),
    ])
    now = datetime.now(timezone.utc)
    incidents = [
        Incident(incident_id=1001, parish="Manchester", incident_date=now-timedelta(days=3), incident_type="Road collision", description="A collision was reported during heavy rain.", report_text="Fictional report: heavy rainfall was noted near the collision. Rain was a possible contributing factor, not a confirmed cause."),
        Incident(incident_id=1002, parish="Manchester", incident_date=now-timedelta(days=8), incident_type="Suspected DUI", description="A driver was investigated for suspected impaired driving.", report_text="Fictional report: suspected impaired-driving investigation. This does not establish guilt or a final legal outcome."),
        Incident(incident_id=1003, parish="Clarendon", incident_date=now-timedelta(days=2), incident_type="Road collision", description="A collision was reported after rainfall.", report_text="Fictional Clarendon report: a collision was recorded after rainfall; causation was not established."),
        Incident(incident_id=1004, parish="Clarendon", incident_date=now-timedelta(days=12), incident_type="Suspected DUI", description="A driver was investigated for suspected impaired driving.", report_text="Fictional sample suspected DUI report in Clarendon."),
        Incident(incident_id=1005, parish="Manchester", incident_date=now-timedelta(days=35), incident_type="Flooding", description="A flooded roadway was reported.", report_text="Fictional report outside a 20-day search window."),
    ]
    session.add_all(incidents)
    session.flush()
    session.add_all([
        Photo(photo_id=5001, incident_id=1001, storage_key="fictional/manchester/1001/photo-1.jpg", caption="Fictional roadway after rainfall"),
        Photo(photo_id=5002, incident_id=1002, storage_key="fictional/manchester/1002/photo-1.jpg", caption="Fictional vehicle inspection"),
        Photo(photo_id=5003, incident_id=1003, storage_key="fictional/clarendon/1003/photo-1.jpg", caption="Fictional road scene"),
        Photo(photo_id=5004, incident_id=1004, storage_key="fictional/clarendon/1004/photo-1.jpg", caption="Fictional vehicle scene"),
    ])
    session.add_all([
        ReportChunk(incident_id=i.incident_id, parish=i.parish, text=f"{i.incident_type}. {i.description} {i.report_text}")
        for i in incidents
    ])
    session.commit()
