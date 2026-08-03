from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import Case, Client, User
from app.schemas.case import CaseCreate, CaseSummaryResponse

router = APIRouter(prefix="/api/cases", tags=["cases"])


@router.post("", response_model=CaseSummaryResponse)
def create_case(payload: CaseCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    client = Client(
        organization_id=user.organization_id,
        full_name=payload.client_name,
        email=payload.client_email,
    )
    db.add(client)
    db.flush()

    case = Case(
        organization_id=user.organization_id,
        client_id=client.id,
        visa_category=payload.visa_category,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.get("", response_model=list[CaseSummaryResponse])
def list_cases(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(Case)
        .filter(Case.organization_id == user.organization_id)
        .order_by(Case.updated_at.desc())
        .all()
    )


@router.get("/{case_id}", response_model=CaseSummaryResponse)
def get_case(case_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    case = (
        db.query(Case)
        .filter(Case.id == case_id, Case.organization_id == user.organization_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case
