from datetime import datetime, timezone
from sqlmodel import SQLModel, Field

def utcnow():
    return datetime.now(timezone.utc)

class Officer(SQLModel, table=True):
    officer_id: int = Field(primary_key=True)
    name: str
    parish: str = Field(index=True)
    role: str = "officer"
    active: bool = True

class Incident(SQLModel, table=True):
    incident_id: int | None = Field(default=None, primary_key=True)
    parish: str = Field(index=True)
    incident_date: datetime = Field(index=True)
    incident_type: str = Field(index=True)
    description: str
    report_text: str

class Photo(SQLModel, table=True):
    photo_id: int | None = Field(default=None, primary_key=True)
    incident_id: int = Field(foreign_key="incident.incident_id", index=True)
    storage_key: str
    caption: str

class ReportChunk(SQLModel, table=True):
    chunk_id: int | None = Field(default=None, primary_key=True)
    incident_id: int = Field(foreign_key="incident.incident_id", index=True)
    parish: str = Field(index=True)
    text: str

class UsageEvent(SQLModel, table=True):
    usage_id: int | None = Field(default=None, primary_key=True)
    officer_id: int = Field(index=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)
    status: str = "reserved"
    estimated_input_tokens: int
    reserved_output_tokens: int
    actual_input_tokens: int | None = None
    actual_output_tokens: int | None = None
    model: str
