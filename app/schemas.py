from pydantic import BaseModel, Field

class RAGQueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    days: int = Field(default=20, ge=1, le=365)

class IncidentPublic(BaseModel):
    incident_id: int
    incident_date: str
    parish: str
    incident_type: str
    description: str
    photo_ids: list[int]

class PhotoPublic(BaseModel):
    photo_id: int
    incident_id: int
    caption: str

class RAGQueryResponse(BaseModel):
    answer: str
    parish_scope: str
    days: int
    incidents: list[IncidentPublic]
    evidence_incident_ids: list[int]
    provider: str
    model: str
    usage: dict

class UsagePublic(BaseModel):
    daily_requests_used: int
    daily_request_limit: int
    monthly_requests_used: int
    monthly_request_limit: int
    daily_input_tokens_reserved: int
    daily_input_token_limit: int
    monthly_input_tokens_reserved: int
    monthly_input_token_limit: int
    max_input_tokens_per_request: int
    max_output_tokens_per_request: int
