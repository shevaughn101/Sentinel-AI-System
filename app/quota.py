from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlmodel import Session, select
from app.config import settings
from app.models import Officer, UsageEvent

def estimate_tokens(text: str) -> int:
    # Rough preflight estimate; real provider tokenization may differ.
    return max(1, (len(text) + 2) // 3)

def period_rows(session: Session, officer_id: int, start: datetime, end: datetime):
    return list(session.exec(select(UsageEvent).where(
        UsageEvent.officer_id == officer_id,
        UsageEvent.created_at >= start,
        UsageEvent.created_at < end
    )).all())

def blocked(message: str):
    raise HTTPException(status_code=429, detail={
        "code": "FREE_TIER_LIMIT_REACHED",
        "message": message,
        "action": "Try again after the quota window resets or reduce the question/date range."
    })

def reserve_quota(session: Session, officer: Officer, prompt: str, model: str):
    now = datetime.now(timezone.utc)
    estimate = estimate_tokens(prompt)
    if estimate > settings.max_input_tokens_per_request:
        blocked(f"Estimated input ({estimate} tokens) exceeds the per-request cap of {settings.max_input_tokens_per_request}.")
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_end = month_start.replace(year=month_start.year + 1, month=1) if month_start.month == 12 else month_start.replace(month=month_start.month + 1)
    daily = period_rows(session, officer.officer_id, day_start, day_end)
    monthly = period_rows(session, officer.officer_id, month_start, month_end)
    if len(daily) >= settings.free_daily_request_cap:
        blocked("Your application's daily free-tier request allowance is finished.")
    if len(monthly) >= settings.free_monthly_request_cap:
        blocked("Your application's monthly free-tier request allowance is finished.")
    if sum(x.estimated_input_tokens for x in daily) + estimate > settings.free_daily_input_token_cap:
        blocked("This request would exceed the daily input-token allowance.")
    if sum(x.estimated_input_tokens for x in monthly) + estimate > settings.free_monthly_input_token_cap:
        blocked("This request would exceed the monthly input-token allowance.")
    row = UsageEvent(officer_id=officer.officer_id, created_at=now, status="reserved",
                     estimated_input_tokens=estimate, reserved_output_tokens=settings.max_output_tokens, model=model)
    session.add(row)
    session.commit()
    session.refresh(row)
    return row

def finish_quota(session: Session, row: UsageEvent, status: str, input_tokens=None, output_tokens=None):
    row.status = status
    row.actual_input_tokens = input_tokens
    row.actual_output_tokens = output_tokens
    session.add(row)
    session.commit()

def usage_summary(session: Session, officer: Officer):
    now = datetime.now(timezone.utc)
    ds = now.replace(hour=0, minute=0, second=0, microsecond=0)
    de = ds + timedelta(days=1)
    ms = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    me = ms.replace(year=ms.year + 1, month=1) if ms.month == 12 else ms.replace(month=ms.month + 1)
    day = period_rows(session, officer.officer_id, ds, de)
    month = period_rows(session, officer.officer_id, ms, me)
    return {
        "daily_requests_used": len(day), "daily_request_limit": settings.free_daily_request_cap,
        "monthly_requests_used": len(month), "monthly_request_limit": settings.free_monthly_request_cap,
        "daily_input_tokens_reserved": sum(x.estimated_input_tokens for x in day),
        "daily_input_token_limit": settings.free_daily_input_token_cap,
        "monthly_input_tokens_reserved": sum(x.estimated_input_tokens for x in month),
        "monthly_input_token_limit": settings.free_monthly_input_token_cap,
        "max_input_tokens_per_request": settings.max_input_tokens_per_request,
        "max_output_tokens_per_request": settings.max_output_tokens,
    }
